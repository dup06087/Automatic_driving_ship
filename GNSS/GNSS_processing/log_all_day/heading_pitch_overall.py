# Matplotlib 라이브러리 임포트
import matplotlib.pyplot as plt

from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np


# 필요한 데이터를 파싱하고 추출하는 함수 정의
def parse_gnrmc(line):
    tokens = line.split(",")
    data = {}
    if tokens[0] in ["$GNRMC", "$GPRMC"] and tokens[2] == "A":  # 데이터가 유효한 경우
        lat_raw = float(tokens[3])
        lat_deg = int(lat_raw / 100)
        lat_min = lat_raw - lat_deg * 100
        data['latitude'] = round(lat_deg + lat_min / 60, 8)

        lon_raw = float(tokens[5])
        lon_deg = int(lon_raw / 100)
        lon_min = lon_raw - lon_deg * 100
        data['longitude'] = round(lon_deg + lon_min / 60, 8)
    return data


def parse_pssn_hrp(line):
    tokens = line.split(",")
    data = {}
    if tokens[0] == "$PSSN" and tokens[1] == "HRP":
        # 토큰에서 heading과 pitch 값을 추출하고, 유효하지 않은 경우 0을 기본값으로 설정
        data['heading'] = float(tokens[4]) if tokens[4] else 0
        data['pitch'] = float(tokens[6]) if tokens[6] else 0
    return data


# 파일에서 데이터를 읽고 파싱하는 함수
def read_and_parse_nma_file(file_path):
    extracted_data = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                gnrmc_data = parse_gnrmc(line.strip())
                if gnrmc_data:
                    extracted_data.append(gnrmc_data)

                pssn_hrp_data = parse_pssn_hrp(line.strip())
                if pssn_hrp_data:
                    extracted_data.append(pssn_hrp_data)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return extracted_data


def calculate_average_and_std(data_list):
    """
    주어진 데이터 리스트의 평균과 표준편차를 계산합니다.
    """
    data_array = np.array(data_list)
    average = np.mean(data_array)
    std_dev = np.std(data_array)
    return average, std_dev

# Haversine 공식 정의
def haversine(lat1, lon1, lat2, lon2):
    # 지구 반지름 (m 단위)
    R = 6371000
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = R * c  # 결과는 미터 단위
    return distance

# 파일 경로 지정 (실제 경로로 수정 필요)
file_path = 'log_10_hours.nma'  # 실제 파일 경로로 수정

# 파일 읽기 및 데이터 추출
extracted_data_from_file = read_and_parse_nma_file(file_path)
print(extracted_data_from_file)

# 위도, 경도, heading, pitch 데이터 추출
headings = [data['heading'] for data in extracted_data_from_file if 'heading' in data]
pitches = [data['pitch'] for data in extracted_data_from_file if 'pitch' in data]

# 위도와 경도의 평균과 표준편차 계산
head_mean, head_std = np.mean(headings), np.std(headings)
pitch_mean, pitch_std = np.mean(pitches), np.std(pitches)



adjusted_pitch = headings - head_mean
adjusted_heading = pitches - pitch_mean


# 위도와 경도 데이터의 표준편차 계산
head_std = np.std(adjusted_heading)
pitch_std = np.std(adjusted_pitch)

time_data = range(len(headings))

# 그래프 그리기 (이전 코드 반복)
plt.figure(figsize=(10, 6))

# Pitch 데이터 그래프
plt.plot(time_data, adjusted_pitch, label='Adjusted Pitch')
plt.axhline(-3*pitch_std, color='r', linestyle='--', label='+-3 Dev : dev={:.2f}'.format(pitch_std))
plt.axhline(3*pitch_std, color='r', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Pitch (degrees)')
plt.title('Pitch Over Time')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))

# Heading 데이터 그래프
plt.plot(time_data, adjusted_heading, label='Adjusted Heading')
plt.axhline(-3*head_std, color='r', linestyle='--', label='+-3 Dev : dev={:.2f}'.format(head_std))
plt.axhline(+3*head_std, color='r', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Heading (degrees)')
plt.title('Heading Over Time')
plt.legend()
plt.grid(True)
plt.show()
