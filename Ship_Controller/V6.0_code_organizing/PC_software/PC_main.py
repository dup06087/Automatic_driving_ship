from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PIL import Image
import numpy as np
from jinja2 import Template
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from haversine import haversine, Unit
import socket, threading, queue, json, traceback, select, re, math, serial, folium, io, sys, json
from PC_commute_with_jetson import Worker
from PC_simulator import run_simulator, stop_simulator, pc_simulator
from PC_ui_control import exe_move_item_up, exe_move_item_down, exe_delete_item, exe_pointing, exe_draw_ship
from PC_initializing_values import initialize_variables

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('../image.png')

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.init_values()

        self.sensor_data = {'mode_jetson': "SELF",'mode_chk': "SELF", 'pwml': None, 'pwmr': None, 'pwml_auto' : None,
                            'pwmr_auto' : None, 'pwml_sim' : None, 'pwmr_sim' : None, "latitude": 37.63124688, "longitude": 127.07633361,
                            'dest_latitude': None, 'dest_longitude' : None, 'velocity': None,
                            'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None, 'IP': None,
                            'com_status': None, 'date' : None, 'distance' : None}
        ### mode : None, driving

        self.init_folium()

        self.worker = Worker()
        self.worker.start()

        ###
        self.timer100 = QTimer(self)
        self.timer100.timeout.connect(self.update_data)
        self.timer100.timeout.connect(self.show_sensor_data)
        #
        self.timer1000 = QTimer(self)
        self.timer1000.timeout.connect(self.draw_ship)
        self.timer1000.timeout.connect(self.route_generate)
        #
        self.timer100.start(50)  # 5 seconds
        self.timer1000.start(1000)

    def init_values(self):
        initialize_variables(self)

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
        exe_pointing(self)

    #해야 할 것 !!!
    def draw_ship(self):
        exe_draw_ship(self)

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
        exe_move_item_up()

    def move_item_down(self):
        exe_move_item_down()

    def delete_item(self):
        exe_delete_item()

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
        pc_simulator(self)

    def stop_simulation(self):
        stop_simulator(self)

    #### self.simulator에서 실행됨
    def simulation(self):
        run_simulator(self)

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

w = Window()
w.show()
sys.exit(app.exec())