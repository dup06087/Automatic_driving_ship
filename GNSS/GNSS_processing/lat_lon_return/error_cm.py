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

file_path = './selected_lat_points.txt'

# 파일에서 heading 값 읽기
with open(file_path, 'r') as file:
    latitudes = [float(line.strip()) for line in file]

file_path = './selected_lon_points.txt'

# 파일에서 heading 값 읽기
with open(file_path, 'r') as file:
    longitudes = [float(line.strip()) for line in file]

# 위도와 경도의 평균과 표준편차 계산
lat_mean, lat_std = np.mean(latitudes), np.std(latitudes)
lon_mean, lon_std = np.mean(longitudes), np.std(longitudes)

# 위도와 경도 데이터의 표준편차 계산
lat_std = np.std(latitudes)
lon_std = np.std(longitudes)

# 각 시점에서의 평균 위치로부터의 거리(오차) 계산
errors = [haversine(lat, lon, lat_mean, lon_mean) for lat, lon in zip(latitudes, longitudes)]

time_data = np.arange(len(latitudes))  # 가정: 데이터 포인트 간의 시간 간격은 동일

# 오차 시각화
plt.figure(figsize=(10, 6))
plt.plot(time_data, errors, label='Location Error from Mean Position')
plt.xlabel('Time (min)')
plt.ylabel('Error (m)')
plt.title('Time vs Location Error')
plt.legend()
plt.grid(True)
plt.show()

# 에러의 평균과 표준편차 계산
error_mean = np.mean(errors)
error_std = np.std(errors)

# 오차 시각화 및 표준편차 표시
plt.figure(figsize=(10, 6))
plt.plot(time_data, errors, label='Location Error from Mean Position', color='blue')
plt.axhline(y=error_mean, color='g', linestyle='-', label='Mean Error ({:0.3f}m)'.format(error_mean))
plt.axhline(y=error_mean + 3 * error_std, color='r', linestyle='--', label='+3 Dev : Dev({:0.3f})'.format(error_std))
# plt.axhline(y=error_mean - 3 * error_std, color='r', linestyle='--', label='-3 Std Dev')
plt.xlabel('Time (min)')
plt.ylabel('Error (m)')
plt.title('Time vs Location Error with Std Deviation')
plt.legend()
plt.grid(True)
plt.show()

# 에러의 평균과 표준편차 출력
print(f"Mean Error: {error_mean:.2f} m")

# 오차에 대한 히스토그램 및 평균, ±3σ 표시
plt.figure(figsize=(10, 6))
n, bins, patches = plt.hist(errors, bins=20, color='skyblue', edgecolor='black', alpha=0.7, label='Error Distribution')

# 평균 오차 및 ±3σ 선 표시
plt.axvline(error_mean, color='g', linestyle='-', linewidth=2, label='Mean Error')
plt.axvline(error_mean + 3 * error_std, color='r', linestyle='--', linewidth=2, label='+3 Std Dev')
plt.axvline(error_mean - 3 * error_std, color='r', linestyle='--', linewidth=2, label='-3 Std Dev')

plt.xlabel('Error (m)')
plt.ylabel('Frequency')
plt.title('Histogram of Location Error')
plt.legend()
plt.grid(True)
plt.show()

# 평균 오차와 표준편차 정보 출력
print(f"Mean Error: {error_mean:.2f} m")
print(f"Std Deviation: {error_std:.2f} m")
print(f"+3 Std Deviation from Mean: {error_mean + 3*error_std:.2f} m")
print(f"-3 Std Deviation from Mean: {error_mean - 3*error_std:.2f} m")