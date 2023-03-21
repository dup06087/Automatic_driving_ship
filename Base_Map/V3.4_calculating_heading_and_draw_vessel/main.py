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

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)
img = Image.open('image.png')

class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def javaScriptAlert(self, securityOrigin: QtCore.QUrl, msg: str):
        f = open('stdout.txt', 'w')
        sys.stdout = f
        coords_dict = json.loads(msg)
        coords = coords_dict['geometry']['coordinates']
        print(coords)
        sys.stdout = sys.__stdout__
        f.close()
        print(coords)

class Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.points_init = False
        self.on_record = True
        coordinate = (37.631104100930436, 127.0779647879758)

        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch = 1)

        self.m = folium.Map(
            zoom_start=5, location=coordinate, control_scale=True
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

        '''rotate'''
        # b = io.BytesIO()
        # img.rotate(45).save(b, format='PNG')
        # b64 = base64.b64encode(b.getvalue())
        #
        # folium.raster_layers.ImageOverlay(
        #     image=f'data:image/png;base64,{ b64.decode("utf-8") }',
        #     bounds=[[37.631104100930436, 127.0779647879758], [37.63804100930436, 127.0900647879758]],
        #     opacity=1,
        #     interactive=False,
        #     cross_origin=False,
        #     zindex=1,
        # ).add_to(self.m)

        '''not rotate'''
        # folium.raster_layers.ImageOverlay(
        #     image='./image.png',
        #     bounds=[[37.631104100930436, 127.0779647879758], [37.63804100930436, 127.0900647879758]],
        #     opacity=1,
        #     interactive=True,
        #     cross_origin=False,
        #     zindex=1,
        # ).add_to(self.m)


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
        latitude = np.random.uniform(37.631104, 38.6311042)
        longitude = np.random.uniform(127.07796, 128.077965)

        # js = Template(
        # #     """ 마커
        # # L.marker([{{latitude}}, {{longitude}}] )
        # #     .addTo({{map}});
        # # L.circleMarker(
        # #     [{{latitude}}, {{longitude}}], {
        # #         "bubblingMouseEvents": true,
        # #         "color": "#3388ff",
        # #         "dashArray": null,
        # #         "dashOffset": null,
        # #         "fill": false,
        # #         "fillColor": "#3388ff",
        # #         "fillOpacity": 0.2,
        # #         "fillRule": "evenodd",
        # #         "lineCap": "round",
        # #         "lineJoin": "round",
        # #         "opacity": 1.0,
        # #         "radius": 2,
        # #         "stroke": true,
        # #         "weight": 5
        # #     }
        # # ).addTo({{map}});
        # # """
        # #     """
        # #     var pointsArray = [];
        # #     pointsArray = L.circleMarker(
        # #         [{{latitude}}, {{longitude}}], {
        # #             "bubblingMouseEvents": true,
        # #             "color": "#3388ff",
        # #             "dashArray": null,
        # #             "dashOffset": null,
        # #             "fill": true,
        # #             "fillColor": "#3388ff",
        # #             "fillOpacity": 0.2,
        # #             "fillRule": "evenodd",
        # #             "lineCap": "round",
        # #             "lineJoin": "round",
        # #             "opacity": 1.0,
        # #             "radius": 2,
        # #             "stroke": true,
        # #             "weight": 5
        # #         }
        # #     ).addTo({{map}});
        # #     """
        # # ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        # # self.view.page().runJavaScript(js)
        # # self.cnt += 1
        #
        #     """
        #         point = L.circleMarker(
        #             [{{latitude}}, {{longitude}}], {
        #                 "bubblingMouseEvents": true,
        #                 "color": "#3388ff",
        #                 "dashArray": null,
        #                 "dashOffset": null,
        #                 "fill": true,
        #                 "fillColor": "#3388ff",
        #                 "fillOpacity": 0.2,
        #                 "fillRule": "evenodd",
        #                 "lineCap": "round",
        #                 "lineJoin": "round",
        #                 "opacity": 1.0,
        #                 "radius": 2,
        #                 "stroke": true,
        #                 "weight": 5
        #             }
        #         )
        #         point.addTo({{map}});
        #         pointsArray.push(point);
        #
        #
        #         if (pointsArray.length >= 5) {
        #             for (var i = 0; i < pointsArray.length; i++) {
        #                 {{map}}.removeLayer(pointsArray[i]);
        #             }
        #         pointsArray = [];
        #         }
        #     """
        # ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        # self.view.page().runJavaScript(js)

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

        '''js erase code'''
        # '''if (pointsArray.length >= 5) {
        # for (var i = 0; i < pointsArray.length; i++) {
        # {{map}}.removeLayer(pointsArray[i]);
        # }
        # pointsArray =[];
        # } else {
        # point.addTo({{map}});
        # }'''

        # def route_generate(self):
        #     latitude = np.random.uniform(37.631104, 38.6311042)
        #     longitude = np.random.uniform(127.07796, 128.077965)
        #
        #     # js = Template(
        #     # #     """ 마커
        #     # # L.marker([{{latitude}}, {{longitude}}] )
        #     # #     .addTo({{map}});
        #     # # L.circleMarker(
        #     # #     [{{latitude}}, {{longitude}}], {
        #     # #         "bubblingMouseEvents": true,
        #     # #         "color": "#3388ff",
        #     # #         "dashArray": null,
        #     # #         "dashOffset": null,
        #     # #         "fill": false,
        #     # #         "fillColor": "#3388ff",
        #     # #         "fillOpacity": 0.2,
        #     # #         "fillRule": "evenodd",
        #     # #         "lineCap": "round",
        #     # #         "lineJoin": "round",
        #     # #         "opacity": 1.0,
        #     # #         "radius": 2,
        #     # #         "stroke": true,
        #     # #         "weight": 5
        #     # #     }
        #     # # ).addTo({{map}});
        #     # # """
        #     # #     """
        #     # #     var pointsArray = [];
        #     # #     pointsArray = L.circleMarker(
        #     # #         [{{latitude}}, {{longitude}}], {
        #     # #             "bubblingMouseEvents": true,
        #     # #             "color": "#3388ff",
        #     # #             "dashArray": null,
        #     # #             "dashOffset": null,
        #     # #             "fill": true,
        #     # #             "fillColor": "#3388ff",
        #     # #             "fillOpacity": 0.2,
        #     # #             "fillRule": "evenodd",
        #     # #             "lineCap": "round",
        #     # #             "lineJoin": "round",
        #     # #             "opacity": 1.0,
        #     # #             "radius": 2,
        #     # #             "stroke": true,
        #     # #             "weight": 5
        #     # #         }
        #     # #     ).addTo({{map}});
        #     # #     """
        #     # # ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        #     # # self.view.page().runJavaScript(js)
        #     # # self.cnt += 1
        #     #
        #     #     """
        #     #         point = L.circleMarker(
        #     #             [{{latitude}}, {{longitude}}], {
        #     #                 "bubblingMouseEvents": true,
        #     #                 "color": "#3388ff",
        #     #                 "dashArray": null,
        #     #                 "dashOffset": null,
        #     #                 "fill": true,
        #     #                 "fillColor": "#3388ff",
        #     #                 "fillOpacity": 0.2,
        #     #                 "fillRule": "evenodd",
        #     #                 "lineCap": "round",
        #     #                 "lineJoin": "round",
        #     #                 "opacity": 1.0,
        #     #                 "radius": 2,
        #     #                 "stroke": true,
        #     #                 "weight": 5
        #     #             }
        #     #         )
        #     #         point.addTo({{map}});
        #     #         pointsArray.push(point);
        #     #
        #     #
        #     #         if (pointsArray.length >= 5) {
        #     #             for (var i = 0; i < pointsArray.length; i++) {
        #     #                 {{map}}.removeLayer(pointsArray[i]);
        #     #             }
        #     #         pointsArray = [];
        #     #         }
        #     #     """
        #     # ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        #     # self.view.page().runJavaScript(js)
        #
        #     js = Template(
        #         """
        #         var point = L.circleMarker(
        #             [{{latitude}}, {{longitude}}], {
        #                 "bubblingMouseEvents": true,
        #                 "color": "#3388ff",
        #                 "dashArray": null,
        #                 "dashOffset": null,
        #                 "fill": true,
        #                 "fillColor": "#3388ff",
        #                 "fillOpacity": 0.2,
        #                 "fillRule": "evenodd",
        #                 "lineCap": "round",
        #                 "lineJoin": "round",
        #                 "opacity": 1.0,
        #                 "radius": 2,
        #                 "stroke": true,
        #                 "weight": 5
        #             }
        #         );
        #         pointsArray.push(point);
        #
        #         if (pointsArray.length >= 5) {
        #             for (var i = 0; i < pointsArray.length; i++) {
        #                 {{map}}.removeLayer(pointsArray[i]);
        #             }
        #             pointsArray = [];
        #         } else {
        #             point.addTo({{map}});
        #         }
        #         """
        #     ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        #
        #     # Leaflet이 초기화될 때 pointsArray를 생성해야 합니다.
        #     init_js = Template("var pointsArray = [];").render()
        #     if self.points_init == False:
        #         self.view.page().runJavaScript(init_js)
        #         self.points_init = True
        #     self.view.page().runJavaScript(js)

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
        print("in")
        triangle1, triangle2, triangle3 = self.calculate_triangle_vertices(37.5665 + random.uniform(-0.0001, 0.0001), 126.9780 + random.uniform(-0.0001, 0.0001), 30 + random.uniform(-20, 20), 0.01)
        print("out")
        latitude1, longitude1 = triangle1
        latitude2, longitude2 = triangle2
        latitude3, longitude3 = triangle3
        print(triangle1, triangle2, triangle3)
        self.view.page().runJavaScript(Template("{{map}}.removeLayer(polygon)").render(map = self.m.get_name()))

        # latitude = np.random.uniform(37.631104, 38.6311042)
        # longitude = np.random.uniform(127.07796, 128.077965)

        js = Template(
            """
            var polygon = L.polygon([
                [{{latitude}}, {{longitude}}],
                [{{latitude2}}, {{longitude2}}],
                [{{latitude3}}, {{longitude3}}]
            ]).addTo({{map}});
            """
        ).render(map=self.m.get_name(), latitude=latitude1, longitude=longitude1,
                 latitude2=latitude2, longitude2=longitude2,
                 latitude3=latitude3, longitude3=longitude3)

        self.view.page().runJavaScript(js)

        print("hi")

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


def main():
    w = Window()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()