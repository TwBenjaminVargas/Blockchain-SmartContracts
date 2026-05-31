from datetime import datetime, timezone
from contextlib import asynccontextmanager
import logging
import sys
from fastapi import Depends, FastAPI, HTTPException, status, Request,Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from listeners.BlockChainWorker import BlockchainWorker
import messages as Messages
from models.AuthorieAddress import AuthorizeAddress
from models.UnauthorizeAddress import UnauthorizeAddress
from models.VerifyProof import VerifyProof
from services.signer import get_signer, Signer
from models.persistence.Call import CallState
from models.CallCreate import CallCreate
from models.UserRegister import UserRegister
from models.ProposalRegister import ProposalRegister
from models.UserPatch import UserPatch
from services.contractManager import get_contract_manager, ContractManager
from web3.exceptions import ContractLogicError
from db.sqliteManager import DBManager, get_db_manager
import re
from models.persistence.User import UserState
import asyncio
import exceptions.contractManagerExceptions as contract_exceptions
import exceptions.SignerExceptions as signer_exceptions
import exceptions.databaseManagerExceptions as db_exceptions


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = get_db_manager()
    signer = get_signer()
    admin_address = signer.admin_address.lower()

    try:
        admin_user = db_manager.getUser(admin_address)
        if not admin_user:
            logger.info(f"Sembrando cuenta de administrador en base de datos: {admin_address}")
            db_manager.createAdminUser(admin_address)
            logger.info("Administrador verificado e insertado con éxito.")
        else:
            logger.info(f"El administrador ya se encuentra registrado. Nonce actual: {admin_user.nonce}")
    except Exception as e:
        logger.critical(
            f"FALLO CRÍTICO AL INICIALIZAR DATOS DEL SISTEMA: {str(e)}. "
            f"El sistema se detendrá inmediatamente por seguridad.", 
            exc_info=True
        )
        # sys.exit(1) aborta el proceso de Python por completo, matando a Uvicorn
        sys.exit(1)
        
    worker = BlockchainWorker()
    
    # Creamos una tarea en segundo plano en el event loop de Python
    worker_task = asyncio.create_task(worker.start_worker(interval_seconds=3))
    logger.info("Tarea del Blockchain Worker registrada en el event loop.")
    
    yield
    
    logger.info("Iniciando apagado controlado del Worker...")
    worker.stop_worker()
    
    try:
        await asyncio.wait_for(worker_task, timeout=5.0)
        logger.info("Worker de Blockchain detenido exitosamente.")
    except asyncio.TimeoutError:
        logger.warning("El Worker tardó demasiado en cerrarse y fue forzado.")

app = FastAPI(title="API de Convocatoria de Propuestas (CFP) - TP 8",lifespan=lifespan)

