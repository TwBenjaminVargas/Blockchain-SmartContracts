from datetime import datetime, timezone
import logging
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import messages as Messages
from src.settings import get_settings, Settings
from src.signer import get_signer, Signer
from src.schemas import CFPSchema
from src.contractManager import get_contract_manager, ContractManager
from web3.exceptions import ContractLogicError


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
            else:
                api_message = Messages.INTERNAL_ERROR

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": api_message}
    )


# ENDPOINTs
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

        plain_message_hex = manager.generate_hex_string_message(
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