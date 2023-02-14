import time

from PyQt5 import uic, QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
import folium, io, sys, json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
import sys
import serial
from folium.plugins import MarkerCluster


form_class = uic.loadUiType("V1_UI.ui")[0]
app = QtWidgets.QApplication(sys.argv)

# arduino = serial.Serial('COM3', 9600)

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
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setContentsMargins(50, 50, 50, 50)

        self.Folium.addWidget(self.view, stretch = 1)

        m = folium.Map(
            location=[37, 128], zoom_start=13
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
        m.add_child(draw)

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
        ).add_to(m)

        data = io.BytesIO()

        m.save(data, close_file=False)

        # self.view = QtWebEngineWidgets.QWebEngineView()
        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(data.getvalue().decode())


w = WindowClass()
w.show()
sys.exit(app.exec_())