import socket
import hashlib
import hmac
import getpass
import os
from log import Log
from encryption import Mayes


ACCEPTED_IPS = [
    '173.68.217.188'  # bpi
                ]


class Signer:
    def __init__(self):
        self.log = Log()
        mayes = Mayes()
        passwd = getpass.getpass()
        if os.path.isfile('constants'):
            print('Secret file found.')
            self.secret = mayes.read_secret(passwd)
        else:
            print('Create secret file.')
            passwd2 = getpass.getpass(prompt='Repeat passwd:')
            while passwd != passwd2:
                print('Passwords do not match.')
                passwd = getpass.getpass()
                passwd2 = getpass.getpass(prompt='Repeat passw:')
            secret = getpass.getpass(prompt='Secret:')
            mayes.create_secret_file(secret, passwd)
            print('Secret file created. Relog to validate.')
            passwd = None
            passwd2 = None
            secret = None
            del passwd2
            del passwd
            del secret
            exit(0)
        passwd = None
        passwd2 = None
        secret = None
        del passwd2
        del passwd
        del secret

    def run_server(self):
        try:
            host = "173.68.217.147"
            port = 18956
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mySocket.bind((host, port))
            mySocket.listen(1)
            # print('waiting for connection...')
            conn, addr = mySocket.accept()
            start = time.time()
            info = 'Connection from: {}'.format(addr)
            print(info)
            self.log.append(info)
            # filter ip
            if addr[0] not in ACCEPTED_IPS:
                info = 'UNKNOWN IP! REJECTING CONNECTION.'
                print(info)
                self.log.append(info)
                conn.close()
                mySocket.close()
                return False
            data = conn.recv(256).decode()
            info = 'Received data: {}'.format(data)
            print(info)
            self.log.append(info)
            signature = self._generate_signature(data)
            signature_bytes = signature.encode()
            info = 'replying signature...'
            print(info)
            self.log.append(info)
            conn.send(signature_bytes)
            conn.close()
            info = 'Execution time: {}'.format(round(time.time() - start), 4)
            print(info)
            self.log.append(info)
            return True
        except Exception as ex:
            info = 'Connection error: {}'.format(ex)
            print(info)
            self.log.append(info)
            return None

    def _generate_signature(self, query_string):
        m = hmac.new(self.secret.encode('utf-8'),query_string.encode('utf-8'),hashlib.sha256)
        return m.hexdigest()

    @staticmethod
    def test_server():
        host = "173.68.217.147"
        port = 5000
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mySocket.bind((host, port))
        mySocket.listen(1)
        print('waiting for connection...')
        conn, addr = mySocket.accept()
        print("Connection from: " + str(addr))
        data = conn.recv(256).decode()
        print('Received data: {}'.format(data))
        if data == 'Ping!':
            reply = 'Pong!'
        else:
            reply = 'unknown msg'
        print('reply: {}'.format(reply))
        conn.send(reply.encode())
        conn.close()
        print('connection closed.')


if __name__ == '__main__':
    signer = Signer()
    while True:
        result = signer.run_server()
        if not result:
            import time
            if result is False:
                time.sleep(10)  # unknown connection rejected
            elif result is None:
                time.sleep(1)  # some error