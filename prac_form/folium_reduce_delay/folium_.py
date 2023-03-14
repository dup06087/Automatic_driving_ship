import io
import sys

from jinja2 import Template

import folium

from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView

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

class CoordinateProvider(QObject):
    signal = pyqtSignal()

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

        self.__CoordinateProvider = CoordinateProvider()
        self.__CoordinateProvider.signal.connect(self.send_coordinate)

        coordinate = (37.631104100930436, 127.0779647879758)

        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch = 1)

        self.m = folium.Map(
            zoom_start=18, location=coordinate, control_scale=True
        )

        # self.m = folium.Map(
        #     zoom_start=18, location=coordinate, control_scale=True, tiles=None
        # )

        # folium.raster_layers.TileLayer(
        #     tiles="http://mt1.google.com/vt/lyrs=m&h1=p1Z&x={x}&y={y}&z={z}",
        #     name="Standard Roadmap",
        #     attr="Google Map",
        # ).add_to(self.m)
        # folium.raster_layers.TileLayer(
        #     tiles="http://mt1.google.com/vt/lyrs=s&h1=p1Z&x={x}&y={y}&z={z}",
        #     name="Satellite Only",
        #     attr="Google Map",
        # ).add_to(self.m)
        # folium.raster_layers.TileLayer(
        #     tiles="http://mt1.google.com/vt/lyrs=y&h1=p1Z&x={x}&y={y}&z={z}",
        #     name="Hybrid",
        #     attr="Google Map",
        # ).add_to(self.m)
        # folium.LayerControl().add_to(self.m)
        # folium.Marker(coordinate).add_to(self.m)

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
        self.m.save(self.data, close_file=False)

        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

    def send_coordinate(self):
        # generate new coordinate randomly

        latitude = np.random.uniform(37.631104, 37.6311042)
        longitude = np.random.uniform(127.07796, 127.077965)

        # emit coordinate_changed signal
        # self.coordinate_changed.emit(latitude, longitude)

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
        ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        self.view.page().runJavaScript(js)

    def GetPosition(self):
        self.__CoordinateProvider.signal.emit()

def main():
    w = Window()
    w.show()

    # provider = CoordinateProvider()
    # provider.coordinate_changed.connect(w.GetPosition)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()