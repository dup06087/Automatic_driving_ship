import serial, threading, time, atexit
from queue import Queue

# class SerialCommunicator:
#     def __init__(self, port, baudrate=115200):
#         self.port = port
#         self.baudrate = baudrate
#         self.serial_port = serial.Serial(self.port, self.baudrate, timeout=0.4)
#
#         # 수신 큐 정의
#         self.receive_queue = Queue()
#
#         # Thread setup for receiving
#         self.receive_thread = threading.Thread(target=self._data_receive_part)
#         # self.receive_thread.daemon = True
#         self.receive_thread.start()
#         print("thread_started")
#
#         # Thread setup for processing received data
#         self.process_receive_thread = threading.Thread(target=self._data_processing_part)
#         # self.process_receive_thread.daemon = True
#         self.process_receive_thread.start()
#         print("thread2_started")
#
#         self.lock = threading.Lock()
#
#
#     # receiving
#     # def _data_receive_part(self):
#     #     while True:
#     #         time.sleep(0.2)
#     #         data = self.serial_port.readline()
#     #         if data:
#     #             self.receive_queue.put(data)
#
#     def _data_receive_part(self):
#         while True:
#             time.sleep(0.2)
#
#             with self.lock: # 락 적용
#                 # 버퍼에 데이터가 있는지 확인
#                 waiting = self.serial_port.in_waiting
#                 data = None
#                 if waiting:
#                     # 버퍼의 모든 데이터 읽기
#                     buffer_data = self.serial_port.read(waiting)
#                     # 줄 단위로 분할
#                     lines = buffer_data.splitlines()
#                     # 마지막 줄만 선택
#                     data = lines[-1] if lines else None
#
#             if data:
#                 self.receive_queue.put(data)
#
#     # received data processing
#     def _data_processing_part(self):
#         while True:
#             time.sleep(0.1)
#             try:
#                 data = self.receive_queue.get(block=False)
#                 # data = byte format
#                 processed_data = self.process_received_data(data)
#                 print(f"Processed Data: {processed_data}")
#             except Exception as e:
#                 print("receive queue error : {}".format(e))
#
#
#     # 오버라이드 가능한 메서드
#     def process_received_data(self, data):
#         return data.decode('utf-8').strip()
#
#     def close(self):
#         self.serial_port.close()

class SerialCommunicator:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_port = serial.Serial(self.port, self.baudrate, timeout=0.4)

        # 수신 큐 정의
        self.receive_queue = Queue()

        # Thread setup for receiving
        self.receive_thread = threading.Thread(target=self._data_receive_part)
        # self.receive_thread.daemon = True
        self.receive_thread.start()
        print("thread_started")

        # Thread setup for processing received data
        self.process_receive_thread = threading.Thread(target=self._data_processing_part)
        # self.process_receive_thread.daemon = True
        self.process_receive_thread.start()
        print("thread2_started")

        self.lock = threading.Lock()

    def add_to_queue(self, data):
        with self.lock:
            self.receive_queue.put(data)

    def get_from_queue(self):
        with self.lock:
            if not self.receive_queue.empty():
                return self.receive_queue.get()
            return None

    # def _data_receive_part(self):
    #     while True:
    #         time.sleep(0.2)
    #
    #         # 버퍼에 데이터가 있는지 확인
    #         waiting = self.serial_port.in_waiting
    #         data = None
    #         if waiting:
    #             # 버퍼의 모든 데이터 읽기
    #             buffer_data = self.serial_port.read(waiting)
    #             # buffer_data = self.serial_port.readlines(waiting)
    #             # 줄 단위로 분할
    #             lines = buffer_data.splitlines()
    #             # 마지막 줄만 선택
    #             data = lines[-1] if lines else None
    #
    #         if data:
    #             self.add_to_queue(data)

    def _data_receive_part(self):
        while True:
            time.sleep(0.2)

            lines = []
            while self.serial_port.in_waiting:
                line = self.serial_port.readline()
                if line:
                    lines.append(line)

            # 버퍼의 모든 줄을 읽은 후 마지막 줄만 선택
            data = lines[-1] if lines else None

            if data:
                self.add_to_queue(data)

    # received data processing
    def _data_processing_part(self):
        while True:
            time.sleep(0.1)
            try:
                data = self.get_from_queue()
                if data:
                    # data = byte format
                    processed_data = self.process_received_data(data)
                    print(f"Processed Data: {processed_data}")
            except Exception as e:
                print("receive queue error : {}".format(e))

    # 오버라이드 가능한 메서드
    def process_received_data(self, data):
        return data.decode('utf-8').strip()

    def close(self):
        self.serial_port.close()

