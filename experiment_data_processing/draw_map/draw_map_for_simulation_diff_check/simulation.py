import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# 데이터 파일 로드
file_path = 'predicted_simulation_results.csv'
data_df = pd.read_csv(file_path)

# 실제 궤적과 예측 궤적 데이터
latitude = data_df['latitude']
longitude = data_df['longitude']
predicted_latitude = data_df['predicted_latitude']
predicted_longitude = data_df['predicted_longitude']

zoom = 0.0001
# Basemap 객체 초기화
map = Basemap(projection='merc', llcrnrlat=min(latitude) - zoom, urcrnrlat=max(latitude) + zoom,
              llcrnrlon=min(longitude) - zoom, urcrnrlon=max(longitude) + zoom, resolution='i')

map.drawcoastlines()
map.fillcontinents(color='coral', lake_color='aqua')
map.drawmapboundary(fill_color='aqua')

# 실제 궤적의 위도와 경도를 맵 좌표계로 변환
x_real, y_real = map(longitude, latitude)
map.plot(x_real, y_real, 'D-', markersize=5, color='green', label='Actual Trajectory')

# 예측된 궤적의 위도와 경도를 맵 좌표계로 변환
x_pred, y_pred = map(predicted_longitude, predicted_latitude)
map.plot(x_pred, y_pred, 'o-', markersize=5, color='red', label='Predicted Trajectory')

plt.title('Actual and Predicted Trajectories')
plt.legend(loc='upper left')
plt.show()
