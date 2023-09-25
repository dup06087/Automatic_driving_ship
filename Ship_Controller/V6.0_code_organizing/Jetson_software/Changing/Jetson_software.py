import math, queue, socket, time, threading, serial, json, random, select, re, atexit
from haversine import haversine
from Jetson_initalizing_values import initialize_variables
from Jetson_serial_communication import serial_nucleo, serial_gnss
from Jetson_socket import JetsonSocket

class boat:
    def __init__(self):
        initialize_variables(self)

        self.current_value = {'mode_jetson': "SELF", 'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto': None,
                              'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, "latitude": 37.633173,
                              "longitude": 127.077618, 'dest_latitude': None, 'dest_longitude': None, 'cnt_destination' : None,
                              'velocity': None,
                              'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                              'com_status': None, 'date': None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None}

        self.serial_gnss = serial_gnss(port="COM3")
        self.serial_nucleo = serial_nucleo(port = "COM7")


        # self.jetson_pc_recv = JetsonSocket().socket_pc_recv
        #
        # self.jetson_pc_send = JetsonSocket().socket_pc_send

        # 'dest_latitude': None, 'dest_longitude': None,
        # self.serial_gnss = serial_gnss(port="/dev/ttyUSB0")
        # self.serial_nucleo = serial_nucleo(port="/dev/ttyUSB0")

        # self.serial_gnss = serial_gnss(port="COM3")
        # self.serial_nucleo = serial_nucleo(port="/dev/ttyUSB0")


    def socket_LiDAR(self):
        server_socket_pc_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = "0.0.0.0"
        port = 5010
        server_address = (host, port)
        server_socket_pc_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc_send.settimeout(1)
        server_socket_pc_send.bind(server_address)
        server_socket_pc_send.listen(1)

        try:
            while True:
                print("Waiting LiDAR")
                client_socket, client_address = server_socket_pc_send.accept()

                try:
                    print(f"Connected by {client_address}")
                    while True:
                        ready_to_read, ready_to_write, _ = select.select([client_socket], [client_socket], [], 1)
                        if ready_to_write:
                            keys_to_extract = ['latitude', 'longitude', 'velocity', 'heading', 'pitch']
                            # 占쏙옙占싸울옙 占쏙옙킬訶占?占쏙옙占쏙옙
                            self.LiDAR_data = { key : self.current_value[key] for key in keys_to_extract if key in self.current_value}
                            try:
                                self.LiDAR_data['dest_latitude'] = self.current_value['dest_latitude'][self.cnt_destination]
                                self.LiDAR_data['dest_longitude'] = self.current_value['dest_longitude'][self.cnt_destination]
                            except:
                                self.LiDAR_data['dest_latitude'] = None
                                self.LiDAR_data['dest_longitude'] = None
                            if isinstance(self.LiDAR_data, dict):
                                message = json.dumps(self.LiDAR_data)
                                message += '\n'  # 占쏙옙占쏙옙占쏙옙 占쌩곤옙
                                try:
                                    client_socket.sendall(message.encode())
                                except Exception as e:
                                    print("lidar sending : ", e)
                            else:
                                print("current_value is not a dictionary.")

                        if ready_to_read:
                            print("ready to read")
                            try:
                                self.received_way_point = client_socket.recv(1024)

                                if self.received_way_point:
                                    self.received_way_point = self.received_way_point.strip()
                                    print("占쏙옙占쏙옙占쏙옙 占쏙옙표 : ", self.received_way_point)
                                    self.flag_avoidance = True
                                    self.way_point = json.loads(self.received_way_point.decode('utf-8'))
                                    self.current_value["waypoint_latitude"] = self.way_point["dest_latitude"]
                                    self.current_value["waypoint_longitude"] = self.way_point["dest_longitude"]
                                    print(self.way_point)
                                else:
                                    self.flag_avoidance = False
                                    self.way_point = None
                                    self.current_value["waypoint_latitude"] = None
                                    self.current_value["waypoint_longitude"] = None
                                    print("Lidar >> Jetson, don't get any data")

                                print("占쏙옙占쏙옙占쏙옙 占쏙옙표 : ", self.received_way_point)
                                # if not self.received_way_point:
                                #     self.flag_avoidance = False
                                #     self.way_point = None
                                # else:
                                #     self.flag_avoidance = True
                                #     self.way_point = json.loads(self.received_way_point.decode('utf-8'))
                                #     print(self.way_point)
                            except:
                                self.flag_avoidance = False
                                self.way_point = None
                                self.current_value["waypoint_latitude"] = None
                                self.current_value["waypoint_longitude"] = None
                                print("LiDAR ?? Jetson : no data received")

                        else: # lidar 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙
                            self.flag_avoidance = False
                            self.way_point = None
                            print("Jetson ?? LiDAR : no data received")
                        time.sleep(0.1)

                except Exception as e:
                    pass
                    # print(f"PC send connection Error: {e}")

                finally:
                    try:
                        client_socket.close()
                    except:
                        pass

        except KeyboardInterrupt:
            print("Send server stopped.")

        finally:
            try:
                server_socket_pc_send.close()
            except:
                pass

    def auto_driving(self):
        print("in the auto driving")
        self.is_driving = False
        self.cnt_destination = 0
        self.current_value['cnt_destination'] = self.cnt_destination

        last_print_time = time.time()  # 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占?占시곤옙 占십깍옙화
        # print("is driving?? ", self.is_driving)
        while True:  # 占쏙옙占쏙옙 :
            try:
                # mode占쏙옙 auto占쏙옙占쏙옙 확占쏙옙
                self.is_driving = True if self.current_value['mode_jetson'] == "AUTO" else False
                # mode占쏙옙 auto占싱몌옙 占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
                if not self.is_driving:
                    self.current_value['pwml_auto'] = 1500
                    self.current_value['pwmr_auto'] = 1500
                    self.distance_to_target = None
                    self.current_value['distance'] = None
                    self.cnt_destination = 0
                    self.current_value['cnt_destination'] = None
                    break  # is_driving占쏙옙 False占쏙옙 占쏙옙占?占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙占쏙옙

                if (self.current_value['latitude'] is not None and self.current_value['longitude'] is not None and
                        self.current_value['dest_latitude'] is not None and self.current_value[
                            'dest_longitude'] is not None):
                    current_latitude = float(self.current_value['latitude'])
                    current_longitude = float(self.current_value['longitude'])
                    current_heading = float(self.current_value['heading'])
                    if self.flag_avoidance:
                        destination_latitude = float(self.current_value["waypoint_latitude"])
                        destination_longitude = float(self.current_value["waypoint_longitude"])
                    else:
                        destination_latitude = float(self.current_value['dest_latitude'][self.cnt_destination])
                        destination_longitude = float(self.current_value['dest_longitude'][self.cnt_destination])
                else:
                    ### if initializing at here...
                    ''' short time irreular gps data can harm '''
                    self.current_value['pwml_auto'] = 1500
                    self.current_value['pwmr_auto'] = 1500
                    return print("XXX")

                # 占쏙옙占?占쏙옙占쏙옙 -180占쏙옙占쏙옙 180 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙환
                if current_heading > 180:
                    current_heading = current_heading - 360

                # Haversine 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙臼占?占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占신몌옙占쏙옙 占쏙옙占?
                self.distance_to_target = haversine((current_latitude, current_longitude),
                                                    (destination_latitude, destination_longitude), unit='m')
                self.current_value['distance'] = float(self.distance_to_target)

                # 占쏙옙占쌘곤옙 占쏙옙占쏙옙占쏙옙占쏙옙 占싱뤄옙占?占쏙옙占쏙옙 占쌘북울옙 占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占?
                target_angle = math.degrees(
                    math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))

                # 占쏙옙占쏙옙占?占쏙옙표 占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占?
                angle_diff = target_angle - current_heading
                if angle_diff > 180:
                    angle_diff -= 360
                elif angle_diff < -180:
                    angle_diff += 360

                # 占쏙옙占쏙옙 占쏙옙占싱울옙 占쏙옙占쏙옙 throttle 占쏙옙 roll 占쏙옙占쏙옙 占쏙옙占?
                throttle_component = self.distance_to_target * math.cos(math.radians(angle_diff))
                roll_component = self.distance_to_target * math.sin(math.radians(angle_diff))

                # PWM 占쏙옙 占쏙옙占?
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

                if float(self.distance_to_target) <= 3:
                    self.cnt_destination += 1
                    self.current_value['cnt_destination'] = self.cnt_destination
                    ''' 占쏙옙占썩에 self.destination.setText() 占쌩곤옙占쌔억옙占쏙옙'''
                    # 占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙 확占쏙옙 占쏙옙, stop_driving 호占쏙옙
                    if self.cnt_destination >= len(self.current_value['dest_latitude']):
                        self.is_driving = False
                        self.cnt_destination = 0
                        self.current_value['cnt_destination'] = None
                        self.current_value['mode_jetson'] = "SELF"
                        self.current_value['pwml_auto'] = 0
                        self.current_value['pwmr_auto'] = 0
                        self.distance_to_target = None
                        self.current_value['distance'] = None
                        self.current_value["dest_latitude"] = None
                        self.current_value["dest_longitude"] = None
                        return print("Arrived")

                current_time = time.time()
                if current_time - last_print_time >= 1:  # 占쏙옙占쏙옙占쏙옙 占쏙옙占?占쏙옙 1占쏙옙 占쏙옙占?占쏙옙占쏙옙 확占쏙옙
                    try:
                        # print(self.distance_to_target)
                        # print("x :", throttle_component, "y : ", roll_component)
                        # print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)
                        last_print_time = current_time  # 占쏙옙占쏙옙占쏙옙 占쏙옙占?占시곤옙 占쏙옙占쏙옙占쏙옙트
                    except:
                        print("NOOOOOp")
                # print("self.current_value : \n{}".format(self.current_value))
                time.sleep(0.05)
            except Exception as e:
                self.current_value['pwml_auto'] = 1500
                self.current_value['pwmr_auto'] = 1500
                print("auto driving error : ", e)

    def thread_start(self):
        self.serial_nucleo_thread = threading.Thread(target=self.serial_nucleo.run)
        self.serial_nucleo_thread.start()
        self.serial_nucleo_thread.join()

        self.serial_gnss_thread = threading.Thread(target=self.serial_gnss)
        self.serial_gnss_thread.start()
        self.serial_gnss_thread.join()

        # self.jetson_pc_recv_thread = threading.Thread(target=self.jetson_pc_recv)
        # self.jetson_pc_recv_thread.start()
        # self.jetson_pc_recv_thread.join()
        # self.jetson_pc_send_thread = threading.Thread(target=self.jetson_pc_send)
        # self.jetson_pc_send_thread.start()
        while True:
            # if self.end == 1:
            #     break

            try:
                pass
                # print("trying")
                if not self.serial_gnss.is_alive():
                    self.serial_gnss_thread = threading.Thread(target=self.serial_gnss)
                    self.serial_gnss_thread.start()
                    self.serial_gnss_thread.join()
                    print("restart gnss")
                if not self.serial_nucleo_thread.is_alive():
                    self.serial_nucleo_thread = threading.Thread(target=self.serial_nucleo.run)
                    self.serial_nucleo_thread.start()
                    self.serial_nucleo_thread.join()
                    print("restart nucleo")
                # if not self.jetson_pc_recv_thread.is_alive():
                #     self.jetson_pc_recv_thread = threading.Thread(target=self.jetson_pc_recv)
                #     self.jetson_pc_recv_thread.start()
                #     print("restart jetson socket recv")
                # if not self.jetson_pc_send_thread.is_alive():
                #     self.jetson_pc_send_thread = threading.Thread(target=self.jetson_pc_send)
                #     self.jetson_pc_send_thread.start()
                #     print("restart jetson socket send")
            except Exception as e:
                print("passed : ",e)
                pass


Boat = boat()
Boat.thread_start()