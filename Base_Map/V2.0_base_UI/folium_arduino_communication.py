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

        self.m = folium.Map(
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



        # folium.Circle([37 + (52.8163/60), 127 + (32.26924/60)],
        #               radius=100,
        #               color='blue'
        #               ).add_to(m)

        self.data = io.BytesIO()

        self.m.save(self.data, close_file=False)

        # self.view = QtWebEngineWidgets.QWebEngineView()
        self.page = WebEnginePage(self.view)  ### get coords
        self.view.setPage(self.page)  ### get coords
        self.view.setHtml(self.data.getvalue().decode())

    def GetPosition(self):

        self.m = folium.Map(
            location=[37.6313, 127.0759], zoom_start=13, tiles='Stamen TonerBackground',
            attr="toner-bcg")


        folium.TileLayer('Stamen Terrain').add_to(self.m)
        folium.TileLayer('Stamen Toner').add_to(self.m)
        folium.TileLayer('Stamen Water Color').add_to(self.m)
        folium.TileLayer('cartodbpositron').add_to(self.m)
        folium.TileLayer('cartodbdark_matter').add_to(self.m)
        folium.LayerControl().add_to(self.m)

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

        folium.Circle([37.6313, 127.0759],
                      radius=100,
                      color='blue'
                      ).add_to(self.m)

        self.data = io.BytesIO()

        self.m.save(self.data, close_file=False)

        self.view.setHtml(self.data.getvalue().decode())


w = WindowClass()
w.show()
sys.exit(app.exec_())