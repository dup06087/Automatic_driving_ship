import serial
import time
from random import randint

# 시리얼 포트를 열고, 115200bps로 설정합니다.
ser = serial.Serial("COM7", 115200)

while True:
    # 시리얼 포트에서 데이터를 읽습니다.
    data = ser.readline().decode("utf-8")

    # 읽은 데이터를 출력합니다.
    print("Received: " + data)

    # 1초간 대기합니다.
    time.sleep(1)

    # 임의의 문자열을 생성합니다.
    len = randint(1, 100)
    data = ""
    for i in range(len):
        data += chr(ord("a") + randint(0, 25))

    # 시리얼 포트에 데이터를 전송합니다.
    ser.write(data.encode("utf-8"))