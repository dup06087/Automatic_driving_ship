import threading
import socket
import time

def dict_to_str(d):
    items = []
    for k, v in d.items():
        items.append(f"{k}={v}")
    return ",".join(items)

class DataThread(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.running = False
        self.current_value = {"latitude": None, "longitude": None, "heading": None, "velocity": None}

    def run(self):
        self.running = True
        data_counter = 0
        while self.running:
            try:
                # 소켓 연결
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))

                # 데이터 수신 및 전송
                while self.running:
                    data = sock.recv(1024).decode().strip()
                    print(data)
                    if data.startswith('$GPHDT') or data.startswith('$GPRMC') or data.startswith('$GNHDT') or data.startswith('$GNRMC'):
                        tokens = data.split(',')
                        if tokens[0] == '$GPHDT' or tokens[0] == '$GNHDT':
                            try:
                                self.current_value['heading'] = tokens[1]
                            except ValueError:
                                self.current_value['heading'] = None
                        elif tokens[0] == '$GPRMC' or tokens[0] == '$GNRMC':
                            try:
                                self.current_value['latitude'] = tokens[3]
                                self.current_value['longitude'] = tokens[5]
                                self.current_value['velocity'] = tokens[7]
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
                sock.close()
                # 재접속 시도
                time.sleep(10)
                continue

    def stop(self):
        self.running = False

data_thread = DataThread('localhost', 5000)
data_thread.start()