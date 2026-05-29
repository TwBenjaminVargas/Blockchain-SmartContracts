from datetime import datetime, timezone
import logging
from fastapi import Depends, FastAPI, HTTPException, status, Request,Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import messages as Messages
from services.signer import get_signer, Signer
from models.persistence.Call import CallState
from models.CallCreate import CallCreate
from models.UserRegister import UserRegister
from models.ProposalRegister import ProposalRegister
from services.contractManager import get_contract_manager, ContractManager
from web3.exceptions import ContractLogicError
from db.sqliteManager import DBManager, get_db_manager
import re
from models.persistence.User import UserState

import exceptions.contractManagerExceptions as contract_exceptions
import exceptions.SignerExceptions as signer_exceptions
import exceptions.databaseManagerExceptions as db_exceptions


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger("app")

app = FastAPI(title="API de Convocatoria de Propuestas (CFP) - TP 8")

#formato de respuesta personalizada para errores HTTP y validación de datos
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    # Validar mimetype solo si el método espera un body
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_MIMETYPE}
            )
        
    errors = exc.errors()
    logger.error(f"Validation errors: {errors}")
    
    if errors:
        first_error = errors[0]
        location = first_error.get("loc", [])
        error_type = first_error.get("type", "")
        
        #Prioridad máxima a los campos faltantes (missing)
        if error_type == "missing":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.MISSING_FIELD}
            )

        # Errores en parámetros de ruta (path)
        if "path" in location and "address" in location:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_ADDRESS}
            )

        # Errores específicos de formato en el cuerpo (body)
        if len(location) > 1 and location[0] == "body":
            field_name = location[1]
            
            if field_name == "callId":
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_CALLID})
            elif field_name in ["closingTime", "closing_time"] or any("closing" in str(loc).lower() for loc in location):
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_TIME_FORMAT})
            elif field_name == "signature":
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_SIGNATURE})
            elif field_name == "address":
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_ADDRESS})
            elif field_name == "proposal":
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_PROPOSAL})

        # Fallback para el formato de closing_time
        if any("closing" in str(loc).lower() for loc in location):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_TIME_FORMAT}
            )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": Messages.MISSING_FIELD}
    )


@app.post(
    "/create", 
    status_code=status.HTTP_201_CREATED,
    summary="Registra un llamado a presentación de propuestas",
    response_description="La convocatoria ha sido registrada exitosamente"
)
async def create(
    payload: CallCreate,
    manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer),
    db_manager: DBManager = Depends(get_db_manager)
):  
    try:
        try:
            calculated_call_id = manager.generate_call_id(
                title=payload.title, 
                description=payload.description
            )
        except contract_exceptions.CryptographicHashingException:
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        if payload.callId.lower() != calculated_call_id.lower():
            return JSONResponse(status_code=400, content={"message": Messages.INVALID_CALLID})
        try:
            if db_manager.existsCall(payload.callId):
                return JSONResponse(status_code=403, content={"message": Messages.ALREADY_CREATED})
        except db_exceptions.DatabaseConnectionException as sc_err:
            logger.error(f"Error de conexión con la base de datos local: {str(sc_err)}")
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})
        try:
            plain_message_hex = manager.generate_hex_str_create_message(call_id_hex=payload.callId)
        except contract_exceptions.CryptographicHashingException as e:
            logger.error(f"Error estructurando mensaje binario: {str(e)}")
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        try:
            emisor_address = signer.get_signer_address(
                message_hexstr=plain_message_hex,
                signature_hex=payload.signature
            )
        except signer_exceptions.InvalidSignatureException as ise:
            return JSONResponse(status_code=400, content={"message": Messages.INVALID_SIGNATURE})

        try:
            is_authorized = manager.is_address_authorized(emisor_address)
        except contract_exceptions.NodeRPCException as sc_err:
            logger.error(f"Error de conexión con CFPFactory: {str(sc_err)}")
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        if not is_authorized:
            return JSONResponse(status_code=403, content={"message": Messages.UNAUTHORIZED})
        
        try:
            db_manager.createPendingCall(call_id=payload.callId, title=payload.title,
                                                    description=payload.description,
                                                    signature=payload.signature,
                                                    creator_address=emisor_address)
        except db_exceptions.RecordAlreadyExistsException:
            return JSONResponse(status_code=403, content={"message": Messages.ALREADY_CREATED})
        except db_exceptions.DatabaseWriteException as db_write_err:
            logger.error(f"Error al escribir en la base de datos local: {str(db_write_err)}")
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        return {"message": Messages.OK}

    except Exception as e:
        logger.error(f"Fallo no controlado en el flujo del endpoint: {str(e)}")
        return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})
                            
                            
