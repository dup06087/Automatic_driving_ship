import matplotlib

matplotlib.use('Agg')  # 'Agg' 백엔드를 사용하도록 설정

from matplotlib import pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import FuncFormatter


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
file_path = 'lat_lon_rtk.txt'  # 실제 파일 경로로 수정

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

# 데이터의 평균을 계산하고, 각 데이터 포인트에서 평균을 빼서 조정합니다.
latitude_mean = np.mean(latitudes)
longitude_mean = np.mean(longitudes)

latitudes_adjusted = [lat - latitude_mean for lat in latitudes]
longitudes_adjusted = [lon - longitude_mean for lon in longitudes]


# Y축 레이블 포맷을 조정하는 함수 정의
def scale_formatter(x, pos):
    return f"{x * 1e7:.0f}"

# 위도 그래프 그리기
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(latitudes_adjusted)], latitudes_adjusted, label='Adjusted Latitude')
plt.xlabel('Time')
plt.ylabel('Adjusted Latitude (x1e7)')
plt.title('Latitude over Time with Mean at Zero')
plt.gca().yaxis.set_major_formatter(FuncFormatter(scale_formatter))
plt.legend()
plt.grid(True)
plt.savefig('adjusted_latitude_over_time.png')
plt.close()

# 경도 그래프 그리기
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(longitudes_adjusted)], longitudes_adjusted, label='Adjusted Longitude')
plt.xlabel('Time')
plt.ylabel('Adjusted Latitude (x1e7)')
plt.title('Longitude over Time with Mean at Zero')
plt.gca().yaxis.set_major_formatter(FuncFormatter(scale_formatter))
plt.legend()
plt.grid(True)
plt.savefig('adjusted_longitude_over_time.png')
plt.close()

# 위도 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(latitudes)], latitudes, label='Latitude')
plt.xlabel('Time')
plt.ylabel('Latitude')
plt.title('Latitude over Time')
plt.legend()
plt.savefig('latitude_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

# 경도 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(longitudes)], longitudes, label='Longitude')
plt.xlabel('Time')
plt.ylabel('Longitude')
plt.title('Longitude over Time')
plt.legend()
plt.savefig('longitude_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(headings)], headings, label='Heading')
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Heading over Time')
plt.legend()
plt.savefig('heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

# Pitch 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(pitches)], pitches, label='Pitch')
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('Pitch over Time')
plt.legend()
plt.savefig('pitch_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

# 위도, 경도, heading, pitch의 평균과 표준편차 계산
latitude_avg, latitude_std = calculate_average_and_std(latitudes)
longitude_avg, longitude_std = calculate_average_and_std(longitudes)
heading_avg, heading_std = calculate_average_and_std(headings)
pitch_avg, pitch_std = calculate_average_and_std(pitches)

# 결과 출력
print(f"Latitude - Average: {latitude_avg}, Std Dev: {latitude_std}")
print(f"Longitude - Average: {longitude_avg}, Std Dev: {longitude_std}")
print(f"Heading - Average: {heading_avg}, Std Dev: {heading_std}")
print(f"Pitch - Average: {pitch_avg}, Std Dev: {pitch_std}")

# 위도와 경도 데이터의 평균을 원점으로 하는 새로운 좌표계에서의 데이터 계산
latitudes_adjusted = [lat - latitude_avg for lat in latitudes]
longitudes_adjusted = [lon - longitude_avg for lon in longitudes]

# 새로운 좌표계에서의 데이터를 이용하여 그래프 그리기
plt.figure(figsize=(10, 6))
plt.scatter(latitudes_adjusted, longitudes_adjusted, label='Data Points')
plt.xlabel('Latitude (adjusted)')
plt.ylabel('Longitude (adjusted)')
plt.title('Data Points with Mean at Origin')
plt.axhline(0, color='red', linestyle='--', label='Mean Latitude')
plt.axvline(0, color='green', linestyle='--', label='Mean Longitude')
plt.legend()
plt.grid(True)
plt.savefig('data_points_with_mean_at_origin.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


from scipy.stats import gaussian_kde
import numpy as np

# Pitch 데이터에 대한 확률 밀도 추정 및 그래프 그리기
pitch_data = np.array(pitches)
pitch_kde = gaussian_kde(pitch_data)
pitch_x = np.linspace(min(pitch_data), max(pitch_data), 500)
pitch_y = pitch_kde(pitch_x)

plt.figure(figsize=(10, 6))
plt.plot(pitch_x, pitch_y, label='Pitch Distribution')
plt.xlabel('Pitch')
plt.ylabel('Probability Density')
plt.title('Gaussian Distribution of Pitch')
plt.legend()
plt.savefig('pitch_distribution.png')
plt.close()

# Heading 데이터에 대한 확률 밀도 추정 및 그래프 그리기
heading_data = np.array(headings)
heading_kde = gaussian_kde(heading_data)
heading_x = np.linspace(min(heading_data), max(heading_data), 500)
heading_y = heading_kde(heading_x)

plt.figure(figsize=(10, 6))
plt.plot(heading_x, heading_y, label='Heading Distribution')
plt.xlabel('Heading')
plt.ylabel('Probability Density')
plt.title('Gaussian Distribution of Heading')
plt.legend()
plt.savefig('heading_distribution.png')
plt.close()

time_data = np.arange(len(headings))

# Heading 데이터에 대한 추세선 그리기
plt.figure(figsize=(10, 6))
plt.plot(time_data, headings, label='Heading', linestyle='-')
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Time vs. Heading')
plt.legend()
plt.savefig('time_vs_heading.png')
plt.close()

# Pitch 데이터에 대한 추세선 그리기
plt.figure(figsize=(10, 6))
plt.plot(time_data, pitches, label='Pitch', linestyle='-')
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('Time vs. Pitch')
plt.legend()
plt.savefig('time_vs_pitch.png')
plt.close()