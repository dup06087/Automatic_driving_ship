import time

from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
import folium, io, sys, json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
import sys
from PyQt5.QtCore import QObject, pyqtSignal,QTimer
import serial
from folium.plugins import MarkerCluster
import numpy as np
from jinja2 import Template

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)

# arduino = serial.Serial('COM3', 9600)

# class CoordinateProvider(QObject):
#     coordinate_changed = pyqtSignal(float, float)
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#     def generate_coordinate(self):
        # # import random
        # #
        # # center_lat, center_lng = 41.8828, 12.4761
        # # x, y = (random.uniform(-0.001, 0.001) for _ in range(2))
        # # latitude = center_lat + x
        # # longitude = center_lng + y
        # # self.coordinate_changed.emit(latitude, longitude)

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

##### Qt widget Layout
class WindowClass(QMainWindow, form_class):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch = 1)

        self.m = folium.Map(
            location=[37.631104100930436, 127.0779647879758], zoom_start=13
        )

        # Marking_Object = CoordinateProvider()
        # Marking_Object.coordinate_changed.connect(self.GetPosition)
        # self.GetPosition.connect(Marking_Object.generate_coordinate)

        folium.raster_layers.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=m&h1=p1Z&x={x}&y={y}&z={z}",
            name="Standard Roadmap",
            attr="Google Map",
        ).add_to(self.m)
        folium.raster_layers.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=s&h1=p1Z&x={x}&y={y}&z={z}",
            name="Satellite Only",
            attr="Google Map",
        ).add_to(self.m)
        folium.raster_layers.TileLayer(
            tiles="http://mt1.google.com/vt/lyrs=y&h1=p1Z&x={x}&y={y}&z={z}",
            name="Hybrid",
            attr="Google Map",
        ).add_to(self.m)

        folium.LayerControl().add_to(self.m)
        folium.Marker((37.631104100930436, 127.0779647879758)).add_to(self.m)

        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': False,
                'polygon': False,
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

        self.data = io.BytesIO()
        # self.car_marker = folium.Marker(location=[37.631104100930436, 127.0779647879758], icon=folium.Icon(color='blue'), icon_size = (100,100))
        # self.car_marker.add_to(self.m)

        self.m.save(self.data, close_file=False)

        # self.view = QtWebEngineWidgets.QWebEngineView()
        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

    # def GetPosition(self, latitude, longitude):
    def GetPosition(self, latitude = 37, longitude= 127):
        js = Template(
            """
        L.marker([{{latitude}}, {{longitude}}] )
            .addTo({{map}});
        L.circleMarker(
            [{{latitude}}, {{longitude}}], {
                "bubblingMouseEvents": true,
                "color": "#3388ff",
                "dashArray": null,
                "dashOffset": null,
                "fill": false,
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
        ).addTo({{map}});
        """
        ).render(map=self.map.get_name(), latitude=latitude, longitude=longitude)
        self.view.page().runJavaScript(js)
        # pass


w = WindowClass()
w.show()


# provider.start()

sys.exit(app.exec_())