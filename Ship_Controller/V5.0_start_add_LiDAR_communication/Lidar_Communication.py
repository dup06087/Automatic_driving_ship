import socket
import json
import time
import threading

class Client:
    def __init__(self, host='localhost', port=5010):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

        try:
            while True:
                try:
                    print("running")
                    # 수신 데이터 처리
                    data = self.client_socket.recv(1024).strip()
                    received_dict = json.loads(data.decode('utf-8'))
                    print(f"Received data: {received_dict}")

                except (json.JSONDecodeError, TypeError, ValueError):
                    print("Error occurred while decoding received data")
                    continue

                try:
                    # 송신 데이터 처리
                    # send_data = [dest_lat_evasion, dest_lon_evasion]
                    send_data = "hihi"
                    self.client_socket.sendall(send_data.encode('utf-8'))
                    print("Sended Data : ", send_data)
                except:
                    print("nopppe")

                time.sleep(0.1)

        except Exception as e:
            print(f"Connection Error: {e}")

        finally:
            self.client_socket.close()
            print("Disconnected")

def run_client():
    host = "localhost"
    port = 5010
    client = Client(host, port)
    client.start()

if __name__ == "__main__":
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
    while True:
        try:
            if not client_thread.is_alive():
                client_thread = threading.Thread(target=run_client)
                client_thread.start()
                print("restart t1")
        except:
            print("t1 restart failed")

