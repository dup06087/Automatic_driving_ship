import random
import time
import serial
import re

def send_data(ser, mode, pwm_left, pwm_right):
    send_message = "mode:{},pwm_left:{},pwm_right:{}\n".format(mode, pwm_left, pwm_right).encode()
    ser.write(send_message)
    print("Sent message:", send_message)

def is_valid_data(data):
    pattern = re.compile(r"mode:(AUTO|SELF|SMLT),pwm_left:\d+,pwm_right:\d+")
    return bool(pattern.match(data))

def main():
    port_nucleo = "COM8"
    baudrate = 115200

    while True:
        try:
            ser_nucleo = serial.Serial(port_nucleo, baudrate=baudrate, timeout=10)
            last_print_time = time.time()

            while True:
                # Generate random mode and pwm values
                # mode_str = random.choice(["AUTO", "MANUAL"])
                mode_str = "SMLT"
                pwm_left_auto = random.randint(1000, 2000)
                pwm_right_auto = random.randint(1000, 2000)

                # Send data and wait for the response
                send_data(ser_nucleo, mode_str, pwm_left_auto, pwm_right_auto)
                response = ser_nucleo.readline().decode().strip()
                if is_valid_data(response):
                    print("Received response:", response)
                else:
                    print("nucleo가 이상한 데이터 보냈어요ㅠ")
                time.sleep(0.5)

        except Exception as e:
            print("Nucleo:", e)
            print("End serial_nucleo")
            time.sleep(1)
        finally:
            try:
                ser_nucleo.close()
            except:
                pass

if __name__ == "__main__":
    main()