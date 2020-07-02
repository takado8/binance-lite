import socket


def get_signature(data_to_sign):
    try:
        print('connecting to zero server...')
        host = '173.68.217.147'
        port = 18956  # socket server port number
        client_socket = socket.socket()  # instantiate
        client_socket.settimeout(6)
        client_socket.connect((host, port))  # connect to the server
        data_to_sign_bytes = data_to_sign.encode()
        client_socket.send(data_to_sign_bytes)  # send message
        data = client_socket.recv(64).decode()  # receive response
        client_socket.close()  # close the connection
        if data:
            print('sign received.')
            return [data]
        else:
            print('SIGNING ERROR.')
            return [False, 'SIGNING ERROR.']
    except Exception as ex:
        print('Error:')
        print(ex)
        return [False, str(ex)]


def test():
    host = '173.68.217.147'
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.settimeout(2)
    client_socket.connect((host, port))  # connect to the server
    message = 'Ping!'
    client_socket.send(message.encode())  # send message
    data = client_socket.recv(64).decode()  # receive response
    print('Received from server: ' + data)  # show in terminal
    if data == 'Pong!':
        print('Test is positive')
    else:
        print('Test is negative')
    client_socket.close()  # close the connection


if __name__ == '__main__':
    test()