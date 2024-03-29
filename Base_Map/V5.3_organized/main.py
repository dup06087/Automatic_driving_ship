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


form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('image.png')

class Worker(QtCore.QThread):
    data_received = pyqtSignal(object)

    def run(self):
        try:
            self.message = {"mode": None, "dest_latitude": None, "dest_longitude": None}
            # self.sensor_data = None

            while True:
                host, port = 'localhost', 5001
                stop_event = threading.Event()
                client_socket = None

                while not stop_event.is_set():
                    try:
                        if not client_socket:
                            # 소켓 생성 및 서버에 연결
                            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client_socket.connect((host, port))
                            print("Connected to server")

                        # 소켓이 쓰기 가능한지 확인
                        _, ready_to_write, _ = select.select([], [client_socket], [], 0.5)
                        if ready_to_write:
                            # 데이터 전송
                            message = json.dumps(self.message)
                            client_socket.sendall(message.encode())

                        # 지금 받아올 때의 문제!!
                        # 소켓이 읽기 가능한지 확인
                        ready_to_read, _, _ = select.select([client_socket], [], [], 0.5)
                        if ready_to_read:
                        #     # 데이터 수신
                            data = client_socket.recv(1024).decode()
                            print("여기 확인 : ", data)
                            self.data = json.loads(data)
                            print("자꾸 잘못 받아오는 부분 self.data : ", self.data )

                        print("Jetson >> COM : ", self.data)
                        print("COM >> Jetson, send : ", message)
                        time.sleep(1)


                    except (socket.error, Exception) as e:
                        print(f"Error: {e}")
                        traceback.print_exc()  # 스택 추적 정보 출력
                        client_socket = None
                        time.sleep(5)

                # 소켓 닫기
                if client_socket:
                    client_socket.close()
        except:
            print("pass")

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.thread = None
        self.model = QStandardItemModel(self)
        self.points_init = False
        self.on_record = True
        self.is_driving = False
        self.combo_mode.setEnabled(False)
        self.flag_simulation = False
        self.simulation_thread = None
        self.simulation_pwml_auto = None
        self.simulation_pwmr_auto = None
        self.flag_simulation_data_init = False
        self.sensor_data = {'mode': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None, 'pwmr_auto' : None, "latitude": 37.63124688, "longitude": 127.07633361, 'dest_latitude': None, 'dest_longitude' : None,
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.timeout.connect(self.draw_ship)
        self.timer.timeout.connect(self.route_generate)
        self.timer.timeout.connect(self.show_sensor_data)
        # self.timer.timeout.connect(self.auto_driving)
        # self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)  # 5 seconds

    def update_data(self):
        try:
            self.sensor_data = self.worker.data
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
            latitude = self.sensor_data['latitude']
            longitude = self.sensor_data['longitude']

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
            lat = float(self.sensor_data['latitude'])
            lon = float(self.sensor_data['longitude'])
            head = float(self.sensor_data['heading']) if self.sensor_data['heading'] != None else 0

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
        self.worker.message = {"mode" : None, "dest_latitude" : None, "dest_longitude" : None}
        self.sensor_data["dest_latitude"] = None
        self.sensor_data["dest_longitude"] = None
        self.sensor_data["pwml_auto"] = None
        self.sensor_data["pwmr_auto"] = None
        self.edit_destination.setText(str(self.sensor_data["dest_latitude"]) + ", " + str(self.sensor_data["dest_longitude"]))
        self.edit_pwml_auto.setText("None")
        self.edit_pwmr_auto.setText("None")

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

            self.edit_pwml_simulation.setText(str(self.simulation_pwml_auto))
            self.edit_pwmr_simulation.setText(str(self.simulation_pwmr_auto))
            print("done?")
        except:
            print("why?")

        # print(self.sensor_data)

    def start_driving(self):
        # if self.sensor_data["mode"] == "AUTO":
        try:
            destination_longitude, destination_latitude = self.get_selected_coordinates()
            self.edit_destination.setText(str(destination_longitude) + ", " + str(destination_latitude))
            # self.edit_distance.setText(str())
            self.sensor_data['dest_latitude'] = destination_latitude
            self.sensor_data['dest_longitude'] = destination_longitude
            self.worker.message = {"mode" : "AUTO", "dest_latitude" : str(destination_latitude), "dest_longitude" : str(destination_longitude)}
            print("self.worker.message : ", self.worker.message)
            ### self.worker.message를 통해 보내는 데이터는 > mode와 목적지
            # 즉, { "목적지" : str(destination_longitude) + ", " + str(destination_latitude), "mode" : self
        except:
            return print("No destination")

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

    def simulator(self):

        if self.simulation_thread is None:
            self.simulation_thread = threading.Thread(target=self.simulation)
            self.simulation_thread.start()
            self.btn_simulation.setText("Simulation STOP")
        else:
            self.stop_simulation()
            self.simulation_thread = None
            self.btn_simulation.setText("Simulation START")

    def stop_simulation(self):
        self.flag_simulation = False
        if self.simulation_thread is not None:
            self.simulation_thread.join()

    def simulation(self):
        print("log0")
        self.flag_simulation = True
        print("log0.1")

        # self.simulation_lat = float(self.sensor_data['latitude'])
        # print("log0.2")
        # self.simulation_lon = float(self.sensor_data['longitude'])
        # print("log0.3")
        # self.simulation_head = self.sensor_data['heading'] if self.sensor_data['heading'] is not None else 0
        # print("log1")

        try:
            current_latitude = float(self.sensor_data['latitude'])
            current_longitude = float(self.sensor_data['longitude'])
            destination_latitude = float(self.sensor_data['dest_latitude'])
            destination_longitude = float(self.sensor_data['dest_longitude'])
        except:
            self.stop_simulation()
            self.simulation_thread = None
            self.btn_simulation.setText("Simulation START")
            print("destination_latitude 없음")
            return

        current_heading = self.sensor_data['heading'] if self.sensor_data['heading'] is not None else 0

        try:
            if self.sensor_data['distance'] != None:
                print("log2")
                while self.flag_simulation:
                    print("log3")

                    if current_heading > 180:
                        current_heading = current_heading - 360

                    # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
                    self.simulation_distance_to_target = haversine((current_latitude, current_longitude),
                                                                   (destination_latitude, destination_longitude),
                                                                   unit='m')

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

                    print("left : {}, right :{}".format(self.simulation_pwml_auto, self.simulation_pwmr_auto))
                    try:
                        print("log4")
                        if self.simulation_pwml_auto == self.simulation_pwmr_auto and self.simulation_pwml_auto != 1500:
                            print("log5")
                            # Go straight
                            lat_diff = 0.00001 * math.cos(math.radians(current_heading))
                            lng_diff = 0.00001 * math.sin(math.radians(current_heading))
                        elif self.simulation_pwml_auto < self.simulation_pwmr_auto:
                            print("log6")
                            # Turn right
                            heading_diff = math.radians(5)
                            lat_diff = 0.00001 * math.cos(math.radians(current_heading - heading_diff))
                            lng_diff = 0.00001 * math.sin(math.radians(current_heading - heading_diff))
                            current_heading -= math.degrees(heading_diff)
                        elif self.simulation_pwml_auto > self.simulation_pwmr_auto:
                            print("log7")
                            # Turn left
                            heading_diff = math.radians(5)
                            lat_diff = 0.00001 * math.cos(math.radians(current_heading + heading_diff))
                            lng_diff = 0.00001 * math.sin(math.radians(current_heading + heading_diff))
                            current_heading += math.degrees(heading_diff)

                        else:
                            print("log7")
                            print("error")

                        self.simulation_head = current_heading
                        current_latitude = round(lat_diff + current_latitude, 8)
                        current_longitude = round(lng_diff + current_longitude, 8)
                        self.simulation_lat = current_latitude
                        self.simulation_lon = current_longitude
                        # self.current_value['latitude'] = round(lat_diff + self.current_value['latitude'], 8)
                        # self.current_value['longitude'] = round(lng_diff + self.current_value['longitude'], 8)

                        print("log8")
                        if self.simulation_distance_to_target < 2:
                            print("log9")
                            # Stop the boat
                            self.flag_simulation = False
                            self.simulation_pwml_auto = 1500
                            self.simulation_pwmr_auto = 1500
                            print("Boat has reached the destination!")
                            break

                        print("log9")
                        self.flag_simulation_data_init = True
                        time.sleep(1)

                    except Exception as E:
                        print("simulator Error : ", E)
                        time.sleep(1)
            else:
                print("The boat has already arrived at the destination!")

        except:
            self.stop_simulation()
            self.simulation_thread = None
            print("목적지가 없습니다")

    # def auto_driving(self):
    #     # while self.is_driving:
    #     print("in the auto driving")
    #     last_print_time = time.time()  # 마지막으로 출력한 시간 초기화
    #
    #
    #     while self.flag_simulation:
    #
    #         print("어디1")
    #         current_longitude = self.simulation_lon
    #         print("어디2")
    #         current_latitude = self.simulation_lat
    #         print("어디3")
    #         current_heading = self.simulation_head
    #         print("어디4")
    #         destination_latitude = float(self.sensor_data['dest_latitude'])
    #         print("어디5")
    #         destination_longitude = float(self.sensor_data['dest_longitude'])
    #         print("어디6")
    #
    #         # 헤딩 값을 -180에서 180 사이의 값으로 변환
    #         if current_heading > 180:
    #             current_heading = current_heading - 360
    #
    #         # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
    #         self.simulation_distance_to_target = haversine((current_latitude, current_longitude),
    #                                             (destination_latitude, destination_longitude), unit='m')
    #
    #         # 선박과 목적지가 이루는 선의 자북에 대한 각도 계산
    #         target_angle = math.degrees(
    #             math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))
    #
    #         # 헤딩과 목표 각도 간의 차이 계산
    #         angle_diff = target_angle - current_heading
    #         if angle_diff > 180:
    #             angle_diff -= 360
    #         elif angle_diff < -180:
    #             angle_diff += 360
    #
    #         # 각도 차이에 따른 throttle 및 roll 성분 계산
    #         throttle_component = self.simulation_distance_to_target * math.cos(math.radians(angle_diff))
    #         roll_component = self.simulation_distance_to_target * math.sin(math.radians(angle_diff))
    #
    #         # PWM 값 계산
    #         Kf = 2.5
    #         # Kd = 0.25 * 800 / (2 * math.pi * 100)
    #         Kd = 0.318
    #
    #         Uf = Kf * throttle_component
    #         Uf = max(1550 - 1500, min(Uf, 1750 - 1500))
    #
    #         Ud = Kd * roll_component
    #         max_diff = 800 * 0.125
    #         Ud = max(-max_diff, min(Ud, max_diff))
    #
    #         PWM_right = 1500 + Uf - Ud
    #         PWM_left = 1500 + Uf + Ud
    #
    #         self.simulation_pwml_auto = int(PWM_left)
    #         self.simulation_pwmr_auto = int(PWM_right)
    #
    #         current_time = time.time()
    #         if current_time - last_print_time >= 1:  # 마지막 출력 후 1초 경과 여부 확인
    #             try:
    #                 # print(self.distance_to_target)
    #                 # print("x :", throttle_component, "y : ", roll_component)
    #                 # print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)
    #                 last_print_time = current_time  # 마지막 출력 시간 업데이트
    #             except:
    #                 pass
    #         print("simulation pwml, pwmr : {}, {}".format(self.simulation_pwml_auto, self.simulation_pwmr_auto) )
    #         time.sleep(0.1)

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
