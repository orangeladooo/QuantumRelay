"""
crypto.py - Placeholder CryptoService for PQC-Chatt.
Replace encrypt/decrypt with real PQC logic later.
"""


class CryptoService:
    def encrypt(self, message: str) -> str:
        return message

    def decrypt(self, message: str) -> str:
        return message


# Singleton instance to import across the app
crypto_service = CryptoService()
