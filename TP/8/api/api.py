from datetime import datetime, timezone
import logging
from fastapi import Depends, FastAPI, HTTPException, status, Request,Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import messages as Messages
from src.signer import get_signer, Signer
from src.schemas import CFPSchema, RegisterSchema, RegisterProposalSchema
from src.contractManager import get_contract_manager, ContractManager
from web3.exceptions import ContractLogicError
import re



logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger("app")

#TODO organizar el directorio, separar endpoints
app = FastAPI(title="API de Convocatoria de Propuestas (CFP) - TP 8")

#formato de respuesta personalizada para errores HTTP y validación de datos
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

# TODO ver si se pueden separar por clases los manejadores de errores, para no tener todo en api.py
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    
    # Mensaje por defecto en caso de estructura rota o campos ausentes
    api_message = Messages.MISSING_FIELD
    logging.error(f"Validation errors: validation errors: {exc.errors()}")
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        location = first_error.get("loc", [])
        error_type = first_error.get("type", "")

        # Si el error está en el cuerpo del JSON recibido
        if len(location) > 1 and location[0] == "body":
            field_name = location[1]
            
            if error_type == "missing":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": Messages.MISSING_FIELD}
                )
                
            elif field_name == "callId":
                api_message = Messages.INVALID_CALLID
            elif field_name in ["closingTime", "closing_time"]:
                api_message = Messages.INVALID_TIME_FORMAT
            elif field_name == "signature":
                api_message = Messages.INVALID_SIGNATURE
            elif field_name == "address":
                api_message = Messages.INVALID_ADDRESS
            elif field_name == "proposal":
                api_message = Messages.INVALID_PROPOSAL
            else:
                api_message = Messages.INTERNAL_ERROR

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": api_message}
    )


@app.post(
    "/create", 
    status_code=status.HTTP_201_CREATED, # Código por defecto para creación exitosa
    summary="Crea una nueva convocatoria de propuestas (CFP)",
    response_description="La convocatoria ha sido creado exitosamente en el sistema"
)

async def createFor_CFP (
    request: Request,
    payload: CFPSchema,
    manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer)):
    """
    Endpoint asíncrono para la creación de propuestas (CFP).
    """
    
    content_type = request.headers.get("content-type", "")
    
    if "application/json" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_MIMETYPE
        )

    try:
        #  Transformar la fecha a Unix timestamp (uint256)
        unix_ts = int(payload.closing_time.timestamp())
        
        if unix_ts <= int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.INVALID_CLOSING_TIME
            )

        plain_message_hex = manager.generate_hex_str_create_message(
            call_id_hex=payload.callId,
            unix_timestamp=unix_ts
        )

        try:
            emisor_address = signer.get_signer_address(
                message_hexstr=plain_message_hex,
                signature_hex=payload.signature
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.INVALID_SIGNATURE
            )

        tx_not_signed = manager.create_cfp_for(
            from_address=signer.address,
            creator_address=emisor_address,
            call_id_hex=payload.callId,
            unix_timestamp=unix_ts
        )

        tx_signed_bytes = signer.sign_transaction(tx_not_signed)

        tx_hash_hex = manager.execute_transaction(tx_signed_bytes)
        
        receipt = manager.get_transaction_receipt(tx_hash_hex)
        
            
        if receipt.get("status") != 1:
            revert_reason_cle = manager.raise_revert_reason(tx_hash_hex)
            
        
        return {"message": Messages.OK}
    
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en el Smart Contract: {cle.message}")
        error_message = manager.map_revert_reason_to_message(cle.message)
        
        if error_message in [Messages.ALREADY_CREATED, Messages.UNAUTHORIZED]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        elif error_message == Messages.INVALID_CLOSING_TIME:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=Messages.INTERNAL_ERROR)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Fallo no controlado en el flujo del endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )

@app.post(
    "/register", 
    status_code=status.HTTP_200_OK,
    summary="Permite a un usuario registrarse para crear llamados, y los autoriza de inmediato",
    response_description="El usuario ha sido registrado y autorizado exitosamente para crear llamados"
)

async def register_and_authorize_user (
    request: Request,
    payload: RegisterSchema,
    manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer)):
    """
    Permite a un usuario registrarse para crear llamados, y los autoriza de inmediato
    """
    
    content_type = request.headers.get("content-type", "")
    
    if "application/json" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_MIMETYPE
        )

    try:
        
        plain_message_hex = manager.generate_hex_str_register_message()

        try:
            emisor_address = signer.get_signer_address(
                message_hexstr=plain_message_hex,
                signature_hex=payload.signature
            )
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.INVALID_SIGNATURE
            )
            
        if emisor_address.lower() != payload.address.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=Messages.INVALID_SIGNATURE
            )
            
        tx_not_signed = manager.authorize_user(from_address=signer.address, user_address=payload.address)
        tx_signed_bytes = signer.sign_transaction(tx_not_signed)
        tx_hash_hex = manager.execute_transaction(tx_signed_bytes)
        receipt = manager.get_transaction_receipt(tx_hash_hex)
        
        if receipt.get("status") != 1:
            revert_reason_cle = manager.raise_revert_reason(tx_hash_hex)        
        
        return {"message": Messages.OK}
    
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en el Smart Contract: {cle.message}")
        error_message = manager.map_revert_reason_to_message(cle.message)
        
        if error_message in [Messages.ALREADY_AUTHORIZED]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=Messages.INTERNAL_ERROR)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Fallo no controlado en el flujo del endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )

