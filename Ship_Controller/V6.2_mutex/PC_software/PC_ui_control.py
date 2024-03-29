from jinja2 import Template
from PyQt5.QtGui import QStandardItemModel
import math

def draw_obstacle(self):
    pass

def exe_init_values(self):
    self.thread = None
    self.model = QStandardItemModel(self)
    self.points_init = False
    self.on_record = True
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

    self.simulation_distance_to_target = None

    self.btn_stop_driving.setEnabled(False)

def get_destinations_from_gui(self):
    ## 자율 운항 중인지 확인은 >> mode_pc_command == "AUTO" 일 때
    self.waypoints_list = []
    view = self.waypoints  # self.waypoints widget 이름
    model = view.model()
    try:
        for row in range(model.rowCount()):
            index = model.index(row, 0)  # 0 is for the first column
            coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
            coordinates_list = coordinates_str.strip('[]').split(', ')
            try:
                longitude = float(coordinates_list[0])
                latitude = float(coordinates_list[1])
            except ValueError:
                break
            self.waypoints_list.append((longitude, latitude))

    except:
        return print("목적지가 없습니다.")

    self.lst_dest_longitude = [coord[0] for coord in self.waypoints_list]
    self.lst_dest_latitude = [coord[1] for coord in self.waypoints_list]

def exe_route_generate(self):
    # 이전 위치에서 일정 거리만큼 북동쪽 방향으로 이동

    if self.flag_simulation:
        try:
            latitude = self.simulation_lat
            longitude = self.simulation_lon
        except:
            self.btn_pointing.setText("Pointing START")
            print("목적지를 수신받지 않았습니다.")
            return
    else:
        try:
            latitude = self.sensor_data['latitude']
            longitude = self.sensor_data['longitude']
        except:
            return print("Nooop")
    js = Template(
        """
        if ({{on_record}}) {
            var point = L.circleMarker(
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
            );
            pointsArray.push(point);
            point.addTo({{map}});
        }
        """
    ).render(map=self.m.get_name(), latitude=latitude, longitude=longitude, on_record=str(self.on_record).lower())
    # Leaflet이 초기화될 때 pointsArray를 생성해야 합니다.
    init_js = Template("var pointsArray = [];").render()
    if self.points_init == False:
        self.view.page().runJavaScript(init_js)
        self.points_init = True
    self.view.page().runJavaScript(js)

def exe_get_selected_coordinates(self):
    view = self.waypoints
    model = view.model()
    index = view.currentIndex()

    if not index.isValid():
        return None

    coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
    coordinates_list = coordinates_str.strip('[]').split(', ')

    try:
        longitude = float(coordinates_list[0])
        latitude = float(coordinates_list[1])

    except ValueError:
        return None

    return longitude, latitude

def exe_show_sensor_data(self):
    try:
        for key, value in self.sensor_data.items():
            try:
                edit_name = 'edit_' + key

                if key == "mode_chk":
                    if value == 1000:
                        if hasattr(self, edit_name):
                            edit_widget = getattr(self, edit_name)

                            if value is not None:
                                edit_widget.setText("SELF")
                                # edit_widget.setText(str(1))
                            else:
                                edit_widget.setText("")

                    elif value == 2000:
                        if hasattr(self, edit_name):
                            edit_widget = getattr(self, edit_name)

                            if value is not None:
                                edit_widget.setText("AUTO")
                                # edit_widget.setText(str(1))
                            else:
                                edit_widget.setText("")

                elif hasattr(self, edit_name):
                    edit_widget = getattr(self, edit_name)

                    if value is not None:
                        edit_widget.setText(str(value))
                        # edit_widget.setText(str(1))
                    else:
                        edit_widget.setText("")

            except:
                print("not showing data : ", key)

        # setting pc variable
        try:
            self.edit_IP.setText(str(self.worker.server_ip))
            self.edit_jetson_socket_status.setText(str(self.worker.jetson_socket_status))
        except Exception as e:
            print("why??? : ", e)

        try:
            if self.simulation_distance_to_target is not None:
                self.edit_distance_simulation.setText(str(self.simulation_distance_to_target))
                self.edit_pwml_sim.setText(str(self.simulation_pwml_auto))
                self.edit_pwmr_sim.setText(str(self.simulation_pwmr_auto))
            else:
                self.edit_distance_simulation.setText("")

        except Exception as e:
            print(e)
            pass

        lst_dest_longitude = [coord[0] for coord in self.waypoints_list]
        lst_dest_latitude = [coord[1] for coord in self.waypoints_list]

        try:
            self.edit_current_mode.setText(str(self.sensor_data['mode_chk']))
        except Exception as e:
            pass
            # print("show sensordata", e)
    except:
        pass

