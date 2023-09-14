import serial
from queue import Queue
import threading

class SerialCommunicator:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_port = serial.Serial(self.port, self.baudrate, timeout=0.4)

        # 수신 큐 정의
        self.receive_queue = Queue()

        # Thread setup for receiving
        self.receive_thread = threading.Thread(target=self._data_receive_part)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # Thread setup for processing received data
        self.process_receive_thread = threading.Thread(target=self._data_processing_part)
        self.process_receive_thread.daemon = True
        self.process_receive_thread.start()

    def _data_receive_part(self):
        while True:
            data = self.serial_port.readline()
            if data:
                self.receive_queue.put(data)

    def _data_processing_part(self):
        while True:
            data = self.receive_queue.get()
            if data:
                processed_data = self.process_received_data(data)
                print(f"Processed Data: {processed_data}")

    # 오버라이드 가능한 메서드
    def process_received_data(self, data):
        return data.decode('utf-8').strip()

    def close(self):
        self.serial_port.close()


class SerialTransceiver(SerialCommunicator):
    def __init__(self, port, baudrate=115200):
        super().__init__(port, baudrate)
        self.transmit_queue = Queue()

        # Thread setup for processing transmit data and sending
        self.process_transmit_thread = threading.Thread(target=self._data_transmission_part)
        self.process_transmit_thread.daemon = True
        self.process_transmit_thread.start()

    def _data_transmission_part(self):
        while True:
            data = self.transmit_queue.get()
            if data:
                processed_data = self.prepare_data_for_transmission(data)
                self.serial_port.write(processed_data)

    def prepare_data_for_transmission(self, data):
        return data.encode('utf-8')

    # 이제 데이터를 큐에 추가만 해놓으면, 스레드가 처리하고 보냅니다.
    def send_data(self, data):
        self.transmit_queue.put(data)


class serial_gnss(SerialCommunicator):
    def process_received_data(self, data):
        # 장비 1을 위한 데이터 처리 로직
        decoded_data = data.decode('utf-8').strip()
        # ... 여기에 추가 처리
        return decoded_data


class serial_nucleo(SerialTransceiver):
    def process_received_data(self, data):
        # 장비 2를 위한 데이터 처리 로직
        decoded_data = data.decode('utf-8').strip()
        # ... 여기에 추가 처리
        return decoded_data

    def prepare_data_for_transmission(self, data):
        # 장비 2을 위한 송신 데이터 처리 로직
        # ... 여기에 추가 처리
        return data.encode('utf-8')