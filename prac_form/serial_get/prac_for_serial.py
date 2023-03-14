import serial
import random
import time

# USB 시리얼 포트 설정
ser = serial.Serial('COM7', 9600, timeout=1)

while True:
    # 무작위 정수 생성
    value = random.randint(0, 100)

    # 무작위 정수를 USB 시리얼 포트로 보내기
    ser.write(str(value).encode())
    print(f"Sent: {value}")

    # USB 시리얼 포트에서 값을 읽어와서 출력하기
    received = ser.readline().decode().rstrip()
    if received:
        print(f"Received: {received}")

    # 1초 대기
    time.sleep(1)