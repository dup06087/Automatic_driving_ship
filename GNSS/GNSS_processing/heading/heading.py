import matplotlib

# matplotlib.use('Agg')  # 'Agg' 백엔드를 사용하도록 설정

from matplotlib import pyplot as plt
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
file_path = 'log_head_latest.nma'  # 실제 파일 경로로 수정

# 파일 읽기 및 데이터 추출
extracted_data_from_file = read_and_parse_nma_file(file_path)
print(extracted_data_from_file)

# 파일 읽기 및 데이터 추출 후 Heading 데이터를 처리
extracted_data_from_file = read_and_parse_nma_file(file_path)

# 시간 축을 위한 인덱스 생성
time_indexes = range(len(extracted_data_from_file))

# Heading 데이터 추출 및 360도 이상인 값 조정
headings = [data['heading'] for data in extracted_data_from_file if 'heading' in data]
headings = [h - 360 if h >= 180 else h for h in headings]
# headings = headings[:1000]

# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_indexes[:len(headings)], headings, label='Heading')
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Heading over Time')
plt.legend()
plt.savefig('heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

heading_avg, heading_std = calculate_average_and_std(headings)

print(f"Heading - Average: {heading_avg}, Std Dev: {heading_std}")


from scipy.stats import gaussian_kde
import numpy as np

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


import mplcursors

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

line, = plt.plot(time_indexes[:len(headings)], headings, label='Heading')  # plot 반환값을 line 변수에 저장
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Heading over Time')
plt.legend()
# 클릭한 데이터 포인트 정보를 저장할 변수 초기화
selected_point = {'index': None, 'xdata': None, 'ydata': None}

# 마우스 호버링 시 데이터 포인트 강조
cursor = mplcursors.cursor(line, hover=True)

@cursor.connect("add")
def on_add(sel):
    # 강조된 데이터 포인트 정보 저장
    selected_point['index'] = sel.target.index
    selected_point['xdata'], selected_point['ydata'] = sel.target

# 클릭 이벤트 처리 함수
def on_click(event):
    if selected_point['index'] is not None:
        # 클릭한 위치에 마커 추가
        ax.plot(selected_point['xdata'], selected_point['ydata'], marker='o', color='red', markersize=10)
        plt.draw()  # 그래프 업데이트

        # 선택된 데이터 포인트 정보 출력 및 파일에 저장
        print(f"Selected Time: {selected_point['xdata']}, Pitch: {selected_point['ydata']}")
        with open("selected_data_points.txt", "a") as file:
            file.write(f"{selected_point['ydata']}\n")

# 클릭 이벤트 리스너 등록
fig.canvas.mpl_connect('button_press_event', on_click)

plt.show()
plt.close()
