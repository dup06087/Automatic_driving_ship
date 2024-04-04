import sys
import threading

import keyboard
from PyQt5.QtCore import QThread
import socket
import json
import time
from PyQt5.QtWidgets import QApplication

class Client(QThread):
    def __init__(self, send_coeff_port=5002, receive_port=5004, send_port=5003, receive_obstacle_port=5005):
        super(Client, self).__init__()
        self.receive_port = receive_port
        self.send_port = send_port
        self.send_coeff_port = send_coeff_port
        self.receive_obstacle_port = receive_obstacle_port
        self.init_values()
        self.send_data = {"mode_pc_command": "SELF", "dest_latitude": None, "dest_longitude": None}
        self.send_coeff_data = {"coeff_kf" : self.coeff_Kf_value,"coeff_kd" : self.coeff_Kd_value, "voxel_size" : self.coeff_voxel_size_value, "intensity" : self.coeff_intensity_value, "dbscan_eps" : self.coeff_eps_value, "dbscan_minpoints" : self.coeff_minpoints_value, "coeff_vff_repulsive_force" : self.coeff_vff_force_value}
        self.received_data = {}
        self.obstacle_data = []

        # self.jetson_ip = '117.17.187.187'
        self.jetson_ip = '223.171.136.213'
        # self.jetson_ip = '192.168.0.8'

        self.socket_statuses = {
            "send_socket": True,
            "send_coeff_socket": True,
            "receive_socket": True,
            "receive_obstacle_socket": True
        }

        self.is_communicating = False

    # when program started gone > txt file need
    def init_values(self):
        self.coeff_Kf_value = None
        self.coeff_Kd_value = None
        self.coeff_voxel_size_value = None
        self.coeff_intensity_value = None
        self.coeff_eps_value = None
        self.coeff_minpoints_value = None
        self.coeff_vff_force_value = None

        config_filename = 'config.txt'
        try:
            with open(config_filename, 'r') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    setattr(self, key, float(value))
        except FileNotFoundError:
            print(f"{config_filename} not found. Creating a new one with default values.")
            self.set_default_values()
            self.write_default_values_to_file(config_filename)
        except ValueError:
            print("Error processing configuration file. Using default values.")
            self.set_default_values()
        except Exception as e:
            print("coeff init error : ", e)

        print("init coeff value done")

    def set_default_values(self):
        # 모든 설정 값을 None으로 설정
        self.coeff_Kf_value = 1  # 예시 기본값
        self.coeff_Kd_value = 1  # 예시 기본값
        self.coeff_voxel_size_value = 0.05  # 예시 기본값
        self.coeff_intensity_value = 5  # 예시 기본값
        self.coeff_eps_value = 0.1  # 예시 기본값
        self.coeff_minpoints_value = 5  # 예시 기본값
        self.coeff_vff_force_value = 1  # 예시 기본값

    def write_default_values_to_file(self, filename):
        with open(filename, 'w') as file:
            file.write(f"coeff_Kf_value={self.coeff_Kf_value}\n")
            file.write(f"coeff_Kd_value={self.coeff_Kd_value}\n")
            file.write(f"coeff_voxel_size_value={self.coeff_voxel_size_value}\n")
            file.write(f"coeff_intensity_value={self.coeff_intensity_value}\n")
            file.write(f"coeff_eps_value={self.coeff_eps_value}\n")
            file.write(f"coeff_minpoints_value={self.coeff_minpoints_value}\n")
            file.write(f"coeff_vff_force_value={self.coeff_vff_force_value}\n")

    def run(self):
        while True:
            try:
                print("regenerating")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_obstacle_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_coeff_socket:
                    self.is_communicating = True

                    send_socket.settimeout(5)
                    send_coeff_socket.settimeout(5)
                    receive_socket.settimeout(5)
                    receive_obstacle_socket.settimeout(5)

                    send_socket.connect((self.jetson_ip, self.send_port))
                    send_coeff_socket.connect((self.jetson_ip, self.send_coeff_port))
                    receive_socket.connect((self.jetson_ip, self.receive_port))
                    receive_obstacle_socket.connect((self.jetson_ip, self.receive_obstacle_port))

                    # 각 함수를 별도의 스레드로 실행
                    send_thread = threading.Thread(target=self.handle_send_data, args=(send_socket,))
                    send_coeff_thread = threading.Thread(target=self.handle_send_coeff_data, args=(send_coeff_socket,))

                    receive_thread = threading.Thread(target=self.handle_receive_data, args=(receive_socket,))
                    receive_obstacle_thread = threading.Thread(target=self.handle_receive_obstacle_data,
                                                     args=(receive_obstacle_socket,))

                    send_thread.start()
                    send_coeff_thread.start()
                    receive_thread.start()
                    receive_obstacle_thread.start()

                    while self.is_communicating:
                        print("communicating well")
                        time.sleep(5)

                    self.is_communicating = False
                    for key in self.socket_statuses.keys():
                        self.socket_statuses[key] = False

                    print("socket ended")

            except (ConnectionRefusedError, ConnectionResetError, OSError, BrokenPipeError, socket.timeout) as e:
                print(f"Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

            except Exception as e:
                print("communication unknown error : ", e)

    def update_socket_status(self, socket_name, status):
        self.socket_statuses[socket_name] = status

    def handle_send_data(self, send_socket):
        self.update_socket_status("send_socket", True)
        self.last_sent_command = None  # 마지막으로 전송된 명령을 추적하기 위한 변수
        send_socket.settimeout(5.0)  # 5초 후에 타임아웃되도록 설정

        prev_time_heartbeat = 0
        while self.is_communicating:
            try:
                try:
                    # Attempt to send a null byte to check socket status
                    send_socket.sendall(b'\x00')
                    # print("Socket is still alive.")
                except Exception as e:
                    print("Socket might be closed, error:", e)
                    self.update_socket_status("send_socket", False)
                    break
                time.sleep(0.1)

                if self.send_data != self.last_sent_command and self.validate_data(self.send_data):
                    try:
                        message = json.dumps(self.send_data) + '\n'
                        send_socket.sendall(message.encode())
                        self.last_sent_command = self.send_data  # 전송된 명령 업데이트
                        print("Sent to jetson: ", self.send_data)

                        try:
                            ack = send_socket.recv(1024).strip()
                            if ack.decode() != "ack":
                                print("No ack received. Resending...")
                                self.last_sent_command = None  # 재전송을 위해 None으로 설정
                                continue
                            else:
                                print("sended well")
                        except socket.timeout:
                            print("Socket receive timeout occurred - ack")
                            self.last_sent_command = None  # 재전송을 위해 None으로 설정
                            continue

                    except (BrokenPipeError, TimeoutError):
                        print("Send connection lost. Attempting to reconnect...")
                        self.update_socket_status("send_socket", False)
                        break

                    except Exception as e:
                        print("Handle send data error: ", e)
                        # self.update_socket_status("send_socket", False)
                        break

            except Exception as e:
                print("receive socket error : ", e)
            time.sleep(0.2)  # 데이터 확인 간격
        self.is_communicating = False

    def handle_send_coeff_data(self, send_socket):
        try:
            self.update_socket_status("send_coeff_socket", True)
            self.last_sent_coeff_command = None  # 마지막으로 전송된 명령을 추적하기 위한 변수
            send_socket.settimeout(5.0)  # 5초 후에 타임아웃되도록 설정

            while self.is_communicating:
                try:
                    # Attempt to send a null byte to check socket status
                    send_socket.sendall(b'\x00')
                    # print("Socket is still alive.")
                except Exception as e:
                    print("Socket might be closed, error:", e)
                    self.update_socket_status("send_coeff_socket", False)
                    break

                time.sleep(0.1)

                try:
                    if self.send_coeff_data != self.last_sent_coeff_command:
                        try:
                            message = json.dumps(self.send_coeff_data) + '\n'
                            send_socket.sendall(message.encode())
                            self.last_sent_coeff_command = self.send_coeff_data  # 전송된 명령 업데이트
                            try:
                                ack = send_socket.recv(1024).strip()
                                if ack.decode() != "ack":
                                    print("No ack received. Resending...")
                                    self.last_sent_coeff_command = None  # 재전송을 위해 None으로 설정
                                    continue
                                else:
                                    print("sended well")
                            except socket.timeout:
                                print("Socket receive timeout occurred - ack")
                                self.last_sent_coeff_command = None  # 재전송을 위해 None으로 설정
                                continue

                        except (BrokenPipeError, TimeoutError):
                            print("Send connection lost. Attempting to reconnect...")
                            self.update_socket_status("send_coeff_socket", False)
                            break

                        except Exception as e:
                            print("Handle send data error: ", e)
                            # self.update_socket_status("send_coeff_socket", False)
                            break

                except Exception as e:
                    print("coeff error ", e)

                time.sleep(0.1)  # 데이터 확인 간격

            self.is_communicating = False

        except Exception as e:
            print("coeff error : ", e)

    def handle_receive_data(self, receive_socket):
        self.update_socket_status("receive_socket", True)
        data = ""
        cnt_receive = 0
        while self.is_communicating:
            try:
                try:
                    data = receive_socket.recv(5120)
                    if not data:  # 빈 문자열이 반환되면 루프 종료z
                        break

                    received_dict = json.loads(data.decode('utf-8'))
                    self.received_data = received_dict
                    self.update_socket_status("receive_socket", True)
                    cnt_receive = 0
                    # print(f"recv {self.received_data}")

                except json.JSONDecodeError as e:
                    cnt_receive += 1
                    print("receive json error : ", e, " cnt : ", cnt_receive)
                    print("received error raw data : \n", data.decode('utf-8'))
                    data = ""
                    if cnt_receive >= 10:
                        break

            except (BrokenPipeError, TimeoutError):
                print("receive brokenpipe error")
                self.update_socket_status("receive_socket", False)
                break

            except Exception as e:
                print("handle receive data : ", e)
                self.update_socket_status("receive_socket", False)
                break

            time.sleep(0.05)
        self.is_communicating = False

    def handle_receive_obstacle_data(self, receive_socket):
        # TODO : overflow 해결해야함함
        data_buffer = ""
        self.update_socket_status("receive_obstacle_socket", True)
        cnt_obstacle = 0
        current_print_time = 0
        last_print_time = 0
        while self.is_communicating:
            try:
                data = receive_socket.recv(1024*5).decode().strip()
                # print("raw data : \n", data)
                # print("obstacle data : ", data)
                if not data:
                    cnt_obstacle += 1
                    print("obstacle error cnt : ", cnt_obstacle)
                    if cnt_obstacle >= 10:
                        print("communication error0")
                        break

                data_buffer += data

                # Find the last occurrence of '[[' and the first occurrence of ']]\n' after it
                start_index = data_buffer.rfind('[[')
                end_index = data_buffer.find(']]', start_index)

                if start_index != -1 and end_index != -1:
                    # Extract the message and process it
                    message = data_buffer[start_index:end_index + 3]  # Include ']]\n'
                    try:
                        obstacle_parsed_data = json.loads(message)
                        self.obstacle_data = obstacle_parsed_data
                        self.update_socket_status("receive_obstacle_socket", True)
                        print("obstacle : ", self.obstacle_data)

                        # Discard processed data
                        data_buffer = data_buffer[end_index + 3:]
                        cnt_obstacle = 0

                    except json.JSONDecodeError as e:
                        print("obstacle error : ", e)
                        # Clear the buffer to avoid processing the same erroneous data again
                        data_buffer = ""

                elif start_index != -1 and end_index == -1: # start index는 있고, end_index가 없음 > 아직다 안옴
                    cnt_obstacle += 1
                    if cnt_obstacle >= 10:
                        print("waiting buffer >> cnt : ", cnt_obstacle)
                    # print("index not found")
                    # ']]\n' not found, keep the buffer and wait for more data
                    continue

                elif start_index == -1 and end_index != -1: # 그럴 일 없지만 > 아직 다 안 온 것
                    cnt_obstacle += 1
                    if cnt_obstacle >= 10:
                        print("communication error2")
                    # print("index not found")
                    # ']]\n' not found, keep the buffer and wait for more data
                    continue

                else: # break는 아니었고, "[" , "]" 둘 다 없음, 아무것도 detected 된 것이 없을때, 빈 리스트 옴
                    current_print_time = time.time()
                    if current_print_time - last_print_time >= 1:
                        print("no obstacle detected")
                        last_print_time = current_print_time

                time.sleep(0.02)

            except (ConnectionError, socket.error, TimeoutError, BrokenPipeError) as e:
                print("obstacle socket error:", e)
                self.update_socket_status("receive_obstacle_socket", False)
                self.obstacle_data = []
                break

            except socket.timeout:
                print("Timeout occurred, server may have disconnected.")
                self.update_socket_status("receive_obstacle_socket", False)
                self.obstacle_data = []
                break

            except Exception as e:
                print("Unhandled exception:", e)
                self.update_socket_status("receive_obstacle_socket", False)
                self.obstacle_data = []
                break

            time.sleep(0.2) # 이거 줄여야 하는거 아닌가

        self.is_communicating = False

    def validate_data(self, data):
        required_keys = ["mode_pc_command", "dest_latitude", "dest_longitude"]
        return all(key in data for key in required_keys)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # Qt 응용 프로그램 인스턴스 생성
    client = Client()
    client.start()  # QThread 시작

    all(client.socket_statuses.values())

    time_prev = 0
    while True:
        time_ = time.time()
        if time_ - time_prev >= 1:
            print("from jetson obstacle data : ", client.obstacle_data)
            print("from jetson : ", client.received_data)
            print("to jetson : ", client.send_data)
            time_prev = time_

    app.exec_()  # 이벤트 루프 시작