import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# 데이터 로드
file_path = 'log_current_value.csv'
df = pd.read_csv(file_path)

# 다음 위치 데이터 생성
df['next_latitude'] = df['latitude'].shift(-1)
df['next_longitude'] = df['longitude'].shift(-1)
df['next_heading'] = df['heading'].shift(-1)
df['next_velocity'] = df['velocity'].shift(-1)
df = df.dropna()  # 마지막 행 제거

# 입력 특성 및 타겟 설정
X = df[['pwml_chk', 'pwmr_chk']]
Y = df[['next_latitude', 'next_longitude', 'next_velocity', 'next_heading']]

# 데이터 분할
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 선형 회귀 모델 초기화 및 훈련
model = LinearRegression()
model.fit(X_train, Y_train)

# 시뮬레이션 데이터 로드
simulation_data_file_path = 'autonomous_driving_extracted_log_one_cycle.csv'
simulation_df = pd.read_csv(simulation_data_file_path)

# 초기 위치 데이터 설정
current_latitude = simulation_df.iloc[0]['latitude']
current_longitude = simulation_df.iloc[0]['longitude']

# 예측된 결과를 저장할 리스트
predicted_latitudes = [current_latitude]
predicted_longitudes = [current_longitude]

# PWM 값만 사용하여 순차적 예측 수행
for index, row in simulation_df.iterrows():
    if index == 0:
        continue  # 첫 번째 행은 이미 초기 값으로 사용함

    # 현재 PWM 값으로 다음 위치 예측
    current_pwm = [[row['pwml_chk'], row['pwmr_chk']]]
    print(current_pwm)
    predicted_location = model.predict(current_pwm)[0]  # 예측 실행
    print("predicted_location : ", predicted_location)
    # 예측된 위도와 경도를 다음 입력으로 사용
    current_latitude, current_longitude = predicted_location[0], predicted_location[1]
    print(current_latitude, current_longitude)
    predicted_latitudes.append(current_latitude)
    predicted_longitudes.append(current_longitude)

# 예측 결과를 DataFrame에 저장
simulation_df['predicted_latitude'] = predicted_latitudes
simulation_df['predicted_longitude'] = predicted_longitudes


# 결과를 CSV 파일로 저장
output_file_path = 'predicted_simulation_results.csv'

simulation_df.to_csv(output_file_path, index=False)

print(f"Predicted results saved to {output_file_path}")
