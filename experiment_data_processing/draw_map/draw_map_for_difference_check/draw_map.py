import json
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# 파일 경로
file_path = "autodrive_extracted_log_one_cycle.txt"

# 위도와 경도를 저장할 리스트
latitude = []
longitude = []
dest_latitude = []
dest_longitude = []

# 파일 열기 및 데이터 읽기
with open(file_path, 'r') as file:
    for line in file:
        if line.strip():  # 빈 줄은 무시
            corrected_line = line.strip().replace("'", '"').replace("None", "null")
            data = json.loads(corrected_line)
            latitude.append(data['latitude'])
            longitude.append(data['longitude'])
            # dest_latitude와 dest_longitude에 대해 null 체크 후 추가
            if data['dest_latitude'] is not None:
                dest_latitude.extend(data['dest_latitude'])
            if data['dest_longitude'] is not None:
                dest_longitude.extend(data['dest_longitude'])

zoom = 0.00001
# Basemap 객체 초기화
map = Basemap(projection='merc', llcrnrlat=min(latitude) - zoom, urcrnrlat=max(latitude) + zoom,
              llcrnrlon=min(longitude) - zoom, urcrnrlon=max(longitude) + zoom, resolution='i')

# 그리드 라인과 축 라벨 추가
map.drawmeridians(range(int(min(longitude)), int(max(longitude)), 1), labels=[0,0,0,1])
map.drawparallels(range(int(min(latitude)), int(max(latitude)), 1), labels=[1,0,0,0])

map.drawcoastlines()
map.drawcountries()
map.fillcontinents(color='aqua', lake_color='aqua')
map.drawmapboundary(fill_color='aqua')

# 웨이포인트의 위도와 경도를 맵 좌표계로 변환
x_dest, y_dest = map(dest_longitude, dest_latitude)

# 웨이포인트 마커를 지도에 플롯
# waypoints, = map.plot(x_dest, y_dest, marker=True, markersize=5, label='Waypoints', color = "blue")
waypoints = map.scatter(x_dest, y_dest, zorder=5, s=30, color='blue', marker='o', edgecolor='black', label='Waypoints')

# 위도와 경도를 맵 좌표계로 변환
x, y = map(longitude, latitude)

# 포인트를 지도에 플롯
Trajectory, = map.plot(x, y, marker=None, color='red', markersize=10, label="Trajectory")

scale_lon = 0.00005
scale_lat = 0.00001
# map.drawmapscale(lon=max(longitude) - scale, lat=min(latitude) + scale, lon0=longitude[0], lat0=latitude[0], length=100, labelstyle='simple', units='m', barstyle='fancy')
map.drawmapscale(lon=max(longitude) - scale_lon, lat=min(latitude) + scale_lat, lon0=longitude[0], lat0=latitude[0], length=10, labelstyle='simple', units='m', barstyle='fancy')

plt.title('Trajectory on Map')
plt.legend(handles=[waypoints, Trajectory], loc='upper left')

plt.show()

