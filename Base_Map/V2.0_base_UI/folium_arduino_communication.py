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

        ### google ###
        tiles = "http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}"
        # tiles = "http://mt0.google.com/vt/lyrs=y&hl=ko&x={x}&y={y}&z={z}" #hybrid
        # tiles = "http://mt0.google.com/vt/lyrs=t&hl=ko&x={x}&y={y}&z={z}" # terrain only
        # tiles = "http://mt0.google.com/vt/lyrs=s&hl=ko&x={x}&y={y}&z={z}" # staellite only
        attr = "Google"
        # self.m = folium.Map(
        #     location=[37.631104100930436, 127.0779647879758], zoom_start=13, tiles=tiles, attr=attr, max_zoom= 22)

        ### folium ###
        self.m = folium.Map(
            location=[37.631104100930436, 127.0779647879758], zoom_start=13, max_zoom=22)


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
        # self.page = WebEnginePage(self.view)  ### get coords
        # self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

    # def GetPosition(self, latitude, longitude):
    def GetPosition(self, latitude = 37.63124636111111, longitude= 127.07569480555556):
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