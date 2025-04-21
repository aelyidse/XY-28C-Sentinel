from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import time

class LowLatencyCrypto:
    def __init__(self):
        self.key = os.urandom(32)  # 256-bit key
        self.nonce_size = 12  # 96-bit nonce for GCM
        self.tag_size = 16  # 128-bit authentication tag
        
    def encrypt(self, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
        """Encrypt data with low-latency AES-GCM"""
        nonce = os.urandom(self.nonce_size)
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return nonce, ciphertext, encryptor.tag
        
    def decrypt(self, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
        """Decrypt AES-GCM encrypted data"""
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
        
    def benchmark(self, data_size: int = 1024) -> dict:
        """Benchmark encryption/decryption performance"""
        data = os.urandom(data_size)
        
        # Encryption benchmark
        start = time.perf_counter()
        nonce, ciphertext, tag = self.encrypt(data)
        encrypt_time = time.perf_counter() - start
        
        # Decryption benchmark
        start = time.perf_counter()
        decrypted = self.decrypt(nonce, ciphertext, tag)
        decrypt_time = time.perf_counter() - start
        
        return {
            'data_size': data_size,
            'encrypt_time': encrypt_time,
            'decrypt_time': decrypt_time,
            'throughput': data_size / encrypt_time
        }