#formato de respuesta personalizada para errores HTTP y validación de datos
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    # 1. Validación estricta de JSON en métodos de escritura
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_MIMETYPE}
            )
        
    errors = exc.errors()
    logger.error(f"Errores nativos de Pydantic interceptados: {errors}")
    
    if not errors:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.MISSING_FIELD})
        
    first_error = errors[0]
    error_type = first_error.get("type", "")
    location = first_error.get("loc", [])
    ctx = first_error.get("ctx", {})
    
    EXCEPTION_MESSAGE_MAP = {
        "InvalidProposalException": Messages.INVALID_PROPOSAL,
        "ProofTooLongException": Messages.PROOF_TOO_LONG,
        "MissingFieldException": Messages.MISSING_FIELD,
        "InvalidTitleException": Messages.INVALID_TITLE,
        "TitleTooLongException": Messages.TITLE_TOO_LONG,
        "DescriptionTooLongException": Messages.DESCRIPTION_TOO_LONG,
        "TooManyFilesException": Messages.TOO_MANY_FILES,
        "InvalidNameException": Messages.INVALID_NAME,
        "NameTooLongException": Messages.NAME_TOO_LONG,
        "InvalidSignatureException": Messages.INVALID_SIGNATURE,
        "InvalidAddressException": Messages.INVALID_ADDRESS,
        "InvalidCallIdException": Messages.INVALID_CALLID,
    }

    if ctx and "error" in ctx:
        inner_error = ctx["error"]
        
        # Obtener el nombre de la clase
        error_class_name = type(inner_error).__name__
        
        error_str = str(inner_error) 

        # Busqueda de coincidencia con excepciones
        for class_name, message in EXCEPTION_MESSAGE_MAP.items():
            if class_name == error_class_name or class_name in error_str:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": message})

    # Fallback
    if error_type in ["missing", "type_error.missing"]:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.MISSING_FIELD})
        
    field_name = location[1] if len(location) > 1 else (location[0] if location else None)
    
    if field_name == "proof":
        if "list" in error_type or "type" in error_type:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_PROPOSAL})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.PROOF_TOO_LONG})
        
    if field_name in ["proposalId", "leaf", "proposal", "files"]:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_PROPOSAL})
    if field_name == "signature":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_SIGNATURE})
    if field_name == "address":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_ADDRESS})
    if field_name == "callId":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_CALLID})
    if field_name == "name":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_NAME})
    if field_name == "title":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_TITLE})

    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.MISSING_FIELD})  
    
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
        local_user = db_manager.getUser(payload.address)
        if local_user:
            if local_user.state != UserState.ARCHIVED:
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": Messages.ALREADY_IN_SYSTEM})
            
            local_user.name = payload.name
            local_user.signature = payload.signature
            local_user.state = UserState.REGISTERED
            db_manager.updateExistingUser(local_user)
            # Retorno Exitoso
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": UserState.REGISTERED.value}
            )
            
        is_onchain_authorized = contract_manager.is_address_authorized(payload.address)
        is_onchain_registered = contract_manager.is_address_registered(payload.address)

        if is_onchain_registered:
            determined_status = UserState.REGISTERED
            if is_onchain_authorized:
                determined_status = UserState.AUTHORIZED
        else:
            determined_status = UserState.PENDING
            
        
        db_manager.createUser(address=payload.address, name=payload.name, signature=payload.signature, state=determined_status)

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
    summary="Registra una propuesta de forma anónima asociándola a un llamado"
)
async def register_proposal(
    payload: ProposalRegister,
    db_manager: DBManager = Depends(get_db_manager),
    signer: Signer = Depends(get_signer),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        try:
            if db_manager.existsCall(payload.callId):
                logger.debug(f"CallId {payload.callId} validado localmente en la base de datos.")
            else:
                logger.warning(f"CallId {payload.callId} no encontrado en BD local. Buscando on-chain...")
                _, cfp_address = contract_manager.get_call_details(payload.callId)
                
                if not cfp_address or cfp_address == "0x0000000000000000000000000000000000000000":
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        content={"message": Messages.CALLID_NOT_FOUND}
                    )
                logger.info(f"CallId {payload.callId} verificado con éxito on-chain en el contrato {cfp_address}.")

        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={"message": Messages.INTERNAL_ERROR}
            )
        except (contract_exceptions.InvalidContractAddressException, contract_exceptions.BlockchainReadException):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={"message": Messages.INTERNAL_ERROR}
            )
            
        proposal_id, merkle_proofs, t_hash, d_hash = contract_manager.generate_merkle_tree(
            call_id=payload.callId,
            title=payload.title,
            description=payload.description,
            files=payload.files
        )

        if db_manager.existsProposal(proposal_id):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={"message": Messages.ALREADY_REGISTERED}
            )
        try:
            tx_not_signed = contract_manager.register_proposal(
                from_address=signer.address,
                call_id_hex=payload.callId,
                proposal_hex=proposal_id 
            )


            tx_signed_bytes = signer.sign_transaction(tx_not_signed)


            tx_hash_hex = contract_manager.execute_transaction(tx_signed_bytes)
            
            receipt = contract_manager.get_transaction_receipt(tx_hash_hex)
            logger.info(f"Confirmación on-chain exitosa para propuesta {proposal_id} en el bloque {receipt.get('blockNumber')}")
            
            mining_block = receipt.get('blockNumber')
            block_data = contract_manager.get_block_data_by_number(block_number=mining_block)
            block_timestamp = block_data.get('timestamp')
            
        except contract_exceptions.BlockchainContractLogicException as bcle:
            error_message = contract_manager.map_revert_reason_to_message(bcle.message)
            
            if error_message == Messages.ALREADY_REGISTERED:
                return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": error_message})
            elif error_message == Messages.CALLID_NOT_FOUND:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": error_message})
            else:
                return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})

        except contract_exceptions.BlockchainTransactionException as bte:
            logger.error(f"Fallo de infraestructura en la red blockchain: {str(bte)}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})

        except contract_exceptions.UnderfundedWalletException as uwe:
            logger.critical(f"ALERTA OPERATIVA: El nodo rechazó la operación por falta de gas. {str(uwe)}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})

        try:
            db_manager.register_proposal(
                call_id=payload.callId,
                proposal_id=proposal_id,
                title=payload.title,
                title_hash=t_hash,               
                description=payload.description,
                description_hash=d_hash,         
                files=payload.files,             
                proofs=merkle_proofs,            
                created=block_timestamp,
                blocknumber=mining_block,
                sender=receipt.get('from')       
            )
        except db_exceptions.RecordAlreadyExistsException:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, 
                content={"message": Messages.ALREADY_REGISTERED}
            )
        except db_exceptions.DatabaseWriteException:
            logger.error(f"Error crítico: Transacción minada con éxito pero falló el guardado local en SQLite para: {proposal_id}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content={"message": Messages.INTERNAL_ERROR}
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "OK",
                "proposalId": proposal_id,
                "proof": merkle_proofs
            }
        )

    except Exception as e:
        logger.error(f"Fallo no controlado en el flujo del endpoint /register-proposal: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={"message": Messages.INTERNAL_ERROR}
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
    db_manager: DBManager = Depends(get_db_manager),
    manager: ContractManager = Depends(get_contract_manager)
):
    if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": Messages.INVALID_CALLID}
        )

    cfp_address = None

    try:
        call_record = db_manager.getCall(call_id)
        
        if call_record:
            if call_record.state != CallState.PENDING:
                cfp_address = call_record.contractAddress
            else:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": Messages.CALLID_NOT_FOUND}
                 )
                
                
    except db_exceptions.DatabaseConnectionException as db_err:
        logger.error(f"Fallo de lectura en BD local al buscar {call_id}: {str(db_err)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )

    if not cfp_address:
        try:
            creator_address, contract_chain_address = manager.get_call_details(call_id_hex=call_id)
             
            address_zero = "0x" + "0" * 40
            if creator_address == address_zero or contract_chain_address == address_zero:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": Messages.CALLID_NOT_FOUND}
                )
                
            cfp_address = contract_chain_address
            
        except (contract_exceptions.InvalidContractAddressException, contract_exceptions.BlockchainReadException) as chain_err:
            logger.error(f"Error al obtener detalles del llamado en la Blockchain: {str(chain_err)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )
        except Exception as e:
            logger.error(f"Fallo inesperado al conectar con el nodo RPC para recuperar el llamado: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

    try:
        timestamp = manager.get_cfp_closing_time_by_address(cfp_address=cfp_address)
        
        iso_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        
        return {"closingTime": iso_date}
        
    except contract_exceptions.InvalidContractAddressException as ice:
        logger.error(f"Dirección de contrato inválida o no compatible detectada: {str(ice)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    except contract_exceptions.BlockchainReadException as bre:
        logger.error(f"Error de infraestructura de red al leer closingTime: {str(bre)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    except Exception as e:
        logger.error(f"Fallo no controlado en la fase final de /closing-time: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
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
    "/proposal-data/{call_id}/{proposal}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene la información técnica y procedencia de una propuesta registrada"
)
async def get_proposal_data(
    call_id: str = Path(..., description="Hash identificador del llamado (0x...)"),
    proposal: str = Path(..., description="Hash raíz de Merkle de la propuesta (0x...)"),
    db_manager: DBManager = Depends(get_db_manager),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        if not re.match(r"^0x[a-fA-F0-9]{64}$", call_id):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_CALLID})
            
        if not re.match(r"^0x[a-fA-F0-9]{64}$", proposal):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": Messages.INVALID_PROPOSAL})

        local_data = None
        try:
            # Trae una tupla (proposal_record, closing_time)
            local_data = db_manager.get_proposal_with_call_state(call_id, proposal)
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})

        is_locally_registered = local_data is not None


        sender: str
        block_number: int
        timestamp_unix: int
        closing_time_unix: int
        proposal_record = None


        try:
            if is_locally_registered:
                proposal_record, closing_time_local = local_data
                logger.debug(f"Propuesta {proposal} y llamado encontrados localmente. Minimizando tráfico con el nodo RPC.")
                
                sender = proposal_record.sender
                block_number = proposal_record.blocknumber
                timestamp_unix = proposal_record.created
                
                if closing_time_local is not None:
                    closing_time_unix = closing_time_local
                else:
                    logger.debug("Falta 'closingTime' local. Realizando consulta de rescate a la Blockchain.")
                    _, cfp_address = contract_manager.get_call_details(call_id)
                    if cfp_address == "0x0000000000000000000000000000000000000000":
                        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": Messages.CALLID_NOT_FOUND})
                    closing_time_unix = contract_manager.get_cfp_closing_time_by_address(cfp_address)
            else:
                logger.debug(f"Propuesta {proposal} ausente en BD local. Extrayendo auditoría de la EVM.")
                
                _, cfp_address = contract_manager.get_call_details(call_id)
                if cfp_address == "0x0000000000000000000000000000000000000000":
                    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": Messages.CALLID_NOT_FOUND})

                sender, block_number, timestamp_unix = contract_manager.get_cfp_proposal_data(cfp_address, proposal)
                
                if block_number == 0:
                    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": Messages.PROPOSAL_NOT_FOUND})

                closing_time_unix = contract_manager.get_cfp_closing_time_by_address(cfp_address)

        except contract_exceptions.InvalidContractAddressException:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": Messages.CALLID_NOT_FOUND})
        except contract_exceptions.BlockchainReadException:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})


        current_time_unix = int(datetime.now(timezone.utc).timestamp())
        call_state = "open" if current_time_unix < closing_time_unix else "closed"

        response_content = {
            "sender": sender,
            "blockNumber": block_number,
            "timestamp": datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "estado": call_state
        }

        if is_locally_registered and proposal_record:
            response_content["title"] = proposal_record.title
            response_content["description"] = proposal_record.description
            
            full_proofs = db_manager.get_proof(proposal)
            if full_proofs:
                # Acceso seguro mediante introspección soportando camelCase o snake_case
                t_hash_key = getattr(proposal_record, "titleHash", getattr(proposal_record, "title_hash", None))
                d_hash_key = getattr(proposal_record, "descriptionHash", getattr(proposal_record, "description_hash", None))
                call_id_key = call_id.lower()
                
                filtered_proofs = {}
                for key in [call_id_key, t_hash_key, d_hash_key]:
                    if key and key in full_proofs:
                        filtered_proofs[key] = [h.lower() for h in full_proofs[key]]
                
                response_content["proof"] = filtered_proofs

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_content)

    except Exception as e:
        logger.error(f"Fallo no controlado en el endpoint GET /proposal-data: {str(e)}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": Messages.INTERNAL_ERROR})
    