@app.post(
    "/register-proposal", 
    status_code=status.HTTP_201_CREATED,
    summary="Permite a un usuario registrar una propuesta en un determinado llamado.Este registro es anónimo, es decir, la dirección que quedará registrada en el contrato es la utilizada por el servidor de la API.",
    response_description="La propuesta ha sido registrada exitosamente en el sistema"
)

async def register_proposal (
    request: Request,
    payload: RegisterProposalSchema,
    manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer)):
    """
    Endpoint asíncrono para el registro de propuestas en un llamado específico.
    Este registro es anónimo, es decir, la dirección que quedará registrada en el
    contrato es la utilizada por el servidor de la API. 
    """
    
    content_type = request.headers.get("content-type", "")
    
    if "application/json" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_MIMETYPE
        )

    try:
        

        tx_not_signed = manager.register_proposal(
            from_address=signer.address,
            call_id_hex=payload.callId,
            proposal_hex=payload.proposal
        )

        tx_signed_bytes = signer.sign_transaction(tx_not_signed)

        tx_hash_hex = manager.execute_transaction(tx_signed_bytes)
        
        receipt = manager.get_transaction_receipt(tx_hash_hex)
        
            
        if receipt.get("status") != 1:
            revert_reason_cle = manager.raise_revert_reason(tx_hash_hex)
            
        
        return {"message": Messages.OK}
    
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en el Smart Contract: {cle.message}")
        error_message = manager.map_revert_reason_to_message(cle.message)
        
        if error_message == Messages.ALREADY_REGISTERED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
        elif error_message == Messages.CALLID_NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=Messages.INTERNAL_ERROR)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Fallo no controlado en el flujo del endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
        
@app.get(
    "/authorized/{address}",
    status_code=status.HTTP_200_OK,
    summary="Verifica el estado de autorización de una dirección",
    response_description="Retorna si la dirección provista está autorizada o no"
)
async def check_address_authorization(
    address: str = Path(
        ...,
        description="Dirección de Ethereum a consultar",
        pattern=r"^0x[a-fA-F0-9]{40}$",
        examples=["0x3Bdd62278057288b1F486cBD775986AD042F5E4A"]
    ),
    manager: ContractManager = Depends(get_contract_manager)
):
    """
    Consulta on-chain el estado de una dirección y retorna si está autorizada para crear llamados.
    """
    try:
        logger.debug(f"Consultando estado de autorización para: {address}")
        
        is_authorized = manager.is_address_authorized(account_address=address)
        
        return {"authorized": is_authorized}

    #// except ContractLogicError as cle:
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /authorized: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
    

@app.get(
    "/calls/{call_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene los detalles de un llamado específico",
    response_description="Retorna la dirección del creador y del contrato del llamado"
)
async def get_call_by_id(
    call_id: str = Path(..., description="Hash que identifica al llamado"),
    manager: ContractManager = Depends(get_contract_manager)
):
    if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_CALLID
        )

    try:
        creator_address, cfp_address = manager.get_call_details(call_id_hex=call_id)
        
        address_zero = "0x" + "0" * 40
        if creator_address == address_zero or cfp_address == address_zero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.CALLID_NOT_FOUND
            )
            
        return {
            "creator": creator_address,
            "cfp": cfp_address
        }

    except HTTPException as http_ex:
        raise http_ex
        
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en el contrato al buscar el llamado: {cle.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /calls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
    
    
@app.get(
    "/closing-time/{call_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene la fecha y hora de cierre de un llamado",
    response_description="Retorna el closingTime en formato ISO 8601"
)
async def get_closing_time_by_id(
    call_id: str = Path(..., description="Hash que identifica al llamado"),
    manager: ContractManager = Depends(get_contract_manager)
):
    if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_CALLID
        )

    try:
        creator_address, cfp_address = manager.get_call_details(call_id_hex=call_id)
        
        address_zero = "0x" + "0" * 40
        if creator_address == address_zero or cfp_address == address_zero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.CALLID_NOT_FOUND
            )
            
        timestamp = manager.get_cfp_closing_time_by_address(cfp_address=cfp_address)
        
        iso_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        
        return {"closingTime": iso_date}
        
    except HTTPException as http_ex:
        raise http_ex
        
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en la EVM al consultar tiempo de cierre: {cle.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /closing-time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
