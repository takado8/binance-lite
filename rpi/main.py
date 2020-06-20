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


def server():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(1)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))

    # receive data stream. it won't accept data packet greater than 1024 bytes
    data = conn.recv(1024).decode()
    if not data:
        # if data is not received break
        return
    print("from connected user: " + str(data))
    reply = 'signature'
    conn.send(reply.encode())  # send data to the client

    conn.close()  # close the connection


def test_server():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(1)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    # receive data stream. it won't accept data packet greater than 1024 bytes
    data = conn.recv(1024).decode()
    if not data:
        print('no data.')
        return
    print("from connected user: " + str(data))
    reply = 'Pong!'
    conn.send(reply.encode())  # send data to the client
    conn.close()  # close the connection


if __name__ == '__main__':
    test_server()