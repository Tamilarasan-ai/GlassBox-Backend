"""Custom SQLAlchemy column types for encrypted data"""
from sqlalchemy.types import TypeDecorator, Text
from app.core.encryption import encryption_service


class EncryptedText(TypeDecorator):
    """
    Encrypted text column type
    
    Automatically encrypts data before storing in database
    and decrypts when retrieving. Uses Fernet symmetric encryption.
    """
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt before storing in database"""
        if value is not None:
            return encryption_service.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """Decrypt when retrieving from database"""
        if value is not None:
            return encryption_service.decrypt(value)
        return value
