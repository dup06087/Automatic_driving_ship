import socket
import threading
import time
import json
import subprocess

class Server:
    def __init__(self, receive_port=5003, send_port=5004):
        self.receive_port = receive_port
        self.send_port = send_port
        self.data_to_send = {"a": 1}  # 예시 데이터

    def receive_messages(self, receive_socket):
        while True:
            try:
                data = receive_socket.recv(1024)
                if not data:
                    break
                try:
                    received_data = json.loads(data.decode())
                    print(f"Received: {received_data}")
                except json.JSONDecodeError:
                    print("Received non-JSON data.")
            except ConnectionResetError:
                print("Receive connection lost.")
                break

    def send_messages(self, send_socket):
        while True:
            try:
                message = json.dumps(self.data_to_send) + '\n'
                send_socket.send(message.encode())
                print(f"Sent: {message}")
                time.sleep(2)
            except BrokenPipeError:
                print("Send connection lost. Attempting to reconnect...")
                break
            except ConnectionResetError:
                print("Connection was reset by the client. Attempting to reconnect...")
                break

    def run(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receive_socket, \
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_socket:

                    self.kill_process_using_port(self.receive_port)
                    self.kill_process_using_port(self.send_port)

                    receive_socket.bind(('0.0.0.0', self.receive_port))
                    receive_socket.listen(1)
                    print(f"Receiving server listening on port {self.receive_port}")

                    send_socket.bind(('0.0.0.0', self.send_port))
                    send_socket.listen(1)
                    print(f"Sending server listening on port {self.send_port}")

                    receive_client, _ = receive_socket.accept()
                    print("Accepted receive connection")

                    send_client, _ = send_socket.accept()
                    print("Accepted send connection")

                    receive_thread = threading.Thread(target=self.receive_messages, args=(receive_client,))
                    send_thread = threading.Thread(target=self.send_messages, args=(send_client,))

                    receive_thread.start()
                    send_thread.start()

            except (OSError, ConnectionResetError) as e:
                print(f"Error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def kill_process_using_port(self, port_number):
        try:
            result = subprocess.check_output(f"lsof -i :{port_number} | grep LISTEN | awk '{{print $2}}'", shell=True).decode().strip()
            if result:
                process_id = result.split('\n')[0]
                subprocess.run(f"kill -9 {process_id}", shell=True)
                print(f"Killed process {process_id} using port {port_number}")
            else:
                print(f"No process using port {port_number}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    server = Server()
    server.run()
