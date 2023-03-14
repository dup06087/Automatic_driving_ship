# TCP server example
# By Socket 통신
import random
import socket
import time

# 실제로는 ip socket 통신 아니고, serial 통신 사용하니까 바꿔줘야 함
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", 5000))
server_socket.listen(5)

print("TCPServer Waiting for client on port 5000")

while 1:
    client_socket, address = server_socket.accept()
    print("I got a connection from ", address)
    while 1:
        # serial 통신으로 같은 포맷의 값만 랜덤으로 (random.randint 부분) 계속 송신
        data = """$GNRMC,084449.00,A,{0},N,{1},E,{2},,240223,8.8,W,D*16
        $GNHDT,{3},T*1F""".format(random.randint(0,10), random.randint(0,10), random.randint(0,10), random.randint(0,10))

        if (data == 'Q' or data == 'q'):
            client_socket.send(data.encode())
            client_socket.close()
            break
        else:
            client_socket.send(data.encode())

        time.sleep(1)

server_socket.close()
print("SOCKET closed... END")