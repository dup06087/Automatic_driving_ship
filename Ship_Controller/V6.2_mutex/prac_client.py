import socket
import threading
import time
import json
import select
import copy

class Client:
    def __init__(self, receive_port=5004, send_port=5003):
        self.receive_port = receive_port
        self.send_port = send_port
        self.message = {"mode_pc_command": "SELF", "dest_latitude": None, "dest_longitude": None}
        self.data = self.init_data = {
            'dest_latitude': None, 'dest_longitude': None, 'mode_pc_command': "SELF", 'com_status': False,
            'mode_chk': None, 'pwml_chk': None, 'pwmr_chk': None,
            'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, 'cnt_destination': None,
            'distance': None, "waypoint_latitude": None, "waypoint_longitude": None,
            'velocity': None, 'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None,
            'IP': None, 'date': None, "longitude": 127.077618, "latitude": 37.633173,
        }
        self.obstacle_data = {}
        self.jetson_socket_status = False

    def send_messages(self, send_socket):
        while True:
            if self.validate_data(self.message):
                message = json.dumps(self.message) + '\n'
                try:
                    send_socket.send(message.encode())
                    print(f"Sent: {message}")
                except (BrokenPipeError, ConnectionResetError) as e:
                    print(f"Send connection error: {e}. Attempting to reconnect...")
                    break
            time.sleep(2)

    def receive_messages(self, receive_socket, data_buffer):
        while True:
            try:
                data = receive_socket.recv(1024)
                if data:
                    data_buffer += data
                    if b'\n' in data_buffer:
                        data_line, data_buffer = data_buffer.split(b'\n', 1)
                        received_dict = json.loads(data_line.decode('utf-8'))
                        self.data = received_dict
                        self.jetson_socket_status = True
                        print(f"Received: {self.data}")
            except ConnectionResetError:
                print("Receive connection lost.")
                break

    def run(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_socket:

                    send_socket.connect(('localhost', self.send_port))
                    print("Connected to the server for sending.")
                    receive_socket.connect(('localhost', self.receive_port))
                    print("Connected to the server for receiving.")
                    data_buffer = b''

                    send_thread = threading.Thread(target=self.send_messages, args=(send_socket,))
                    receive_thread = threading.Thread(target=self.receive_messages, args=(receive_socket, data_buffer))

                    send_thread.start()
                    receive_thread.start()

                    send_thread.join()
                    receive_thread.join()

            except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
                print(f"Error: {e}. Server is unavailable. Retrying in 5 seconds...")
                time.sleep(5)

    def validate_data(self, data):
        required_keys = ["mode_pc_command", "dest_latitude", "dest_longitude"]
        return all(key in data for key in required_keys)

if __name__ == "__main__":
    client = Client()
    client.run()
