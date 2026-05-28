from fastapi import Depends
from src.settings import Settings, get_settings
from sqlmodel import Field, Session, SQLModel, create_engine
from models.persistence.Call import Call
import logging


logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)
        
    def addCall(self, call: Call) -> Call:
        """
        Recibe un objeto 'Call' (ya validado y con sus campos internos calculados),
        abre una sesión con la base de datos, lo persiste en SQLite y lo devuelve actualizado.
        """
        
        with Session(self.engine) as session:
            session.add(call)      # 1. Prepara el objeto para la inserción
            session.commit()       # 2. Escribe físicamente en el archivo .db
            session.refresh(call)  # 3. Trae los datos frescos desde el archivo (por seguridad)
            return call            # 4. Devuelve el objeto guardado
    
    def existsCall(self, call_id: str) -> bool:
        """
        Verifica de forma booleana si un callId ya existe en la API local (SQLite).
        Retorna True si existe, False en caso contrario.
        """
        with Session(self.engine) as session:
            existing_call = session.get(Call, call_id)
            return existing_call is not None

    def createPendingCall(self, call_id: str, title: str, description: str, signature: str, creator_address: str) -> Call:
        """
        Instancia un nuevo objeto 'Call' con estado 'PENDING' de forma inicial,
        lo persiste localmente en la base de datos y retorna el objeto guardado.
        
        Cualquier error en la base de datos se propagará hacia afuera como una Exception.
        """
        try:
            nuevo_llamado = Call(
                callId=call_id,
                title=title,
                description=description,
                signature=signature,
                creator=creator_address,
                state="PENDING"
            )
            # Reutilizamos el método addCall para impactar la base de datos
            return self.addCall(nuevo_llamado)
            
        except Exception as e:
            logger.error(f"Error al registrar el llamado PENDING en la BD: {str(e)}")
            raise Exception(str(e))
        

def get_db_manager(settings: Settings = Depends(get_settings)) -> DBManager:
    """
    Inyecta de forma interna la configuración del archivo .env.
    """
    return DBManager(
        db_path=settings.db_path
    )