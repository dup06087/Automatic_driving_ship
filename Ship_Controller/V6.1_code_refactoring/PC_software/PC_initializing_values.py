from PyQt5.QtGui import QStandardItemModel

def initialize_variables(self):
    self.thread = None
    self.model = QStandardItemModel(self)
    self.points_init = False
    self.on_record = True
    self.is_auto_driving = False
    self.cnt_destination = 0
    self.prev_destination = None

    self.flag_simulation = False
    self.simulation_thread = None
    self.simulation_pwml_auto = None
    self.simulation_pwmr_auto = None
    self.flag_simulation_data_init = False

    # 여기는 draw_ship 초기 변수 >> 지우면 안 됨
    self.simulation_lat = 37.63124688
    self.simulation_lon = 127.07633361
    self.simulation_head = 0

