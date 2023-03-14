import base64

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

form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)

img = Image.open('image.png')
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

        b = io.BytesIO()
        img.rotate(45).save(b, format='PNG')
        b64 = base64.b64encode(b.getvalue())

        folium.raster_layers.ImageOverlay(
            image=f'data:image/png;base64,{ b64.decode("utf-8") }',
            bounds=[[37.631104100930436, 127.0779647879758], [37.63804100930436, 127.0900647879758]],
            opacity=1,
            interactive=False,
            cross_origin=False,
            zindex=1,
        ).add_to(self.m)

        # folium.raster_layers.ImageOverlay(
        #     image='./image.png',
        #     bounds=[[37.631104100930436, 127.0779647879758], [37.63804100930436, 127.0900647879758]],
        #     opacity=1,
        #     interactive=True,
        #     cross_origin=False,
        #     zindex=1,
        # ).add_to(self.m)

        self.marker = None

        self.data = io.BytesIO()
        self.m.save(self.data, close_file=False)

        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(5000)  # 5 seconds

    def send_coordinate(self):
        # generate new coordinate randomly

        latitude = np.random.uniform(37.631104, 37.6311042)
        longitude = np.random.uniform(127.07796, 127.077965)

        js = Template(
        #     """ 마커
        # L.marker([{{latitude}}, {{longitude}}] )
        #     .addTo({{map}});
        # L.circleMarker(
        #     [{{latitude}}, {{longitude}}], {
        #         "bubblingMouseEvents": true,
        #         "color": "#3388ff",
        #         "dashArray": null,
        #         "dashOffset": null,
        #         "fill": false,
        #         "fillColor": "#3388ff",
        #         "fillOpacity": 0.2,
        #         "fillRule": "evenodd",
        #         "lineCap": "round",
        #         "lineJoin": "round",
        #         "opacity": 1.0,
        #         "radius": 2,
        #         "stroke": true,
        #         "weight": 5
        #     }
        # ).addTo({{map}});
        # """
            """
            L.circleMarker(
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
            ).addTo({{map}});
            """
        ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude)
        self.view.page().runJavaScript(js)

    def GetPosition(self):
        self.__CoordinateProvider.signal.emit()

    def update_image(self):
        print("hi")
        bounds = [[37.631104100930436, 127.0779647879758], [38.804100930436, 128.900647879758]]

        image_overlay_js = Template("""
            var bounds = {bounds};
            var imageUrl = './image.png';
            var imageBounds = L.latLngBounds(bounds);
            L.imageOverlay(imageUrl, imageBounds, {
                opacity: 1,
                interactive: true,
                crossOrigin: false,
                zIndex: 1
            }).addTo(map);
        """).render(bounds = bounds, map = self.m.get_name())
        self.view.page().runJavaScript(image_overlay_js)

def main():
    w = Window()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()