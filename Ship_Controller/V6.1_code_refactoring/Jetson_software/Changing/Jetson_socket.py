import socket
import select
import time
import json

class JetsonSocket:
    def __init__(self):
        self.current_value = {'mode_jetson': "SELF", 'mode_chk': "SELF", 'pwml': None, 'pwmr': None,
                              'pwml_auto': None, 'pwmr_auto': None, 'pwml_sim': None, 'pwmr_sim': None,
                              "latitude": 37.633173, "longitude": 127.077618, 'dest_latitude': None,
                              'dest_longitude': None, 'cnt_destination': None, 'velocity': None,
                              'heading': 0, 'roll': None, 'pitch': None, 'validity': None, 'time': None,
                              'IP': None, 'com_status': None, 'date': None, 'distance': None,
                              "waypoint_latitude": None, "waypoint_longitude": None}

    def socket_pc_recv(self, client_socket='0.0.0.0', recv_port=5004):
        server_socket_pc_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = recv_port
        server_address = (host, port)
        server_socket_pc_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc_recv.bind(server_address)
        server_socket_pc_recv.listen(1)

        while True:
            try:
                client_socket, client_address = server_socket_pc_recv.accept()
                print(f"Connected by {client_address}")
                last_print_time = time.time()
                while True:
                    data = client_socket.recv(1024).strip()
                    if not data:
                        break

                    # print(data)
                    try:
                        received_dict = json.loads(data.decode('utf-8'))
                        self.current_value['mode_jetson'] = received_dict['mode_jetson']
                        self.current_value['dest_latitude'] = received_dict['dest_latitude']
                        self.current_value['dest_longitude'] = received_dict['dest_longitude']
                        # print("PC >> Jetson", received_dict)  # 占쏙옙쨔占?占쌩곤옙

                        # if not self.current_value['is_driving']:
                        #     self.current_value['pwml_auto'] = 0
                        #     self.current_value['pwmr_auto'] = 0



                    # print(self.distance_to_target)
                    # print("x :", throttle_component, "y : ", roll_component)
                    # print("PWM_right : ", PWM_right, "PWM_left : ", PWM_left)


                    except (json.JSONDecodeError, TypeError, ValueError):
                        current_time = time.time()
                        if current_time - last_print_time >= 1:
                            try:
                                print("Waiting for destination")
                                last_print_time = current_time  # 占쏙옙占쏙옙占쏙옙 占쏙옙占?占시곤옙 占쏙옙占쏙옙占쏙옙트
                            except:
                                print("NOOOOOp")
                        continue

                    time.sleep(0.1)
            except Exception as e:
                print(f"PC recv connection Error: {e}")
                continue

            finally:
                client_socket.close()

    ### receive from PC
    def socket_pc_send(self, client_socket='0.0.0.0', send_port=5003):
        server_socket_pc_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = client_socket
        port = send_port
        server_address = (host, port)
        server_socket_pc_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket_pc_send.bind(server_address)
        server_socket_pc_send.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket_pc_send.accept()

                try:
                    print(f"Connected by {client_address}")

                    while True:
                        ready_to_read, ready_to_write, _ = select.select([], [client_socket], [], 1)
                        if ready_to_write:

                            if isinstance(self.current_value, dict):
                                message = json.dumps(self.current_value)
                                message += '\n'  # 占쏙옙占쏙옙占쏙옙 占쌩곤옙
                                try:
                                    client_socket.sendall(message.encode())
                                    # print("Jetson >> pc, send : ", message)  # 占쏙옙쨔占?占쌩곤옙
                                except OSError as e:
                                    print("Error in sending message:", e)  # 占쏙옙占쏙옙 占쏙옙쨔占?占쌩곤옙
                                    raise Exception("Connection with client has been closed.")
                            else:
                                print("current_value is not a dictionary.")

                        time.sleep(0.05)

                except Exception as e:
                    print(f"PC send connection Error: {e}")

                finally:
                    client_socket.close()

        except KeyboardInterrupt:
            print("Send server stopped.")
        finally:
            server_socket_pc_send.close()