class serial_gnss(SerialCommunicator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_value = {'validity' : None, 'latitude' : None, 'longitude' : None, 'velocity' : None, 'time' :  None, 'date' : None, 'heading' : None, 'pitch' : None}
        self.data_counter = 0
        print("initialized gnss")
        # daemon
        # while True:
        #     time.sleep(0.1)

    # thread로 돌아가는 메인 코드
    def process_received_data(self, data):
        try:
            decoded_data = data.decode('utf-8').strip()

            if not decoded_data.startswith('$'):
                time.sleep(0.1)
                return

            tokens = decoded_data.split(',')
            print("tokens : ", tokens)
            header = tokens[0]

            if header in ['$GPRMC', '$GNRMC']:
                self._process_gnrmc_data(tokens)
                print("gnrmc_data processing done")
            elif header == '$PSSN':  # HRP
                self._process_pssn_data(tokens)
                print("pssn_data processing done")
            else:
                print("GNSS 데이터 오류 발생")
                return

            print("done processing")
            print("curent data : ", self.current_value)
        except Exception as e:
            print(f"Error processing data: {e}")

    def _process_gnrmc_data(self, tokens):
        try:
            validity = tokens[2]
            if validity == "V": # V : invalid, A : valid
                self.current_value['validity'] = validity
                return

            self.current_value['validity'] = validity
            lat_min = float(tokens[3])
            lat_deg = int(lat_min / 100)
            lat_min -= lat_deg * 100
            self.current_value['latitude'] = round(lat_deg + lat_min / 60, 8)

            lon_sec = float(tokens[5])
            lon_deg = int(lon_sec / 100)
            lon_min = (lon_sec / 100 - lon_deg) * 100
            self.current_value['longitude'] = round(lon_deg + lon_min / 60, 8)

            self.current_value['velocity'] = float(tokens[7])

        except ValueError as e:
            print(f"Error processing GNRMC data: {e}")


    def _process_pssn_data(self, tokens):
        try:
            self.current_value['time'] = tokens[2]
            self.current_value['date'] = tokens[3]
            self.current_value['heading'] = float(tokens[4])
            self.current_value['pitch'] = float(tokens[6])

        except ValueError as e:
            # when heading pitch is not comming heading pitch raw data comes '' not None
            print(f"Error heading pitch processing PSSN data: {e}")
            self.current_value['heading'] = None
            self.current_value['pitch'] = None


class serial_nucleo(SerialCommunicator):
    def __init__(self, port, baudrate=9600):
        super().__init__(port, baudrate)

        # Transmit queue and thread
        self.transmit_queue = Queue()
        self.process_transmit_thread = threading.Thread(target=self._data_transmission_part)
        # self.process_transmit_thread.daemon = True
        self.process_transmit_thread.start()

    def send_data(self, data):
        self.transmit_queue.put(data)

    def _data_transmission_part(self):
        while True:
            time.sleep(0.2)
            # data = None
            # while not self.transmit_queue.empty():  # 큐가 비어있지 않은 동안
            #     data = self.transmit_queue.get()  # 큐에서 데이터를 꺼내옵니다.
            data = self.transmit_queue.get()
            if data:
                processed_data = self.prepare_data_for_transmission(data)
                self.serial_port.write(processed_data)

    def prepare_data_for_transmission(self, data):
        mode_str = "AUTO"
        pwm_left_auto = 1200
        pwm_right_auto = 1500
        data_str = f"mode:{mode_str},PWML:{pwm_left_auto},PWMR:{pwm_right_auto}\n"
        return data_str.encode()

    # queue에서 받아온 것 처리해서 쓸모있는 것으로
    def process_received_data(self, data):
        decoded_data = data.decode('utf-8').strip()
        if "mode:" in decoded_data and "PWML:" in decoded_data and "PWMR:" in decoded_data:
            parsed_data = dict(item.split(":") for item in decoded_data.split(","))
            parsed_mode = str(parsed_data.get('mode', 'UNKNOWN').strip())
            parsed_pwml = int(parsed_data.get('PWML', '0').strip())
            parsed_pwmr = int(parsed_data.get('PWMR', '0').strip())
            print("parsed : {}, {}, {} ".format(parsed_mode, parsed_pwml, parsed_pwmr))
        else:
            print("Received unexpected data")
        return decoded_data

    def run(self):
        while True:
            time.sleep(0.2)
            try:
                self.send_data("123")
            except Exception as e:
                print(f"Nucleo communication error: {e}")
                time.sleep(0.005)

# serial_gnss("COM3")
# serial_nucleo("COM7")
# serial_nucleo("COM7").run()