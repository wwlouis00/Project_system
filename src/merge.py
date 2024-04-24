#!/usr/bin/python
# -*- coding: UTF-8 -*-
import cv2
import numpy as np


def _gray2rgb(gray_image, color_dict):

    # 定義新涵式
    rgb_image = np.zeros(shape=(*gray_image.shape, 3))
    # 上色
    for i in range(rgb_image.shape[0]):
        for j in range(rgb_image.shape[1]):
            # 不同的灰度值上不同的顏色
            if gray_image[i, j] < 127:
                rgb_image[i, j, :] = color_dict["black"]
            else:
                rgb_image[i, j, :] = color_dict["red"]
    return rgb_image.astype(np.uint8)


def addImage():
    img1 = cv2.imread("./para/tmp/dye.png")
    src = cv2.imread("./para/tmp/ROI_image_new.png")
    h, w, _ = img1.shape

    img2 = cv2.resize(src, (w, h))

    alpha = 0.7
    beta = 1 - alpha
    gamma = 3
    img_add = cv2.addWeighted(img1, alpha, img2, beta, gamma)

    cv2.imwrite('./para/tmp/merged_image.png', img_add)
    print("finish")


def merge():
    color_dict = {"black": [0, 0, 0],
                  "red": [0, 0, 255]}

    ROI_all = cv2.imread("./para/tmp/ROI_of_all.bmp", 0)

    ret, th2 = cv2.threshold(ROI_all, 70, 255, cv2.THRESH_BINARY)
    img_new_2 = _gray2rgb(th2, color_dict)
    cv2.imwrite("./para/tmp/ROI_image_new.png", img_new_2)

    addImage()
