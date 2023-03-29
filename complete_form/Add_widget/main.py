from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets # pip install pyqtwebengine
from folium.plugins import Draw, MousePosition
import folium, io, sys, json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMainWindow, QLabel
from PyQt5 import uic

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
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

    data = io.BytesIO() ### data.getvalue().decode()는 html문서
    print("data : ", data)

    m.save(data, close_file=False)
    print(m)
    print("data2 = ", data)
    print(data.getvalue().decode())
    class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
        def javaScriptAlert(self, securityOrigin: QtCore.QUrl, msg: str):
            coords_dict = json.loads(msg)
            coords = coords_dict['geometry']['coordinates']
            print(coords)
            w.folium_output.grab().save("hi.PNG")

view = QtWebEngineWidgets.QWebEngineView()
page = WebEnginePage(view)
print("Page : ", page)
view.setPage(page) ### get coords
view.setHtml(data.getvalue().decode()) # set bytesIO to html for visualzing

# form_class = uic.loadUiType("folium_in_Qt.ui")[0]
class WindowClass(QMainWindow) :
    def __init__(self) :
        super().__init__()
        # self.setupUi(self)

        layout = QVBoxLayout()

        self.folium_output = view

        # self.folium_output(view.show())
        # self.folium_output.show(view.show())
        layout.addWidget(self.folium_output)

        # self.btn1 = QPushButton("PLAY")
        # self.btn1.clicked.connect(self.SendData)
        # layout.addWidget(self.btn1)

        # self.btn_stop = QPushButton("STOP")
        # self.btn_stop.clicked.connect(self.stopVideo)
        # layout.addWidget(self.btn_stop)

        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

    # def SendData(self):
    #     pass
        ### serial 통신

w = WindowClass()
w.show()
sys.exit(app.exec_())