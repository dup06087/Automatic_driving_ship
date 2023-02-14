import time

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
import folium, io, sys, json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
import sys
import serial

arduino = serial.Serial('COM3', 9600)
app = QtWidgets.QApplication(sys.argv)

#####folium
m = folium.Map(location=[37,128], zoom_start=13)

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

view = QtWebEngineWidgets.QWebEngineView()
page = WebEnginePage(view) ### get coords
view.setPage(page) ### get coords
view.setHtml(data.getvalue().decode()) # set bytesIO to html for visualzing

##### folium end

##### Qt widget Layout
class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()

        layout = QVBoxLayout()
        self.folium_output = view

        # self.folium_output(view.show())
        # self.folium_output.show(view.show())
        layout.addWidget(self.folium_output)

        self.btn1 = QPushButton("Send")
        self.btn1.clicked.connect(self.SendData)
        layout.addWidget(self.btn1)

        self.btn_stop = QPushButton("AddWidgets")
        # self.btn_stop.clicked.connect()
        layout.addWidget(self.btn_stop)

        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

    def SendData(self):
        pass

w = WindowClass()
w.show()

sys.exit(app.exec_())