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

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('image.png')

class Worker(QtCore.QThread):
    def run(self):
        self.message = {"mode" : None, "dest_latitude" : None, "dest_longitude" : None}
        self.sensor_data = None

        print("where?")
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

                    # 데이터 전송
                    message = json.dumps(self.message)
                    # 데이터 수신
                    client_socket.sendall(message.encode())
                    data = client_socket.recv(1024).decode()
                    print(data)
                    data = json.loads(data)
                    self.sensor_data = data
                    print("Jetson >> COM, receive : ", self.sensor_data)
                    print("COM >> Jetson, send : ", message)
                    # print(f"Received server data: {data}")

                    time.sleep(1)

                except socket.error as e:
                    # 소켓 오류 처리
                    print(f"Socket error: {e}")
                    client_socket = None
                    time.sleep(5)

                except Exception as e:
                    # 예외 처리
                    print(f"PC data Error: {e}")
                    time.sleep(5)

            # 소켓 닫기
            if client_socket:
                client_socket.close()

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
        for line_edit in self.findChildren(QtWidgets.QLineEdit):
            line_edit.setReadOnly(True)

        self.sensor_data = {'mode': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None, 'pwmr_auto' : None, "latitude": 37.633173, "longitude": 127.077618, 'dest_latitude': None, 'dest_longitude' : None,
                            'velocity': None,
                            'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'date' : None}
        ### mode : None, driving

        ### 비교
        '''
        self.current_value = {'mode': None, 'pwml': None, 'pwmr': None, "latitude": None, "longitude": None, 'dest_latitude': None, 'dest_longitude' : None,
                            'velocity': None,
                            'heading': None, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'data' : None}
        '''
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.draw_ship)
        self.timer.timeout.connect(self.route_generate)
        self.timer.timeout.connect(self.show_sensor_data)
        self.timer.start(1000)  # 5 seconds

        self.worker = Worker()
        self.worker.start()

    def route_generate(self):
        # 이전 위치에서 일정 거리만큼 북동쪽 방향으로 이동
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
        ).render(map=self.m.get_name(), latitude=self.sensor_data['latitude'], longitude=self.sensor_data['longitude'], on_record=str(self.on_record).lower())
        # Leaflet이 초기화될 때 pointsArray를 생성해야 합니다.
        init_js = Template("var pointsArray = [];").render()
        if self.points_init == False:
            self.view.page().runJavaScript(init_js)
            self.points_init = True
        self.view.page().runJavaScript(js)

    def pointing(self): ## 경로 지우는 용도로 써야겠다
        if self.on_record == False:
            self.on_record = True
            return

        self.on_record = False
        js = """
                for (var i = 0; i < pointsArray.length; i++) {
                    {{map}}.removeLayer(pointsArray[i]);
                }
                pointsArray = [];
            """
        self.view.page().runJavaScript(Template(js).render(map=self.m.get_name()))

    def draw_ship(self):
        # generate new coordinate randomly
        # self.latitude += 0.00001
        # self.longitude += 0.00001

        triangle1, triangle2, triangle3 = self.calculate_triangle_vertices(self.sensor_data['latitude'], self.sensor_data['longitude'],
                                                                           self.sensor_data['heading'], 0.01)
        latitude1, longitude1 = triangle1
        latitude2, longitude2 = triangle2
        latitude3, longitude3 = triangle3
        self.view.page().runJavaScript(Template("{{map}}.removeLayer(polygon)").render(map = self.m.get_name()))

        # latitude = np.random.uniform(37.631104, 38.6311042)
        # longitude = np.random.uniform(127.07796, 128.077965)

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
        if self.worker.sensor_data != None:
            print("show_sensor_data exist")
            self.sensor_data = self.worker.sensor_data
            print("current data : ", self.sensor_data)
            try:
                for key, value in self.sensor_data.items():
                    if key != 'destination':
                        try:
                            edit_name = 'edit_' + key
                            if hasattr(self, edit_name):
                                edit_widget = getattr(self, edit_name)
                                if value is not None:
                                    edit_widget.setText(str(value))
                                else:
                                    edit_widget.setText("None")


                        except:
                            print("not showing data : ", key)
                    elif key == "destination":
                        pass
                    else:
                        print("error")

                if self.sensor_data['mode'] == "SELF":
                    self.combo_mode.setCurrentText("SELF")  # 클릭된 값에 따라 변경
                elif self.sensor_data['mode'] == "AUTO":
                    self.combo_mode.setCurrentText("AUTO")  # 클릭된 값에 따라 변경
                else:
                    print("error UI in changing mode")
            except:
                print("why?")


        # print(self.sensor_data)

    def start_driving(self):
        # if self.sensor_data["mode"] == "AUTO":
        try:
            destination_longitude, destination_latitude = self.get_selected_coordinates()
            self.edit_destination.setText(str(destination_longitude) + ", " + str(destination_latitude))
            self.worker.message = str(destination_longitude) + ", " + str(destination_latitude)
            self.worker.message = {"mode" : "AUTO", "dest_latitude" : str(destination_latitude), "dest_longitude" : str(destination_longitude)}
            self.edit_mode.setText("AUTO")
            print("self.worker.message : ", self.worker.message)
            ### self.worker.message를 통해 보내는 데이터는 > mode와 목적지
            # 즉, { "목적지" : str(destination_longitude) + ", " + str(destination_latitude), "mode" : self
        except:
            return print("No destination")

        # elif self.sensor_data["mode"] == "SELF":
        #     print("change to AUTO mode")
        #
        # elif self.sensor_data["mode"] == None:
        #     print("change to AUTO mode")
        #
        # else:
        #     print("ERROR during start_driving")


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
