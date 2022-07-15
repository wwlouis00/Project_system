from camera import camera
from public_method import crop
from public_method import write_to_csv
from public_method import read_from_csv
from public_method import str_to_list
from time import sleep
import numpy as np
import cv2
import math
import os

# parameters setting
# you can get rid of the shadow region of the well by increasing it
thresholding_offset = 25


def erode(image, kernel_para=3, iterations=1):
    kernel = np.ones((kernel_para, kernel_para), np.uint8)
    image_ero = cv2.erode(image, kernel, iterations=iterations)
    return image_ero


def dilate(image, kernel_para=3, iterations=1):
    kernel = np.ones((kernel_para, kernel_para), np.uint8)
    image_dil = cv2.dilate(image, kernel, iterations=iterations)
    return image_dil

def unsharp(image):
    blur_img = cv2.GaussianBlur(image, (0, 0), 100)
    image_unsharp = cv2.addWeighted(image, 2, blur_img, -25, 0)
    return image_unsharp

def binarize(image):
    # the variable "thresholding_offset"
    # is used to get rid of the shadow region that we aren't interested in
    ret1, _ = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)
    ret2, mask = cv2.threshold(image, ret1+thresholding_offset,
                               255, cv2.THRESH_BINARY)
    return mask


class Calibration:
    def __init__(self):
        pass

    @staticmethod
    def _calculate_average(image):
        averages = [0] * 16
        ROI_of_each_well = np.zeros(image.shape, dtype='uint8')

        for i in range(0, 16):
            ROI_of_each_well = cv2.imread(f'./para/tmp/ROI_{i+1}.bmp', 0)
            hist = cv2.calcHist([image], [0], mask=ROI_of_each_well, histSize=[256], ranges=[0, 256])
            # find out the average of each well
            total_val = 0
            pixel_num = 0
            for val, count in enumerate(hist):
                total_val += val*count
                pixel_num += count
            averages[i] = int(total_val/pixel_num)
        return averages

    @staticmethod
    def _save_image_with_value(image_name, image, value):
        """
        get 'mask_of_all' & 'coordinates_of_wells' from folder
        :param image_name:
        :param value:
        :param image:
        :return None:
        """
        mask = cv2.imread('./para/tmp/ROI_of_all.bmp', 0)
        image_masked = cv2.bitwise_and(image, image, mask)
        coordinates = read_from_csv('./para/tmp/coordinates.csv')
        for i in range(0, 16):
            coordinates[i] = str_to_list(coordinates[i])
            cv2.putText(image_masked, str(value[i]), (coordinates[i][0], coordinates[i][1] - 10),
                        cv2.FONT_HERSHEY_TRIPLEX, 0.5, (66, 211, 249), 1, cv2.LINE_AA)
        cv2.imwrite(f'./para/tmp/{image_name}_with_value.png', image_masked)
        print("Save image.")
        return None

    @staticmethod
    def _save_image_without_value(image_name, image):
        """
        get 'mask_of_all' & 'coordinates_of_wells' from folder
        :param image_name:
        :param value:
        :param image:
        :return None:
        """
        cv2.imwrite(f'./para/tmp/{image_name}.png', image)
        print("Save image.")
        return None

    @staticmethod
    def _get_image(framerate, iso):
        sleep(1)
        cam = camera(framerate, iso)
        try:
            image, ss, ISO = cam.shot()
        finally:
            cam.close()

        # gray scaling
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        print("Convert to graylevel...")
        image = crop(image)

        return image, ss, ISO

    @staticmethod
    def check_necessity():
        print("Check necessity...")
        for i in range(0, 16):
            if os.path.exists(f"./para/tmp/ROI_{i+1}.bmp") is False:
                print(f"File 'ROI_{i+1}.bmp' does no exist!")
                return False
        if os.path.exists("./para/tmp/ROI_of_all.bmp") is False:
            print("File ROI_of_all.bmp does not exist!")
            return False
        if os.path.exists("./para/tmp/coordinates.csv") is False:
            print("File coordinates.csv does not exist!")
            return False
        print("Checking has done!")
        return True

    @staticmethod
    def generate_mask(framerate, iso):
        """

        :return image:
        :return mask
        """
        image, ss, ISO = Calibration._get_image(framerate, iso)

        # binmagarization & processing
        mask = binarize(unsharp(image))
        mask = dilate(erode(mask))
        return image, mask

    @staticmethod
    def get_center_coordinate_of_ROI(mask_of_image):
        """
        it will produce a csv file which contain coordinates of every wells
        :param mask_of_image:
        :return a list of coordinates of wells' center:
        """
        ret, binary = cv2.threshold(mask_of_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, hierachy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        uCon = []
        bCon = []
        radiusList = []

        for i, c in enumerate(contours):
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            perimeter = cv2.arcLength(c, True)
            radius = perimeter / (2 * math.pi)

            if len(radiusList):
                radiusList.append(int(radius))
            else:
                radiusList = [int(radius)]

            if i + 1 <= 8:
                if len(bCon):
                    bCon.append((cY, cX))
                else:
                    bCon = [(cY, cX)]
            else:
                if len(uCon):
                    uCon.append((cY, cX))
                else:
                    uCon = [(cY, cX)]
        uROI = sorted(uCon, key=lambda x: x[1], reverse=False)
        bROI = sorted(bCon, key=lambda x: x[1], reverse=False)
        coordinate_of_wells = uROI + bROI

        # write coordinates to csv file
        write_to_csv('./para/tmp/coordinates.csv', coordinate_of_wells)

        return coordinate_of_wells, min(radiusList)-1

    @staticmethod
    def generate_ROI_pictures(mask):
        """

        :param mask:
        :return:
        """
        coordinate_of_wells, radius = Calibration.get_center_coordinate_of_ROI(mask)
        ROI_of_all = np.zeros(shape=mask.shape, dtype='uint8')
        ROI = [0] * 16
        num_of_pixels = 0
        for i, coor in enumerate(coordinate_of_wells):
            # create corresponding ROI of each wells
            ROI[i] = np.zeros(shape=mask.shape, dtype='uint8')
            # define calculate boundary
            start_point = [coor[0] - radius, coor[1] - radius]
            end_point = [coor[0] + radius, coor[1] + radius]

            for x in range(start_point[1], end_point[1] + 1):
                for y in range(start_point[0], end_point[0] + 1):
                    distance = ((x - coor[1]) ** 2 + (y - coor[0]) ** 2) ** 0.5
                    if distance <= radius and mask[y, x] == 255:
                        ROI[i][y, x] = 255
                        ROI_of_all[y, x] = 255
                        num_of_pixels += 1

            # save ROI_image
            cv2.imwrite(f'./para/tmp/ROI_{i + 1}.bmp', ROI[i])
        cv2.imwrite('./para/tmp/ROI_of_all.bmp', ROI_of_all)
        print("All ROI pictures are saved!")

        return None

    @staticmethod
    def calibrate_for_dye(framerate, iso):
        image, mask = Calibration.generate_mask(framerate, iso)
        Calibration._save_image_without_value('dye', image)
        print("Generate ROI pictures...")
        Calibration.generate_ROI_pictures(mask)
        print("Calculate values...")
        value = Calibration._calculate_average(image)
        Calibration._save_image_with_value('dye', image, value)
        return value

    @staticmethod
    def calibrate_for_water(framerate, iso):
        image, ss, ISO = Calibration._get_image(framerate, iso)
        value = Calibration._calculate_average(image)
        Calibration._save_image_with_value("water", image, value)
        return value
