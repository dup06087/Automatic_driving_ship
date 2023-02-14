import copy
import sys

from PIL import Image
import numpy as np

import Color_Extractor

binary_img = Color_Extractor.binary_img
print(binary_img)

# distance array initializing
# distance_img = np.Nan, sys.maxsize, 0
distance_img = np.zeros(binary_img.shape)
for i in range(len(binary_img)):
    for j in range(len(binary_img[0])):
        if binary_img[i][j] == 0:
            distance_img[i][j] = np.NaN
        elif binary_img[i][j] == 255:
            distance_img[i][j] = sys.maxsize

# print(distance_img)

distance_img[183][399] = 0
final_img = copy.deepcopy(distance_img)
current_pixel =[189,388]
counter = 0

#final_img : 0~value, sys.maxsize, np.NaN
while final_img[current_pixel[0]][current_pixel[1]] == sys.maxsize:
    print(++counter)
    inner_counter = 0

    for i in range(len(binary_img)):
        for j in range(len(binary_img[0])):
            if np.isnan(distance_img[i][j]):
                continue

            elif distance_img[i][j] != sys.maxsize:
                continue

            else:
                buffer = []
                for m in range(3):
                    for n in range(3):
                        if m == 1 and n == 1:
                            continue

                        try:
                            buffer.append(distance_img[i - 1 + m][j - 1 + n])
                        except Exception as e:
                            # print(e , "Occured -> pass")
                            pass

                buffer = [value for value in buffer if (not np.isnan(value)) and value != sys.maxsize]

                try:
                    final_img[i][j] = max(buffer) + 1
                except:
                    pass

    distance_img = copy.deepcopy(final_img)

np.set_printoptions(threshold=sys.maxsize)
# print(distance_img)
Image.fromarray(final_img).show()

np.save("./final_array", final_img)



# max(route_array)
# np.argmax()