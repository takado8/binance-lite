import socket
import hashlib
import hmac
from operator import itemgetter


API_SECRET = 'CqcTMoFGymVIw9opl9ZSD62J1tLmKLLYNc3VvSi3uhiZAC0dLlE5jl7MhDp1A5t5'


def _generate_signature(query_string):
    m = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
    return m.hexdigest()


def _order_params(data):
    """Convert params to list with signature as last element

    :param data:
    :return:

    """
    has_signature = False
    params = []
    for key, value in data.items():
        if key == 'signature':
            has_signature = True
        else:
            params.append((key, value))
    # sort parameters by key
    params.sort(key=itemgetter(0))
    if has_signature:
        params.append(('signature', data['signature']))
    return params


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
    test_server()