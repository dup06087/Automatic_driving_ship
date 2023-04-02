import math
import queue
import socket
import time
from haversine import haversine
import threading
import serial
import json
import random
import select

class boat:
    def __init__(self):
        self.end = 0
        self.flag_exit = False
        self.is_driving = False
        self.distance_to_target = 0

        self.err_prev = 0
        self.time_prev = 0

        self.heading = 0
        self.latnow = 0
        self.lngnow = 0
        self.sendToPc = ""

        self.isready = False
        self.isdriving = False
        self.isfirst = True
        # enddriving="0"
        self.driveindex = 0

        self.current_value = {'mode': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None, 'pwmr_auto' : None, "latitude": 37.633173, "longitude": 127.077618, 'dest_latitude' : None, 'dest_longitude' : None,
                         'velocity': None,
                         'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                         'com_status': None, 'date': None, 'distance' : None}

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
                if ser_gnss.in_waiting > 0:
                    data = ser_gnss.readline().decode().strip()
                    # print("GNSS > Jetson : ",data)
                    if data.startswith('$'):
                        tokens = data.split(',')

                        if tokens[0] == '$GPRMC' or tokens[0] == '$GNRMC':
                            try:
                                if tokens[2] == "A":
                                    pass
                                else:
                                    continue

                                self.current_value['validity'] = tokens[2] ## A = valid, V = not Valid

                                lat_min = float(tokens[3])
                                lat_deg = int(lat_min / 100)
                                lat_min -= lat_deg * 100
                                lat = lat_deg + lat_min / 60
                                self.current_value['latitude'] = round(lat,8)

                                lon_sec = float(tokens[5])
                                lon_deg = int(lon_sec / 100)
                                lon_min = (lon_sec / 100 - lon_deg) * 100

                                lon = lon_deg + lon_min / 60
                                self.current_value['longitude'] = round(lon, 8)

                                self.current_value['velocity'] = float(tokens[7])
                            except ValueError:
                                continue

                        elif tokens[0] == '$PSSN': #HRP
                            try:
                                self.current_value['time'] = tokens[2] # UTC
                                self.current_value['date'] = tokens[3] # date
                                self.current_value['heading'] = float(tokens[4])
                                self.current_value['roll'] = float(tokens[5])
                                self.current_value['pitch'] = float(tokens[6])

                            except ValueError:
                                # print("GNSS >> position fix 문제")
                                self.current_value['heading'] = None
                                self.current_value['roll'] = None
                                self.current_value['pitch'] = None

                        else:
                            print("GNSS 수신 상태 불량")
                        # print("self.current value : ", self.current_value)

                        data_counter += 1
                        if data_counter % 2 == 0:
                                self.message = self.dict_to_str(self.current_value)
                                data_counter = 0
                                # print(self.message)

                                # print("GNSS >> Jetson : ", self.current_value)
                                self.latnow = self.current_value['latitude']
                                self.heading = self.current_value['heading']
                                self.lngnow = self.current_value['longitude']

                else:
                    time.sleep(0.2)

        except Exception as e:
                print(f'GNSS >> Error : {e}')

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
                pwm_left_auto = int(self.current_value['pwml_auto'] if self.current_value['pwml_auto'] is not None else 0)
                pwm_right_auto = int(self.current_value['pwmr_auto'] if self.current_value['pwmr_auto'] is not None else 0)

                ###여기는 Jetson >> Nucleo 인데, 무조건 pwm_auto값만 보내는거, 그냥 pwm값은 보낼 필요가 없음 :: 현재 랜덤값 나중에는 else random.randint에 값 제대로 해야함, 즉 1500 or 0
                data_str = f"mode:{mode_str},pwm_left:{pwm_left_auto},pwm_right:{pwm_right_auto}\n".strip()
                '''nucleo는 data_str을 계속 받아, pwm_left_auto, pwm_right_auto로 둔다.'''
                # 데이터 전송
                ser_nucleo.write(data_str.encode())

                if ser_nucleo.in_waiting > 0:
                    # 데이터 읽어오기
                    data = ser_nucleo.readline().decode('utf-8').strip()  # 줄 바꿈 문자를 기준으로 데이터 읽기

                    # 데이터 파싱
                    try:
                        parsed_data = dict(item.split(":") for item in data.split(","))

                        self.current_value['mode'] = str(parsed_data.get('mode', 'UNKNOWN').strip())
                        self.current_value['pwml'] = int(parsed_data.get('pwm_left', '0').strip())
                        self.current_value['pwmr'] = int(parsed_data.get('pwm_right', '0').strip())

                    except:
                        pass

                current_time = time.time()
                if current_time - last_print_time >= 1:  # 마지막 출력 후 1초 경과 여부 확인
                    try:
                        # print("Jetson >> Nucleo, send : ", data_str)
                        # print("Nucleo >> Received : ", data.decode('utf-8').strip())
                        # print("Nucleo >> Jetson, Received : ", f"mode:{self.current_value['mode']},pwm_left:{self.current_value['pwml']},pwm_right:{self.current_value['pwmr']}")
                        last_print_time = current_time  # 마지막 출력 시간 업데이트
                    except:
                        pass

                time.sleep(0.02) ## delay없으면 serial에 쓰기전에 가져가 버림

        except Exception as e:
            print("Nucleo : ", e)
            print("end serial_nucleo")

        finally:
            # ser_nucleo.close() #serial은 알아서 변수가 없어지나봄
            pass

    def socket_pc(self, client_socket='localhost', ip=5001):  # rasp > pc
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
                        # 소켓이 읽기 가능한지 확인
                        ready_to_read, ready_to_write, _ = select.select([client_socket], [client_socket], [], 0.5)
                        if ready_to_read:
                            # 클라이언트로부터 데이터 수신
                            data = client_socket.recv(1024).strip()
                            # print(data)
                            # 수신한 데이터가 없으면 반복문 종료
                            try:
                                received_dict = json.loads(data.decode('utf-8'))
                                # print("COM >> Jetson, received_dict : ", received_dict)
                                self.current_value['dest_latitude'] = received_dict['dest_latitude']
                                self.current_value['dest_longitude'] = received_dict['dest_longitude']
                                if self.current_value['dest_latitude'] is not None and self.current_value['dest_longitude'] and self.current_value['mode'] == "AUTO":
                                    self.is_driving = True
                                else:
                                    self.is_driving = False

                            except:
                                print("not get data yet")

                        if ready_to_write:
                            # 클라이언트에게 데이터 전송
                            if type(self.current_value) == dict:
                                message = self.current_value
                                message = json.dumps(message)
                                client_socket.sendall(message.encode())
                            else:
                                print("딕트형이 아니네>?")

                        time.sleep(1)

                except (Exception) as e:
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
            # while not send_well:
            #     ## 밑의 한 줄은 시뮬레이션 용 currentdata 초기화
            #     self.current_value['heading'] = 0
            #     print("self.current_value \n", self.current_value)
            #     try:
            #         if self.current_value['latitude'] is not None and self.current_value['longitude'] is not None and self.current_value['heading'] is not None and self.current_value['dest_latitude'] is not None and self.current_value['dest_longitude'] is not None:
            #             # print("auto driving")
            #             send_well = True
            #         else:
            #             time.sleep(1)
            #             print("하나 이상의 데이터를 수신받지 못함, auto driving 실행 안 함")
            #             # return
            #     except Exception as E:
            #         print(E)
            #         print("하나 이상의 데이터를 수신받지 못함, auto driving 실행 안 함2")
            #         time.sleep(1)

            if (self.current_value['latitude'] is not None and self.current_value['longitude'] is not None and
                    self.current_value['dest_latitude'] is not None and self.current_value[
                        'dest_longitude'] is not None):
                current_latitude = float(self.current_value['latitude'])
                current_longitude = float(self.current_value['longitude'])
                try:
                    current_heading = float(self.current_value['heading'])
                except:
                    current_heading = 0
                destination_latitude = float(self.current_value['dest_latitude'])
                destination_longitude = float(self.current_value['dest_longitude'])
            else:
                return

            # 헤딩 값을 -180에서 180 사이의 값으로 변환
            if current_heading > 180:
                current_heading = current_heading - 360

            # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
            self.distance_to_target = haversine((current_latitude, current_longitude),
                                                (destination_latitude, destination_longitude), unit='m')
            self.current_value['distance'] = float(self.distance_to_target)

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
                    # print(self.distance_to_target)
                    # print("x :", throttle_component, "y : ", roll_component)
                    # print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)
                    last_print_time = current_time  # 마지막 출력 시간 업데이트
                except:
                    pass
            print("self.current_value : \n{}".format(self.current_value))
            time.sleep(0.1)

    def thread_start(self):
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)
        t3 = threading.Thread(target=self.socket_pc)
        t4 = threading.Thread(target=self.auto_driving)
        # t5 = threading.Thread(target=self.simulator)
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
                # if not t5.is_alive():
                #     t5 = threading.Thread(target=self.simulator)
                #     t5.start()
                #     print("restart t5")

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

            print("thread alive? t1 : {}, t2 : {}, t3 : {}, t4 : {}".format(t1.is_alive(), t2.is_alive(), t3.is_alive(), t4.is_alive()))

            time.sleep(5)

Boat = boat()
Boat.thread_start()

