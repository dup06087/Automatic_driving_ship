import json
import random
import socket
import threading
import time


class DataGeneratorThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.is_running = False

    def run(self):
        self.is_running = True

        while self.is_running:
            try:
                # 연결되어 있지 않다면 소켓을 생성하고 서버에 연결합니다
                if self.socket is None:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect((self.host, self.port))

                # 서버로부터 데이터를 수신합니다
                data = self.socket.recv(1024)

                # 수신된 데이터가 없으면 통신이 끊어졌다고 판단합니다
                if not data:
                    raise socket.error

                # 수신된 데이터를 디코딩하고 dict형으로 변환합니다
                decoded_data = data.decode()
                json_data = json.loads(decoded_data)
                data_dict = dict(json_data)

                # 전역변수로 받아온 데이터를 사용하도록 할 수 있습니다
                # ...

            except socket.error:
                # 통신이 끊어졌을 때 소켓을 닫고 다시 시작합니다
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
                    print("socket restart")

thread = DataGeneratorThread('localhost', 1234)
thread.start()