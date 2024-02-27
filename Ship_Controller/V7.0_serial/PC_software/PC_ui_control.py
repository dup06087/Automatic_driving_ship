import time

from jinja2 import Template
from PyQt5.QtGui import QStandardItemModel
import math
import time
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

    self.sim = None

    self.prev_dest_latitude = None
    self.prev_dest_longitude = None
    self.prev_cnt_destination = 0

    self.last_sent_command = None
    self.prev_sensor_data_arrived = False

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
        print("목적지가 없습니다.")
        return False

    self.lst_dest_longitude = [coord[0] for coord in self.waypoints_list]
    self.lst_dest_latitude = [coord[1] for coord in self.waypoints_list]

    return True

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

def exe_draw_waypoint(self):
    try:
        print("try drawing")
        if self.sensor_data['waypoint_latitude'] is not None:
            js = Template(
                """
                if (true) {
            if (!window.waypoint) {
                // 웨이포인트 객체가 존재하지 않으면 생성
                window.waypoint = L.circleMarker(
                    [{{latitude}}, {{longitude}}], {
                        "color": "red",
                        "fillColor": "red",
                        "fillOpacity": 0.5,
                        "radius": 2,
                        "stroke": true,
                        "weight": 5
                    }
                );
                window.waypoint.addTo({{map}});
            }
            else {
                // 웨이포인트 객체가 이미 존재하면 위치 업데이트
                window.waypoint.setLatLng([{{latitude}}, {{longitude}}]);
            }
        }
                """
            ).render(map=self.m.get_name(), latitude=self.sensor_data['waypoint_latitude'], longitude=self.sensor_data['waypoint_longitude'])
            self.view.page().runJavaScript(js)
            print("done")
            # self.view.page().runJavaScript(js)
    except Exception as e:
        print("waypoint error : ", e)



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
                            edit_widget.setText("SELF")

                    elif value == 2000:
                        if hasattr(self, edit_name):
                            edit_widget = getattr(self, edit_name)
                            edit_widget.setText("AUTO")

                    elif value == 0:
                        if hasattr(self, edit_name):
                            edit_widget = getattr(self, edit_name)
                            edit_widget.setText("binding")

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
            self.edit_IP.setText(str(self.worker.jetson_ip))
            self.edit_jetson_socket_status.setText(str(all(self.worker.socket_statuses.values())))
        except Exception as e:
            pass

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
    # 지구 반경 (미터 단위)
    earth_radius = 6371000

    # 위도(lat), 경도(lon)를 radian 단위로 변환
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    # 방위각(heading)를 radian 단위로 변환
    heading_rad = math.radians(heading)

    # 선박의 길이를 라디안 단위로 변환
    height_radian = (ship_size / 2) / earth_radius

    # 이등변삼각형의 내심 좌표 계산
    center_lat_rad = lat_rad
    center_lon_rad = lon_rad
    # center_lat_rad = lat_rad - height_radian * math.cos(heading_rad)
    # center_lon_rad = lon_rad + height_radian * math.sin(heading_rad) / math.cos(lat_rad)

    # 각 꼭지점의 방위각 계산
    angles = [heading_rad, heading_rad + math.radians(150), heading_rad - math.radians(150)]

    # 꼭지점 좌표를 저장할 리스트 초기화
    vertices = []

    # 각 꼭지점의 좌표 계산
    for angle in angles:
        # 위도와 경도의 차이값 계산
        dlat_rad = math.cos(angle) * height_radian
        dlon_rad = math.sin(angle) * height_radian / math.cos(lat_rad)

        # 위도와 경도의 차이값을 더해 새로운 좌표를 계산 (라디안 단위로)
        new_lat_rad = center_lat_rad + dlat_rad
        new_lon_rad = center_lon_rad + dlon_rad

        # 꼭지점 좌표를 리스트에 추가 (도 단위로 변환)
        vertices.append((math.degrees(new_lat_rad), math.degrees(new_lon_rad)))

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

    ship_size = 1.05  ## m단위

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


def update_current_marker(self):
    # 이전 마커를 제거합니다. window 객체에 마커를 저장하여 전역적으로 접근할 수 있게 합니다.

    # 새 위치 데이터가 있을 경우에만 마커를 업데이트합니다.
    if self.sensor_data["dest_latitude"] != self.prev_dest_latitude or self.sensor_data["dest_longitude"] != self.prev_dest_longitude or self.sensor_data["cnt_destination"] != self.prev_cnt_destination:
        self.prev_dest_latitude = self.sensor_data["dest_latitude"]
        self.prev_dest_longitude = self.sensor_data["dest_longitude"]
        self.prev_cnt_destination = self.sensor_data["cnt_destination"]

        self.view.page().runJavaScript("""
            if (window.currentMarker) {
                window.currentMarker.remove();
                window.currentMarker = null;
            }
        """)

        # 새 마커를 추가합니다.
        js_add_marker = Template("""
            var redMarker = L.AwesomeMarkers.icon({
                markerColor: 'red',
                icon: 'coffee' // 사용하고자 하는 Font Awesome 아이콘 이름
            });

            // 마커 객체를 생성하고 지도에 추가합니다.
            window.currentMarker = L.marker([{{current_lat}}, {{current_lon}}], {icon: redMarker}).addTo({{map}});
        """).render(
            map=self.m.get_name(),
            current_lat=self.sensor_data["dest_latitude"][self.sensor_data["cnt_destination"]],
            current_lon=self.sensor_data["dest_longitude"][self.sensor_data["cnt_destination"]]
        )
        self.view.page().runJavaScript(js_add_marker)