@app.get(
    "/registrations/{address}",
    status_code=status.HTTP_200_OK,
    summary="Obtiene el estado de registro de una dirección en el sistema",
)
async def get_registration_status(
    address: str = Path(..., description="Ethereum address (0x...)"),
    db_manager: DBManager = Depends(get_db_manager),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_ADDRESS}
            )

        # Intento de recuperacion local para evitar llamadas a la blockchain
        try:
            local_user = db_manager.getUser(address)
            if local_user:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status": local_user.state.value,
                        "name": local_user.name,
                        "nonce": local_user.nonce
                    }
                )
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        # Flujo de rescate/fallback mediante consulta On-Chain
        try:
            is_reg = contract_manager.is_address_registered(address)
            
            if not is_reg:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": Messages.INVALID_ADDRESS}
                )
                
            is_auth = contract_manager.is_address_authorized(address)
            
            # Si esta registrado pero no autorizado, su estado es "registered"
            account_status = "authorized" if is_auth else "registered"
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": account_status}
            )

        except contract_exceptions.BlockchainReadException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

    except Exception as e:
        logger.error(f"Fallo no manejado en GET /registrations/{address}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )

@app.patch(
    "/registrations/{address}",
    status_code=status.HTTP_200_OK,
    summary="Actualiza el nombre asociado a una dirección registrada, incrementando su nonce para mantener la sincronización con la blockchain"
)
async def update_registration_name(
    payload: UserPatch,
    address: str = Path(..., description="Ethereum address (0x...)"),
    db_manager: DBManager = Depends(get_db_manager),
    contract_manager: ContractManager = Depends(get_contract_manager),
    signer: Signer = Depends(get_signer)
):
    try:
        if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_ADDRESS}
            )

        address_lower = address.lower()

        try:
            user = db_manager.getUser(address_lower)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": Messages.NOT_REGISTERED}
                )
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        if user.nonce >= 0xFFFFFFFF:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.NONCE_OVERFLOW}
            )

        try:
            message_hex = contract_manager.generate_hex_str_user_patch(user.nonce, payload.name)
            recovered_address = signer.get_signer_address(message_hex, payload.signature)
        except Exception as e:
            logger.error(f"Error al verificar la firma para actualización de registro de {address_lower}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_SIGNATURE}
            )

        if recovered_address.lower() != address_lower:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_SIGNATURE}
            )

        try:
            user.name = payload.name
            user.nonce += 1
            db_manager.updateExistingUser(user)
        except db_exceptions.DatabaseWriteException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "OK"}
        )

    except Exception as e:
        logger.error(f"Fallo no manejado en PATCH /registrations/{address}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )

@app.get(
    "/admin/nonce",
    status_code=status.HTTP_200_OK,
    summary="Retorna el nonce actual del administrador para firmas de autorizacion"
)
async def get_admin_nonce(
    db_manager: DBManager = Depends(get_db_manager),
    signer: Signer = Depends(get_signer)
):
    try:
        admin_address = signer.admin_address
        
        try:
            admin_user = db_manager.getUser(admin_address)
        except db_exceptions.DatabaseConnectionException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"nonce": admin_user.nonce}
        )

    except Exception as e:
        logger.error(f"Unhandled exception in GET /admin/nonce: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )

@app.post(
    "/authorize/{address}",
    status_code=status.HTTP_200_OK
)
async def authorize_address(
    payload: AuthorizeAddress,
    address: str = Path(..., description="Dirección de la wallet que será autorizada"),
    db_manager: DBManager = Depends(get_db_manager),
    signer: Signer = Depends(get_signer),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        # Validar formato hexadecimal de la dirección del parámetro de ruta
        target_address = address.strip()
        if not re.match(r"^(0x)?[0-9a-fA-F]{40}$", target_address):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_ADDRESS}
            )

        # Verificar existencia del usuario objetivo en la base de datos local
        target_user = db_manager.getUser(target_address)
        if not target_user or target_user.state == UserState.ARCHIVED:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": Messages.NOT_REGISTERED}
            )

        # Obtener la cuenta del administrador local para extraer su nonce actual
        admin_user = db_manager.getUser(signer.admin_address)
        current_admin_nonce = admin_user.nonce

        if current_admin_nonce >= 2**32 - 1:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.NONCE_OVERFLOW}
            )

        #Reconstruir el mensaje binario esperado y verificar la firma criptográfica
        raw_msg = contract_manager.generate_hex_str_authorize_address(current_admin_nonce, target_address)
        is_valid_signature = signer.check_admin_sign(raw_msg, payload.signature)
        
        if not is_valid_signature:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_SIGNATURE}
            )

        # Operaciones On-Chain en la Blockchain
        try:
            tx_dict = contract_manager.authorize_user(signer.address, target_address)
            raw_tx_bytes = signer.sign_transaction(tx_dict)
            tx_hash = contract_manager.execute_transaction(raw_tx_bytes)
            _ = contract_manager.get_transaction_receipt(tx_hash)
            
        except contract_exceptions.BlockchainContractLogicException as bcle:
            error_message = contract_manager.map_revert_reason_to_message(bcle.message)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": error_message}
            )
        except (contract_exceptions.NodeRPCException, contract_exceptions.BlockchainTransactionException):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        # Persistir cambios locales en la base de datos tras éxito On-Chain
        db_manager.incrementUserNonce(signer.admin_address)
        db_manager.authorizeUser(target_address)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "OK"}
        )

    except db_exceptions.DatabaseConnectionException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    except Exception as e:
        logger.error(f"Unexpected crash in POST /authorize: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )

@app.post(
    "/unauthorize/{address}",
    status_code=status.HTTP_200_OK
)
async def unauthorize_address(
    payload: UnauthorizeAddress,
    address: str = Path(..., description="Dirección de la wallet que será desautorizada"),
    db_manager: DBManager = Depends(get_db_manager),
    signer: Signer = Depends(get_signer),
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        # Validar formato hexadecimal de la dirección del parámetro de ruta
        target_address = address.strip()
        if not re.match(r"^(0x)?[0-9a-fA-F]{40}$", target_address):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_ADDRESS}
            )

        # Verificar existencia del usuario objetivo en la base de datos local
        target_user = db_manager.getUser(target_address)
        if not target_user or target_user.state == UserState.ARCHIVED:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": Messages.NOT_REGISTERED}
            )

        # Obtener la cuenta del administrador local para extraer su nonce actual
        admin_user = db_manager.getUser(signer.admin_address)
        current_admin_nonce = admin_user.nonce

        if current_admin_nonce >= 2**32 - 1:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.NONCE_OVERFLOW}
            )

        #Reconstruir el mensaje binario esperado y verificar la firma criptográfica
        raw_msg = contract_manager.generate_hex_str_unauthorize_address(current_admin_nonce, target_address)
        is_valid_signature = signer.check_admin_sign(raw_msg, payload.signature)
        
        if not is_valid_signature:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": Messages.INVALID_SIGNATURE}
            )

        # Operaciones On-Chain en la Blockchain
        try:
            tx_dict = contract_manager.unauthorize_user(signer.address, target_address)
            raw_tx_bytes = signer.sign_transaction(tx_dict)
            tx_hash = contract_manager.execute_transaction(raw_tx_bytes)
            _ = contract_manager.get_transaction_receipt(tx_hash)
            created_count = contract_manager.get_created_by_count(target_address)
        except contract_exceptions.BlockchainContractLogicException as bcle:
            error_message = contract_manager.map_revert_reason_to_message(bcle.message)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": error_message}
            )
        except (contract_exceptions.NodeRPCException,
                contract_exceptions.BlockchainTransactionException,
                contract_exceptions.BlockchainReadException):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": Messages.INTERNAL_ERROR}
            )

        # Persistir cambios locales en la base de datos tras éxito On-Chain
        db_manager.incrementUserNonce(signer.admin_address)
        db_manager.unauthorizeUser(target_address,created_count)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "OK"}
        )

    except db_exceptions.DatabaseConnectionException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    except Exception as e:
        logger.error(f"Unexpected crash in POST /unauthorize: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    
@app.post(
    "/verify-proof",
    status_code=status.HTTP_200_OK
)
async def verify_proof(
    payload: VerifyProof,
    contract_manager: ContractManager = Depends(get_contract_manager)
):
    try:
        is_valid = contract_manager.verify_merkle_proof(
            proposal_id=payload.proposalId,
            leaf=payload.leaf,
            proof=payload.proof
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"valid": is_valid}
        )

    except contract_exceptions.CryptographicHashingException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )
    except Exception as e:
        logger.error(f"Unexpected crash in POST /verify-proof: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": Messages.INTERNAL_ERROR}
        )