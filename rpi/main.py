import socket
import hashlib
import hmac
import getpass
import os
from rpi.encryption import Mayes


# API_SECRET = 'CqcTMoFGymVIw9opl9ZSD62J1tLmKLLYNc3VvSi3uhiZAC0dLlE5jl7MhDp1A5t5'


class Signer:
    def __init__(self):
        mayes = Mayes()
        passwd = getpass.getpass()
        if os.path.isfile('constants'):
            print('Secret file found.')
            self.secret = mayes.read_secret(passwd)
        else:
            print('Create secret file.')
            secret = getpass.getpass(prompt='Secret:')
            mayes.create_secret_file(secret, passwd)
            print('Secret file created. Relog to validate.')
            exit(0)

    def run_server(self):
        host = "173.68.217.147"
        port = 18956
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mySocket.bind((host, port))
        mySocket.listen(1)
        print('waiting for connection...')
        conn, addr = mySocket.accept()
        print("Connection from: " + str(addr))
        data = conn.recv(256).decode()
        print('Received data: {}'.format(data))
        signature = self._generate_signature(data)
        signature_bytes = signature.encode()
        print('signature size: {}'.format(len(signature_bytes)))
        print('replying signature...')
        conn.send(signature_bytes)
        conn.close()
        print('connection closed.')

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
        signer.run_server()