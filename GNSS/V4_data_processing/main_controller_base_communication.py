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
        self.current_value = {'mode': None, 'pwml': None, 'pwmr': None, "latitude": None, "longitude": None,
                            'velocity': None,
                            'heading': None, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'date' : None}
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
            self.port_nucleo = "COM7"
            ser_nucleo = serial.Serial(self.port_nucleo, baudrate=115200)

            print("trying")
            while True:
                print("running")
                # sendToMbed = self.sendToMbedQ.get(True, 2)
                # ser.write(sendToMbed.encode())
                # ser.write('hi'.encode())
                if ser_nucleo.readable():
                    # 데이터 읽어오기
                    data = ser_nucleo.readline() # nucleo 개행문자 \n으로 해야함
                    print("Received nucleo data : ", data.decode('utf-8'))

        except Exception as e:
            print(e)
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
                            print("received_dict : ", received_dict)
                            self.current_value['mode'] = received_dict['mode']
                            self.current_value['dest_latitude'] = received_dict['dest_latitude']
                            self.current_value['dest_longitude'] = received_dict['dest_longitude']
                        except:
                            print("not get data yet")
                        # 수신한 데이터 출력


                        # 클라이언트에게 데이터 전송
                        message = {'mode': "SELF", 'pwml': random.random(), 'pwmr': random.random(), "latitude": 37.633173, "longitude": 127.077618,
                            'velocity': random.random(), 'heading': 0, 'roll': random.random(), 'pitch': random.random(), 'validity': random.random(), 'time': random.random(), 'IP': random.random(),
                            'com_status': random.random(), 'date' : random.random()}
                        message = json.dumps(message)
                        print("message : ",message)
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


        # while True:
        #     try:
        #         data = client_socket.recv(1024)
        #         if not data:
        #             print('Disconnected by ' + addr[0], ':', addr[1])
        #             break
        #         self.recDataPc1 = data.decode()
        #         client_socket.send(self.sendToPc.encode())
        #         # #global self.flag_exit
        #         if self.flag_exit:
        #             break
        #     except ConnectionResetError as e:
        #         print("Disconnected by", addr[0], ':', addr[1])
        #         print(f"e: {e}")

    def auto_driving(self):
        while self.is_driving:
            try:
                if self.current_value['latitude'] is not None and self.current_value['longitude'] is not None and self.current_value['heading'] is not None and self.current_value['dest_latitude'] is not None and self.current_value['dest_longitude']:
                    print("auto driving")
                else:
                    return print("하나 이상의 데이터를 수신받지 못함")
            except:
                pass

            current_latitude = self.current_value['latitude']
            current_longitude = self.current_value['longitude']
            current_heading = self.current_value['heading']
            destination_latitude = self.current_value['dest_latitude']
            destination_longitude = self.current_value['dest_longitude']

            Kf = 1.0
            Kd = 1.0

            # 헤딩 값을 -180에서 180 사이의 값으로 변환
            if current_heading > 180:
                current_heading = current_heading - 360

            # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
            distance_to_target = haversine((current_latitude, current_longitude),
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
            throttle_component = distance_to_target * math.cos(math.radians(angle_diff))
            roll_component = distance_to_target * math.sin(math.radians(angle_diff))

            # PWM 값 계산
            Uf = Kf * throttle_component
            Ud = Kd * roll_component
            PWM_right = Uf + Ud
            PWM_left = Uf - Ud

            print(distance_to_target)
            print("x :", throttle_component, "y : ", roll_component)
            print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)


    def thread_start(self):
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)
        t3 = threading.Thread(target=self.socket_pc)

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

            except queue.Empty:
                # print("Queue is Empty")
                pass
            except KeyboardInterrupt:
                # print("Ctrl+C Pressed.")
                # global self.flag_exit
                self.flag_exit = True
                t1.join()
                t2.join()
            # t3.join()
            # t4.join()

            print("thread alive? : ", t1.is_alive(), t2.is_alive(), t3.is_alive())

            time.sleep(5)

Boat = boat()
Boat.thread_start()

