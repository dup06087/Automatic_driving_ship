import matplotlib.pyplot as plt
import numpy as np

### original pitch
file_path = 'pitches.txt'

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
# plt.show()
plt.savefig("Original pitch")

##### filtered pitch
file_path = 'filtered_pitches.txt'

# 파일에서 pitch 값 읽기
with open(file_path, 'r') as file:
    filtered_pitches = [float(line.strip()) for line in file]

# 평균과 표준편차 계산
filtered_mean_value = np.mean(filtered_pitches)
filtered_std_dev = np.std(filtered_pitches)

# 평균을 0으로 맞추고 표준편차로 나누어 정규화(normalization) 수행
normalized_filtered_pitches = (filtered_pitches - filtered_mean_value) / filtered_std_dev

# 정규화된 데이터의 새로운 평균과 표준편차 계산
normalized_filtered_mean = abs(np.mean(normalized_filtered_pitches))
normalized_filtered_std_dev = np.std(normalized_filtered_pitches)

# 정규화된 데이터로 히스토그램 그리기
plt.figure(figsize=(10, 6))
plt.hist(normalized_filtered_pitches, bins=10, alpha=0.7, density=True, label='Normalized Pitch Distribution')
plt.axvline(normalized_filtered_mean, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {normalized_filtered_mean:.2f}')
plt.axvline(normalized_filtered_mean + 3*filtered_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+3σ (Standard Deviation: {filtered_std_dev:.2f})')
plt.axvline(normalized_filtered_mean - 3*filtered_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-3σ (Standard Deviation: {filtered_std_dev:.2f})')

# plt.axvline(normalized_mean + normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+1 Std Dev: {normalized_mean + normalized_std_dev:.2f}')
# plt.axvline(normalized_mean - normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-1 Std Dev: {normalized_mean - normalized_std_dev:.2f}')
plt.xlabel('sigma')
plt.ylabel('Frequency')
plt.title('Normalized filtered Pitch Value Distribution')
plt.legend()
plt.savefig("filtered pitch")
# plt.show()


##### original heading


file_path = 'headings.txt'

# 파일에서 pitch 값 읽기
with open(file_path, 'r') as file:
    headings = [float(line.strip()) for line in file]

# 평균과 표준편차 계산
mean_value = np.mean(headings)
std_dev = np.std(headings)

# 평균을 0으로 맞추고 표준편차로 나누어 정규화(normalization) 수행
normalized_headings = (headings - mean_value) / std_dev

# 정규화된 데이터의 새로운 평균과 표준편차 계산
normalized_mean = abs(np.mean(normalized_headings))
normalized_std_dev = np.std(normalized_headings)

# 정규화된 데이터로 히스토그램 그리기
plt.figure(figsize=(10, 6))
plt.hist(normalized_headings, bins=10, alpha=0.7, density=True, label='Normalized Pitch Distribution')
plt.axvline(normalized_mean, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {normalized_mean:.2f}')
plt.axvline(normalized_mean + 3*std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+3σ (Standard Deviation: {std_dev:.2f})')
plt.axvline(normalized_mean - 3*std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-3σ (Standard Deviation: {std_dev:.2f})')

# plt.axvline(normalized_mean + normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+1 Std Dev: {normalized_mean + normalized_std_dev:.2f}')
# plt.axvline(normalized_mean - normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-1 Std Dev: {normalized_mean - normalized_std_dev:.2f}')
plt.xlabel('sigma')
plt.ylabel('Frequency')
plt.title('Normalized Pitch Value Distribution')
plt.legend()
# plt.show()
plt.savefig("Original heading")

##### filtered heading

file_path = 'filtered_headings.txt'

# 파일에서 pitch 값 읽기
with open(file_path, 'r') as file:
    filtered_headings = [float(line.strip()) for line in file]

# 평균과 표준편차 계산
filtered_mean_value = np.mean(filtered_headings)
filtered_std_dev = np.std(filtered_headings)

# 평균을 0으로 맞추고 표준편차로 나누어 정규화(normalization) 수행
normalized_filtered_headings = (filtered_headings - filtered_mean_value) / filtered_std_dev

# 정규화된 데이터의 새로운 평균과 표준편차 계산
normalized_filtered_mean = abs(np.mean(normalized_filtered_headings))
normalized_filtered_std_dev = np.std(normalized_filtered_headings)

# 정규화된 데이터로 히스토그램 그리기
plt.figure(figsize=(10, 6))
plt.hist(normalized_filtered_headings, bins=10, alpha=0.7, density=True, label='Normalized Pitch Distribution')
plt.axvline(normalized_filtered_mean, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {normalized_filtered_mean:.2f}')
plt.axvline(normalized_filtered_mean + 3*filtered_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+3σ (Standard Deviation: {filtered_std_dev:.2f})')
plt.axvline(normalized_filtered_mean - 3*filtered_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-3σ (Standard Deviation: {filtered_std_dev:.2f})')

# plt.axvline(normalized_mean + normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'+1 Std Dev: {normalized_mean + normalized_std_dev:.2f}')
# plt.axvline(normalized_mean - normalized_std_dev, color='g', linestyle='dashed', linewidth=2, label=f'-1 Std Dev: {normalized_mean - normalized_std_dev:.2f}')
plt.xlabel('sigma')
plt.ylabel('Frequency')
plt.title('Normalized filtered Pitch Value Distribution')
plt.legend()
plt.savefig("filtered heading")
# plt.show()