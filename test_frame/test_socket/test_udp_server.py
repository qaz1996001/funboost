import socket

BUFSIZE = 2
ip_port = ('127.0.0.1', 9999)
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP protocol
server.bind(ip_port)
while True:
    data, client_addr = server.recvfrom(BUFSIZE)
    print('server received data', data)

    server.sendto(data.upper(), client_addr)

server.close()