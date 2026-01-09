"""Encryption Service for Data at Rest"""
from cryptography.fernet import Fernet
from app.core.config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data using Fernet"""
    
    def __init__(self):
        if not settings.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY not set in environment. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext
        
        encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext
        
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            # Log but don't expose cryptographic errors
            import logging
            logging.error(f"Decryption failed: {type(e).__name__}")
            raise ValueError("Failed to decrypt data")


# Singleton instance
encryption_service = EncryptionService()
