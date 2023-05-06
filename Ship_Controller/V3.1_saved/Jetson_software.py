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
import re
import atexit

class boat:
    def __init__(self):
        self.end = 0
        self.flag_exit = False
        self.distance_to_target = 0

        self.err_prev = 0
        self.time_prev = 0

        self.sendToPc = ""

        self.isready = False
        self.isdriving = False
        self.isfirst = True
        # enddriving="0"
        self.driveindex = 0

        self.current_value = {'mode_jetson': "SELF", 'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto': None,
                              'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, "latitude": 37.633173,
                              "longitude": 127.077618, 'dest_latitude': None, 'dest_longitude': None,
                              'velocity': None,
                              'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                              'com_status': None, 'date': None, 'distance': None}

        # 'dest_latitude': None, 'dest_longitude': None,
        self.message = None

    def dict_to_str(self, d):
        items = []
        for k, v in d.items():
            items.append(f"{k} = {v}")
        return ",".join(items)

    def serial_gnss(self):  # NMEA data
        try:
            # port_gnss = "/dev/ttyACM1"
            port_gnss = "/dev/tty_septentrio0" ### 23.04.19 settings >> usb1 > 0
            # port_gnss = "/dev/tty_septentrio1" ### belonged to septentrio port
            ser_gnss = serial.Serial(port_gnss, baudrate=115200)
            data_counter = 0
            while True:
                print("self.running running")
                if ser_gnss.in_waiting > 0:
                    data = ser_gnss.readline().decode().strip()
                    print("GNSS > Jetson : ",data)
                    if data.startswith('$'):
                        tokens = data.split(',')

                        if tokens[0] == '$GPRMC' or tokens[0] == '$GNRMC':
                            try:
                                if tokens[2] == "A":
                                    pass
                                else:
                                    self.current_value['validity'] = tokens[2]
                                    continue

                                self.current_value['validity'] = tokens[2]  ## A = valid, V = not Valid

                                lat_min = float(tokens[3])
                                lat_deg = int(lat_min / 100)
                                lat_min -= lat_deg * 100
                                lat = lat_deg + lat_min / 60
                                self.current_value['latitude'] = round(lat, 8)

                                lon_sec = float(tokens[5])
                                lon_deg = int(lon_sec / 100)
                                lon_min = (lon_sec / 100 - lon_deg) * 100

                                lon = lon_deg + lon_min / 60
                                self.current_value['longitude'] = round(lon, 8)

                                self.current_value['velocity'] = float(tokens[7])
                            except ValueError:
                                continue

                        elif tokens[0] == '$PSSN':  # HRP
                            try:
                                self.current_value['time'] = tokens[2]  # UTC
                                self.current_value['date'] = tokens[3]  # date
                                self.current_value['heading'] = float(tokens[4])
                                # self.current_value['roll'] = float(tokens[5])
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

                else:
                    time.sleep(0.1)

                # print(self.current_value)

        except Exception as e:
            print(f'GNSS >> Error : {e}')

        finally:
            # ser_gnss.close() #필요가 없네?
            pass

    def send_data(self, ser, mode, pwm_left, pwm_right):
        send_message = "mode:{},pwm_left:{},pwm_right:{}\n".format(mode, pwm_left, pwm_right).encode()
        ser.write(send_message)
        # print("Jetson >> Nucleo : ", send_message)

    def is_valid_data(self, data):
        pattern = re.compile(r"mode:(AUTO|SELF|SMLT|WAIT),pwm_left:(\d+|None),pwm_right:(\d+|None)")
        return bool(pattern.match(data))

    '''Serial 데이터 정리
        Jetson >> Nucleo값이 다음과 같을 떄 :
        mode : SELF, pwml : 0, pwmr : 0 >> pwml_auto, pwmr_auto 초기화 한 후로 데이터 못 받음 current_value에서 받아오는것 문제
        mode : SELF, pwml : 0, pwmr : 0 >> self 모드에서 데이터 수신 잘 하는중

        Nucleo >> Jetson
        mode : AUTO, pwml : 0, pwmr : 0 >> AUTO 모드에서 종기 꺼짐
        mode : SELF, pwml : 4500, pwmr : 0 >> 송수신기 연결 X
        mode : SELF, pwml : None, pwmr : None >> pwml_auto, pwmr_auto 값 X
        mode : None, pwml : None, pwmr : None >> Jetson이 데이터 수신 못받는 중 >> respone 변수 문제있음
        mode : WAIT, pwml : 0, pwmr : 0 >> auto 기다리는 중
    '''

    def close_serial_port(self, ser):
        try:
            if ser and ser.is_open:
                ser.close()
                print("시리얼 포트가 닫혔습니다.")
        except:
            print("nucleo 연결 해제 안 된 듯")

    def serial_nucleo(self):
        port_nucleo = "/dev/ttyACM0"
        # port_nucleo = "/dev/tty_nucleo_f401re2"
        baudrate = 115200

        while True:
            try:
                ser_nucleo = serial.Serial(port_nucleo, baudrate=baudrate, timeout=10)
                atexit.register(self.close_serial_port, ser_nucleo)
                last_print_time = time.time()

                while True:
                    # Generate random mode and pwm values
                    # mode_str = random.choice(["AUTO", "MANUAL"])
                    mode_str = self.current_value['mode_jetson']
                    pwm_left_auto = int(
                        self.current_value['pwml_auto'] if self.current_value['pwml_auto'] is not None else 1)
                    pwm_right_auto = int(
                        self.current_value['pwmr_auto'] if self.current_value['pwmr_auto'] is not None else 2)
                    # Send data and wait for the response
                    self.send_data(ser_nucleo, mode_str, pwm_left_auto, pwm_right_auto)

                    response = ser_nucleo.readline().decode().strip()
                    try:
                        if self.is_valid_data(response):
                            parsed_data = dict(item.split(":") for item in response.split(","))
                            self.current_value['mode_chk'] = str(parsed_data.get('mode', 'UNKNOWN').strip())
                            self.current_value['pwml'] = int(parsed_data.get('pwm_left', '0').strip())
                            self.current_value['pwmr'] = int(parsed_data.get('pwm_right', '0').strip())
                        else:
                            print("nucleo가 이상한 데이터 보냈어요ㅠ")
                    except:
                        print("error")

                    # print("Jetson >> Nucleo, send : ", data_str.encode())
                    print("Nucleo >> Jetson, mode : {}, pwml : {}, pwmr : {}".format(self.current_value['mode_chk'],
                                                                                     self.current_value['pwml'],
                                                                                     self.current_value['pwmr']))
                    time.sleep(0.05)

            except Exception as e:
                print("Nucleo:", e)
                print("End serial_nucleo")
                time.sleep(1)
            finally:
                try:
                    ser_nucleo.close()
                    time.sleep(1)
                except:
                    time.sleep(1)
                    pass

    ### receive from PC
    def socket_pc_recv(self, client_socket='0.0.0.0', recv_port=5004):
        server_socket_pc_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = recv_port
        server_address = (host, port)
        server_socket_pc_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc_recv.bind(server_address)
        server_socket_pc_recv.listen(1)

        while True:
            try:
                client_socket, client_address = server_socket_pc_recv.accept()
                print(f"Connected by {client_address}")
                last_print_time = time.time()
                while True:
                    data = client_socket.recv(1024).strip()
                    if not data:
                        break

                    # print(data)
                    try:
                        received_dict = json.loads(data.decode('utf-8'))
                        self.current_value['mode_jetson'] = received_dict['mode_jetson']
                        self.current_value['dest_latitude'] = float(received_dict['dest_latitude'])
                        self.current_value['dest_longitude'] = float(received_dict['dest_longitude'])
                        # print("PC >> Jetson", received_dict)  # 출력문 추가

                        # if not self.current_value['is_driving']:
                        #     self.current_value['pwml_auto'] = 0
                        #     self.current_value['pwmr_auto'] = 0



                    # print(self.distance_to_target)
                    # print("x :", throttle_component, "y : ", roll_component)
                    # print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)


                    except (json.JSONDecodeError, TypeError, ValueError):
                        current_time = time.time()
                        if current_time - last_print_time >= 1:
                            try:
                                print("Waiting for destination")
                                last_print_time = current_time  # 마지막 출력 시간 업데이트
                            except:
                                print("NOOOOOp")
                        continue

                    time.sleep(0.1)
            except Exception as e:
                print(f"PC recv connection Error: {e}")
                continue

            finally:
                client_socket.close()

    ### receive from PC
    def socket_pc_send(self, client_socket='0.0.0.0', send_port=5003):
        server_socket_pc_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = send_port
        server_address = (host, port)
        server_socket_pc_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc_send.bind(server_address)
        server_socket_pc_send.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket_pc_send.accept()

                try:
                    print(f"Connected by {client_address}")

                    while True:
                        ready_to_read, ready_to_write, _ = select.select([], [client_socket], [], 1)
                        if ready_to_write:

                            if isinstance(self.current_value, dict):
                                message = json.dumps(self.current_value)
                                message += '\n'  # 구분자 추가
                                try:
                                    client_socket.sendall(message.encode())
                                    # print("Jetson >> pc, send : ", message)  # 출력문 추가
                                except OSError as e:
                                    print("Error in sending message:", e)  # 에러 출력문 추가
                                    raise Exception("Connection with client has been closed.")
                            else:
                                print("current_value is not a dictionary.")

                        time.sleep(0.05)

                except Exception as e:
                    print(f"PC send connection Error: {e}")

                finally:
                    client_socket.close()

        except KeyboardInterrupt:
            print("Send server stopped.")
        finally:
            server_socket_pc_send.close()

    def auto_driving(self):
        print("in the auto driving")
        send_well = False

        last_print_time = time.time()  # 마지막으로 출력한 시간 초기화
        # print("is driving?? ", self.is_driving)
        while True:  # 무한 :
            try:
                is_driving = True if self.current_value['mode_jetson'] == "AUTO" else False
                if not is_driving:
                    self.current_value['pwml_auto'] = 1
                    self.current_value['pwmr_auto'] = 2
                    self.distance_to_target = None
                    self.current_value['distance'] = None
                    break  # is_driving이 False일 경우 루프를 빠져나옴

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
                    return print("XXX")

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
                        print("NOOOOOp")
                # print("self.current_value : \n{}".format(self.current_value))
                time.sleep(0.05)
            except Exception as e:
                print("auto driving error : ", e)

    def thread_start(self):
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)
        t3 = threading.Thread(target=self.socket_pc_recv)
        t4 = threading.Thread(target=self.socket_pc_send)
        t5 = threading.Thread(target=self.auto_driving)
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
                    t3 = threading.Thread(target=self.socket_pc_recv)
                    t3.start()
                    print("restart t3")
                if not t4.is_alive():
                    t4 = threading.Thread(target=self.socket_pc_send)
                    t4.start()
                    print("restart t4")
                if not t5.is_alive():
                    t5 = threading.Thread(target=self.auto_driving)
                    t5.start()
                    print("restart t4")

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

            # print("thread alive? t1 : {}, t2 : {}, t3 : {}, t4 : {}".format(t1.is_alive(), t2.is_alive(), t3.is_alive(), t4.is_alive()))

            time.sleep(5)


Boat = boat()
Boat.thread_start()