@app.post(
    "/register",
    status_code=status.HTTP_200_OK,
    summary="Permite a un usuario registrarse en el sistema de forma local",
    response_description="Registro procesado. Retorna el estado del solicitante al momento de la llamada."
)
async def register(
    payload: UserRegister,
    db_manager: DBManager = Depends(get_db_manager),
    contract_manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer)
):
    """
    Asocia localmente el nombre de un solicitante a su dirección de Ethereum.
    Si la cuenta ya fue registrada pero se encuentra desautorizada, el registro previo se sobrescribe.
    """
    try:
        #Reconstrucción Criptográfica del Mensaje y Recuperación de la Firma
        try:
            message_hex = contract_manager.generate_hex_str_register_message(payload.name)
            recovered_signer = signer.get_signer_address(message_hex, payload.signature)
            
            if recovered_signer.lower() != payload.address.lower():
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_SIGNATURE})
                
        except (signer_exceptions.InvalidSignatureException, signer_exceptions.InvalidInputException, 
                contract_exceptions.InvalidInputTypeException, contract_exceptions.TextEncodingException, 
                contract_exceptions.CryptographicHashingException):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_SIGNATURE})
        
        # Control de Reglas de Negocio / Verificación de estados en Blockchain y Base de Datos Local
        is_onchain_authorized = contract_manager.is_address_authorized(payload.address)
        local_user = db_manager.getUser(payload.address)

        if is_onchain_authorized:
            determined_status = UserState.AUTHORIZED
        else:
            determined_status = UserState.PENDING

        if local_user:
            if local_user.state == UserState.AUTHORIZED:
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": Messages.ALREADY_IN_SYSTEM})
            
            # Si existía pero fue desautorizado, se permite sobreescribir los datos
            local_user.name = payload.name
            local_user.signature = payload.signature
            local_user.state = determined_status
            db_manager.updateExistingUser(local_user)
        else:
            db_manager.createPendingUser(address=payload.address, name=payload.name, signature=payload.signature)

        # Retorno Exitoso
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": determined_status.value}
        )

    except Exception as e:
        logger.error(f"Fallo no controlado en /register: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    
@app.post(
    "/register-proposal",
    status_code=status.HTTP_201_CREATED,
    summary="Registra una propuesta de forma anónima asociándola a un llamado",
    response_description="La propuesta ha sido procesada e indexada mediante su árbol de Merkle",
)
async def register_proposal(
    payload: ProposalRegister,
    db_manager: DBManager = Depends(get_db_manager),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        # Verificar existencia del llamado padre (Requisito 404)
        try:
            if not db_manager.existsCall(payload.callId):
                return JSONResponse(status_code=404, content={"message": Messages.CALLID_NOT_FOUND})
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        # Generación del proposalId (Raíz Merkle) y sus pruebas estructurales
        proposal_id, merkle_proofs, t_hash, d_hash = contract_manager.generate_merkle_tree(
            call_id=payload.callId,
            title=payload.title,
            description=payload.description,
            files=payload.files
        )

        # Control de colisión por duplicados
        if db_manager.existsProposal(proposal_id):
            return JSONResponse(status_code=403, content={"message": Messages.ALREADY_REGISTERED})

        # Guardar registro completo en base de datos local
        try:
            db_manager.register_proposal(
                call_id=payload.callId,
                proposal_id=proposal_id,
                title=payload.title,
                title_hash=t_hash,
                description=payload.description,
                description_hash=d_hash,
                files=payload.files,
                proofs=merkle_proofs
            )
        except db_exceptions.RecordAlreadyExistsException:
            return JSONResponse(status_code=403, content={"message": Messages.ALREADY_REGISTERED})
        except db_exceptions.DatabaseWriteException:
            return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})

        #Respuesta exitosa estructurada
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "OK",
                "proposalId": proposal_id,
                "proof": merkle_proofs
            }
        )

    except Exception as e:
        logger.error(f"Fallo no controlado en /register-proposal: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"message": Messages.INTERNAL_ERROR})
    
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
    
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_ADDRESS
        )
        
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
    summary="Obtiene la información de un llamado registrado localmente"
)
async def get_call(
    call_id: str = Path(..., description="Hash identificador del llamado (0x...)"),
    db_manager: DBManager = Depends(get_db_manager)
):
    try:
        # Validación estricta del formato del callId (Requisito 400)
        if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content={"message": Messages.INVALID_CALLID}
            )

        # Búsqueda del registro en la base de datos local
        try:
            call_record = db_manager.getCall(call_id)
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={"message": Messages.INTERNAL_ERROR}
            )

        #Control de existencia (Requisito 404)
        if not call_record:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={"message": Messages.CALLID_NOT_FOUND}
            )

        current_state = call_record.state

        if current_state == CallState.PENDING:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "title": call_record.title,
                    "description": call_record.description,
                    "status": "pending"
                }
            )
            
        elif current_state == CallState.CREATED:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "creator": call_record.creator,
                    "cfp": call_record.contractAddress if call_record.contractAddress else "0x0000000000000000000000000000000000000000",
                    "title": call_record.title,
                    "description": call_record.description,
                    "status": "created"
                }
            )
            
        else:
            # Salvaguarda por si existiera otro estado interno no mapeado
            logger.error(f"Estado inesperado '{call_record.state}' para el llamado {call_id}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={"message": Messages.INTERNAL_ERROR}
            )

    except Exception as e:
        logger.error(f"Fallo no controlado en GET /calls/{{call_id}}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={"message": Messages.INTERNAL_ERROR}
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


@app.get(
    "/contract-address",
    status_code=status.HTTP_200_OK,
    summary="Obtiene la dirección del contrato factoría",
    response_description="Retorna la dirección de Ethereum del contrato principal"
)
async def get_factory_address(
    manager: ContractManager = Depends(get_contract_manager)
):
    try:
        factory_address = manager.contract_address
        return {"address": factory_address}
        
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /contract-address: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )

