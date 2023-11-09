import math, queue, socket, time, threading, serial, json, random, select, re, atexit
from haversine import haversine
from Jetson_initalizing_values import initialize_variables

class boat:
    def __init__(self):
        initialize_variables(self)

        self.current_value = {'mode_jetson': "SELF", 'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto': None,
                              'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, "latitude": 37.633173,
                              "longitude": 127.077618, 'dest_latitude': None, 'dest_longitude': None, 'cnt_destination' : None,
                              'velocity': None,
                              'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                              'com_status': None, 'date': None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None}

        # 'dest_latitude': None, 'dest_longitude': None,

    def dict_to_str(self, d):
        items = []
        for k, v in d.items():
            items.append(f"{k} = {v}")
        return ",".join(items)

    def serial_gnss(self):  # NMEA data
        try:
            port_gnss = "/dev/ttyACM1"
            # port_gnss = "/dev/tty_septentrio0" ### 23.04.19 settings >> usb1 > 0
            # port_gnss = "/dev/tty_septentrio1" ### belonged to septentrio port
            ser_gnss = serial.Serial(port_gnss, baudrate=115200)
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
                                # print("GNSS >> position fix 占쏙옙占쏙옙")
                                self.current_value['heading'] = None
                                self.current_value['roll'] = None
                                self.current_value['pitch'] = None

                        else:
                            print("GNSS 占쏙옙占쏙옙 占쏙옙占쏙옙 占쌀뤄옙")
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
            # ser_gnss.close() #占십요가 占쏙옙占쏙옙?
            pass

    def send_data(self, ser, mode, pwm_left, pwm_right):
        send_message = "mode:{},pwm_left:{},pwm_right:{}\n".format(mode, pwm_left, pwm_right).encode()
        ser.write(send_message)
        # print("Jetson >> Nucleo : ", send_message)

    def is_valid_data(self, data):
        pattern = re.compile(r"mode:(AUTO|SELF|SMLT|WAIT|ERRR|REST|ERR0|ERR1|ERR2|ERR3),pwm_left:(\d+|None),pwm_right:(\d+|None)")
        return bool(pattern.match(data))

    '''Serial 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
        Jetson >> Nucleo占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙 :
        mode : SELF, pwml : 0, pwmr : 0 >> pwml_auto, pwmr_auto 占십깍옙화 占쏙옙 占식뤄옙 占쏙옙占쏙옙占쏙옙 占쏙옙 占쏙옙占쏙옙 current_value占쏙옙占쏙옙 占쌨아울옙占승곤옙 占쏙옙占쏙옙
        mode : SELF, pwml : 0, pwmr : 0 >> self 占쏙옙恙∽옙占?占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙 占싹댐옙占쏙옙

        Nucleo >> Jetson
        mode : AUTO, pwml : 0, pwmr : 0 >> AUTO 占쏙옙恙∽옙占?占쏙옙占쏙옙 占쏙옙占쏙옙
        mode : SELF, pwml : 4500, pwmr : 0 >> 占쌜쇽옙占신깍옙 占쏙옙占쏙옙 X
        mode : SELF, pwml : None, pwmr : None >> pwml_auto, pwmr_auto 占쏙옙 X
        mode : None, pwml : None, pwmr : None >> Jetson占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쌨댐옙 占쏙옙 >> respone 占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙占쏙옙
        mode : WAIT, pwml : 0, pwmr : 0 >> auto 占쏙옙摸占쏙옙占?占쏙옙
    '''

    def close_serial_port(self, ser):
        try:
            if ser and ser.is_open:
                ser.close()
                print("占시몌옙占쏙옙 占쏙옙트占쏙옙 占쏙옙占쏙옙占쏙옙占싹댐옙.")
        except:
            print("nucleo 占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙 占쏙옙 占쏙옙")

    def serial_nucleo(self):
        port_nucleo = "/dev/ttyACM0"
        # port_nucleo = "COM7"
        # port_nucleo = "/dev/tty_nucleo_f401re2"
        baudrate = 115200

        while True:
            try:
                ser_nucleo = serial.Serial(port_nucleo, baudrate=baudrate, timeout=0.4)
                atexit.register(self.close_serial_port, ser_nucleo)
                last_print_time = time.time()

                while True:
                    try:
                        # Generate random mode and pwm values
                        # mode_str = random.choice(["AUTO", "MANUAL"])
                        mode_str = self.current_value['mode_jetson']
                        pwm_left_auto = int(
                            self.current_value['pwml_auto'] if self.current_value['pwml_auto'] is not None else 1500)
                        pwm_right_auto = int(
                            self.current_value['pwmr_auto'] if self.current_value['pwmr_auto'] is not None else 1500)
                        # Send data and wait for the response
                        ser_nucleo.flush()
                        self.send_data(ser_nucleo, mode_str, pwm_left_auto, pwm_right_auto)

                        print(f"Jetson >> Nucleo, mode : {mode_str}, pwml : {pwm_left_auto}, pwmr : {pwm_right_auto}")
                        response = ser_nucleo.readline().decode().strip()

                        if self.is_valid_data(response):
                            parsed_data = dict(item.split(":") for item in response.split(","))
                            self.current_value['mode_chk'] = str(parsed_data.get('mode', 'UNKNOWN').strip())
                            self.current_value['pwml'] = int(parsed_data.get('pwm_left', '0').strip())
                            self.current_value['pwmr'] = int(parsed_data.get('pwm_right', '0').strip())
                        else:
                            print("nucleo sent unexpected data")

                        print("Nucleo >> Jetson, mode : {}, pwml : {}, pwmr : {}".format(
                            self.current_value['mode_chk'],
                            self.current_value['pwml'],
                            self.current_value['pwmr']))
                    except:
                        print("nucleo communication error")

                    # print("Jetson >> Nucleo, send : ", data_str.encode())

                    time.sleep(0.1)

            except Exception as e:
                print("Nucleo:", e)
                print("End serial_nucleo")
                time.sleep(0.005)
            finally:
                try:
                    print("nucleo error")
                    ser_nucleo.close()
                    time.sleep(0.005)
                except:
                    print("nucleo error2")
                    time.sleep(0.005)
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
                        self.current_value['dest_latitude'] = received_dict['dest_latitude']
                        self.current_value['dest_longitude'] = received_dict['dest_longitude']
                        # print("PC >> Jetson", received_dict)  # 占쏙옙쨔占?占쌩곤옙

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
                                last_print_time = current_time  # 占쏙옙占쏙옙占쏙옙 占쏙옙占?占시곤옙 占쏙옙占쏙옙占쏙옙트
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
                                message += '\n'  # 占쏙옙占쏙옙占쏙옙 占쌩곤옙
                                try:
                                    client_socket.sendall(message.encode())
                                    # print("Jetson >> pc, send : ", message)  # 占쏙옙쨔占?占쌩곤옙
                                except OSError as e:
                                    print("Error in sending message:", e)  # 占쏙옙占쏙옙 占쏙옙쨔占?占쌩곤옙
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
        t1 = threading.Thread(target=self.serial_gnss)
        t2 = threading.Thread(target=self.serial_nucleo)
        t3 = threading.Thread(target=self.socket_pc_recv)
        t4 = threading.Thread(target=self.socket_pc_send)
        t5 = threading.Thread(target=self.auto_driving)
        t6 = threading.Thread(target=self.socket_LiDAR)
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
                    print("restart t5")
                if not t6.is_alive():
                    t6 = threading.Thread(target=self.socket_LiDAR)
                    t6.start()
                    print("restart t6")

            except KeyboardInterrupt:
                # print("Ctrl+C Pressed.")
                # global self.flag_exit
                self.flag_exit = True
                # t1.join()
                # t2.join()
                # t3.join()
                # t4.join()

            # print("thread alive? t1 : {}, t2 : {}, t3 : {}, t4 : {}".format(t1.is_alive(), t2.is_alive(), t3.is_alive(), t4.is_alive()))

            time.sleep(1)

Boat = boat()
Boat.thread_start()