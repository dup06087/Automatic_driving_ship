import sys
import threading

import keyboard
from PyQt5.QtCore import QThread
import socket
import json
import time
from PyQt5.QtWidgets import QApplication


class Client(QThread):
    def __init__(self, receive_port=5004, send_port=5003, receive_obstacle_port=5005):
        super(Client, self).__init__()
        self.receive_port = receive_port
        self.send_port = send_port
        self.receive_obstacle_port = receive_obstacle_port
        self.send_data = {"mode_pc_command": "SELF", "dest_latitude": None, "dest_longitude": None}
        self.received_data = {}
        self.obstacle_data = []

        self.jetson_ip = '117.17.187.211'

        self.socket_statuses = {
            "send_socket": False,
            "receive_socket": False,
            "receive_obstacle_socket": False
        }

        self.is_communicating = False

    def run(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_obstacle_socket:

                    receive_socket.settimeout(3)
                    receive_obstacle_socket.settimeout(3)

                    send_socket.connect((self.jetson_ip, self.send_port))
                    receive_socket.connect((self.jetson_ip, self.receive_port))
                    receive_obstacle_socket.connect((self.jetson_ip, self.receive_obstacle_port))

                    # 각 함수를 별도의 스레드로 실행
                    send_thread = threading.Thread(target=self.handle_send_data, args=(send_socket,))
                    receive_thread = threading.Thread(target=self.handle_receive_data, args=(receive_socket,))
                    receive_obstacle_thread = threading.Thread(target=self.handle_receive_obstacle_data,
                                                     args=(receive_obstacle_socket,))

                    send_thread.start()
                    receive_thread.start()
                    receive_obstacle_thread.start()

                    self.is_communicating = True
                    while self.is_communicating:
                        print("communicating well")
                        time.sleep(5)

                    print("socket restart")

            except (ConnectionRefusedError, ConnectionResetError, OSError, BrokenPipeError, socket.timeout) as e:
                print(f"Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)


    def update_socket_status(self, socket_name, status):
        self.socket_statuses[socket_name] = status

    def handle_send_data(self, send_socket):
        self.update_socket_status("send_socket", True)
        self.last_sent_command = None  # 마지막으로 전송된 명령을 추적하기 위한 변수
        send_socket.settimeout(1.0)  # 5초 후에 타임아웃되도록 설정

        while True:
            # check connection status
            try:
                send_socket.sendall("heartbeat".encode())  # 'a' 대신 'heartbeat'으로 변경
                print("sent heart beat")
            except:
                self.update_socket_status("send_socket", False)
                print("not sent heart beat")
                break
            try:
                if self.send_data != self.last_sent_command and self.validate_data(self.send_data):
                    print("in the if")
                    try:
                        print("in the try")
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

                    except KeyboardInterrupt:
                        send_socket.close()
                        break

                    except Exception as e:
                        print("Handle send data error: ", e)
                        self.update_socket_status("send_socket", False)
                        break
            except Exception as e:
                print(e)
            time.sleep(0.2)  # 데이터 확인 간격
        self.is_communicating = False

    def handle_receive_data(self, receive_socket):
        self.update_socket_status("receive_socket", True)
        data = ""
        while True:
            try:
                try:
                    data = receive_socket.recv(1024)
                    if not data:  # 빈 문자열이 반환되면 루프 종료z
                        break

                    received_dict = json.loads(data.decode('utf-8'))
                    self.received_data = received_dict
                    self.update_socket_status("receive_socket", True)
                    # print(f"recv {self.received_data}")

                except json.JSONDecodeError as e:
                    print("receive json error : ", e)
                    data = ""

            except (BrokenPipeError, TimeoutError):
                print("receive brokenpipe error")
                self.update_socket_status("receive_socket", False)
                break

            except KeyboardInterrupt:
                print("keyboard interrupt")
                receive_socket.close()
                break

            except Exception as e:
                print("handle receive data : ", e)
                self.update_socket_status("receive_socket", False)
                break

            time.sleep(0.01)
        self.is_communicating = False

    def handle_receive_obstacle_data(self, receive_socket):
        # TODO : overflow 해결해야함함
        data_buffer = ""
        self.update_socket_status("receive_obstacle_socket", True)

        while True:
            try:
                data = receive_socket.recv(1024).decode().strip()
                if not data:
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
                        # print("obstacle : ", self.obstacle_data)

                        # Discard processed data
                        data_buffer = data_buffer[end_index + 3:]

                    except json.JSONDecodeError as e:
                        print("obstacle error : ", e)
                        # Clear the buffer to avoid processing the same erroneous data again
                        data_buffer = ""

                elif start_index != -1 and end_index == -1:
                    # print("index not found")
                    # ']]\n' not found, keep the buffer and wait for more data
                    continue

                else:
                    print("???")

            except (ConnectionError, socket.error, TimeoutError, BrokenPipeError) as e:
                print("obstacle socket error:", e)
                self.update_socket_status("receive_obstacle_socket", False)
                self.obstacle_data = []
                break

            except KeyboardInterrupt:
                print("keyboard interrupt commute with jetson")
                receive_socket.close()
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

            time.sleep(0.1)

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