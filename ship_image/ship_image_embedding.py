import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSlider, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set up main window
        self.setWindowTitle("Ship Image")
        self.setGeometry(100, 100, 800, 600)

        # Set up central widget
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        # Set up layout
        layout = QVBoxLayout(centralWidget)

        # Set up label for roll slider
        rollLabel = QLabel("Roll")
        layout.addWidget(rollLabel)

        # Set up roll slider
        self.rollSlider = QSlider(Qt.Horizontal)
        self.rollSlider.setRange(-90, 90)
        self.rollSlider.setTickInterval(10)
        self.rollSlider.setTickPosition(QSlider.TicksBelow)
        self.rollSlider.valueChanged.connect(self.updateShip)
        layout.addWidget(self.rollSlider)

        # Set up label for pitch slider
        pitchLabel = QLabel("Pitch")
        layout.addWidget(pitchLabel)

        # Set up pitch slider
        self.pitchSlider = QSlider(Qt.Horizontal)
        self.pitchSlider.setRange(-90, 90)
        self.pitchSlider.setTickInterval(10)
        self.pitchSlider.setTickPosition(QSlider.TicksBelow)
        self.pitchSlider.valueChanged.connect(self.updateShip)
        layout.addWidget(self.pitchSlider)

        # Set up label for yaw slider
        yawLabel = QLabel("Yaw")
        layout.addWidget(yawLabel)

        # Set up yaw slider
        self.yawSlider = QSlider(Qt.Horizontal)
        self.yawSlider.setRange(-180, 180)
        self.yawSlider.setTickInterval(10)
        self.yawSlider.setTickPosition(QSlider.TicksBelow)
        self.yawSlider.valueChanged.connect(self.updateShip)
        layout.addWidget(self.yawSlider)

        # Define initial ship dimensions
        self.length = 20
        self.width = 5
        self.height = 10

        # Define initial ship vertices
        self.vertices = np.array([
            [-self.length/2, -self.width/2, -self.height/2],
            [self.length/2, -self.width/2, -self.height/2],
            [self.length/2, self.width/2, -self.height/2],
            [-self.length/2, self.width/2, -self.height/2],
            [-self.length/2, -self.width/2, self.height/2],
            [self.length/2, -self.width/2, self.height/2],
            [self.length/2, self.width/2, self.height/2],
            [-self.length/2, self.width/2, self.height/2]
        ])

        # Define initial ship faces
        self.faces = np.array([
            [0,1,2],
            [0,2,3],
            [1,5,6],
            [1,6,2],
            [5,4,7],
            [5,7,6],
            [4,0,3],
            [4,3,7],
            [3,2,6],
            [3,6,7],
            [4,5,1],

            [4, 1, 0]
        ])

        # Define figure and axes
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')

        # Plot initial ship image
        self.ship = self.ax.plot_trisurf(self.vertices[:, 0], self.vertices[:, 1], self.faces, self.vertices[:, 2],
                                         cmap=plt.cm.Spectral)

        # Update ship image with initial angles
        self.updateShip()

        # Add figure canvas to layout
        canvas = self.fig.canvas
        layout.addWidget(canvas)

        # Show main window
        self.show()

    def updateShip(self):
        # Get roll, pitch, and yaw angles from sliders
        roll = np.radians(self.rollSlider.value())
        pitch = np.radians(self.pitchSlider.value())
        yaw = np.radians(self.yawSlider.value())

        # Define rotation matrix
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                       [np.sin(yaw), np.cos(yaw), 0],
                       [0, 0, 1]])
        Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                       [0, 1, 0],
                       [-np.sin(pitch), 0, np.cos(pitch)]])
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(roll), -np.sin(roll)],
                       [0, np.sin(roll), np.cos(roll)]])
        R = Rz.dot(Ry.dot(Rx))

        # Rotate ship vertices
        vertices = self.vertices.dot(R)

        # Update ship image with rotated vertices
        self.ship._segments3d = np.array([vertices[face] for face in self.faces])

        # Redraw ship image
        self.fig.canvas.draw()

if __name__ == 'main':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.updateShip()
    sys.exit(app.exec_())