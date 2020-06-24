import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import os


class Mayes(object):
    def __init__(self):
        self.bs = AES.block_size

    def create_secret_file(self, secret_plain, passwd):
        secret_enc = self.encrypt(secret_plain, passwd)
        with open('constants', 'wb+') as file:
            file.write(secret_enc)

    def read_secret(self, passwd):
        if os.path.isfile('constants'):
            with open('constants', 'rb') as file:
                enc = file.read()
                decr = self.decrypt(enc, passwd)
                return decr
        else:
            print('cannot find secret file.')

    def encrypt(self, raw, passwd):
        key = self._get_key_from_passwd(passwd)
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc, passwd):
        key = self._get_key_from_passwd(passwd)
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _get_key_from_passwd(key):
        return hashlib.sha256(key.encode()).digest()

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]