import math
import queue
import socket
import time
from haversine import haversine
import threading
import serial
import json
import random

class boat:
    def __init__(self):
        self.end = 0
        self.flag_exit = False
        self.destLat = []
        self.destLng = []
        self.is_driving = False
        for i in range(20):
            self.destLat.append('0')
            self.destLng.append('0')  ################initialize target destination list

        self.err_prev = 0
        self.time_prev = 0

        QUEUE_SIZE = 30
        self.mq = queue.Queue(QUEUE_SIZE)
        self.sendToMbedQ = queue.Queue(QUEUE_SIZE)
        self.heading = 0
        self.latnow = 0
        self.lngnow = 0
        self.sendToPc = ""

        self.destindex_max = 20
        self.isready = False
        self.isdriving = False
        self.isfirst = True
        # enddriving="0"
        self.driveindex = 0
        self.recDataPc1 = "0x6,DX,37.13457284,127.98545235,SELF,0,0x3"

        ## GNSS
        # self.current_value = {'mode': None, 'pwml': None, 'pwmr': None, "latitude": None, "longitude": None,
        #                     'velocity': None,
        #                     'heading': None, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
        #                     'com_status': None, 'date' : None}

        self.current_value = {'mode': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None, 'pwmr_auto' : None, "latitude": 37.633173, "longitude": 127.077618,
                         'velocity': None,
                         'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                         'com_status': None, 'date': None}

        # 'dest_latitude': None, 'dest_longitude': None,
        self.message = None

    def dict_to_str(self, d):
        items = []
        for k, v in d.items():
            items.append(f"{k} = {v}")
        return ",".join(items)

    def serial_gnss(self):  # NMEA data
        try:
            self.port_gnss = "COM6"
            ser_gnss = serial.Serial(self.port_gnss, baudrate=115200)
            data_counter = 0
            while True:
                # print("self.running running")
                data = ser_gnss.readline().decode().strip()
                # print(data)
                if data.sdftartswith('$'):
                    tokens = data.split(',')
                    if tokens[0] == '$PSSN': #HRP
                        try:
                            self.current_value['time'] = tokens[2] # UTC
                            self.current_value['date'] = tokens[3] # date
                            self.current_value['heading'] = tokens[4]
                            self.current_value['roll'] = tokens[5]
                            self.current_value['pitch'] = tokens[6]


                        except ValueError:
                            self.current_value['heading'] = None
                    # print("error2")
                    elif tokens[0] == '$GPRMC' or tokens[0] == '$GNRMC':
                        try:
                            self.current_value['latitude'] = tokens[3]
                            self.current_value['longitude'] = tokens[5]
                            self.current_value['velocity'] = tokens[7]
                        except ValueError:
                            continue

                    print("current value : ", self.current_value)

                    data_counter += 1
                    if data_counter % 2 == 0:
                            self.message = self.dict_to_str(self.current_value)
                            data_counter = 0
                            print(self.message)
                            print(self.current_value)
                            self.latnow = self.current_value['latitude']
                            self.heading = self.current_value['heading']
                            self.lngnow = self.current_value['longitude']

        except Exception as e:
                print(f'Error: {e}')

        finally:
            # ser_gnss.close() #필요가 없네?
            pass

    def serial_nucleo(self):  # rasp > mbed
        try:
            self.port_nucleo = "COM8"
            ser_nucleo = serial.Serial(self.port_nucleo, baudrate=115200)

            last_print_time = time.time()  # 마지막으로 출력한 시간 초기화

            while True:
                mode_str = self.current_value['mode']
                pwm_left = int(self.current_value['pwml_auto'] if self.current_value['pwml_auto'] is not None else 1800)
                pwm_right = int(self.current_value['pwmr_auto'] if self.current_value['pwmr_auto'] is not None else 1800)

                # data_str = f"<mode:{mode_str} pwm_left:{pwm_left} pwm_right:{pwm_right}>"
                data_str = f"mode:{mode_str},pwm_left:{pwm_left},pwm_right:{pwm_right}\n"
                '''nucleo는 data_str을 계속 받아, pwm_left_auto, pwm_right_auto로 둔다.'''
                # 데이터 전송
                ser_nucleo.write(data_str.encode())

                if ser_nucleo.in_waiting > 0:
                    # 데이터 읽어오기
                    data = ser_nucleo.readline().decode('utf-8').strip()  # 줄 바꿈 문자를 기준으로 데이터 읽기

                    # 데이터 파싱
                    try:
                        parsed_data = dict(item.split(":") for item in data.split(","))

                        mode_str = parsed_data.get('mode', 'UNKNOWN')
                        pwm_left = int(parsed_data.get('pwm_left', '0'))
                        pwm_right = int(parsed_data.get('pwm_right', '0'))

                        self.current_value['mode'] = mode_str.strip()

                    except:
                        pass

                current_time = time.time()
                if current_time - last_print_time >= 1:  # 마지막 출력 후 1초 경과 여부 확인
                    try:
                        print("Jetson >> Nucleo, send : ", data_str)
                        # print("Nucleo >> Received : ", data.decode('utf-8').strip())
                        print("Nucleo >> Jetson, Received : ", f"mode:{mode_str},pwm_left:{pwm_left},pwm_right:{pwm_right}")
                        last_print_time = current_time  # 마지막 출력 시간 업데이트
                    except:
                        pass
                time.sleep(0.2)

        except Exception as e:
            print("Nucleo : ", e)
            print("end serial_nucleo")

        finally:
            # ser_nucleo.close() #serial은 알아서 변수가 없어지나봄
            pass

    def socket_pc(self, client_socket = 'localhost', ip = 5001):  # rasp > pc
        server_socket_pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = ip
        server_address = (host, port)
        server_socket_pc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc.bind(server_address)
        server_socket_pc.listen(1)

        try:
            while True:
                # 클라이언트로부터의 연결 요청을 받음
                client_socket, client_address = server_socket_pc.accept()

                try:
                    # 연결한 클라이언트 정보 출력
                    print(f"Connected by {client_address}")

                    while True:
                        # 클라이언트로부터 데이터 수신
                        data = client_socket.recv(1024)

                        # 수신한 데이터가 없으면 반복문 종료
                        if not data:
                            break

                        try:
                            received_dict = json.loads(data.decode('utf-8'))
                            print("COM >> Jetson, received_dict : ", received_dict)
                            self.current_value['dest_latitude'] = received_dict['dest_latitude']
                            self.current_value['dest_longitude'] = received_dict['dest_longitude']
                            if self.current_value['dest_latitude'] is not None and self.current_value['dest_longitude'] and self.current_value['mode'] == "AUTO":
                                self.is_driving = True
                            else:
                                self.is_driving = False

                        except:
                            print("not get data yet")
                        # 수신한 데이터 출력

                        # 클라이언트에게 데이터 전송
                        message = self.current_value



                        message = json.dumps(message)
                        print("Jetson >> COM, send : ",message)
                        client_socket.sendall(message.encode())

                        time.sleep(1)

                except Exception as e:
                    # 예외 처리
                    print(f"pc 연결 Error: {e}")
                finally:
                    # 클라이언트 소켓 닫기
                    client_socket.close()

        except KeyboardInterrupt:
            # Ctrl+C를 눌러서 서버를 중지할 때 예외 처리
            print("Server stopped.")
        finally:
            # 서버 소켓 닫기
            server_socket_pc.close()

    def auto_driving(self):
        # while self.is_driving:
        print("in the auto driving")
        send_well = False
        last_print_time = time.time()  # 마지막으로 출력한 시간 초기화
        while True:
            while not send_well:
                try:
                    if self.current_value['latitude'] is not None and self.current_value['longitude'] is not None and self.current_value['heading'] is not None and self.current_value['dest_latitude'] is not None and self.current_value['dest_longitude']:
                        print("auto driving")
                        send_well = True
                    else:
                        time.sleep(1)
                        print("하나 이상의 데이터를 수신받지 못함, auto driving 실행 안 함")
                        # return
                except:
                    print("하나 이상의 데이터를 수신받지 못함, auto driving 실행 안 함")
                    time.sleep(1)
                    # return

            current_latitude = float(self.current_value['latitude'])
            current_longitude = float(self.current_value['longitude'])
            current_heading = float(self.current_value['heading'])
            destination_latitude = float(self.current_value['dest_latitude'])
            destination_longitude = float(self.current_value['dest_longitude'])



            # 헤딩 값을 -180에서 180 사이의 값으로 변환
            if current_heading > 180:
                current_heading = current_heading - 360

            # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
            self.distance_to_target = haversine((current_latitude, current_longitude),
                                           (destination_latitude, destination_longitude), unit='m')

            # 선박과 목적지가 이루는 선의 자북에 대한 각도 계산
            target_angle = math.degrees(
                math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))

            # 헤딩과 목표 각도 간의 차이 계산
            angle_diff = target_angle - current_heading
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # 각도 차이에 따른 throttle 및 roll 성분 계산
            throttle_component = self.distance_to_target * math.cos(math.radians(angle_diff))
            roll_component = self.distance_to_target * math.sin(math.radians(angle_diff))

            # PWM 값 계산
            Kf = 2.5
            # Kd = 0.25 * 800 / (2 * math.pi * 100)
            Kd = 0.318

            Uf = Kf * throttle_component
            Uf = max(1550 - 1500, min(Uf, 1750 - 1500))

            Ud = Kd * roll_component
            max_diff = 800 * 0.125
            Ud = max(-max_diff, min(Ud, max_diff))

            PWM_right = 1500 + Uf - Ud
            PWM_left = 1500 + Uf + Ud

            self.current_value["pwml_auto"] = int(PWM_left)
            self.current_value["pwmr_auto"] = int(PWM_right)

            current_time = time.time()
            if current_time - last_print_time >= 1:  # 마지막 출력 후 1초 경과 여부 확인
                try:
                    print(self.distance_to_target)
                    print("x :", throttle_component, "y : ", roll_component)
                    print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)
                    last_print_time = current_time  # 마지막 출력 시간 업데이트
                except:
                    pass
            time.sleep(0.1)

    def simulator(self):
        while True:
            print("simulator start")
            try:
                if self.current_value['pwml_auto'] == self.current_value['pwmr_auto'] and self.current_value['pwmr_auto'] != 1500:
                    # Go straight
                    lat_diff = 0.00001 * math.cos(math.radians(self.current_value['heading']))
                    lng_diff = 0.00001 * math.sin(math.radians(self.current_value['heading']))
                elif self.current_value['pwml_auto'] < self.current_value['pwmr_auto']:
                    # Turn right
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(self.current_value['heading'] - heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(self.current_value['heading'] - heading_diff))
                    self.current_value['heading'] -= math.degrees(heading_diff)
                elif self.current_value['pwml_auto'] > self.current_value['pwmr_auto']:
                    # Turn left
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(self.current_value['heading'] + heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(self.current_value['heading'] + heading_diff))
                    self.current_value['heading'] += math.degrees(heading_diff)

                else:
                    print("error")

                # lat_distance = haversine((self.current_value['latitude'], self.current_value['longitude']),
                #                          (self.current_value['dest_latitude'], self.current_value['dest_longitude']),
                #                          unit='m')

                self.current_value['latitude'] += lat_diff
                self.current_value['longitude'] += lng_diff

                if self.distance_to_target <= 10:
                    # Stop the boat
                    self.current_value['pwml_auto'] = 1500
                    self.current_value['pwmr_auto'] = 1500
                    print("Boat has reached the destination!")
                    break

                # Update current position

                time.sleep(1)
            except:
                print("Nope")
                time.sleep(1)


    def thread_start(self):
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)
        t3 = threading.Thread(target=self.socket_pc)
        t4 = threading.Thread(target=self.auto_driving)
        t5 = threading.Thread(target=self.simulator)
        while True:
            # print("executed")
            if self.end == 1:
                break
            # print("going1")
            # self.cs, self.addr = self.server_socket.accept()



            # print("done?")
            try:
                if not t1.is_alive():
                    t1 = threading.Thread(target=self.serial_gnss)
                    t1.start()
                    print("restart t1")
                if not t2.is_alive():
                    t2 = threading.Thread(target=self.serial_nucleo)
                    t2.start()
                    print("restart t2")
                if not t3.is_alive():
                    t3 = threading.Thread(target=self.socket_pc)
                    t3.start()
                    print("restart t3")
                if not t4.is_alive():
                    t4 = threading.Thread(target=self.auto_driving)
                    t4.start()
                    print("restart t4")
                if not t5.is_alive():
                    t5 = threading.Thread(target=self.simulator)
                    t5.start()
                    print("restart t5")

            except queue.Empty:
                # print("Queue is Empty")
                pass
            except KeyboardInterrupt:
                # print("Ctrl+C Pressed.")
                # global self.flag_exit
                self.flag_exit = True
                # t1.join()
                # t2.join()
                # t3.join()
                # t4.join()

            print("thread alive? t1 : {}, t2 : {}, t3 : {}, t4 : {}, t5 : {}".format(t1.is_alive(), t2.is_alive(), t3.is_alive(), t4.is_alive(), t5.is_alive()))

            time.sleep(5)

Boat = boat()
Boat.thread_start()

