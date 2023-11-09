from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets
import socket
import threading
import json
import select
import traceback
import time

# all client
class Worker(QtCore.QThread):
    def __init__(self):
        super().__init__()
        # self.message : jetson에게 보내는 메세지
        self.message = {"mode_jetson": "SELF", "dest_latitude": None, "dest_longitude": None}
        # self.data : jetson한테 받는 메세지
        self.data = {'mode_jetson': "SELF",'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None,
                            'pwmr_auto' : None, 'pwml_sim' : None, 'pwmr_sim' : None, "latitude": 37.63124688, "longitude": 127.07633361,
                            'dest_latitude': None, 'dest_longitude' : None, 'velocity': None,
                            'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'date' : None, 'distance' : None}

        self.flag_auto_driving = None
        self.connection = False  # 속성 초기화
        self.recv_host, self.recv_port, self.send_host, self.send_port = self.get_network_settings()

    def get_network_settings(self):
        # 설정을 반환하는 코드 작성 (예제에서는 'Lan port' 사용)
        # return '223.171.136.213', 5003, '223.171.136.213', 5004
        return '192.168.0.21', 5003, '192.168.0.21', 5004

    def run(self):
        stop_event = threading.Event()
        recv_socket = None
        send_socket = None
        print("Receiving readying")
        data_buffer = b''

        while not stop_event.is_set():
            try:
                if not recv_socket:
                    recv_socket = self.create_socket(self.recv_host, self.recv_port)
                if not send_socket:
                    send_socket = self.create_socket(self.send_host, self.send_port)

                ready_to_read, ready_to_write, _ = select.select([recv_socket], [send_socket], [], 1)
                self.handle_receive_data(ready_to_read, recv_socket, data_buffer)
                self.handle_send_data(ready_to_write, send_socket)

                time.sleep(0.05)
            except (socket.error, ConnectionResetError, json.JSONDecodeError, TypeError, ValueError) as e:
                self.handle_exception(e, recv_socket, send_socket)

        self.close_socket(recv_socket)
        self.close_socket(send_socket)

    def create_socket(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        return s

    def handle_receive_data(self, ready_to_read, recv_socket, data_buffer):
        if ready_to_read:
            data = recv_socket.recv(1024)
            if data:
                data_buffer += data
                if b'\n' in data_buffer:
                    data_line, data_buffer = data_buffer.split(b'\n', 1)
                    received_dict = json.loads(data_line.decode('utf-8'))
                    self.connection = True
                    if self.validate_data(received_dict):
                        self.data = received_dict

    def handle_send_data(self, ready_to_write, send_socket):
        if ready_to_write and self.flag_auto_driving:
            if self.validate_data(self.message):
                message = json.dumps(self.message) + '\n'
                send_socket.sendall(message.encode())
                self.connection = True
                self.flag_auto_driving = False

    def handle_exception(self, e, recv_socket, send_socket):
        self.connection = False
        print(f"Error: {e}")
        traceback.print_exc()
        self.close_socket(recv_socket)
        self.close_socket(send_socket)
        time.sleep(1)

    def close_socket(self, s):
        if s:
            s.close()

    def validate_data(self, data):
        required_keys = ["mode_jetson", "dest_latitude", "dest_longitude"]
        return all(key in data for key in required_keys)