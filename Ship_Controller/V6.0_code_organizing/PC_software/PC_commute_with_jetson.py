from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
import socket
import threading
import json
import select
import traceback
import time

class Worker(QtCore.QThread):
    def __init__(self):
        super().__init__()
        # 송신 값
        self.message = {"mode_jetson": "SELF", "dest_latitude": None, "dest_longitude": None}

        # 수신 시 에러방지용 초기화 > 사실 데이터 훨씬 많음
        self.data = {"mode_jetson": "SELF", "dest_latitude": None, "dest_longitude": None}

        # 자율 주행 시작 플래그
        self.flag_auto_driving = None

    def run(self):
        # 117.17.187.60::25234
        # recv_host, recv_port = '117.17.187.60', 5001
        # send_host, send_port = '117.17.187.60', 5002
        ''' Wifi 사용시 ''' # 또한, jetson 프로그램에서도 pc send, recv 포트 바꿔줘야함
        # recv_host, recv_port = '223.171.136.213', 5001
        # send_host, send_port = '223.171.136.213', 5002
        ''' Lan port 사용시 ''' # 또한, jetson 프로그램에서도 pc send, recv 포트 바꿔줘야함
        recv_host, recv_port = '223.171.136.213', 5003
        send_host, send_port = '223.171.136.213', 5004
        '''local 실험시''' # 마찬가지로, 포트 변경 필요
        # recv_host, recv_port = 'localhost', 5003
        # send_host, send_port = 'localhost', 5004

        self.ip_address = recv_host

        # recv_host, recv_port = '192.168.0.62', 5001
        # send_host, send_port = '192.168.0.62', 5002
        stop_event = threading.Event()
        recv_socket = None
        send_socket = None
        print("receiving readying")

        data_buffer = b''

        while not stop_event.is_set():
            try:
                if not recv_socket:
                    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    recv_socket.settimeout(5)
                    recv_socket.connect((recv_host, recv_port))
                    print("Connected to recv server")

                if not send_socket:
                    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    send_socket.settimeout(5)
                    send_socket.connect((send_host, send_port))
                    print("Connected to send server")

                ready_to_read, ready_to_write, _ = select.select([recv_socket], [send_socket], [], 1)

                ### PC에서 읽기
                if ready_to_read:
                    try:
                        data = recv_socket.recv(1024)
                    except socket.timeout:
                        print("Receive timeout. Trying again...")
                        continue
                    except ConnectionResetError:
                        print("Connection reset by remote host. Reconnecting...")
                        recv_socket.close()
                        recv_socket = None
                        continue

                    if data:
                        data_buffer = b''  # 버퍼를 초기화합니다.
                        data_buffer += data

                        if b'\n' in data_buffer:
                            data_line, data_buffer = data_buffer.split(b'\n', 1)
                            try:
                                received_dict = json.loads(data_line.decode('utf-8'))
                                self.connection = True
                                print("Jetson >> PC", received_dict)
                            except (json.JSONDecodeError, TypeError, ValueError):
                                print("Failed to decode received data from client.")
                            else:
                                if self.validate_received_data(received_dict):
                                    self.data = received_dict
                                else:
                                    print("Invalid data received. Discarding...")

                # PC에서 jetson에 쓰기
                if ready_to_write:
                    if self.flag_auto_driving == True:
                        if self.validate_message(self.message):
                            message = json.dumps(self.message)
                            message += '\n'
                            send_socket.sendall(message.encode())
                            self.connection = True
                            self.flag_auto_driving = False
                            print("COM >> Jetson, send : ", message.encode())
                        else:
                            print("Invalid message. Not sending...")

                time.sleep(0.05)

            except (socket.error, Exception) as e:
                self.connection = False
                print(f"Error: {e}")
                traceback.print_exc()
                if recv_socket:
                    recv_socket.close()
                    recv_socket = None
                if send_socket:
                    send_socket.close()
                    send_socket = None
                time.sleep(1)

        if recv_socket:
            recv_socket.close()

        if send_socket:
            send_socket.close()

    def validate_received_data(self, data):
        # 데이터 형식 및 값 검증 로직 작성
        required_keys = ["mode_jetson", "dest_latitude", "dest_longitude"]
        for key in required_keys:
            if key not in data:
                return False

        return True

    def validate_message(self, message):
        # 메시지 형식 및 값 검증 로직 작성
        # 예를 들어, 필수 키가 있는지 확인하고, 위도와 경도가 올바른 범위 내에 있는지 확인
        required_keys = ["mode_jetson", "dest_latitude", "dest_longitude"]
        for key in required_keys:
            if key not in message:
                return False

        return True