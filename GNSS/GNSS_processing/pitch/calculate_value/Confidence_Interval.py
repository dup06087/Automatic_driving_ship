import numpy as np
import scipy.stats as stats

file_path = './log_for_test.nma'

# 파일에서 pitch 값 읽기
with open(file_path, 'r') as file:
    pitches = [float(line.strip()) for line in file]

# 주어진 데이터를 사용하여 신뢰 구간 계산
data = np.array(pitches) # pitch 데이터
mean = np.mean(data)
std_dev = np.std(data, ddof=1) # 표본 표준편차
n = len(data)

# 95% 신뢰 구간을 위한 z 값
confidence_level = 0.95
z = stats.norm.ppf(1 - (1 - confidence_level) / 2)

# 신뢰 구간 계산
margin_of_error = z * (std_dev / np.sqrt(n))
confidence_interval = (mean - margin_of_error, mean + margin_of_error)

print(confidence_interval)