import numpy as np
import sys
import copy
from PIL import Image

final_img = np.load('./final_array.npy')
route_array = copy.deepcopy(final_img)
###route_array 값 : -1, 0 ~ value
for i in range(final_img.shape[0]):
    for j in range(final_img.shape[1]):
        if route_array[i][j] == sys.maxsize or np.isnan(route_array[i][j]):
            route_array[i][j] = -1

# def largest_indices(ary, n):
#     """Returns the n largest indices from a numpy array."""
#     flat = ary.flatten()
#     indices = np.argpartition(flat, -n)[-n:]
#     indices = indices[np.argsort(-flat[indices])]
#     return np.unravel_index(indices, ary.shape)
# print(route_array[largest_indices(route_array, 1000)])

current_pixel_x = 189
current_pixel_y = 388

print(route_array[183][399])
print(route_array[current_pixel_x][current_pixel_y])

# while True:
#     current_pixel_x = 189
#     current_pixel_y = 388
#     buffer = []
#
#     # while True:
#     for m in range(3):
#         for n in range(3):
#             if m == 1 and n == 1:
#                 continue
#
#             try:
#                 buffer.append((route_array[current_pixel_x - 1 + m][current_pixel_y - 1 + n]))
#             except IndexError as e:
#                 print(e)
#
#     smaller_idx_list = np.argwhere(buffer < route_array[current_pixel_x, current_pixel_y])
#     print(smaller_idx_list)
#     for i in range(len(smaller_idx_list)):
#         print(i)
#         m = smaller_idx_list[i] // 3
#         n = smaller_idx_list[i] % 3
#         try:
#             current_pixel_x = current_pixel_x - 1 + m
#             current_pixel_y = current_pixel_y - 1 + n
#             print(route_array[current_pixel_x][current_pixel_y])
#         except:
#             print("error")