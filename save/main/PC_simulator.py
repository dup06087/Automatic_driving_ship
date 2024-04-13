import math, time, threading
import random

from haversine import haversine


def run_simulator(self):
    self.flag_simulation = True

    self.sim_waypoints_list = []
    view = self.waypoints
    model = view.model()

    for row in range(model.rowCount()):
        index = model.index(row, 0)  # 0 is for the first column
        coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
        coordinates_list = coordinates_str.strip('[]').split(', ')

        try:
            longitude = float(coordinates_list[0])
            latitude = float(coordinates_list[1])

        except ValueError:
            self.stop_simulation()
            self.btn_simulation.setText("Simulation START")
            return print("nopp")

        self.sim_waypoints_list.append((longitude, latitude))

    try:
        current_latitude = float(self.sensor_data['latitude'])
        current_longitude = float(self.sensor_data['longitude'])
        lst_dest_longitude = [coord[0] for coord in self.sim_waypoints_list]
        lst_dest_latitude = [coord[1] for coord in self.sim_waypoints_list]

    except:
        self.stop_simulation()
        self.btn_simulation.setText("Simulation START")
        print("destination_latitude 없음")
        return

    current_heading = self.sensor_data['heading'] if self.sensor_data['heading'] != 0 else random.randint(0, 360)
    print(f"current heading value : {current_heading}")
    self.sim_cnt_destination = 0
    prev_sim_cnt_destination = 0
    try:
        while self.flag_simulation:
            if self.sim_cnt_destination >= len(lst_dest_latitude):
                self.stop_simulation()
                self.btn_simulation.setText("Simulation START")
                self.btn_drive.setEnabled(True)
                self.btn_stop_driving.setEnabled(False)

                # self.flag_simulation = False

                return

            destination_latitude = float(lst_dest_latitude[self.sim_cnt_destination])
            destination_longitude = float(lst_dest_longitude[self.sim_cnt_destination])
            print(current_latitude, current_longitude, destination_longitude, destination_latitude)

            self.worker.message = {"mode_pc_command": "SMLT", "dest_latitude": destination_latitude,
                                   "dest_longitude": destination_longitude}

            if current_heading > 180:
                current_heading = current_heading - 360

            # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
            self.simulation_distance_to_target = haversine((current_latitude, current_longitude),
                                                           (destination_latitude, destination_longitude),
                                                           unit='m')
            # self.sensor_data['distance'] = float(self.simulation_distance_to_target)

            # 선박과 목적지가 이루는 선의 자북에 대한 각도 계산
            target_angle = math.degrees(
                math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))

            # 헤딩과 목표 각도 간의 차이 계산
            angle_diff = target_angle - current_heading
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # 각도 차이에 따른 throttle 및 roll 성분 계산
            throttle_component = self.simulation_distance_to_target * math.cos(math.radians(angle_diff))
            roll_component = self.simulation_distance_to_target * math.sin(math.radians(angle_diff))

            # PWM 값 계산
            Kf = 2.5
            # Kd = 0.25 * 800 / (2 * math.pi * 100)
            Kd = 0.318

            Uf = Kf * throttle_component
            Uf = max(1550 - 1500, min(Uf, 1750 - 1500))

            Ud = Kd * roll_component
            max_diff = 800 * 0.125
            Ud = max(-max_diff, min(Ud, max_diff))

            PWM_right = 1500 + Uf - Ud
            PWM_left = 1500 + Uf + Ud

            self.simulation_pwml_auto = int(PWM_left)
            self.simulation_pwmr_auto = int(PWM_right)

            try:
                if self.simulation_pwml_auto == self.simulation_pwmr_auto and self.simulation_pwml_auto != 1500:
                    # Go straight
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading))
                elif self.simulation_pwml_auto < self.simulation_pwmr_auto:
                    # Turn right
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading - heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading - heading_diff))
                    current_heading -= math.degrees(heading_diff)
                elif self.simulation_pwml_auto > self.simulation_pwmr_auto:
                    # Turn left
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading + heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading + heading_diff))
                    current_heading += math.degrees(heading_diff)

                else:
                    print("error")

                self.simulation_head = current_heading
                current_latitude = round(lat_diff + current_latitude, 8)
                current_longitude = round(lng_diff + current_longitude, 8)
                self.simulation_lat = current_latitude
                self.simulation_lon = current_longitude
                # self.current_value['latitude'] = round(lat_diff + self.current_value['latitude'], 8)
                # self.current_value['longitude'] = round(lng_diff + self.current_value['longitude'], 8)

                if self.simulation_distance_to_target < 2:
                    # Stop the boat
                    prev_sim_cnt_destination = self.sim_cnt_destination
                    self.sim_cnt_destination += 1
                    print("Boat has reached the destination!")

                self.flag_simulation_data_init = True
                print(self.sim_cnt_destination)
                time.sleep(0.1)
            except Exception as E:
                print("simulator Error : ", E)
                time.sleep(1)

    except Exception as e:
        self.stop_simulation()
        self.btn_simulation.setText("Simulation START")
        print("simulation error : ", e)
        return

    self.stop_simulation()
    self.btn_simulation.setText("Simulation START")


def pc_simulator(self):
    try:
        float(self.sensor_data['latitude'])
        float(self.sensor_data['longitude'])
        self.sensor_data['dest_latitude']
        self.sensor_data['dest_longitude']
    except:
        return

    if self.simulation_thread is None:
        self.simulation_thread = threading.Thread(target=self.simulation)
        self.simulation_thread.start()
        self.btn_simulation.setText("Simulation STOP")
        self.btn_drive.setEnabled(False)
        self.btn_stop_driving.setEnabled(False)
        self.btn_simulation.setEnabled(True)
    else:
        self.stop_simulation()
        # self.simulation_thread = None
        self.btn_simulation.setText("Simulation START")
        self.btn_drive.setEnabled(True)
        self.btn_stop_driving.setEnabled(False)
        self.btn_simulation.setEnabled(True)


# execute with stop_simulation()
def stop_simulator(self):
    try:
        print("stop received")
        self.flag_simulation = False
        self.simulation_distance_to_target = None
        self.simulation_pwml_auto = None
        self.simulation_pwmr_auto = None

        self.worker.message['mode_pc_command'] = "SELF"
        self.worker.message['dest_latitude'] = None
        self.worker.message['dest_longitude'] = None
        self.simulation_thread = None

    except Exception as e:
        print("stop simulation error : ", e)