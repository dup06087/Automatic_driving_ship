from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets
import socket
import threading
import json
import select
import traceback
import time
import copy

# all client
class Worker(QtCore.QThread):
    def __init__(self):
        super().__init__()
        # self.message : jetson에게 보내는 메세지
        self.message = {"mode_pc_command": "SELF", "dest_latitude": None, "dest_longitude": None}
        # self.data : jetson한테 받는 메세지
        self.data = {
            # dest_latitude, dest_longitude : list, connected with pc def start_driving
            'dest_latitude': None, 'dest_longitude': None, 'mode_pc_command': "SELF", 'com_status': False, # pc get params
            'mode_chk': "SELF", 'pwml_chk': None, 'pwmr_chk': None, # nucleo get params
            'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, 'cnt_destination' : None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None, # auto drving
            # gnss get params below
            'velocity': None, 'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None, 'date': None,
            "longitude": 127.077618, "latitude": 37.633173,
            # gnss end
            } # cf. com_status undefined

        self.init_data = {
            # dest_latitude, dest_longitude : list, connected with pc def start_driving
            'dest_latitude': None, 'dest_longitude': None, 'mode_pc_command': "SELF", 'com_status': False, # pc get params
            'mode_chk': "SELF", 'pwml_chk': None, 'pwmr_chk': None, # nucleo get params
            'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, 'cnt_destination' : None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None, # auto drving
            # gnss get params below
            'velocity': None, 'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None, 'date': None,
            "longitude": 127.077618, "latitude": 37.633173,
            # gnss end
            } # cf. com_status undefined

        self.jetson_socket_status = False

        self.recv_host, self.recv_port, self.send_host, self.send_port = self.get_network_settings()

    def get_network_settings(self):
        # 설정을 반환하는 코드 작성 (예제에서는 'Lan port' 사용)
        self.server_ip = '223.171.136.213'
        return (self.server_ip, 5003, self.server_ip, 5004)
        # return '192.168.0.21', 5003, '192.168.0.21', 5004

    def run(self):
        recv_socket = None
        send_socket = None
        print("Receiving readying")
        data_buffer = b''

        while True:
            try:
                if not recv_socket:
                    self.data = copy.deepcopy(self.init_data)
                    self.jetson_socket_status = False
                    recv_socket = self.create_socket(self.recv_host, self.recv_port)
                if not send_socket:
                    self.data = copy.deepcopy(self.init_data)
                    self.jetson_socket_status = False
                    send_socket = self.create_socket(self.send_host, self.send_port)

                if recv_socket is not None and send_socket is not None:
                    try:
                        _, ready_to_write, _ = select.select([send_socket], [send_socket], [], 1)
                        # print(ready_to_read, ready_to_write, _)
                        _, ready_to_read, _ = select.select([recv_socket], [recv_socket], [], 1)
                        # print(ready_to_read, ready_to_write, _)
                        if not ready_to_write or not ready_to_read:
                            self.jetson_socket_status = False

                        self.handle_receive_data(ready_to_read, recv_socket, data_buffer)

                        self.handle_send_data(ready_to_write, send_socket)

                    except Exception as e:
                        self.data = copy.deepcopy(self.init_data)
                        self.jetson_socket_status = False
                        recv_socket = self.create_socket(self.recv_host, self.recv_port)
                        send_socket = self.create_socket(self.send_host, self.send_port)

                        print("regenerated : {}".format(e))

                time.sleep(0.05)

            except (socket.error, ConnectionResetError, json.JSONDecodeError, TypeError, ValueError) as e:
                self.data = copy.deepcopy(self.init_data)
                self.jetson_socket_status = False
                self.handle_exception(e, recv_socket, send_socket)

            except Exception as e:
                self.data = copy.deepcopy(self.init_data)
                self.jetson_socket_status = False
                print(f"error : ", e)

    def create_socket(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        return s

    # self.data값을 읽으면 됨
    def handle_receive_data(self, ready_to_read, recv_socket, data_buffer):
        try:
            if ready_to_read:
                data = recv_socket.recv(1024)
                if data:
                    data_buffer += data
                    if b'\n' in data_buffer:
                        data_line, data_buffer = data_buffer.split(b'\n', 1)

                        received_dict = json.loads(data_line.decode('utf-8'))

                        self.data = received_dict
                        self.jetson_socket_status = True

                        print(self.data)

        except Exception as e:
            print(f"??? : {e}, {data}")
            data_buffer = b''

    # self.message를 변경하면 jetson에 알아서 보내짐
    def handle_send_data(self, ready_to_write, send_socket):
        if ready_to_write:
            if self.validate_data(self.message):
                message = json.dumps(self.message) + '\n'
                send_socket.sendall(message.encode())
                print("sened socket")
                self.jetson_socket_status = True

    def handle_exception(self, e, recv_socket, send_socket):
        self.data['com_status'] = False
        print(f"Error: {e}")
        traceback.print_exc()
        self.close_socket(recv_socket)
        self.close_socket(send_socket)
        time.sleep(1)

    def close_socket(self, s):
        if s:
            s.close()
            print("socket.closed")

    def validate_data(self, data):
        required_keys = ["mode_pc_command", "dest_latitude", "dest_longitude"]
        return all(key in data for key in required_keys)

if __name__ == "__main__":
    worker = Worker()
    worker.run()
