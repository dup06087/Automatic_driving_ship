import serial
import time

def send_data_to_mbed(serial_port, data):
    # 데이터를 ', '로 구분하고 개행 문자를 추가하여 Mbed로 전송
    print(f"{data[0]},{data[1]},{data[2]}\n")
    serial_port.write(f"{data[0]},{data[1]},{data[2]}\n".encode())

def read_from_mbed(serial_port):
    # Mbed로부터 데이터 읽기
    return serial_port.readline().decode().strip()

def main():
    # COM포트와 보레이트를 귀하의 설정에 맞게 변경하세요
    with serial.Serial('COM7', 9600, timeout=1) as ser:
        while True:
            # 임의의 데이터를 Mbed로 전송
            send_data_to_mbed(ser, [1.23, 4.56, 7.89])
            time.sleep(1)  # 잠시 대기

            # Mbed로부터의 응답 읽기
            response = read_from_mbed(ser)
            if response:
                print(response)

if __name__ == "__main__":
    main()