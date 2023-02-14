import skimage
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image


def hist_eq_updated(img):
    img_flatten = img.flatten()
    img_flat_nnzero = img_flatten[np.where(img_flatten!=0)]
    image_histogram, bins = np.histogram(img_flat_nnzero,256)
    #print(image_histogram,bins)
    cdf = image_histogram.cumsum() # cumulative distribution function
    #print(cdf)

    eq_img_flatten = np.zeros_like(img_flatten)
    cdf_min = min(cdf)
    cdf_max = max(cdf)
    LUT = np.zeros(256, dtype=img.dtype)
    for val in range(256):
         ind = 0
         flag=False
         for j in range(len(bins)):
             if val==0:
                 flag=True
             if (val>=bins[j]) and (val<=bins[j+1]) or flag==True:
                 break;
             ind = ind + 1
         if flag==True:
             LUT[val] = 0
         else:
             LUT[val] = (((cdf[ind] - cdf_min)/(cdf_max-cdf_min))*254) + 1
    return LUT[img]

final_img = np.load('./final_array.npy')
for i in range(len(final_img)):
    for j in range(len(final_img[0])):
        if final_img[i][j] is np.NaN:
            final_img[i][j] = 0

Img = skimage.io.imread(final_img)
# Img = skimage.io.imread("http://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Portrait_elisha_gray.jpg/220px-Portrait_elisha_gray.jpg")

plt.figure()
plt.subplot(121)
plt.imshow(Img, interpolation='none', cmap='gray')
plt.subplot(122)
plt.imshow(hist_eq_updated(Img), interpolation='none', cmap='gray')