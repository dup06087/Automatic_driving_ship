import math
import queue
import socket
import time
from haversine import haversine
import threading
import serial


class boat:
    def __init__(self):
        self.end = 0
        self.flag_exit = False
        self.destLat = []
        self.destLng = []

        for i in range(20):
            self.destLat.append('0')
            self.destLng.append('0')  ################initialize target destination list

        self.kp_heading = 1.9
        # ki_heading=0.0000000003
        self.ki_heading = 0.0000000002
        self.kd_heading = 0.0000003
        self.P_term_heading = 0
        self.I_term_heading = 0
        self.D_term_heading = 0
        self.err_prev = 0
        self.time_prev = 0
        self.pid_heading_max = 250
        self.pid_heading_min = 0
        self.slowdis = 15
        self.stopdis = 2
        self.savedt = 0
        self.kp_dis = 8

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
        self.running = False
        self.current_value = {"latitude": None, "longitude": None, "heading": None, "velocity": None, 'utc' : None, 'data' : None, 'roll' : None, 'pitch' : None}
        self.message = None

    def dict_to_str(self, d):
        items = []
        for k, v in d.items():
            items.append(f"{k} = {v}")
        return ",".join(items)

    def serial_gnss(self):  # NMEA data
        self.port_gnss = "COM6"
        self.running = True
        data_counter = 0
        while self.running:
            try:
                # 시리얼 포트 열기
                ser_gnss = serial.Serial(self.port_gnss, baudrate=115200)

                # 데이터 수신 및 전송
                while self.running:
                    # print("self.running running")
                    data = ser_gnss.readline().decode().strip()
                    # print(data)
                    if data.startswith('$'):
                        tokens = data.split(',')
                        if tokens[0] == '$PSSN':
                            try:
                                self.current_value['utc'] = tokens[2] # UTC
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

                        # print(self.current_value)

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
                try:
                    ser_gnss.close()
                except:
                    pass
                try:
                    pass
                # sock.close()
                except:
                    pass
                # 재접속 시도
                time.sleep(10)
                continue

    def data_processing(self):
        while True:
            self.recDataPc = self.recDataPc1.split(',')
            dis = 0
            if self.heading < 0:
                heading_360 = -self.heading
            else:
                heading_360 = abs(self.heading - 360)
            heading_360 = round(heading_360, 2)
            azim_deg_raw = 0
            if (self.recDataPc[1] == "DX"):  # save latest target point
                lasttarlat = str(self.recDataPc[2])
                lasttarlng = str(self.recDataPc[3])
                mode = self.recDataPc[4]
                #######################################orders from pc
                if self.recDataPc[5] == "RE":
                    # xsens.resetyaw()
                    pass
                elif self.recDataPc[5] == "CD":  # clear destination
                    # global isfirst
                    self.isfirst = True
                    self.isready = False
                    self.isdriving = False
                    for i in range(self.destindex_max):
                        self.destLat[i] = '0'
                        self.destLng[i] = '0'
                        destindex = 0
                    mode = "SELF"
                    motorright = 1500
                    motorleft = 1500
                elif self.recDataPc[5] == "RD":  # ready (save destination)
                    isready = True
                elif self.recDataPc[5] == "DR":  # auto drive mode
                    isdriving = True
                elif self.recDataPc[5] == "SI":  # save log
                    # xsens.setnorotation()
                    pass
                if mode == "SELF":  # self drive mode
                    mode = "1"
                    motorright = 1500
                    motorleft = 1500
                    destindex = 0
                    self.isready = False
                    self.isdriving = False

                elif mode == "AUTO":  # auto mode
                    mode = "2"
                    motorright = 1500
                    motorleft = 1500
                    if self.isready:  # ready mode : collect waypoints
                        if destindex == 0:
                            if self.destLat[destindex] != lasttarlat or self.destLng[destindex] != lasttarlng:
                                self.destLat[destindex] = lasttarlat
                                self.destLng[destindex] = lasttarlng
                                destindex += 1
                        else:
                            if self.destLat[destindex - 1] != lasttarlat or self.destLng[destindex - 1] != lasttarlng:
                                self.destLat[destindex] = lasttarlat
                                self.destLng[destindex] = lasttarlng
                                destindex += 1
                        driveindex = 0
                        timestarting = time.time()
                    if self.isdriving:  # autodrive mode
                        enddriving = "0"
                        motorright = 1750
                        motorleft = 1750
                        isready = False
                        if (self.destLat[driveindex] != 0 or self.destLng[driveindex] != 0):
                            timenow = time.time()  # plotting time
                            azim_deg_raw = self.azimuth(self.latnow, self.lngnow, float(self.destLat[driveindex]),
                                                        float(self.destLng[driveindex]))
                            if azim_deg_raw < 0:
                                azim_deg = 360 + azim_deg_raw
                            else:
                                azim_deg = azim_deg_raw
                            dis = haversine((self.latnow, self.lngnow),
                                            (float(self.destLat[driveindex]), float(self.destLng[driveindex])),
                                            unit="m")
                            goalAng = round(azim_deg, 2)

                            if heading_360 < 180 and goalAng > 180 + heading_360:
                                err_heading = -((360 - goalAng) + heading_360)
                            elif heading_360 >= 180 and goalAng < heading_360 - 180:
                                err_heading = goalAng + 360 - heading_360
                            else:
                                err_heading = goalAng - heading_360  # goalAng-heading(-180~180)
                            PID_heading = self.pid_heading(err_heading)
                            PID_dis = self.pid_dis(dis)
                            pwm_chai = PID_heading * 2
                            if err_heading > 0:  # Going Right
                                motorleft += PID_heading
                                motorright -= PID_heading
                                if motorright > 2000:
                                    motorright = 2000
                                elif motorleft > 2000:
                                    motorleft = 2000
                                elif motorright < 1500:
                                    motorright = 1500
                                elif motorleft < 1500:
                                    motorleft = 1500
                                if dis > self.stopdis and dis < self.slowdis:
                                    motorright -= (PID_dis + pwm_chai)
                                    motorleft -= PID_dis
                                    if motorright < 1500:
                                        motorright = 1500
                                elif dis <= self.stopdis:
                                    motorright = 1500
                                    motorleft = 1500
                                    driveindex += 1
                            else:
                                motorleft -= PID_heading  # Going Left
                                motorright += PID_heading
                                if motorright > 2000:
                                    motorright = 2000
                                elif motorleft > 2000:
                                    motorleft = 2000
                                elif motorright < 1500:
                                    motorright = 1500
                                elif motorleft < 1500:
                                    motorleft = 1500
                                if dis > self.stopdis and dis < self.slowdis:
                                    motorright -= PID_dis
                                    motorleft -= (PID_dis + pwm_chai)
                                    if motorleft < 1500:
                                        motorleft = 1500
                                elif dis <= self.stopdis:
                                    motorright = 1500
                                    motorleft = 1500
                                    driveindex += 1

            sendToMbed = "S" + mode + "," + "%d" % motorleft + "," + "%d" % motorright + "E"
            # global sendToPc
            self.sendToPc = hex(6) + "," + "DX" + "," + "%.2f" % (self.heading) + "," + "%.8f" % (
                self.latnow) + "," + "%.8f" % (self.lngnow) + "," + str(motorleft) + "," + str(
                motorright) + "," + "%.2f" % (dis) + "," + "%.2f" % (azim_deg_raw) + "," + hex(3)
            self.sendToMbedQ.put(sendToMbed)
            print(self.sendToPc)
            # #global self.flag_exit
            if self.flag_exit:
                break

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
                    print("Received : ", data.decode('utf-8'))

        except Exception as e:
            print(e)
            print("end serial_nucleo")

    def socket_pc(self, client_socket = 'localhost', ip = 5000):  # rasp > pc
        server_socket_pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = ip
        server_address = (host, port)
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

                        # 수신한 데이터 출력
                        print(f"Received data: {data.decode()}")

                        # 클라이언트에게 데이터 전송
                        message = "Hello, client!"
                        client_socket.sendall(message.encode())

                except Exception as e:
                    # 예외 처리
                    print(f"Error: {e}")
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

    def thread_start(self):
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)

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


            # t3 = threading.Thread(target=self.socket_com_main, args=(self.server_socket, self.addr))
            # t3.start()
            # t4 = threading.Thread(target=self.mbed_serial_com_main(self.ser))
            # t4.start()

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

            print("thread alive? : ", t1.is_alive(), t2.is_alive())

            time.sleep(5)
            # print("Ok")

            # threading.Thread(target = self.GNSS_serial_com_main)
            # print("def executed")


Boat = boat()
Boat.thread_start()