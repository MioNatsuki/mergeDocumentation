import logging
from core.models import Bitacora

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('correspondencia_app')

def auditoria(db, usuario_id, accion, modulo, detalles=None, ip_address=None, user_agent=None):
    """Registra evento en bitácora de base de datos"""
    try:
        registro = Bitacora(
            usuario_id=usuario_id,
            accion=accion,
            modulo=modulo,
            detalles=detalles,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(registro)
        db.commit()
        
        # También log en archivo
        logger.info(f"AUDITORIA - {modulo}.{accion} - Usuario: {usuario_id}")
        
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")
        db.rollback()