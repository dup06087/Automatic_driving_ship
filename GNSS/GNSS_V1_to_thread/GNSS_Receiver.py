import socket
import time
import threading
import json

# 윈도우 아니고, Jetson이랑 GNSS랑 Serial 통신 사용하므로 ip통신에서 변경해줘야함
# 여기는 GNSS랑
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 5000))

# 여기는 jetson
GNSS_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
GNSS_server_socket.bind(("localhost", 5001))
GNSS_server_socket.listen(20)

GNSS_socket, address = GNSS_server_socket.accept()

# 필요한 값들 초기화
current_value = {"latitude" : None, "longitude" : None, "heading" : None, "velocity" : None}

# serial 통신 읽기(sock.recv()) > 특이사항 : 이 함수의 출력은 binary string임
def _get_bytes_stream(sock, length):
    buf = b''
    try:
        step = length
        while True:
            data = sock.recv(step)
            if data == "$".encode():
                break
            buf += data
    except Exception as e:
        print(e)
    return buf

def GNSS_get_data():
    while True:
        # "$"를 기준으로 몇 문장 불러올 것인지 > GPRMC, GPHDT 2문장 사용하므로 2문장씩 불러서 파싱
        sentence_cnt = 0
        sentence_number = 2
        while sentence_cnt < sentence_number:
            #파싱할 데이터 담는 리스트
            NMEA_parsed = []

            # 위의 binary string을 string으로 decode 해줌
            data = _get_bytes_stream(client_socket, 1).decode()
            # print("data : ", data)

            # 쌓인 데이터 처리도 한 번에 가능하도록 > 원리 : 최신 값으로 그냥 덮어씀, 오래된거 버림
            # "," 기준으로 파싱
            NMEA_parsed = data.split(",")

            # 파싱한 것의 첫 번째는 NMEA 어떤 형식인지 (ex GGA, RMC, HDT) 나타냄 := NMEA_sentence
            # 가시성을 위해 이것만 따로 저장
            NMEA_sentence = NMEA_parsed[0]
            if NMEA_sentence == ("GNHDT" or "GPHDT"): # 1문장씩 2번 수신하는 것이라(따로 문장의 순서같은것이 없음) if 문을 써서 어떤 문자포맷인지 먼저 체크
                current_value["heading"] = NMEA_parsed[1]
                # cf. GPHDT : yaw 값만 존재
                # cf. GPRMC : 시간, 유효성,위도,북위,경도,동경,속도(노트),사실 heading값인데 왜 안나오는지 모르겠음, 시간, 나침반 기능, 체크썸
            elif NMEA_sentence == ("GNRMC" or "GPRMC"):

                try:
                    current_value["latitude"] = NMEA_parsed[3]
                    current_value["longitude"] = NMEA_parsed[5]
                    current_value["velocity"] = NMEA_parsed[7]
                except:
                    print("Some Value Error Occured")
                    pass

            else:
                print("Error")
                current_value = {"latitude": None, "longitude": None, "heading": None, "velocity": None}

            # 이거는 나중에 오류생기면 잡으려고 남겨둠
            if ( data == 'q' or data == 'Q'):
                client_socket.close()
                break
            else:
                pass
                # print ("RECEIVED:" , data)

            sentence_cnt += 1
            if sentence_cnt == 2:
                sentence_cnt = 0
                break

        #실제 출력은 여기서, 나머지 프린트문은 에러시 로그 남기기위해
        print(current_value)
        GNSS_socket.send(str(current_value).encode())

        time.sleep(0.05) # 시리얼 수신함수 recv가 serial 포트에 데이터 들어올 때까지 기다리므로 짧게해줘서 GNSS 데이터 들어오면 바로 데이터 최신화

    # while 문이 끝나면
    client_socket.close()
    print("socket colsed... END.")

GNSS_data_get_threading = threading.Thread(target=GNSS_get_data)
GNSS_data_get_threading.start()


