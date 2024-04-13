import time

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
# form_class = uic.loadUiType("V1_UI.ui")[0]
form_class = uic.loadUiType("V2_UI.ui")[0]
from math import radians, cos, sin

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.init_values()

        self.sensor_data = {
            # dest_latitude, dest_longitude : list, connected with pc def start_driving
            'dest_latitude': None, 'dest_longitude': None, 'mode_pc_command': "SELF", 'com_status': None,
            "coeff_kf": None, "coeff_kd": None, "voxel_size": None,
            "intensity": None, "dbscan_eps": None,
            "dbscan_minpoints": None, "coeff_vff_repulsive_force": None,
            # pc get params

            'mode_chk': None, 'pwml_chk': None, 'pwmr_chk': None, # nucleo get params
            'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None, 'cnt_destination' : None, 'distance': None, "waypoint_latitude" : None, "waypoint_longitude" : None, # auto drving
            # gnss get params below
            'velocity': None, 'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None, 'date': None,
            "longitude": 127.077618, "latitude": 37.633173, "arrived": False, "flag_autodrive" : False
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
        self.view.page().loadFinished.connect(self.folium_init_static_obstacles)

        self.mutex = QMutex()

        self.worker = Client()
        self.worker.start()


        ###

        self.init_coeff_progressbar()


        self.timer100 = QTimer(self)
        self.timer100.timeout.connect(self.update_data)
        self.timer100.timeout.connect(self.show_sensor_data)
        self.timer100.timeout.connect(self.arrived_detect)
        self.timer100.timeout.connect(self.update_coeff)
        # self.timer100.timeout.connect(self.exe_timer1000_functions)
        self.timer1000 = QTimer(self)
        self.timer1000.timeout.connect(self.exe_timer1000_functions)
        # self.timer1000.timeout.connect(self.draw_ship)
        # self.timer1000.timeout.connect(self.route_generate)
        # self.timer1000.timeout.connect(self.draw_obstacle)
        # self.timer1000.timeout.connect(self.print_values)
        # self.timer1000.timeout.connect(lambda: self.draw_obstacle(self.worker, self.view))

        self.timer5000 = QTimer(self)
        self.timer5000.timeout.connect(self.print_values)
        #
        self.timer100.start(100)  # 5 seconds
        self.timer1000.start(1000)
        self.timer5000.start(5000)

    def update_coeff(self):
        self.worker.coeff_Kf_value = self.coeff_Kf_value
        self.worker.coeff_Kd_value = self.coeff_Kd_value
        self.worker.coeff_voxel_size_value = self.coeff_voxel_size_value
        self.worker.coeff_intensity_value = self.coeff_intensity_value
        self.worker.coeff_eps_value = self.coeff_eps_value
        self.worker.coeff_minpoints_value = self.coeff_minpoints_value
        self.worker.coeff_vff_force_value = self.coeff_vff_force_value

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
            pass
            # print("timer1000 functions error : ", e)

    def draw_waypoint(self):
        exe_draw_waypoint(self)

    def print_values(self):
        print(self.sensor_data)

    def folium_init_static_obstacles(self):


        # 장애물의 좌표 리스트 (위도, 경도) 예시
        obstacles = [
            [[127.07792, 37.633372], [127.077896, 37.633368], [127.077892, 37.633353], [127.077907, 37.633344],
              [127.077927, 37.63335], [127.077932, 37.633369], [127.07792, 37.633372]],
            [[127.077793, 37.633292], [127.077771, 37.633283], [127.077777, 37.63327], [127.077802, 37.633268],
              [127.077811, 37.633285], [127.077793, 37.633292]],
            [[127.078049, 37.633703], [127.078025, 37.633691], [127.078047, 37.633674], [127.078072, 37.633684],
              [127.078074, 37.6337], [127.078049, 37.633703]],
            [[127.077944, 37.633639], [127.077905, 37.633611], [127.077913, 37.633569], [127.077948, 37.633553],
              [127.077985, 37.633565], [127.078, 37.633599], [127.07797, 37.633637], [127.077944, 37.633639]],
            [[127.077766, 37.633535], [127.077816, 37.633507], [127.077894, 37.633486], [127.077962, 37.63348],
              [127.078029, 37.633479], [127.078029, 37.633466], [127.077962, 37.633467], [127.07789, 37.633471],
              [127.077805, 37.633489], [127.077754, 37.633514], [127.077766, 37.633535]],
            [[127.078028, 37.63348], [127.078031, 37.633491], [127.078053, 37.633507], [127.078079, 37.633508],
              [127.0781, 37.633496], [127.078102, 37.633471], [127.078086, 37.63345], [127.078059, 37.633447],
              [127.078037, 37.633456], [127.07803, 37.633465], [127.078028, 37.63348]],
            [[127.078101, 37.633488], [127.078199, 37.633513], [127.07821, 37.633498], [127.078099, 37.63347],
              [127.078101, 37.633488]],
            [[127.078059, 37.633446], [127.078061, 37.633406], [127.07808, 37.633344], [127.078111, 37.633291],
              [127.078143, 37.633249], [127.078169, 37.633261], [127.078125, 37.633306], [127.07809, 37.633361],
              [127.078076, 37.633401], [127.078074, 37.633451], [127.078059, 37.633446]],
            [[127.078332, 37.63343], [127.078273, 37.633458], [127.078219, 37.633515], [127.078203, 37.633565],
              [127.078204, 37.633605], [127.078228, 37.633655], [127.078223, 37.63367], [127.078198, 37.633635],
              [127.078192, 37.6336], [127.078189, 37.633555], [127.0782, 37.633513], [127.078234, 37.633463],
              [127.07827, 37.633433], [127.078302, 37.63342], [127.078327, 37.633408], [127.078332, 37.63343]],
            [[127.077623, 37.633252], [127.077659, 37.633244], [127.077656, 37.633216], [127.077629, 37.6332],
              [127.077608, 37.633205], [127.077623, 37.633252]],
            [[127.078239, 37.633763], [127.078214, 37.633712], [127.078222, 37.63367], [127.078229, 37.633655],
              [127.078251, 37.633633], [127.078298, 37.633611], [127.078326, 37.633594], [127.078362, 37.633558],
              [127.07838, 37.633497], [127.07841, 37.633512], [127.078375, 37.633575], [127.078334, 37.633608],
              [127.078301, 37.633625], [127.078267, 37.63364], [127.078235, 37.633684], [127.078234, 37.633712],
              [127.078255, 37.633754], [127.078239, 37.633763]],
            [[127.07841, 37.63351], [127.078377, 37.633496], [127.078348, 37.633461], [127.078332, 37.633432],
              [127.078324, 37.633399], [127.078336, 37.633361], [127.078373, 37.633327], [127.07841, 37.63351]],
            [[127.078024, 37.633149], [127.078054, 37.633185], [127.078099, 37.633225], [127.07814, 37.633249],
              [127.078169, 37.633261], [127.078202, 37.633276], [127.078264, 37.633289], [127.078305, 37.633309],
              [127.07834, 37.633335], [127.078351, 37.633346], [127.078371, 37.633329], [127.078322, 37.633297],
              [127.078264, 37.633275], [127.078199, 37.633259], [127.078132, 37.633229], [127.078084, 37.633192],
              [127.078047, 37.633132], [127.078015, 37.633128], [127.078024, 37.633149]]

        ]
        static_obstacles = [[[lat, lon] for lon, lat in polygon] for polygon in obstacles]

        # Leaflet에 장애물을 추가하는 JavaScript 코드 생성
        for obstacle_corners in static_obstacles:
            # print(obstacle_corners)
            js_code = Template(
            """
                if (!window.static_obstacle_layer) {
                    window.static_obstacle_layer = L.layerGroup().addTo({{ map }});
                }
                var static_obstacle_polygon = L.polygon(
                    {{ lat_lon_corners }},
                    {
                        "color": "#ff0000",
                        "weight": 1,
                        "fillOpacity": 0.2
                    }
                );
                window.static_obstacle_layer.addLayer(static_obstacle_polygon);
            """
            ).render(
                map=self.m.get_name(),
                lat_lon_corners=obstacle_corners
            )

            self.view.page().runJavaScript(js_code)


        print("folium obstacle inited")


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
            return print("draw obstacle error : lat, lon is None, No gnss data")

        # 기존에 그려진 장애물 제거
        self.view.page().runJavaScript("if (window.obstaclesLayer) {window.obstaclesLayer.clearLayers();}")

        latitude = self.worker.received_data["latitude"]
        longitude = self.worker.received_data["longitude"]
        heading = self.sensor_data['heading']

        for obstacle in self.worker.obstacle_data:  # cx, cy, width, height, rotation
            cx, cy, width, height, rotation = obstacle

            # 장애물의 중심점 계산

            corners = [
                (cx - width/2, cy - height/2),
                (cx + width/2, cy - height/2),
                (cx + width/2, cy + height/2),
                (cx - width/2, cy + height/2)
            ]

            # 장애물 회전 및 heading 적용
            rotated_and_heading_adjusted_corners = []
            for corner in corners:
                # 장애물 중심에서 회전
                rotated_x, rotated_y = self.rotate_point(cx - corner[0], cy - corner[1], rotation)
                # 장애물 중심으로 다시 이동
                rotated_x += cx
                rotated_y += cy
                # 선박의 heading을 고려하여 회전

                adjusted_x, adjusted_y = self.rotate_point(rotated_x, rotated_y, -heading+90)

                rotated_and_heading_adjusted_corners.append((adjusted_x, adjusted_y))

            # 위도/경도 변환 및 Polygon 생성
            lat_lon_corners = []
            for corner in rotated_and_heading_adjusted_corners:
                lat, lon = self.meters_to_latlon(latitude, longitude, corner[0], corner[1])
                lat_lon_corners.append([lat, lon])

            print("ref type : ", lat_lon_corners) #  [[37.629339015080056, 127.07904084461484], [37.62932892186732, 127.0790391622727], [37.6293285224085, 127.07904298312958], [37.629338615621236, 127.07904466547173]]
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

    def rotate_point(self, x, y, angle):
        """주어진 각도로 점(x, y)을 회전시키는 함수. 각도는 도(degree) 단위입니다."""
        radians = math.radians(angle)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)
        rotated_x = cos_theta * x - sin_theta * y
        rotated_y = sin_theta * x + cos_theta * y
        return rotated_x, rotated_y

    def init_values(self):
        exe_init_values(self)

    def init_coeff_progressbar(self):
        set_progress_bar_values(self)

    def init_folium(self):
        coordinate = (self.sensor_data['latitude'], self.sensor_data['longitude'])
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch=1)

        tiles = "http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"
        #         # tiles = "http://mt0.google.com/vt/lyrs=y&hl=ko&x={x}&y={y}&z={z}" #hybrid
        #         # tiles = "http://mt0.google.com/vt/lyrs=t&hl=ko&x={x}&y={y}&z={z}" # terrain only
        # tiles = "http://mt0.google.com/vt/lyrs=s&hl=ko&x={x}&y={y}&z={z}" # staellite only
        attr = "Google"
        self.m = folium.Map(
            location=[37.631104100930436, 127.0779647879758], zoom_start=18, tiles=tiles, attr=attr, max_zoom= 27)

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

    def coeffcient_changing(self):
        exe_coeffcient_changing(self)

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

    def send_coeff(self):
        try:
            self.worker.send_coeff_data = {"coeff_kf": self.worker.coeff_Kf_value, "coeff_kd": self.worker.coeff_Kd_value, "voxel_size": self.worker.coeff_voxel_size_value,
                "intensity": self.worker.coeff_intensity_value, "dbscan_eps": self.worker.coeff_eps_value,
                "dbscan_minpoints": self.worker.coeff_minpoints_value, "coeff_vff_repulsive_force": self.worker.coeff_vff_force_value}

            print("coeff diff check : ", self.worker.last_sent_coeff_command, self.worker.send_data)
        except Exception as e:
            print("main.py send coeff error coeff  : ", e)

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
        f = open('./stdout.txt', 'w')
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
img = Image.open('./image.png')
apply_stylesheet(app, theme='dark_red.xml')
#light_blue #light_cyan_500 #light_lightgreen #light_pink # light_red
w = Window()
w.show()
sys.exit(app.exec())