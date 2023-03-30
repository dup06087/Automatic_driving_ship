import socket

# 소켓 객체 생성
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 서버의 IP 주소와 포트 번호 설정
server_address = ('localhost', 5000)

# 서버에 연결
client_socket.connect(server_address)

try:
    while True:
        # 서버에 데이터 전송
        message = "connected"
        client_socket.sendall(message.encode())

        # 서버로부터 데이터 수신
        data = client_socket.recv(1024)

        # 수신한 데이터 출력
        print(f"Received data: {data.decode()}")
        time.sleep(1)

except Exception as e:
    # 예외 처리
    print(f"Error: {e}")
finally:
    # 소켓 닫기
    client_socket.close()
