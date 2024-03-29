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

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('image.png')

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.thread = None
        self.model = QStandardItemModel(self)

        self.latitude = 37.63319
        self.longitude = 127.077624
        self.dest_lat = None
        self.dest_lon = None
        self.motL_pwm = None
        self.motR_pwm = None

        self.points_init = False
        self.on_record = True
        coordinate = (37.63319, 127.077624)
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
        self.timer.start(2000)  # 5 seconds

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
        ).render(map=self.m.get_name(), latitude=self.latitude, longitude=self.longitude, on_record=str(self.on_record).lower())
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
        self.latitude += 0.00001
        self.longitude += 0.00001

        triangle1, triangle2, triangle3 = self.calculate_triangle_vertices(self.latitude, self.longitude, 30 + random.uniform(-20, 20), 0.01)
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

        # 삼각형 꼭지점 1 계산
        lat1 = math.asin(
            math.sin(lat_rad) * math.cos(height / 6371) + math.cos(lat_rad) * math.sin(height / 6371) * math.cos(
                heading_rad))
        lon1 = lon_rad + math.atan2(math.sin(heading_rad) * math.sin(height / 6371) * math.cos(lat_rad),
                                    math.cos(height / 6371) - math.sin(lat_rad) * math.sin(lat1))

        # 삼각형 꼭지점 2 계산
        angle = math.radians(150)
        lat2 = math.asin(
            math.sin(lat_rad) * math.cos(height / 6371) + math.cos(lat_rad) * math.sin(height / 6371) * math.cos(
                heading_rad + angle))
        lon2 = lon_rad + math.atan2(math.sin(heading_rad + angle) * math.sin(height / 6371) * math.cos(lat_rad),
                                    math.cos(height / 6371) - math.sin(lat_rad) * math.sin(lat2))

        # 삼각형 꼭지점 3 계산
        lat3 = math.asin(
            math.sin(lat_rad) * math.cos(height / 6371) + math.cos(lat_rad) * math.sin(height / 6371) * math.cos(
                heading_rad - angle))
        lon3 = lon_rad + math.atan2(math.sin(heading_rad - angle) * math.sin(height / 6371) * math.cos(lat_rad),
                                    math.cos(height / 6371) - math.sin(lat_rad) * math.sin(lat3))

        # 꼭지점 좌표를 리스트 형태로 반환
        return [(math.degrees(lat1), math.degrees(lon1)), (math.degrees(lat2), math.degrees(lon2)),
                (math.degrees(lat3), math.degrees(lon3))]

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

    def coordinates_diff(self):
        current_location = (self.latitude, self.longitude)
        destination = (self.dest_lat, self.dest_lon)

        # Haversine 거리 계산
        total_distance = haversine(current_location, destination, unit=Unit.METERS)

        # 헤딩 각도와 현재 위치-목표 위치 간의 각도 계산
        d_lon = math.radians(self.dest_lon - self.longitude)
        y = math.sin(d_lon) * math.cos(math.radians(self.dest_lat))
        x = math.cos(math.radians(self.latitude)) * math.sin(math.radians(self.dest_lat)) - \
            math.sin(math.radians(self.latitude)) * math.cos(math.radians(self.dest_lat)) * math.cos(d_lon)
        bearing = math.degrees(math.atan2(y, x))

        # 차이 계산
        angle_diff = bearing - self.heading
        angle_diff_rad = math.radians(angle_diff)

        earth_delta_x = total_distance * math.cos(angle_diff_rad)
        earth_delta_y = total_distance * math.sin(angle_diff_rad)

        # 바디 좌표계로 변환
        body_delta_x = earth_delta_x * math.cos(math.radians(self.heading)) + earth_delta_y * math.sin(math.radians(self.heading))
        body_delta_y = -earth_delta_x * math.sin(math.radians(self.heading)) + earth_delta_y * math.cos(
            math.radians(self.heading))

        return body_delta_x, body_delta_y

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

global_data = {}

w = Window()
w.show()
sys.exit(app.exec())