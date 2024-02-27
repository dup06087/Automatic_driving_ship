from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QMutex, QUrl
from PIL import Image
import numpy as np
from jinja2 import Template
from PyQt5.QtGui import QStandardItem
from haversine import haversine, Unit
import socket, threading, queue, json, traceback, select, re, math, serial, folium, io, sys, json
from PC_ui_control import *
from PC_commute_with_jetson import Client
from PC_simulator import run_simulator, stop_simulator, pc_simulator
from qt_material import apply_stylesheet
import random
form_class = uic.loadUiType("V1_UI.ui")[0]
from math import radians, cos, sin

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.init_values()

        self.sensor_data = {
            # dest_latitude, dest_longitude : list, connected with pc def start_driving
            'dest_latitude': None, 'dest_longitude': None, 'mode_pc_command': "SELF", 'com_status': None, # pc get params
            'mode_chk': None, 'pwml_chk': None, 'pwmr_chk': None, # nucleo get params
            'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, 'cnt_destination' : None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None, # auto drving
            # gnss get params below
            'velocity': None, 'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None, 'date': None,
            "longitude": 127.077618, "latitude": 37.633173, "arrived": False
            # gnss end
            } # cf. com_status undefined
            # dest_latitude, dest_longitude > edit_destination에 [,]로 들어감
            #
            # qtdesigner에 cnt_destination 없음, waypoint_latitude, waypoint_longitude 없음
        '''
        qt designer edit names
        current_mode, mode_chk, pwml_chk, pwmr_chk, mode_pc_command, pwml_auto, pwmr_auto, pwml_sim, pwmr_sim, distance_simulation, edit_distance
        latitude, longitude, destination, heading, velocity, pitch, roll, validity(gps), time, IP, com_status
        X : current_mode
        '''
        self.init_folium()

        self.mutex = QMutex()

        self.worker = Client()
        self.worker.start()


        ###

        self.timer100 = QTimer(self)
        self.timer100.timeout.connect(self.update_data)
        self.timer100.timeout.connect(self.show_sensor_data)
        self.timer100.timeout.connect(self.arrived_detect)
        # self.timer100.timeout.connect(self.exe_timer1000_functions)
        self.timer1000 = QTimer(self)
        self.timer1000.timeout.connect(self.exe_timer1000_functions)
        # self.timer1000.timeout.connect(self.draw_ship)
        # self.timer1000.timeout.connect(self.route_generate)
        # self.timer1000.timeout.connect(self.draw_obstacle)
        self.timer1000.timeout.connect(self.print_values)
        # self.timer1000.timeout.connect(lambda: self.draw_obstacle(self.worker, self.view))

        #
        self.timer100.start(100)  # 5 seconds
        self.timer1000.start(1000)

    def arrived_detect(self):
        try:
            if self.sensor_data["arrived"] and not self.prev_sensor_data_arrived:
                self.btn_drive.setEnabled(True)
                self.btn_stop_driving.setEnabled(False)
                self.btn_simulation.setEnabled(True)
                self.worker.send_data = {"mode_pc_command" : "SELF", "dest_latitude" : None, "dest_longitude" : None} # send는 따로 sensor_data 안 거치고 바로 보냄
            self.prev_sensor_data_arrived = self.sensor_data["arrived"]
        except KeyError:
            pass

        except Exception as e:
            print("arrived detection error : ", e)


    def exe_timer1000_functions(self):
        try:
            self.draw_ship()
            self.route_generate()
            self.draw_obstacle()
            self.draw_waypoint()
            update_current_marker(self)


        except Exception as e:
            print("timer1000 functions error : ", e)

    def draw_waypoint(self):
        exe_draw_waypoint(self)

    def print_values(self):
        print(self.sensor_data)

    def meters_to_latlon(self, lat, lon, delta_x, delta_y):
        # 지구 반경 (미터 단위)
        earth_radius = 6378137.0

        # 라디안 단위로 변환
        dLat = delta_y / earth_radius
        dLon = delta_x / (earth_radius * math.cos(math.pi * lat / 180))

        # 변환된 위도/경도
        new_lat = lat + dLat * 180 / math.pi
        new_lon = lon + dLon * 180 / math.pi

        return new_lat, new_lon

    def draw_obstacle(self):
        # 리스트가 None이거나 비어있는 경우 아무것도 하지 않음
        if not self.worker.obstacle_data:
            return

        if self.worker.received_data["latitude"] is None or self.worker.received_data["longitude"] is None:
            return print("draw obstacle error : lat, lon is None")

        # 기존에 그려진 장애물 제거
        self.view.page().runJavaScript("if (window.obstaclesLayer) {window.obstaclesLayer.clearLayers();}")

        # print("self.worker : ", self.worker.received_data)
        latitude = self.worker.received_data["latitude"]
        longitude = self.worker.received_data["longitude"]

        heading = self.sensor_data['heading']

        for obstacle in self.worker.obstacle_data:
            dx, dy, width, height = obstacle

            # 장애물의 중심점 계산
            cx, cy = dx + width / 2, dy + height / 2

            # 꼭짓점 계산
            corners = [
                (dx, dy),
                (dx + width, dy),
                (dx + width, dy + height),
                (dx, dy + height)
            ]

            # 회전 적용
            rotated_corners = []
            for corner in corners:
                # 장애물을 중심점을 기준으로 회전
                rotated_x, rotated_y = self.rotate_point(corner[0], corner[1], cx, cy, heading)
                rotated_corners.append((rotated_x, rotated_y))

            # 위도/경도 변환 및 Polygon 생성
            lat_lon_corners = []
            for corner in rotated_corners:
                lat, lon = self.meters_to_latlon(latitude, longitude, corner[0], corner[1])
                lat_lon_corners.append([lat, lon])

            # Leaflet Polygon 생성
            js_code = Template(
                """
                if (!window.obstaclesLayer) {
                    window.obstaclesLayer = L.layerGroup().addTo({{ map }});
                }
                var polygon = L.polygon(
                    {{ lat_lon_corners }},
                    {
                        "color": "#ff0000",
                        "weight": 1,
                        "fillOpacity": 0.2
                    }
                );
                window.obstaclesLayer.addLayer(polygon);
                """
            ).render(
                map=self.m.get_name(),
                lat_lon_corners=lat_lon_corners
            )
            self.view.page().runJavaScript(js_code)

    def rotate_point(self, px, py, cx, cy, angle):
        # 포인트 회전 함수
        theta = np.radians(angle)
        dx, dy = px - cx, py - cy
        qx = np.cos(theta) * dx - np.sin(theta) * dy + cx
        qy = np.sin(theta) * dx + np.cos(theta) * dy + cy
        return qx, qy

    def init_values(self):
        exe_init_values(self)

    def init_folium(self):
        coordinate = (self.sensor_data['latitude'], self.sensor_data['longitude'])
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch=1)

        tiles = "http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"
        #         # tiles = "http://mt0.google.com/vt/lyrs=y&hl=ko&x={x}&y={y}&z={z}" #hybrid
        #         # tiles = "http://mt0.google.com/vt/lyrs=t&hl=ko&x={x}&y={y}&z={z}" # terrain only
        #         # tiles = "http://mt0.google.com/vt/lyrs=s&hl=ko&x={x}&y={y}&z={z}" # staellite only
        attr = "Google"
        self.m = folium.Map(
            location=[37.631104100930436, 127.0779647879758], zoom_start=18, tiles=tiles, attr=attr, max_zoom= 22)

        # self.m = folium.Map(
        #     zoom_start=18, location=coordinate, control_scale=True
        # )
        # folium.TileLayer('OpenStreetMap', max_zoom=22).add_to(self.m)

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


    def route_generate(self):
        exe_route_generate(self)

    def pointing(self): ## 경로 지우는 용도로 써야겠다
        exe_pointing(self)

    #해야 할 것 !!!
    def draw_ship(self):
        exe_draw_ship(self)

    def move_item_up(self):
        exe_move_item_up(self)

    def move_item_down(self):
        exe_move_item_down(self)

    def delete_item(self):
        exe_delete_item(self)

    def show_sensor_data(self):
        exe_show_sensor_data(self)

    def get_selected_coordinates(self) -> tuple:
        exe_get_selected_coordinates(self)

    def stop_simulation(self):
        stop_simulator(self)

    # btn 연결 된 것
    def simulator(self):
        pc_simulator(self)

    #### self.simulator에서 thread로 실행됨
    def simulation(self):
        run_simulator(self)

    def stop_driving(self):
        # message 활성화
        self.btn_drive.setEnabled(True)
        self.btn_stop_driving.setEnabled(False)
        self.btn_simulation.setEnabled(True)

        self.worker.send_data = {"mode_pc_command" : "SELF", "dest_latitude" : None, "dest_longitude" : None} # send는 따로 sensor_data 안 거치고 바로 보냄

    # start_driving 버튼 직접 연결된 slot
    # 아직 첫번째 목적지만
    def start_driving(self):
        if not get_destinations_from_gui(self):
            print("cannot start driving")
            return

        self.btn_drive.setEnabled(False)
        self.btn_stop_driving.setEnabled(True)
        self.btn_simulation.setEnabled(False)

        self.worker.send_data = {"mode_pc_command": "AUTO", "dest_latitude": self.lst_dest_latitude, # send는 따로 sensor_data 안 거치고 바로 보냄
                               "dest_longitude": self.lst_dest_longitude}
        print("diff check : ", self.worker.last_sent_command, self.worker.send_data)

    def update_data(self):
        try:
            # self.worker.data > jetson한테 받은 데이터 > 데이터 쓰는 중에 가져가는 것 방지
            self.mutex.lock()
            self.sensor_data = self.worker.received_data
            self.sensor_data["pwml_sim"] = self.simulation_pwml_auto
            self.sensor_data["pwmr_sim"] = self.simulation_pwmr_auto
            # TODO : update

            self.mutex.unlock()
        except Exception as e:
            print("fail to update current data : ", e)
            self.mutex.unlock()


class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def javaScriptAlert(self, securityOrigin: QtCore.QUrl, msg: str):
        f = open('../stdout.txt', 'w')
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

app = QtWidgets.QApplication(sys.argv)
img = Image.open('../image.png')
apply_stylesheet(app, theme='dark_red.xml')
#light_blue #light_cyan_500 #light_lightgreen #light_pink # light_red
w = Window()
w.show()
sys.exit(app.exec())