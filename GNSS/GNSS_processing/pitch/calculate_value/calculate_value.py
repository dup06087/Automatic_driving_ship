import matplotlib.pyplot as plt
import numpy as np

file_path = './log_for_test.nma'

# 파일에서 pitch 값 읽기
with open(file_path, 'r') as file:
    pitches = [float(line.strip()) for line in file]

# 평균과 표준편차 계산
mean_value = np.mean(pitches)
std_dev = np.std(pitches)

# 평균을 0으로 맞추고 표준편차로 나누어 정규화(normalization) 수행
normalized_pitches = (pitches - mean_value) / std_dev

# 정규화된 데이터의 새로운 평균과 표준편차 계산
normalized_mean = abs(np.mean(normalized_pitches))
normalized_std_dev = np.std(normalized_pitches)

# 정규화된 데이터로 히스토그램 그리기
plt.figure(figsize=(10, 6))
plt.hist(normalized_pitches, bins=10, alpha=0.7, density=True, label='Normalized Pitch Distribution')
plt.axvline(normalized_mean, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {normalized_mean:.2f}')
plt.axvline(normalized_mean + 3*std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+3σ (Standard Deviation: {std_dev:.2f})')
plt.axvline(normalized_mean - 3*std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-3σ (Standard Deviation: {std_dev:.2f})')

# plt.axvline(normalized_mean + normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+1 Std Dev: {normalized_mean + normalized_std_dev:.2f}')
# plt.axvline(normalized_mean - normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-1 Std Dev: {normalized_mean - normalized_std_dev:.2f}')
plt.xlabel('sigma')
plt.ylabel('Frequency')
plt.title('Normalized Pitch Value Distribution')
plt.legend()
plt.show()