import socket
import select
import json
import time

def socket_LiDAR():
    server_socket_pc_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "0.0.0.0"
    port = 5010
    server_address = (host, port)
    server_socket_pc_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket_pc_send.bind(server_address)
    server_socket_pc_send.listen(1)

    try:
        while True:
            print("waiting")
            client_socket, client_address = server_socket_pc_send.accept()

            current_value = {'latitude', 'longitude', 'velocity', 'heading', 'pitch', 'dest_latitude', 'dest_longitude'}
            cnt_destination = 0
            try:
                print(f"Connected by {client_address}")
                while True:
                    ready_to_read, ready_to_write, _ = select.select([client_socket], [client_socket], [], 1)

                    if ready_to_write:
                        keys_to_extract = ['latitude', 'longitude', 'velocity', 'heading', 'pitch']
                        # 새로운 딕셔너리 생성
                        LiDAR_data = {key: current_value[key] for key in keys_to_extract if
                                           key in current_value}
                        LiDAR_data['dest_latitude'] = current_value['dest_latitude'][cnt_destination]
                        LiDAR_data['dest_longitude'] = current_value['dest_longitude'][cnt_destination]
                        if isinstance(LiDAR_data, dict):
                            message = json.dumps(LiDAR_data)
                            message += '\n'  # 구분자 추가
                            try:
                                client_socket.sendall(message.encode())
                            except Exception as e:
                                print("lidar sending : ", e)
                        else:
                            print("current_value is not a dictionary.")

                    if ready_to_read:
                        print("ready to read")
                        try:
                            received_way_point = client_socket.recv(1024).strip()
                            print("경유지 좌표 : ", received_way_point)
                            if not received_way_point:
                                flag_avoidance = False
                                way_point = None
                            else:
                                flag_avoidance = True
                                way_point = json.loads(received_way_point.decode('utf-8'))

                        except:
                            print("no data received")

                    time.sleep(0.1)

            except Exception as e:
                print(f"PC send connection Error: {e}")

            finally:
                client_socket.close()

    except KeyboardInterrupt:
        print("Send server stopped.")

    finally:
        server_socket_pc_send.close()