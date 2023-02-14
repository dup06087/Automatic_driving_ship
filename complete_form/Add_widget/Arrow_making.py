import numpy as np
import sys
import copy
from PIL import Image

final_img = np.load('./final_array.npy')

###route_array 값 : -1, 0 ~ value
route_array = copy.deepcopy(final_img)
for i in range(final_img.shape[0]):
    for j in range(final_img.shape[1]):
        if route_array[i][j] == sys.maxsize or np.isnan(route_array[i][j]):
            route_array[i][j] = -1

print("max value : \t")
print(np.max(route_array))
print(np.argmax(route_array))

print(np.unravel_index(route_array.argmax(), route_array.shape))

def largest_indices(ary, n):
    """Returns the n largest indices from a numpy array."""
    flat = ary.flatten()
    indices = np.argpartition(flat, -n)[-n:]
    indices = indices[np.argsort(-flat[indices])]
    return np.unravel_index(indices, ary.shape)
print(route_array[largest_indices(route_array, 1000)])


print(np.where(route_array > 0, route_array, np.inf).argmin())
find_min = np.where(route_array > 0, route_array, np.inf).argmin()
print(np.unravel_index(find_min, route_array.shape))


route_array = np.where(route_array > 0, route_array, np.inf)
current_pixel_x = 189
current_pixel_y = 388

#너비 우선 탐색 사용
## route_array 값 : inf(nan, inf), 0 ~ 도착지 값

route = []
buffer = []

for m in range(3):
    for n in range(3):
        if m == 1 and n == 1:
            continue

        try:
            buffer.append((route_array[current_pixel_x - 1 + m][current_pixel_y - 1 + n]))
        except IndexError as e:
            print(e)


smaller_idx_list = np.argwhere(buffer < route_array[current_pixel_x, current_pixel_y])
route_list = [[(current_pixel_x,current_pixel_y)] for _ in range(len(smaller_idx_list))]
for i in range(len(smaller_idx_list)):
    m = smaller_idx_list[i] // 3
    n = smaller_idx_list[i] % 3

    current_pixel_x = current_pixel_x - 1 + m
    current_pixel_y = current_pixel_y - 1 + n

    print("x,y")
    print(int(current_pixel_x))
    print(current_pixel_y)
    route_list[i].append((int(current_pixel_x), int(current_pixel_y.real)))


print(route_list)
print(buffer)

print(route_array[current_pixel_x, current_pixel_y])

# for k in range((route_list.shape))
#
# for i in range((route_array.shape[0])):
#     for j in range((route_array.shape[1])):

# Image.fromarray(route_array).show()