@app.get(
    "/contract-owner",
    status_code=status.HTTP_200_OK,
    summary="Obtiene la dirección del dueño del contrato factoría",
    response_description="Retorna la dirección de Ethereum del propietario (owner)"
)
async def get_factory_owner(
    manager: ContractManager = Depends(get_contract_manager)
):
    try:
        owner_address = manager.get_factory_contract_owner()
        return {"address": owner_address}
        
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en la EVM al consultar el dueño: {cle.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /contract-owner: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )

@app.get(
    "/proposal-data/{call_id}/{proposal}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene la información detallada de una propuesta",
    response_description="Retorna el emisor, número de bloque y timestamp de la propuesta"
)
async def get_proposal_data_by_id(
    call_id: str = Path(..., description="Hash que identifica al llamado"),
    proposal: str = Path(..., description="Hash que identifica a la propuesta"),
    manager: ContractManager = Depends(get_contract_manager)
):
    if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_CALLID
        )
        
    if not re.match(r"^0x[a-fA-F0-9]{64}$", proposal):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.INVALID_PROPOSAL
        )

    try:
        creator_address, cfp_address = manager.get_call_details(call_id_hex=call_id)
        
        address_zero = "0x" + "0" * 40
        if creator_address == address_zero or cfp_address == address_zero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.CALLID_NOT_FOUND
            )
            
        sender, block_number, timestamp = manager.get_cfp_proposal_data(
            cfp_address=cfp_address, 
            proposal_hex=proposal
        )
        
        if sender == address_zero or block_number == 0 or timestamp == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=Messages.PROPOSAL_NOT_FOUND
            )
            
        iso_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        
        return {
            "sender": sender,
            "blockNumber": block_number,
            "timestamp": iso_date
        }
        
    except HTTPException as http_ex:
        raise http_ex
        
    except ContractLogicError as cle:
        logger.error(f"Error de lógica en la EVM al consultar datos de la propuesta: {cle.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )
        
    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /proposal-data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=Messages.INTERNAL_ERROR
        )