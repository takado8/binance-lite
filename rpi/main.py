import socket
import hashlib
import hmac


API_SECRET = 'CqcTMoFGymVIw9opl9ZSD62J1tLmKLLYNc3VvSi3uhiZAC0dLlE5jl7MhDp1A5t5'


def _generate_signature(query_string):
    m = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
    return m.hexdigest()


def server():
    host = "173.68.217.147"
    port = 5000
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mySocket.bind((host, port))
    mySocket.listen(1)
    print('waiting for connection...')
    conn, addr = mySocket.accept()
    print("Connection from: " + str(addr))
    data = conn.recv(10000).decode()
    print('Received data: {}'.format(data))
    signature = _generate_signature(data)
    signature_bytes = signature.encode()
    print('signature size: {}'.format(len(signature_bytes)))
    print('replying signature...')
    conn.send(signature_bytes)
    conn.close()
    print('connection closed.')


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
    data = conn.recv(1024).decode()
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
    while True:
        server()
