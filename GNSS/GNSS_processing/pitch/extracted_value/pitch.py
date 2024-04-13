import matplotlib

from matplotlib import pyplot as plt
import numpy as np
from scipy.signal import find_peaks


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
file_path = 'log_pitch.nma'  # 실제 파일 경로로 수정

# 파일 읽기 및 데이터 추출
extracted_data_from_file = read_and_parse_nma_file(file_path)
print(extracted_data_from_file)

# 시간 축을 위한 인덱스 생성 (실제 시간 데이터가 있다면 해당 데이터 사용)
time_indexes = range(len(extracted_data_from_file))

headings = [data['heading'] for data in extracted_data_from_file if 'heading' in data]
pitches = [data['pitch'] for data in extracted_data_from_file if 'pitch' in data]

time_data = np.arange(len(pitches))

# 'pitches'는 이미 로드된 데이터로 가정합니다.
# peaks와 troughs를 찾는 작업을 수행합니다.
peaks, _ = find_peaks(pitches)
troughs, _ = find_peaks(-np.array(pitches))

# 극대점과 극소점 중에서 pitch 절대값이 3.5 이하인 것들만 필터링
filtered_peaks = peaks[np.abs(np.array(pitches)[peaks]) <= 3.5]
filtered_troughs = troughs[np.abs(np.array(pitches)[troughs]) <= 3.5]

# 필터링된 극대점과 극소점에 대한 pitch 값 추출
filtered_peaks_values = np.array(pitches)[filtered_peaks]
filtered_troughs_values = np.array(pitches)[filtered_troughs]

# 시간 축 생성 (인덱스를 시간으로 가정)
time_indexes = np.arange(len(pitches))

# 그래프 생성
plt.figure(figsize=(10, 6))

# 전체 pitch 데이터 플롯
plt.plot(time_indexes, pitches, label='Pitch', color='blue')

# 필터링된 극대점 플롯
plt.scatter(filtered_peaks, filtered_peaks_values, color='red', label='Filtered Peaks')

# 필터링된 극소점 플롯
plt.scatter(filtered_troughs, filtered_troughs_values, color='green', label='Filtered Troughs')

# 레이블과 타이틀 추가
plt.title('Filtered Peaks and Troughs in Pitch Data')
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.legend()

plt.show()

# 저장할 데이터를 준비합니다. (peaks와 troughs를 함께 놓습니다.)
combined_indices = np.concatenate((filtered_peaks, filtered_troughs))
combined_values = np.concatenate((filtered_peaks_values, filtered_troughs_values))

np.savetxt('pitch value.txt', combined_values, fmt='%.5f', header='Index Pitch')

'/mnt/data/filtered_peaks_troughs.txt'  # 파일 경로를 반환합니다.

import mplcursors

# 그래프 그리기
plt.figure(figsize=(10, 6))
line, = plt.plot(time_indexes, pitches, label='Pitch')  # plot 반환값을 line 변수에 저장
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('Pitch over Time')
plt.legend()

# 클릭 이벤트 처리 및 데이터 포인트 정보 저장 함수
def on_click(sel):
    # 선택된 데이터 포인트의 x, y 값
    x, y = sel.target
    print(f"Time: {x}, Pitch: {y}")
    # 파일에 저장
    with open("selected_data_points.txt", "a") as file:
        file.write(f"Time: {x}, Pitch: {y}\n")

# mplcursors를 사용하여 클릭 이벤트에 반응하도록 설정
cursor = mplcursors.cursor(line, hover=True)
cursor.connect("add", on_click)

plt.show()