def exe_move_item_up(instance):
    try:
        # Get the current index
        index = instance.waypoints.currentIndex()

        # Check if the current index is not the first index
        if index.row() > 0:
            # Get the item to move
            item = instance.model.takeRow(index.row())

            # Move the item to the new index
            instance.model.insertRow(index.row() - 1, item)

            # Set the current index to the new index
            instance.waypoints.setCurrentIndex(instance.model.indexFromItem(item[0]))
    except:
        pass
def exe_move_item_down(instance):
    try:
        # Get the current index
        index = instance.waypoints.currentIndex()

        # Check if the current index is not the last index
        if index.row() < instance.model.rowCount() - 1:
            # Get the item to move
            item = instance.model.takeRow(index.row())

            # Move the item to the new index
            instance.model.insertRow(index.row() + 1, item)

            # Set the current index to the new index
            instance.waypoints.setCurrentIndex(instance.model.indexFromItem(item[0]))
    except:
        pass

def exe_delete_item(instance):
    # Get the current index
    index = instance.waypoints.currentIndex()

    # Remove the item from the model
    instance.model.removeRow(index.row())

def exe_pointing(instance): ## 경로 지우는 용도로 써야겠다
    if instance.on_record == False:
        instance.on_record = True
        instance.btn_pointing.setText("Pointing STOP")
        return
    elif instance.on_record == True:
        instance.btn_pointing.setText("Pointing START")

    instance.on_record = False
    js = """
            for (var i = 0; i < pointsArray.length; i++) {
                {{map}}.removeLayer(pointsArray[i]);
            }
            pointsArray = [];
        """
    instance.view.page().runJavaScript(Template(js).render(map=instance.m.get_name()))


def calculate_triangle_vertices(lat, lon, heading, ship_size):
    # 위도(lat), 경도(lon)를 radian 단위로 변환
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    # 방위각(heading)를 radian 단위로 변환
    heading_rad = math.radians(heading)

    # 선박의 길이를 이등변삼각형 높이로 설정
    height = ship_size / 2

    # 이등변삼각형의 내심 좌표 계산
    center_lat = math.degrees(lat_rad - height * math.cos(heading_rad))
    center_lon = math.degrees(lon_rad + height * math.sin(heading_rad) / math.cos(lat_rad))

    # 각 꼭지점의 방위각 계산
    angles = [heading_rad, heading_rad + math.radians(150), heading_rad - math.radians(150)]

    # 꼭지점 좌표를 저장할 리스트 초기화
    vertices = []

    # 각 꼭지점의 좌표 계산
    for angle in angles:
        # 위도와 경도의 차이값 계산
        dlat = math.cos(angle) * height / 6371
        dlon = math.sin(angle) * height / (6371 * math.cos(lat_rad))

        # 위도와 경도의 차이값을 더해 새로운 좌표를 계산
        new_lat = lat + math.degrees(dlat)
        new_lon = lon + math.degrees(dlon)

        # 꼭지점 좌표를 리스트에 추가
        vertices.append((new_lat, new_lon))  ##

    # 꼭지점 좌표를 리스트 형태로 반환
    return vertices

def exe_draw_ship(instance):
    if not instance.flag_simulation:
        try:
            lat = float(instance.sensor_data['latitude'])
            lon = float(instance.sensor_data['longitude'])
            head = float(instance.sensor_data['heading']) if instance.sensor_data['heading'] != None else 0
        except:
            return print("here")
    else:
        lat = instance.simulation_lat
        lon = instance.simulation_lon
        head = instance.simulation_head

    ship_size = 0.0105 ## km단위

    triangle1, triangle2, triangle3 = calculate_triangle_vertices(lat, lon, head, ship_size)
    latitude1, longitude1 = triangle1
    latitude2, longitude2 = triangle2
    latitude3, longitude3 = triangle3
    instance.view.page().runJavaScript(Template("{{map}}.removeLayer(polygon)").render(map = instance.m.get_name()))

    js = Template(
        """
        var polygon = L.polygon([
            [{{latitude}}, {{longitude}}],
            [{{latitude2}}, {{longitude2}}],
            [{{latitude3}}, {{longitude3}}]
        ],
        {
            "color": "#000000",
            "weight": 3,
            "opacity": 1,
            "fillColor": "#ff0000",
            "fillOpacity": 1,
            "zIndex": 1000
        }
        ).addTo({{map}});
        """
    ).render(map=instance.m.get_name(), latitude=latitude1, longitude=longitude1,
             latitude2=latitude2, longitude2=longitude2,
             latitude3=latitude3, longitude3=longitude3)

    instance.view.page().runJavaScript(js)