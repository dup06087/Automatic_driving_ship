import threading
import socket
import serial
import time

def dict_to_str(d):
    items = []
    for k, v in d.items():
        items.append(f"{k}={v}")
    return ",".join(items)

class DataThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.running = False
        self.current_value = {"latitude": None, "longitude": None, "heading": None, "velocity": None}

    def run(self):
        self.running = True
        data_counter = 0
        while self.running:
            try:
                # 시리얼 포트 열기
                ser = serial.Serial(self.port, baudrate=115200)

                # 소켓 연결
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', 5001))

                # 데이터 수신 및 전송
                while self.running:
                    data = ser.readline().decode().strip()
                    print(data)
                    if data.startswith('$GPHDT') or data.startswith('$GPRMC') or data.startswith('$GNHDT') or data.startswith('$GNRMC'):
                        tokens = data.split(',')
                        # print(tokens)
                        # print("error1")
                        if tokens[0] == '$GPHDT' or tokens[0] == '$GNHDT':
                            try:
                                self.current_value['heading'] = tokens[1]
                            except ValueError:
                                self.current_value['heading'] = None
                            # print("error2")
                        elif tokens[0] == '$GPRMC' or tokens[0] == '$GNRMC':
                            try:
                                self.current_value['latitude'] = tokens[3]
                                self.current_value['longitude'] = tokens[5]
                                self.current_valu1e['velocity'] = tokens[7]
                            except ValueError:
                                continue

                        data_counter += 1
                        if data_counter % 2 == 0:
                            message = dict_to_str(self.current_value)
                            sock.sendall(message.encode())
                            data_counter = 0
                            print(message)

            except Exception as e:
                print(f'Error: {e}')
                ser.close()
                sock.close()
                # 재접속 시도
                time.sleep(10)
                continue

    def stop(self):
        self.running = False

data_thread = DataThread('COM6')
data_thread.start()