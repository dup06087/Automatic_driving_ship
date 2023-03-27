import socket
import time
import random

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 8000))
        server_socket.listen()
        print("Server started")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Client connected from {addr}")

            while True:
                print("hi")
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    sensor_data = {
                        'mode': random.random(),
                        'pwml': random.random(),
                        'pwmr': random.random(),
                        'position': random.random(),
                        'destination': random.random(),
                        'velocity': random.random(),
                        'heading': random.random(),
                        'roll': random.random(),
                        'pitch': random.random(),
                        'validity': random.random(),
                        'time': random.random(),
                        'IP': random.random(),
                        'com_status': random.random(),
                    }
                    client_socket.sendall(str(sensor_data).encode())

                except socket.error as err:
                    print(f"Socket error: {err}")
                    break

            client_socket.close()
            print(f"Client disconnected from {addr}")

if __name__ == "__main__":
    main()