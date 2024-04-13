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


# 파일 경로 지정 (실제 경로로 수정 필요)
file_path = 'log_10_hours.nma'  # 실제 파일 경로로 수정

# 파일 읽기 및 데이터 추출
extracted_data_from_file = read_and_parse_nma_file(file_path)
print(extracted_data_from_file)

# 위도, 경도, heading, pitch 데이터 추출
latitudes = [data['latitude'] for data in extracted_data_from_file if 'latitude' in data][300:]
longitudes = [data['longitude'] for data in extracted_data_from_file if 'longitude' in data][300:]

print("latitudes : ", latitudes)

# 위도와 경도의 평균과 표준편차 계산
lat_mean, lat_std = np.mean(latitudes), np.std(latitudes)
lon_mean, lon_std = np.mean(longitudes), np.std(longitudes)


adjusted_latitudes = latitudes - lat_mean
adjusted_longitudes = longitudes - lon_mean

print("adjusted_latitudes : ", adjusted_latitudes)

adjusted_latitudes_cm = 11100000 * adjusted_latitudes
adjusted_longitudes_cm = 11100000 * adjusted_longitudes

print("adjusted_latitudes_cm : ", adjusted_latitudes_cm)

time_data = np.arange(len(adjusted_latitudes_cm))  # 시간 데이터, 1분 단위 가정
print(time_data)

lat_cm_std = np.std(adjusted_latitudes_cm)
lon_cm_std = np.std(adjusted_longitudes_cm)

# 시간 대비 위도 변화 그래프
plt.figure(figsize=(10, 6))
plt.plot(time_data, adjusted_latitudes_cm, label='Latitude')
plt.axhline(y= 3 * lat_cm_std, color='r', linestyle='--', label='3 * Std : Std={:0.2f}'.format(lat_cm_std))
plt.axhline(y=-3 * lat_cm_std, color='r', linestyle='--')
plt.xlabel('Time (min)')
plt.ylabel('Latitude error (cm)')
plt.title('Time vs Latitude (Centered)')
plt.legend()
plt.show()

# 시간 대비 경도 변화 그래프
plt.figure(figsize=(10, 6))
plt.plot(time_data, adjusted_longitudes_cm, label='Longitude')
plt.axhline(y=3 * lon_cm_std, color='r', linestyle='--', label='3 * Std : Std={:0.2f}'.format(lat_cm_std))
plt.axhline(y=-3 * lon_cm_std, color='r', linestyle='--')
plt.xlabel('Time (min)')
plt.ylabel('Longitude error (cm)')
plt.title('Time vs Longitude (Centered)')
plt.legend()
plt.show()