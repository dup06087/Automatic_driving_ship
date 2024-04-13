# 원본 데이터 파일 경로
original_file_path = 'log_lat_lon_valid_data_24.04.05.txt'  # 원본 파일 경로를 여기에 입력하세요.
# 결과를 저장할 새로운 파일 경로
new_file_path = 'parsed_data.txt'  # 결과를 저장할 새로운 파일 이름

# 파일 읽기 및 쓰기 작업
try:
    with open(original_file_path, 'r') as original_file, open(new_file_path, 'w') as new_file:
        for line in original_file:
            # ':' 기호를 기준으로 문자열을 분리하고, 오른쪽 부분(1 인덱스)을 추출합니다.
            data_part = line.split(':')[-1].strip()
            # 추출된 문자열을 새로운 파일에 씁니다.
            new_file.write(data_part + '\n')
    print(f"Data has been successfully parsed and saved to {new_file_path}")
except FileNotFoundError:
    print(f"File not found: {original_file_path}")