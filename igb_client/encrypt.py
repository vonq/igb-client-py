from base64 import b64decode
from base64 import b64encode

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class AESCypher:
    """
    A simple AES cipher implementation
    """

    block_size = 16
    tag_size = 16

    def __init__(self, shared_key):
        self.key = b64decode(shared_key)

    def encrypt(self, data: str) -> str:
        iv = get_random_bytes(self.block_size)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return b64encode(iv + ciphertext + tag).decode()

    def decrypt(self, data: str) -> str:
        raw = b64decode(data)
        iv = raw[0 : self.block_size]
        data = raw[self.block_size : -self.tag_size]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=iv)
        plaintext = cipher.decrypt(data)
        return plaintext.decode()
