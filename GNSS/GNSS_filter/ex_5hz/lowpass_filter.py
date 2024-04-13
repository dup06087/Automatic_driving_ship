import matplotlib

from matplotlib import pyplot as plt
import numpy as np


def calculate_average_and_std(data_list):
    """
    주어진 데이터 리스트의 평균과 표준편차를 계산합니다.
    """
    data_array = np.array(data_list)
    average = np.mean(data_array)
    std_dev = np.std(data_array)
    return average, std_dev


# 파일에서 데이터를 읽고 파싱하는 함수
def read_value(file_path):
    extracted_data = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = float(line.strip())
                extracted_data.append(line)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return extracted_data

# 파일 경로 지정 (실제 경로로 수정 필요)
file_heading = 'headings.txt'  # 실제 파일 경로로 수정
file_pitch = 'pitches.txt'  # 실제 파일 경로로 수정
# 파일 읽기 및 데이터 추출
headings = read_value(file_heading)
pitches = read_value(file_pitch)


time_index_headings = range(len(headings))
time_index_pitches = range(len(pitches))
import mplcursors


# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_index_headings, headings, label='Heading')
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('Heading over Time')
plt.legend()
# plt.show()
plt.savefig('heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


# Pitch 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_index_pitches, pitches, label='Pitch')
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('Pitch over Time')
plt.legend()
mplcursors.cursor(hover=True)
# plt.show()
plt.savefig('pitch_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기

data_freq = 2
tau = 1 / (2 * 3.14 * data_freq)
Ts = 0.2 #
alpha = tau / (tau + Ts)
print(alpha)

print(headings)
# Function to apply low-pass filter
def apply_low_pass_filter(data, alpha):
    filtered_data = [data[0]]  # Initialize the filtered data array
    for n in range(1, len(data)):
        filtered_point = alpha * data[n] + (1 - alpha) * filtered_data[-1]
        filtered_data.append(filtered_point)
    return filtered_data

# Applying the low-pass filter to each dataset
filtered_headings = apply_low_pass_filter(headings, alpha)
filtered_pitches = apply_low_pass_filter(pitches, alpha)

# print(filtered_latitudes, filtered_longitudes, filtered_headings, filtered_pitches, alpha)

# Heading 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_index_headings, filtered_headings, label='filtered Heading')
plt.xlabel('Time')
plt.ylabel('Heading')
plt.title('filtered Heading over Time')
plt.legend()
# plt.show()
plt.savefig('filtered heading_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


# Pitch 그래프 저장
plt.figure(figsize=(10, 6))
plt.plot(time_index_pitches, filtered_pitches, label='filtered Pitch')
plt.xlabel('Time')
plt.ylabel('Pitch')
plt.title('filtered Pitch over Time')
plt.legend()
mplcursors.cursor(hover=True)
# plt.show()
plt.savefig('filtered pitch_over_time.png')  # 이미지 파일로 저장
plt.close()  # 그래프 닫기


# filtered_headings 데이터를 파일로 저장
with open('filtered_headings.txt', 'w') as file:
    for heading in filtered_headings:
        file.write(f"{heading}\n")

# filtered_pitches 데이터를 파일로 저장
with open('filtered_pitches.txt', 'w') as file:
    for pitch in filtered_pitches:
        file.write(f"{pitch}\n")

