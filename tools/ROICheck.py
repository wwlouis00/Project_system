#!/usr/bin/python3

import cv2
import numpy as np
import os
from camera import camera
from public_method import *

ROIpath = f"./para/ROIs/ROI_of_all.bmp"

ROI = cv2.imread(ROIpath)
zero = np.zeros(shape=(ROI.shape[0],ROI.shape[1]))

cam = camera(framerate=2,iso=100)
try:
    image, _, _ = cam.shot()
finally:
    cam.close()

# gray scaling
# image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
image = crop(image)

image[:,:,2] = zero
image[:,:,1] = zero
result_image = cv2.addWeighted(ROI, 0.3, image, 2, 0)
cv2.imwrite("/home/pi/FileStore/ROI_image.png",result_image)
cv2.imshow("result", result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

