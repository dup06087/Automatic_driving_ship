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
from PC_commute_with_jetson import Worker
from PC_simulator import run_simulator, stop_simulator, pc_simulator
from qt_material import apply_stylesheet
import random
form_class = uic.loadUiType("V1_UI.ui")[0]

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
            "longitude": 127.077618, "latitude": 37.633173,
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

        self.worker = Worker()
        self.worker.start()

        ###
        self.timer100 = QTimer(self)
        self.timer100.timeout.connect(self.update_data)
        self.timer100.timeout.connect(self.show_sensor_data)
        self.timer100.timeout.connect(self.draw_obstacle)
        # self.timer100.timeout.connect(self.update_obstacles)

        #
        self.timer1000 = QTimer(self)
        self.timer1000.timeout.connect(self.draw_ship)
        self.timer1000.timeout.connect(self.route_generate)
        #
        self.timer100.start(100)  # 5 seconds
        self.timer1000.start(1000)
        self.list_obstacles = []

    def update_obstacles(self):
        # 리스트 초기화
        self.list_obstacles.clear()

        # 현재 위치 기준으로 랜덤 사각형 좌표 생성
        base_lat, base_lon = 37.63144746129919, 127.07645840984198
        for _ in range(5):
            delta_lat = random.uniform(-0.001, 0.001)
            delta_lon = random.uniform(-0.001, 0.001)
            min_lat = base_lat + delta_lat
            min_lon = base_lon + delta_lon
            width = random.uniform(0.0001, 0.0005)
            height = random.uniform(0.0001, 0.0005)
            self.list_obstacles.append([min_lat, min_lon, width, height])

        # 장애물 그리기
        # self.draw_obstacle()

    def draw_obstacle(self):
        # 리스트가 None이거나 비어있는 경우 아무것도 하지 않음
        if not self.list_obstacles:
            return

        # 기존에 그려진 장애물 제거
        self.view.page().runJavaScript("if (window.obstaclesLayer) {window.obstaclesLayer.clearLayers();}")

        # 새 장애물 그리기
        for obstacle in self.list_obstacles:
            min_lat, min_lon, width, height = obstacle
            max_lat = min_lat + height
            max_lon = min_lon + width

            js_code = Template(
                """
                if (!window.obstaclesLayer) {
                    window.obstaclesLayer = L.layerGroup().addTo({{ map }});
                }
                var bounds = [[{{ min_lat }}, {{ min_lon }}], [{{ max_lat }}, {{ max_lon }}]];
                var rectangle = L.rectangle(
                    bounds, {
                        "color": "#ff0000",
                        "weight": 1,
                        "fillOpacity": 0.2
                    }
                );
                window.obstaclesLayer.addLayer(rectangle);
                """
            ).render(
                map=self.m.get_name(),
                min_lat=min_lat,
                min_lon=min_lon,
                max_lat=max_lat,
                max_lon=max_lon
            )
            self.view.page().runJavaScript(js_code)

    def init_values(self):
        exe_init_values(self)

    def init_folium(self):
        coordinate = (self.sensor_data['latitude'], self.sensor_data['longitude'])
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch=1)

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

        self.worker.message = {"mode_pc_command" : "SELF", "dest_latitude" : None, "dest_longitude" : None} # send는 따로 sensor_data 안 거치고 바로 보냄

    # start_driving 버튼 직접 연결된 slot
    # 아직 첫번째 목적지만
    def start_driving(self):
        get_destinations_from_gui(self)

        self.btn_drive.setEnabled(False)
        self.btn_stop_driving.setEnabled(True)
        self.btn_simulation.setEnabled(False)

        self.worker.message = {"mode_pc_command": "AUTO", "dest_latitude": self.lst_dest_latitude, # send는 따로 sensor_data 안 거치고 바로 보냄
                               "dest_longitude": self.lst_dest_longitude}

    def update_data(self):
        try:
            # self.worker.data > jetson한테 받은 데이터 > 데이터 쓰는 중에 가져가는 것 방지
            self.mutex.lock()
            self.sensor_data = self.worker.data
            self.mutex.unlock()
        except:
            print("Nope2")


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