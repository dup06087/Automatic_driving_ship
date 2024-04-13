import random
import serial
import time

ser = serial.Serial('COM1', 115200)  # USB 포트에 연결된 장치의 포트와 baud rate 설정

while True:
    # 같은 포맷의 값을 랜덤으로 생성하여 전송
    data = """$GNRMC,084449.00,A,{0},N,{1},E,{2},,240223,8.8,W,D*16
    $GNHDT,{3},T*1F""".format(random.randint(0,10), random.randint(0,10), random.randint(0,10), random.randint(0,10))
    ser.write(data.encode())  # 데이터 전송

    time.sleep(1)

ser.close()  # 연결 종료