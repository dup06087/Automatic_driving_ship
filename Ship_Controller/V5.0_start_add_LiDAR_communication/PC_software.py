import base64
import random
import time

from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
import folium, io, sys, json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import serial
from PIL import Image
import numpy as np
from jinja2 import Template
import math
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import math
from haversine import haversine, Unit
import socket
import threading
import queue
import json
import traceback
import select
import re


form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('image.png')

class Worker(QtCore.QThread):
    def __init__(self):
        super().__init__()
        # 송신 값
        self.message = {"mode_jetson": "SELF", "dest_latitude": None, "dest_longitude": None}

        # 수신 시 에러방지용 초기화 > 사실 데이터 훨씬 많음
        self.data = {"mode_jetson": "SELF", "dest_latitude": None, "dest_longitude": None}

        # 자율 주행 시작 플래그
        self.flag_auto_driving = None

    def run(self):
        # 117.17.187.60::25234
        # recv_host, recv_port = '117.17.187.60', 5001
        # send_host, send_port = '117.17.187.60', 5002
        ''' Wifi 사용시 ''' # 또한, jetson 프로그램에서도 pc send, recv 포트 바꿔줘야함
        # recv_host, recv_port = '223.171.136.213', 5001
        # send_host, send_port = '223.171.136.213', 5002
        ''' Lan port 사용시 ''' # 또한, jetson 프로그램에서도 pc send, recv 포트 바꿔줘야함
        recv_host, recv_port = '223.171.136.213', 5003
        send_host, send_port = '223.171.136.213', 5004
        '''local 실험시''' # 마찬가지로, 포트 변경 필요
        # recv_host, recv_port = 'localhost', 5003
        # send_host, send_port = 'localhost', 5004

        self.ip_address = recv_host

        # recv_host, recv_port = '192.168.0.62', 5001
        # send_host, send_port = '192.168.0.62', 5002
        stop_event = threading.Event()
        recv_socket = None
        send_socket = None
        print("receiving readying")

        data_buffer = b''

        while not stop_event.is_set():
            try:
                if not recv_socket:
                    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    recv_socket.settimeout(5)
                    recv_socket.connect((recv_host, recv_port))
                    print("Connected to recv server")

                if not send_socket:
                    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    send_socket.settimeout(5)
                    send_socket.connect((send_host, send_port))
                    print("Connected to send server")

                ready_to_read, ready_to_write, _ = select.select([recv_socket], [send_socket], [], 1)

                ### PC에서 읽기
                if ready_to_read:
                    try:
                        data = recv_socket.recv(1024)
                    except socket.timeout:
                        print("Receive timeout. Trying again...")
                        continue
                    except ConnectionResetError:
                        print("Connection reset by remote host. Reconnecting...")
                        recv_socket.close()
                        recv_socket = None
                        continue

                    if data:
                        data_buffer = b''  # 버퍼를 초기화합니다.
                        data_buffer += data

                        if b'\n' in data_buffer:
                            data_line, data_buffer = data_buffer.split(b'\n', 1)
                            try:
                                received_dict = json.loads(data_line.decode('utf-8'))
                                self.connection = True
                                print("Jetson >> PC", received_dict)
                            except (json.JSONDecodeError, TypeError, ValueError):
                                print("Failed to decode received data from client.")
                            else:
                                if self.validate_received_data(received_dict):
                                    self.data = received_dict
                                else:
                                    print("Invalid data received. Discarding...")

                # PC에서 jetson에 쓰기
                if ready_to_write:
                    if self.flag_auto_driving == True:
                        if self.validate_message(self.message):
                            message = json.dumps(self.message)
                            message += '\n'
                            send_socket.sendall(message.encode())
                            self.connection = True
                            self.flag_auto_driving = False
                            print("COM >> Jetson, send : ", message.encode())
                        else:
                            print("Invalid message. Not sending...")

                time.sleep(0.05)

            except (socket.error, Exception) as e:
                self.connection = False
                print(f"Error: {e}")
                traceback.print_exc()
                if recv_socket:
                    recv_socket.close()
                    recv_socket = None
                if send_socket:
                    send_socket.close()
                    send_socket = None
                time.sleep(1)

        if recv_socket:
            recv_socket.close()

        if send_socket:
            send_socket.close()

    def validate_received_data(self, data):
        # 데이터 형식 및 값 검증 로직 작성
        required_keys = ["mode_jetson", "dest_latitude", "dest_longitude"]
        for key in required_keys:
            if key not in data:
                return False

        return True

    def validate_message(self, message):
        # 메시지 형식 및 값 검증 로직 작성
        # 예를 들어, 필수 키가 있는지 확인하고, 위도와 경도가 올바른 범위 내에 있는지 확인
        required_keys = ["mode_jetson", "dest_latitude", "dest_longitude"]
        for key in required_keys:
            if key not in message:
                return False

        return True

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.thread = None
        self.model = QStandardItemModel(self)
        self.points_init = False
        self.on_record = True
        self.is_auto_driving = False
        self.cnt_destination = 0
        self.prev_destination = None

        # self.combo_mode.setEnabled(False)
        self.flag_simulation = False
        self.simulation_thread = None
        self.simulation_pwml_auto = None
        self.simulation_pwmr_auto = None
        self.flag_simulation_data_init = False

        # 여기는 draw_ship 초기 변수 >> 지우면 안 됨
        self.simulation_lat = 37.63124688
        self.simulation_lon = 127.07633361
        self.simulation_head = 0

        self.sensor_data = {'mode_jetson': "SELF",'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None, 'pwmr_auto' : None, 'pwml_sim' : None, 'pwmr_sim' : None, "latitude": 37.63124688, "longitude": 127.07633361, 'dest_latitude': None, 'dest_longitude' : None,
                            'velocity': None,
                            'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'date' : None, 'distance' : None}
        ### mode : None, driving

        coordinate = (self.sensor_data['latitude'], self.sensor_data['longitude'])
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch = 1)

        self.m = folium.Map(
            zoom_start=18, location=coordinate, control_scale=True
        )

        folium.TileLayer('OpenStreetMap', max_zoom=22).add_to(self.m)

        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': False,
                'polygon': True,
                'circle': False,
                'marker': True,
                'circlemarker': False},
            edit_options={'edit': False})
        self.m.add_child(draw)

        formatter = "function(num) {return L.Util.formatNum(num, 3) + ' º ';};"
        MousePosition(
            position="topright",
            separator=" | ",
            empty_string="NaN",
            lng_first=True,
            num_digits=20,
            prefix="Coordinates:",
            lat_formatter=formatter,
            lng_formatter=formatter,
        ).add_to(self.m)

        self.marker = None
        self.polygon_id = None

        self.data = io.BytesIO()
        self.m.save(self.data, close_file=False)

        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

        while self.isVisible():
            app.processEvents()

        for line_edit in self.findChildren(QtWidgets.QLineEdit):
            line_edit.setReadOnly(True)

        self.worker = Worker()
        self.worker.start()

        print("nope")

        self.timer100 = QTimer(self)
        self.timer100.timeout.connect(self.update_data)
        self.timer100.timeout.connect(self.show_sensor_data)
        self.timer100.start(50)  # 5 seconds
        #
        self.timer1000 = QTimer(self)
        self.timer1000.timeout.connect(self.draw_ship)
        self.timer1000.timeout.connect(self.route_generate)
        self.timer1000.start(1000)

    def update_data(self):
        try:
            self.sensor_data = self.worker.data
            # print("self.sensor_data : ", self.sensor_data)
        except:
            print("Nope2")

    def route_generate(self):
        # 이전 위치에서 일정 거리만큼 북동쪽 방향으로 이동

        if self.flag_simulation:
            try:
                latitude = self.simulation_lat
                longitude = self.simulation_lon
            except:
                self.btn_pointing.setText("Pointing START")
                print("목적지를 수신받지 않았습니다.")
                return
        else:
            try:
                latitude = self.sensor_data['latitude']
                longitude = self.sensor_data['longitude']
            except:
                return print("Nooop")
        js = Template(
            """
            if ({{on_record}}) {
                var point = L.circleMarker(
                    [{{latitude}}, {{longitude}}], {
                        "bubblingMouseEvents": true,
                        "color": "#3388ff",
                        "dashArray": null,
                        "dashOffset": null,
                        "fill": true,
                        "fillColor": "#3388ff",
                        "fillOpacity": 0.2,
                        "fillRule": "evenodd",
                        "lineCap": "round",
                        "lineJoin": "round",
                        "opacity": 1.0,
                        "radius": 2,
                        "stroke": true,
                        "weight": 5
                    }
                );
                pointsArray.push(point);
                point.addTo({{map}});
            }
            """
        ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude, on_record=str(self.on_record).lower())
        # Leaflet이 초기화될 때 pointsArray를 생성해야 합니다.
        init_js = Template("var pointsArray = [];").render()
        if self.points_init == False:
            self.view.page().runJavaScript(init_js)
            self.points_init = True
        self.view.page().runJavaScript(js)

    def pointing(self): ## 경로 지우는 용도로 써야겠다
        if self.on_record == False:
            self.on_record = True
            self.btn_pointing.setText("Pointing STOP")
            return
        elif self.on_record == True:
            self.btn_pointing.setText("Pointing START")

        self.on_record = False
        js = """
                for (var i = 0; i < pointsArray.length; i++) {
                    {{map}}.removeLayer(pointsArray[i]);
                }
                pointsArray = [];
            """
        self.view.page().runJavaScript(Template(js).render(map=self.m.get_name()))

    #해야 할 것 !!!
    def draw_ship(self):
        if not self.flag_simulation:
            try:
                lat = float(self.sensor_data['latitude'])
                lon = float(self.sensor_data['longitude'])
                head = float(self.sensor_data['heading']) if self.sensor_data['heading'] != None else 0
            except:
                return print("here")
        else:
            lat = self.simulation_lat
            lon = self.simulation_lon
            head = self.simulation_head

        ship_size = 0.0105 ## km단위

        triangle1, triangle2, triangle3 = self.calculate_triangle_vertices(lat, lon, head, ship_size)
        latitude1, longitude1 = triangle1
        latitude2, longitude2 = triangle2
        latitude3, longitude3 = triangle3
        self.view.page().runJavaScript(Template("{{map}}.removeLayer(polygon)").render(map = self.m.get_name()))

        js = Template(
            """
            var polygon = L.polygon([
                [{{latitude}}, {{longitude}}],
                [{{latitude2}}, {{longitude2}}],
                [{{latitude3}}, {{longitude3}}]
            ],
            {
                "color": "#000000",
                "weight": 3,
                "opacity": 1,
                "fillColor": "#ff0000",
                "fillOpacity": 1,
                "zIndex": 1000
            }
            ).addTo({{map}});
            """
        ).render(map=self.m.get_name(), latitude=latitude1, longitude=longitude1,
                 latitude2=latitude2, longitude2=longitude2,
                 latitude3=latitude3, longitude3=longitude3)

        self.view.page().runJavaScript(js)


    def calculate_triangle_vertices(self, lat, lon, heading, ship_size):
        # 위도(lat), 경도(lon)를 radian 단위로 변환
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        # 방위각(heading)를 radian 단위로 변환
        heading_rad = math.radians(heading)

        # 선박의 길이를 이등변삼각형 높이로 설정
        height = ship_size / 2

        # 이등변삼각형의 내심 좌표 계산
        center_lat = math.degrees(lat_rad - height * math.cos(heading_rad))
        center_lon = math.degrees(lon_rad + height * math.sin(heading_rad) / math.cos(lat_rad))

        # 각 꼭지점의 방위각 계산
        angles = [heading_rad, heading_rad + math.radians(150), heading_rad - math.radians(150)]

        # 꼭지점 좌표를 저장할 리스트 초기화
        vertices = []

        # 각 꼭지점의 좌표 계산
        for angle in angles:
            # 위도와 경도의 차이값 계산
            dlat = math.cos(angle) * height / 6371
            dlon = math.sin(angle) * height / (6371 * math.cos(lat_rad))

            # 위도와 경도의 차이값을 더해 새로운 좌표를 계산
            new_lat = lat + math.degrees(dlat)
            new_lon = lon + math.degrees(dlon)

            # 꼭지점 좌표를 리스트에 추가
            vertices.append((new_lat, new_lon)) ##

        # 꼭지점 좌표를 리스트 형태로 반환
        return vertices

    def move_item_up(self):
        # Get the current index
        index = self.waypoints.currentIndex()

        # Check if the current index is not the first index
        if index.row() > 0:
            # Get the item to move
            item = self.model.takeRow(index.row())

            # Move the item to the new index
            self.model.insertRow(index.row() - 1, item)

            # Set the current index to the new index
            self.waypoints.setCurrentIndex(self.model.indexFromItem(item[0]))

    def move_item_down(self):
        # Get the current index
        index = self.waypoints.currentIndex()

        # Check if the current index is not the last index
        if index.row() < self.model.rowCount() - 1:
            # Get the item to move
            item = self.model.takeRow(index.row())

            # Move the item to the new index
            self.model.insertRow(index.row() + 1, item)

            # Set the current index to the new index
            self.waypoints.setCurrentIndex(self.model.indexFromItem(item[0]))

    def delete_item(self):
        # Get the current index
        index = self.waypoints.currentIndex()

        # Remove the item from the model
        self.model.removeRow(index.row())

    def stop_driving(self):
        # message 활성화
        self.worker.flag_auto_driving = True
        self.worker.message = {"mode_jetson" : "SELF", "dest_latitude" : None, "dest_longitude" : None}

        self.is_auto_driving = False
        self.sensor_data['mode_jetson'] = "SELF"
        self.sensor_data["dest_latitude"] = None
        self.sensor_data["dest_longitude"] = None
        self.sensor_data["pwml_auto"] = None
        self.sensor_data["pwmr_auto"] = None
        self.edit_destination.setText(str(self.sensor_data["dest_latitude"]) + ", " + str(self.sensor_data["dest_longitude"]))
        self.edit_mode_jetson.setText("SELF") ########
        self.edit_pwml_auto.setText("None")
        self.edit_pwmr_auto.setText("None")

        # auto_driving 목적지 관련 변수
        self.prev_destination = None
        self.cnt_destination = 0


    def show_sensor_data(self):
        try:

            for key, value in self.sensor_data.items():
                try:
                    edit_name = 'edit_' + key
                    if hasattr(self, edit_name):
                        edit_widget = getattr(self, edit_name)

                        if value is not None:
                            edit_widget.setText(str(value))
                            # edit_widget.setText(str(1))
                        else:
                            edit_widget.setText("None")

                except:
                    print("not showing data : ", key)
            try:
                if self.simulation_distance_to_target is not None:
                    self.edit_distance_simulation.setText(str(self.simulation_distance_to_target))
                    self.edit_pwml_simulation.setText(str(self.simulation_pwml_auto))
                    self.edit_pwmr_simulation.setText(str(self.simulation_pwmr_auto))
            except Exception as e:
                # print("why...? ", e)
                pass

            try:
                if self.worker.connection:
                    self.edit_IP.setText(str(self.worker.ip_address))
                    self.edit_com_status.setText("양호")
                else:
                    self.edit_IP.setText(None)
                    self.edit_com_status.setText(None)
            except:
                pass

            lst_dest_longitude = [coord[0] for coord in self.waypoints_list]
            lst_dest_latitude = [coord[1] for coord in self.waypoints_list]

            try:
                self.edit_current_mode.setText(str(self.sensor_data['mode_chk']))
                self.edit_destination.setText(str(str(self.sensor_data['cnt_destination']) + ", " + str(lst_dest_latitude[int(self.sensor_data["cnt_destination"])]) + ", " + str(lst_dest_longitude[int(self.sensor_data["cnt_destination"])])))
            except Exception as e:
                pass
                # print("show sensordata", e)
        except:
            pass
            # print("why?")

        # print(self.sensor_data)

    def select_destination(self):
        try:
            destination_longitude, destination_latitude = self.get_selected_coordinates()
            print("???", destination_longitude, destination_latitude)

            self.edit_destination.setText(str(destination_longitude) + ", " + str(destination_latitude))
            # self.edit_distance.setText(str())
            self.sensor_data['dest_latitude'] = destination_latitude
            self.sensor_data['dest_longitude'] = destination_longitude
            self.worker.message['dest_latitude'] = float(self.sensor_data['dest_latitude'])
            self.worker.message['dest_longitude'] = float(self.sensor_data['dest_longitude'])
            print("sensor_Data[dest_latitude] : {}, sensor_data[dest_longitude] : {}".format(self.sensor_data['dest_latitude'], self.sensor_data['dest_longitude']))
            # self.worker.message = "dest_latitude" : float(self.sensor_data['dest_latitude']), "dest_longitude" : float(self.sensor_data['dest_longitude'])}
            # print("self.worker.message : ", self.worker.message)
        except:
            return print("No destination")

    # start_driving 버튼 직접 연결된 slot
    def start_driving(self):
        self.cnt_destination = 0
        self.prev_destination = None
        self.worker.flag_auto_driving = True

        ## 자율 운항 중인지 확인은 >> mode_jetson == "AUTO" 일 때
        # Iterate through each item in the QListWidget
        self.waypoints_list = []
        view = self.waypoints
        model = view.model()
        try:
            for row in range(model.rowCount()):
                index = model.index(row, 0)  # 0 is for the first column
                coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
                coordinates_list = coordinates_str.strip('[]').split(', ')
                try:
                    longitude = float(coordinates_list[0])
                    latitude = float(coordinates_list[1])
                except ValueError:
                    break
                self.waypoints_list.append((longitude, latitude))

        except:
            self.worker.flag_auto_driving = False
            return print("목적지가 없습니다.")

        lst_dest_longitude = [coord[0] for coord in self.waypoints_list]
        lst_dest_latitude = [coord[1] for coord in self.waypoints_list]


        self.is_auto_driving = True
        self.worker.message = {"mode_jetson": "AUTO", "dest_latitude": lst_dest_latitude,
                               "dest_longitude": lst_dest_longitude}

    def get_selected_coordinates(self) -> tuple:
        view = self.waypoints
        model = view.model()
        index = view.currentIndex()

        if not index.isValid():
            return None

        coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
        coordinates_list = coordinates_str.strip('[]').split(', ')

        try:
            longitude = float(coordinates_list[0])
            latitude = float(coordinates_list[1])

        except ValueError:
            return None

        return longitude, latitude

    # btn 연결 된 것
    def simulator(self):
        try:
            float(self.sensor_data['latitude'])
            float(self.sensor_data['longitude'])
            self.sensor_data['dest_latitude']
            self.sensor_data['dest_longitude']
        except:
            return

        if self.simulation_thread is None:
            self.simulation_thread = threading.Thread(target=self.simulation)
            self.simulation_thread.start()
            self.btn_simulation.setText("Simulation STOP")
        else:
            self.stop_simulation()
            self.simulation_thread = None
            self.btn_simulation.setText("Simulation START")

    def stop_simulation(self):
        try:
            print("stop received")
            self.flag_simulation = False
            self.simulation_distance_to_target = None
            self.simulation_pwml_auto = None
            self.simulation_pwmr_auto = None
            self.edit_destination.setText("None")
            self.worker.message['mode_jetson'] = "SELF"
            self.worker.message['dest_latitude'] = None
            self.worker.message['dest_longitude'] = None
            self.sensor_data['mode_jetson'] = "SELF"
            self.sensor_data['dest_latitude'] = None
            self.sensor_data['dest_longitude'] = None
            # if self.simulation_thread is not None:
            #     print(15)
            #     self.simulation_thread.join()
            self.simulation_thread = None
        except Exception as e:
            print("stop simulation error : ", e)

    #### self.simulator에서 실행됨
    def simulation(self):
        self.flag_simulation = True

        self.worker.message = {"mode_jetson": "SMLT", "dest_latitude": 2, "dest_longitude": 1}

        self.sim_waypoints_list = []
        view = self.waypoints
        model = view.model()

        for row in range(model.rowCount()):
            index = model.index(row, 0)  # 0 is for the first column
            coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
            coordinates_list = coordinates_str.strip('[]').split(', ')

            try:
                longitude = float(coordinates_list[0])
                latitude = float(coordinates_list[1])

            except ValueError:
                self.stop_simulation()
                self.btn_simulation.setText("Simulation START")
                return print("nopp")

            self.sim_waypoints_list.append((longitude, latitude))

        try:
            current_latitude = float(self.sensor_data['latitude'])
            current_longitude = float(self.sensor_data['longitude'])
            lst_dest_longitude = [coord[0] for coord in self.sim_waypoints_list]
            lst_dest_latitude = [coord[1] for coord in self.sim_waypoints_list]
        except:
            self.stop_simulation()
            self.btn_simulation.setText("Simulation START")
            print("destination_latitude 없음")
            return

        current_heading = self.sensor_data['heading'] if self.sensor_data['heading'] is not None else 0

        self.sim_cnt_destination = 0
        prev_sim_cnt_destination = 0
        try:
            while self.flag_simulation:
                print(1)
                if self.sim_cnt_destination >= len(lst_dest_latitude):
                    self.flag_simulation = False
                    # print("The boat has visited all destinations!")
                    # self.stop_simulation()
                    # print(1)
                    # self.btn_simulation.setText("Simulation START")
                    # print(2)
                    return

                # if prev_sim_cnt_destination == 0 or prev_sim_cnt_destination != self.sim_cnt_destination:
                #     self.edit_destination.setText(str(self.sim_cnt_destination))

                print(2)
                destination_latitude = float(lst_dest_latitude[self.sim_cnt_destination])
                destination_longitude = float(lst_dest_longitude[self.sim_cnt_destination])
                print(current_latitude, current_longitude, destination_longitude, destination_latitude)
                print(3)
                if current_heading > 180:
                    current_heading = current_heading - 360

                print(4)

                # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
                self.simulation_distance_to_target = haversine((current_latitude, current_longitude),
                                                               (destination_latitude, destination_longitude),
                                                               unit='m')
                print(5)
                # self.sensor_data['distance'] = float(self.simulation_distance_to_target)

                # 선박과 목적지가 이루는 선의 자북에 대한 각도 계산
                target_angle = math.degrees(
                    math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))

                print(6)
                # 헤딩과 목표 각도 간의 차이 계산
                angle_diff = target_angle - current_heading
                if angle_diff > 180:
                    angle_diff -= 360
                elif angle_diff < -180:
                    angle_diff += 360

                print(7)
                # 각도 차이에 따른 throttle 및 roll 성분 계산
                throttle_component = self.simulation_distance_to_target * math.cos(math.radians(angle_diff))
                roll_component = self.simulation_distance_to_target * math.sin(math.radians(angle_diff))

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

                self.simulation_pwml_auto = int(PWM_left)
                self.simulation_pwmr_auto = int(PWM_right)

                print(7)
                # print("left : {}, right :{}".format(self.simulation_pwml_auto, self.simulation_pwmr_auto))
                try:
                    if self.simulation_pwml_auto == self.simulation_pwmr_auto and self.simulation_pwml_auto != 1500:
                        # Go straight
                        lat_diff = 0.00001 * math.cos(math.radians(current_heading))
                        lng_diff = 0.00001 * math.sin(math.radians(current_heading))
                    elif self.simulation_pwml_auto < self.simulation_pwmr_auto:
                        # Turn right
                        heading_diff = math.radians(5)
                        lat_diff = 0.00001 * math.cos(math.radians(current_heading - heading_diff))
                        lng_diff = 0.00001 * math.sin(math.radians(current_heading - heading_diff))
                        current_heading -= math.degrees(heading_diff)
                    elif self.simulation_pwml_auto > self.simulation_pwmr_auto:
                        # Turn left
                        heading_diff = math.radians(5)
                        lat_diff = 0.00001 * math.cos(math.radians(current_heading + heading_diff))
                        lng_diff = 0.00001 * math.sin(math.radians(current_heading + heading_diff))
                        current_heading += math.degrees(heading_diff)

                    else:
                        print("error")

                    self.simulation_head = current_heading
                    current_latitude = round(lat_diff + current_latitude, 8)
                    current_longitude = round(lng_diff + current_longitude, 8)
                    self.simulation_lat = current_latitude
                    self.simulation_lon = current_longitude
                    # self.current_value['latitude'] = round(lat_diff + self.current_value['latitude'], 8)
                    # self.current_value['longitude'] = round(lng_diff + self.current_value['longitude'], 8)

                    if self.simulation_distance_to_target < 2:
                        # Stop the boat
                        prev_sim_cnt_destination = self.sim_cnt_destination
                        self.sim_cnt_destination += 1
                        print("Boat has reached the destination!")

                    self.flag_simulation_data_init = True
                    print(self.sim_cnt_destination)
                    print(9)
                    time.sleep(0.1)
                except Exception as E:
                    print("simulator Error : ", E)
                    time.sleep(1)

        except Exception as e:
            self.stop_simulation()
            self.btn_simulation.setText("Simulation START")
            print("simulation error : ", e)
            return

        self.stop_simulation()
        self.btn_simulation.setText("Simulation START")

class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def javaScriptAlert(self, securityOrigin: QtCore.QUrl, msg: str):
        f = open('stdout.txt', 'w')
        sys.stdout = f
        coords_dict = json.loads(msg)
        coords = coords_dict['geometry']['coordinates']
        sys.stdout = sys.__stdout__
        f.close()

        item = QStandardItem(str(coords))
        w.model.appendRow(item)
        w.waypoints.setModel(w.model)

        for row in range(w.model.rowCount()):
            for column in range(w.model.columnCount()):
                index = w.model.index(row, column)
                item = w.model.data(index)
                # print(f"Row {row}, Column {column}: {item}")

w = Window()
w.show()
sys.exit(app.exec())