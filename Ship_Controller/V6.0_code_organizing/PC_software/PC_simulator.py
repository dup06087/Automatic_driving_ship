import math, time, threading
from haversine import haversine, Unit


def run_simulator(instance):
    instance.flag_simulation = True
    
    instance.worker.message = {"mode_jetson": "SMLT", "dest_latitude": 2, "dest_longitude": 1}
    
    instance.sim_waypoints_list = []
    view = instance.waypoints
    model = view.model()
    
    for row in range(model.rowCount()):
        index = model.index(row, 0)  # 0 is for the first column
        coordinates_str = model.data(index, 0)  # 0 is for Qt.DisplayRole
        coordinates_list = coordinates_str.strip('[]').split(', ')
    
        try:
            longitude = float(coordinates_list[0])
            latitude = float(coordinates_list[1])
    
        except ValueError:
            instance.stop_simulation()
            instance.btn_simulation.setText("Simulation START")
            return print("nopp")
    
        instance.sim_waypoints_list.append((longitude, latitude))
    
    try:
        current_latitude = float(instance.sensor_data['latitude'])
        current_longitude = float(instance.sensor_data['longitude'])
        lst_dest_longitude = [coord[0] for coord in instance.sim_waypoints_list]
        lst_dest_latitude = [coord[1] for coord in instance.sim_waypoints_list]
    except:
        instance.stop_simulation()
        instance.btn_simulation.setText("Simulation START")
        print("destination_latitude 없음")
        return
    
    current_heading = instance.sensor_data['heading'] if instance.sensor_data['heading'] is not None else 0
    
    instance.sim_cnt_destination = 0
    prev_sim_cnt_destination = 0
    try:
        while instance.flag_simulation:
            print(1)
            if instance.sim_cnt_destination >= len(lst_dest_latitude):
                instance.flag_simulation = False
                # print("The boat has visited all destinations!")
                # instance.stop_simulation()
                # print(1)
                # instance.btn_simulation.setText("Simulation START")
                # print(2)
                return
    
            # if prev_sim_cnt_destination == 0 or prev_sim_cnt_destination != instance.sim_cnt_destination:
            #     instance.edit_destination.setText(str(instance.sim_cnt_destination))
    
            print(2)
            destination_latitude = float(lst_dest_latitude[instance.sim_cnt_destination])
            destination_longitude = float(lst_dest_longitude[instance.sim_cnt_destination])
            print(current_latitude, current_longitude, destination_longitude, destination_latitude)
            print(3)
            if current_heading > 180:
                current_heading = current_heading - 360
    
            print(4)
    
            # Haversine 공식을 사용하여 두 지점 사이의 거리를 계산
            instance.simulation_distance_to_target = haversine((current_latitude, current_longitude),
                                                           (destination_latitude, destination_longitude),
                                                           unit='m')
            print(5)
            # instance.sensor_data['distance'] = float(instance.simulation_distance_to_target)
    
            # 선박과 목적지가 이루는 선의 자북에 대한 각도 계산
            target_angle = math.degrees(
                math.atan2(destination_longitude - current_longitude, destination_latitude - current_latitude))
    
            print(6)
            # 헤딩과 목표 각도 간의 차이 계산
            angle_diff = target_angle - current_heading
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360
    
            print(7)
            # 각도 차이에 따른 throttle 및 roll 성분 계산
            throttle_component = instance.simulation_distance_to_target * math.cos(math.radians(angle_diff))
            roll_component = instance.simulation_distance_to_target * math.sin(math.radians(angle_diff))
    
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
    
            instance.simulation_pwml_auto = int(PWM_left)
            instance.simulation_pwmr_auto = int(PWM_right)
    
            print(7)
            # print("left : {}, right :{}".format(instance.simulation_pwml_auto, instance.simulation_pwmr_auto))
            try:
                if instance.simulation_pwml_auto == instance.simulation_pwmr_auto and instance.simulation_pwml_auto != 1500:
                    # Go straight
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading))
                elif instance.simulation_pwml_auto < instance.simulation_pwmr_auto:
                    # Turn right
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading - heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading - heading_diff))
                    current_heading -= math.degrees(heading_diff)
                elif instance.simulation_pwml_auto > instance.simulation_pwmr_auto:
                    # Turn left
                    heading_diff = math.radians(5)
                    lat_diff = 0.00001 * math.cos(math.radians(current_heading + heading_diff))
                    lng_diff = 0.00001 * math.sin(math.radians(current_heading + heading_diff))
                    current_heading += math.degrees(heading_diff)
    
                else:
                    print("error")
    
                instance.simulation_head = current_heading
                current_latitude = round(lat_diff + current_latitude, 8)
                current_longitude = round(lng_diff + current_longitude, 8)
                instance.simulation_lat = current_latitude
                instance.simulation_lon = current_longitude
                # instance.current_value['latitude'] = round(lat_diff + instance.current_value['latitude'], 8)
                # instance.current_value['longitude'] = round(lng_diff + instance.current_value['longitude'], 8)
    
                if instance.simulation_distance_to_target < 2:
                    # Stop the boat
                    prev_sim_cnt_destination = instance.sim_cnt_destination
                    instance.sim_cnt_destination += 1
                    print("Boat has reached the destination!")
    
                instance.flag_simulation_data_init = True
                print(instance.sim_cnt_destination)
                print(9)
                time.sleep(0.1)
            except Exception as E:
                print("simulator Error : ", E)
                time.sleep(1)
    
    except Exception as e:
        instance.stop_simulation()
        instance.btn_simulation.setText("Simulation START")
        print("simulation error : ", e)
        return
    
    instance.stop_simulation()
    instance.btn_simulation.setText("Simulation START")

def pc_simulator(instance):
    try:
        float(instance.sensor_data['latitude'])
        float(instance.sensor_data['longitude'])
        instance.sensor_data['dest_latitude']
        instance.sensor_data['dest_longitude']
    except:
        return

    if instance.simulation_thread is None:
        instance.simulation_thread = threading.Thread(target=instance.simulation)
        instance.simulation_thread.start()
        instance.btn_simulation.setText("Simulation STOP")
    else:
        instance.stop_simulation()
        instance.simulation_thread = None
        instance.btn_simulation.setText("Simulation START")
        

def stop_simulator(instance):
    try:
        print("stop received")
        instance.flag_simulation = False
        instance.simulation_distance_to_target = None
        instance.simulation_pwml_auto = None
        instance.simulation_pwmr_auto = None
        instance.edit_destination.setText("None")
        instance.worker.message['mode_jetson'] = "instance"
        instance.worker.message['dest_latitude'] = None
        instance.worker.message['dest_longitude'] = None
        instance.sensor_data['mode_jetson'] = "instance"
        instance.sensor_data['dest_latitude'] = None
        instance.sensor_data['dest_longitude'] = None
        # if instance.simulation_thread is not None:
        #     print(15)
        #     instance.simulation_thread.join()
        instance.simulation_thread = None

    except Exception as e:
        print("stop simulation error : ", e)