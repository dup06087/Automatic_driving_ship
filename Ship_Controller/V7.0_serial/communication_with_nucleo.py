import random
import re
import serial
import atexit
import time


def is_valid_data(data):
    pattern = re.compile(r"mode:(AUTO|SELF|SMLT|WAIT),pwm_left:(\d+|None),pwm_right:(\d+|None)")
    return bool(pattern.match(data))

def serial_nucleo():
    # port_nucleo = "/dev/ttyACM0"
    port_nucleo = "COM8"
    # port_nucleo = "/dev/tty_nucleo_f401re2"
    baudrate = 115200
    current_value = {"mode_jetson" : "AUTO", "pwml_auto" : random.randint(1500, 1900), "pwmr_auto" : random.randint(1500,1900)}
    received_data = None
    prev_print_time = 0
    while True:
        try:
            ser_nucleo = serial.Serial(port_nucleo, baudrate=baudrate, timeout=0.6)
            response = None
            prev_print_time = time.time()

            while True:
                try:
                    current_value["pwml_auto"] = random.randint(1500, 1900)
                    current_value["pwmr_auto"] = random.randint(1500, 1900)
                    prev_time = time.time()
                    # Generate random mode and pwm values
                    # mode_str = random.choice(["AUTO", "MANUAL"])
                    mode_str = current_value['mode_jetson']
                    pwm_left_auto = int(
                        current_value['pwml_auto'] if current_value['pwml_auto'] is not None else 1500)
                    pwm_right_auto = int(
                        current_value['pwmr_auto'] if current_value['pwmr_auto'] is not None else 1500)
                    # Send data and wait for the response
                    send_message = "mode:{},pwm_left:{},pwm_right:{}\n".format(mode_str, pwm_left_auto, pwm_right_auto).encode()
                    # ser_nucleo.write(send_message)
                    prev_response = response
                    response = ser_nucleo.readline().decode().strip()
                    if not is_valid_data(response):
                        received_data = response
                        response = prev_response



                    # parsed_data = dict(item.split(":") for item in response.split(","))
                    # current_value['mode_chk'] = str(parsed_data.get('mode', 'UNKNOWN').strip())
                    # current_value['pwml'] = int(parsed_data.get('pwm_left', '0').strip())
                    # current_value['pwmr'] = int(parsed_data.get('pwm_right', '0').strip())

                except:
                    print("nucleo communication error")

                # print("Jetson >> Nucleo, send : ", data_str.encode())
                # print("Nucleo >> Jetson, mode : {}, pwml : {}, pwmr : {}".format(current_value['mode_chk'],
                #                                                                  current_value['pwml'],
                #                                                                  current_value['pwmr']))
                time.sleep(0.0001)
                current_time = time.time()
                if current_time - prev_print_time >= 1:
                    print("시간 : ", current_time - prev_time)
                    print(response)
                    print("irregular data : ", received_data)
                    # print(f"Jetson >> Nucleo, mode : {mode_str}, pwml : {pwm_left_auto}, pwmr : {pwm_right_auto}")


        except Exception as e:
            print("Nucleo:", e)
            print("End serial_nucleo")
            time.sleep(0.005)
        finally:
            try:
                print("nucleo error")
                ser_nucleo.close()
                time.sleep(0.005)
            except:
                print("nucleo error2")
                time.sleep(0.005)
                pass

serial_nucleo()