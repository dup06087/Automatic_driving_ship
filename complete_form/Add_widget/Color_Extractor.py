from PIL import Image
import numpy as np
import sys

img = Image.open("hi.png")
# img.show()

np_img = np.array(img)
# print(np_img)
# print(type(np_img))
# print(np_img.shape)
# print(np_img[:,:,0:3].shape)
RGB_Img = np_img[:,:,0:3]
# print(RGB_Img)

# for i in range(len(RGB_Img[0][0])):
for j in range(len(RGB_Img)):
    for k in range(len(RGB_Img[0])): ### RGB_Img[j][k][i]
        if RGB_Img[j][k][0] == 170 and RGB_Img[j][k][1] == 211 and RGB_Img[j][k][2] == 223:
            RGB_Img[j][k][0] = 255
            RGB_Img[j][k][1] = 255
            RGB_Img[j][k][2] = 255
        else:
            RGB_Img[j][k][0] = 0
            RGB_Img[j][k][1] = 0
            RGB_Img[j][k][2] = 0


# print("RGB_IMG : ", RGB_Img)

# np_to_IMG = Image.fromarray(RGB_Img, 'RGB')
# np_to_IMG.show()

binary_img = RGB_Img[:,:,0]
# Image.fromarray(binary_img).show()

distance_array = np.zeros(binary_img.shape)
# print(distance_array)
# 초기화
for i in range(len(binary_img)):
    for j in range(len(binary_img[0])):
        if binary_img[i][j] == 255:
            distance_array[i][j] = 1036800001
        elif binary_img[i][j] == 0:
            distance_array[i][j] = -1
        else:
            # print("error")
            pass

final_array = distance_array
#goal pixel
distance_array[183][399] = 0
current_pixel =[189,388]
print("here" , distance_array[current_pixel[0], current_pixel[1]])
for i in range(len(binary_img)):
    for j in range(len(binary_img[0])):
        if distance_array[i][j] == -1:
            pass
        else:
            Not_None_buffer = []
            for m in range(3):
                for n in range(3):
                    # print("m, n : ", m,n)
                    try:
                        if distance_array[i-1+m][j-1+n] != -1:
                            Not_None_buffer.append(distance_array[i-1+m][j-1+n])
                        else:
                            pass
                            # print("pass")
                    except:
                        pass
            # print(min(Not_None_buffer))
            # print("buffer : ", Not_None_buffer)

            check_array = np.array(1036800001) * len(Not_None_buffer)
            check_array = ( check_array == Not_None_buffer)
            if (len(Not_None_buffer) != 0) and False in check_array:
                # print("done")
                final_array[i][j] = min(Not_None_buffer) + 1
            # print('final_array : ', final_array)
