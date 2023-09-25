import serial, threading, time, atexit
from queue import Queue

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
    # receiving
    def _data_receive_part(self):
        while True:
            data = self.serial_port.readline()
            print("read data : ", data)
            if data:
                self.receive_queue.put(data)

    # received data processing
    def _data_processing_part(self):
        while True:
            data = self.receive_queue.get()
            if data:
                #data = byte format
                print("data : ", data)
                processed_data = self.process_received_data(data)
                print(f"Processed Data: {processed_data}")

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


class SerialTransceiver(SerialCommunicator):
    def __init__(self, port, baudrate=115200):
        super().__init__(port, baudrate)
        self.transmit_queue = Queue()

        # Thread setup for processing transmit data and sending
        self.process_transmit_thread = threading.Thread(target=self._data_transmission_part)
        # self.process_transmit_thread.daemon = True
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


class serial_nucleo(SerialTransceiver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = kwargs.get('port')  # or "COM7" or "/dev/tty_nucleo_f401re2"
        self.baudrate = 115200
        self.ser_nucleo = serial.Serial(self.port, baudrate=self.baudrate, timeout=0.4)
        # atexit.register(self.close_serial_port, self.ser_nucleo)

    def process_received_data(self, data):
        print("process received data start")
        # Decode and parse the received data
        decoded_data = data.decode('utf-8').strip()
        print("decoded_data : ", decoded_data)
        print("decoded_data type : ", type(decoded_data))
        # Check if the data is valid
        if self.is_valid_data(decoded_data):
            print("valid data came")
            parsed_data = dict(item.split(":") for item in decoded_data.split(","))
            # self.current_value['mode_chk'] = str(parsed_data.get('mode', 'UNKNOWN').strip())
            # self.current_value['pwml'] = int(parsed_data.get('pwm_left', '0').strip())
            # self.current_value['pwmr'] = int(parsed_data.get('pwm_right', '0').strip())
        else:
            print("nucleo sent unexpected data")
        return decoded_data

    def prepare_data_for_transmission(self, data):
        # Prepare the data string for transmission
        # mode_str = self.current_value['mode_jetson']
        # pwm_left_auto = int(self.current_value['pwml_auto'] if self.current_value['pwml_auto'] is not None else 1500)
        # pwm_right_auto = int(self.current_value['pwmr_auto'] if self.current_value['pwmr_auto'] is not None else 1500)
        # data_str = f"mode:{mode_str},pwm_left:{pwm_left_auto},pwm_right:{pwm_right_auto}"
        # return data_str.encode('utf-8')
        return data.encode('utf-8')

    def is_valid_data(self, data):
        # Define the validation logic for the received data
        print("invalid data came")
        return "mode:" in data and "pwm_left:" in data and "pwm_right:" in data

    def run(self):
        while True:
            try:
                print("ready to try")
                self.send_data("mode:AUTO,pwm_left:2,pwm_right:3")  # !!! put data here
                print("sended_data")
                print("")
                # received_data = self._data_receive_part()
                # print("received_data")
                # self.process_received_data(received_data)
                # print("received data processed")
                time.sleep(0.1)
            except Exception as e:
                print(f"Nucleo communication error: {e}")
                time.sleep(0.005)

serial_nucleo("COM7").run()