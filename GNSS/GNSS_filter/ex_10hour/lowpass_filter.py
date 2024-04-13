import matplotlib

from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np

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
file_path = 'log_for_test.nma'  # 실제 파일 경로로 수정

# 파일 읽기 및 데이터 추출
extracted_data_from_file = read_and_parse_nma_file(file_path)
print(extracted_data_from_file)

# 시간 축을 위한 인덱스 생성 (실제 시간 데이터가 있다면 해당 데이터 사용)
time_indexes = range(len(extracted_data_from_file))

# 위도, 경도, heading, pitch 데이터 추출
latitudes = [data['latitude'] for data in extracted_data_from_file if 'latitude' in data]
longitudes = [data['longitude'] for data in extracted_data_from_file if 'longitude' in data]
headings = [data['heading'] for data in extracted_data_from_file if 'heading' in data]
pitches = [data['pitch'] for data in extracted_data_from_file if 'pitch' in data]

import mplcursors

lat_mean, lat_std = np.mean(latitudes), np.std(latitudes)
lon_mean, lon_std = np.mean(longitudes), np.std(longitudes)

heading_mean, heading_std = np.mean(headings), np.std(headings)
pitch_mean, pitch_std = np.mean(pitches), np.std(pitches)

# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(headings)], headings, label='std={:.3f}'.format(heading_std))
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Heading over Time')
plt.legend()
# plt.show()
plt.savefig('heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


# Pitch 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(pitches)], pitches, label='std={:.3f}'.format(pitch_std))
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('Pitch over Time')
plt.legend()
mplcursors.cursor(hover=True)
# plt.show()
plt.savefig('pitch_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

data_freq = 1 / 60
tau = 1 / (2 * 3.14 * data_freq)
Ts = 60
alpha = tau / (tau + Ts)
print(alpha)

# Function to apply low-pass filter
def apply_low_pass_filter(data, alpha):
    filtered_data = [data[0]]  # Initialize the filtered data array
    for n in range(1, len(data)):
        filtered_point = alpha * data[n] + (1 - alpha) * filtered_data[-1]
        filtered_data.append(filtered_point)
    return filtered_data

# Applying the low-pass filter to each dataset
filtered_latitudes = apply_low_pass_filter(latitudes, alpha)
filtered_longitudes = apply_low_pass_filter(longitudes, alpha)
filtered_headings = apply_low_pass_filter(headings, alpha)
filtered_pitches = apply_low_pass_filter(pitches, alpha)

print(filtered_latitudes, filtered_longitudes, filtered_headings, filtered_pitches, alpha)


# 위도와 경도의 평균과 표준편차 계산
filtered_lat_mean, filtered_lat_std = np.mean(filtered_latitudes), np.std(filtered_latitudes)
filtered_lon_mean, filtered_lon_std = np.mean(filtered_longitudes), np.std(filtered_longitudes)

filtered_heading_mean, filtered_heading_std = np.mean(filtered_headings), np.std(filtered_headings)
filtered_pitch_mean, filtered_pitch_std = np.mean(filtered_pitches), np.std(filtered_pitches)

# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(headings)], filtered_headings, label='std={:.3f}'.format(filtered_heading_std))
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('filtered Heading over Time')
plt.legend()
# plt.show()
plt.savefig('filtered heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


# Pitch 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(pitches)], filtered_pitches, label='std={:.3f}'.format(filtered_pitch_std))
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('filtered Pitch over Time')
plt.legend()
mplcursors.cursor(hover=True)
# plt.show()
plt.savefig('filtered pitch_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


##### original 위경도


# 각 시점에서의 평균 위치로부터의 거리(오차) 계산
errors = [haversine(lat, lon, lat_mean, lon_mean) for lat, lon in zip(latitudes, longitudes)]

time_data = np.arange(len(latitudes))  # 가정: 데이터 포인트 간의 시간 간격은 동일

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
plt.title('Location error')
plt.legend()
plt.grid(True)
# plt.show()
plt.savefig("location error")

##### filtered 위경도
# 위도와 경도의 평균과 표준편차 계산
filtered_lat_mean, filtered_std = np.mean(filtered_latitudes), np.std(filtered_latitudes)
filtered_lon_mean, filtered_lon_std = np.mean(filtered_longitudes), np.std(filtered_longitudes)

# 위도와 경도 데이터의 표준편차 계산
filtered_lat_std = np.std(filtered_latitudes)
filtered_lon_std = np.std(filtered_longitudes)

# 각 시점에서의 평균 위치로부터의 거리(오차) 계산
errors = [haversine(lat, lon, filtered_lat_mean, filtered_lon_mean) for lat, lon in zip(filtered_latitudes, filtered_longitudes)]

time_data = np.arange(len(filtered_latitudes))  # 가정: 데이터 포인트 간의 시간 간격은 동일

# 에러의 평균과 표준편차 계산
filtered_error_mean = np.mean(errors)
filtered_error_std = np.std(errors)

# 오차 시각화 및 표준편차 표시
plt.figure(figsize=(10, 6))
plt.plot(time_data, errors, label='Location Error from Mean Position', color='blue')
plt.axhline(y=filtered_error_mean, color='g', linestyle='-', label='Mean Error ({:0.3f}m)'.format(filtered_error_mean))
plt.axhline(y=filtered_error_mean + 3 * filtered_error_std, color='r', linestyle='--', label='+3 Dev : Dev({:0.3f})'.format(filtered_error_std))
# plt.axhline(y=error_mean - 3 * error_std, color='r', linestyle='--', label='-3 Std Dev')
plt.xlabel('Time (min)')
plt.ylabel('Error (m)')
plt.title('filtered Location error')
plt.legend()
plt.grid(True)
# plt.show()
plt.savefig("filtered location error")

##### original location error scatter
adjusted_latitudes = latitudes - lat_mean
adjusted_longitudes = longitudes - lon_mean

print("adjusted_latitudes : ", adjusted_latitudes)

adjusted_latitudes_cm = 11100000 * adjusted_latitudes
adjusted_longitudes_cm = 11100000 * adjusted_longitudes


lat_cm_std = np.std(adjusted_latitudes_cm)
lon_cm_std = np.std(adjusted_longitudes_cm)


# 그래프에 포인트와 표준편차 타원 표시
fig, ax = plt.subplots(figsize=(10, 6))

# 데이터 포인트 표시
ax.scatter(adjusted_longitudes_cm, adjusted_latitudes_cm, color='blue', label='filtered position')

# 표준편차 타원 표시
ellipse = Ellipse((0, 0), 2*3*lon_cm_std, 2*3*lat_cm_std, edgecolor='r', facecolor='none', linestyle='--', label='Std Deviation')
ax.add_patch(ellipse)


ax.axhline(0, color='black', linestyle='--')
ax.axvline(0, color='black', linestyle='--')
ax.set_xlabel('Longitude (cm)')
ax.set_ylabel('Latitude (cm)')
ax.set_title('original location - center at 0')
ax.legend()
ax.grid(True)

# plt.show()
plt.savefig("location scatter")

##### filtered location scatter plot

adjusted_latitudes = filtered_latitudes - filtered_lat_mean
adjusted_longitudes = filtered_longitudes - filtered_lon_mean

print("adjusted_latitudes : ", adjusted_latitudes)

adjusted_filtered_latitudes_cm = 11100000 * adjusted_latitudes
adjusted_filtered_longitudes_cm = 11100000 * adjusted_longitudes


filtered_lat_cm_std = np.std(adjusted_filtered_latitudes_cm)
filtered_lon_cm_std = np.std(adjusted_filtered_longitudes_cm)


# 그래프에 포인트와 표준편차 타원 표시
fig, ax = plt.subplots(figsize=(10, 6))

# 데이터 포인트 표시
ax.scatter(adjusted_filtered_longitudes_cm, adjusted_filtered_latitudes_cm, color='blue', label='filtered position')

# 표준편차 타원 표시
ellipse = Ellipse((0, 0), 2*3*filtered_lon_cm_std, 2*3*filtered_lat_cm_std, edgecolor='r', facecolor='none', linestyle='--', label='Std Deviation')
ax.add_patch(ellipse)


ax.axhline(0, color='black', linestyle='--')
ax.axvline(0, color='black', linestyle='--')
ax.set_xlabel('Longitude (cm)')
ax.set_ylabel('Latitude (cm)')
ax.set_title('filtered location - center at 0')
ax.legend()
ax.grid(True)

# plt.show()
plt.savefig("filtered location scatter")

##### difference check between filtered and original
# 그래프에 포인트와 표준편차 타원 표시
fig, ax = plt.subplots(figsize=(10, 6))

# 데이터 포인트 표시
ax.scatter(adjusted_filtered_longitudes_cm, adjusted_filtered_latitudes_cm, color='blue', label='filtered position')
ax.scatter(adjusted_longitudes_cm, adjusted_latitudes_cm, color='red', label='original position', alpha=0.5)

# 표준편차 타원 표시
ellipse_filtered = Ellipse((0, 0), 2*3*filtered_lon_cm_std, 2*3*filtered_lat_cm_std, edgecolor='b', facecolor='none', linestyle='--', label='Filtered SD')
ax.add_patch(ellipse_filtered)
ellipse_original = Ellipse((0, 0), 2*3*lon_cm_std, 2*3*lat_cm_std, edgecolor='r', facecolor='none', linestyle='--', label='original SD')
ax.add_patch(ellipse_original)

ax.axhline(0, color='black', linestyle='--')
ax.axvline(0, color='black', linestyle='--')
ax.set_xlabel('Longitude (cm)')
ax.set_ylabel('Latitude (cm)')
ax.set_title('filtered location - center at 0')
ax.legend()
ax.grid(True)

# plt.show()
plt.savefig("difference check scatter")
