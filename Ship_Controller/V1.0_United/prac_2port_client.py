from PyQt5.QtCore import QThread, pyqtSignal
import socket

HOST = '127.0.0.1'  # 로컬 루프백 주소
PORT1 = 8000  # 송신용 포트 번호
PORT2 = 9000  # 수신용 포트 번호


class ReceiverThread(QThread):
    message_received = pyqtSignal(str)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT2))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    self.message_received.emit(message)


class SenderThread(QThread):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT1))
            s.sendall(self.message.encode())


while True:
    message = "hi server"
    sender_thread = SenderThread(message)
    sender_thread.start()

    receiver_thread = ReceiverThread()
    receiver_thread.message_received.connect(print)
    receiver_thread.start()

    sender_thread.wait()
    receiver_thread.wait()