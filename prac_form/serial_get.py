import serial
import time

# 시리얼 포트 설정
# 이 부분은 실제 사용하는 COM 포트에 맞게 수정해야 합니다. 예: 'COM3', '/dev/ttyUSB0', 등등
ser = serial.Serial(port='COM7', baudrate=115200, timeout=10)

# 파일에 데이터를 저장할 준비
with open('jetson_xavier_nx_uart_log.txt', 'a') as file:
    try:
        while True:
            if ser.in_waiting > 0:
                # data = ser.readline().decode('utf-8').strip() # 데이터 읽기
                data = ser.readline().decode('utf-8')
                print(data) # 콘솔에 데이터 출력
                file.write(data) # 파일에 데이터 쓰기
                file.write("\n")  # 파일에 데이터 쓰기

    finally:
        ser.close() # 시리얼 포트 닫기
