from camera import camera
from datetime import datetime
import numpy as np
import cv2
import csv
import os


def initialize():
    if not os.path.isdir('./para'):
        print("Directory 'para' does not exist.")
        os.mkdir('./para')
        print("Directory 'para' is established.")
    if not os.path.isdir('./para/ROIs'):
        print("Directory './para/ROIs' does not exist.")
        os.mkdir('./para/ROIs')
        print("Directory './para/ROIs' is established.")
    if not os.path.isdir('./para/tmp'):
        print("Directory './para/tmp' does not exist.")
        os.mkdir('./para/tmp')
        print("Directory './para/tmp' is established.")
    if not os.path.isdir('./result'):
        print("Directory 'result' does not exist.")
        os.mkdir('./result')
        print("Directory 'result' is established.")


def create_image_windows():
    zeros = np.zeros((camera.height, camera.width), dtype='uint8')
    cv2.imshow('image', zeros)
    return None


def calculate_average_mode(image):
    """

    :param image:
    :return:
    """
    mode = [0] * 16
    ROI_of_each_well = np.zeros((camera.height, camera.width), dtype='uint8')

    for i in range(0, 16):
        ROI_of_each_well = cv2.imread(f'./para/ROIs/ROI_{i+1}.bmp', 0)
        hist = cv2.calcHist([image], [0], mask=ROI_of_each_well, histSize=[256], ranges=[0, 256])
        # find out the three largest numbers
        hist_sorted = np.sort(hist, axis=0)
        if hist_sorted[-2] <= 3: # the well has nothing
            mode[i] = 0
        else:
            for j in range(0, 256):
                if hist[j] == hist_sorted[-1]:
                    num_one = j
                    count_one = hist[j]
                if hist[j] == hist_sorted[-2]:
                    num_two = j
                    count_two = hist[j]
                if hist[j] == hist_sorted[-3]:
                    num_three = j
                    count_three = hist[j]
                if hist[j] == hist_sorted[-4]:
                    num_four = j
                    count_four = hist[j]
                if hist[j] == hist_sorted[-5]:
                    num_five = j
                    count_five = hist[j]
            # get weighted-average mode
            mode[i] = int((num_one*count_one + num_two*count_two + num_three*count_three + num_four*count_four + num_five*count_five)/(count_one+count_two+count_three+count_four+count_five))
    return mode


def calculate_average(image):
    averages = [0] * 16
    ROI_of_each_well = np.zeros(image.shape, dtype='uint8')

    for i in range(0, 16):
        ROI_of_each_well = cv2.imread(f'./para/ROIs/ROI_{i+1}.bmp', 0)
        hist = cv2.calcHist([image], [0], mask=ROI_of_each_well, histSize=[256], ranges=[0, 256])
        # find out the average of each well
        total_val = 0
        pixel_num = 0
        for val, count in enumerate(hist):
            total_val += val*count
            pixel_num += count
        averages[i] = int(total_val/pixel_num)
    return averages


def save_image_with_value(image_name, image, value, save_folder='./result'):
    """
    get 'mask_of_all' & 'coordinates_of_wells' from folder
    :param image_name:
    :param value:
    :param image:
    :return None:
    """
    mask = cv2.imread('./para/ROIs/ROI_of_all.bmp', 0)
    image_masked = cv2.bitwise_and(image, image, mask)
    coordinates = read_from_csv('./para/ROIs/coordinates.csv')
    for i in range(0, 16):
        coordinates[i] = str_to_list(coordinates[i])
        cv2.putText(image_masked, str(value[i]), (coordinates[i][0], coordinates[i][1] - 10),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.5, (66, 211, 249), 1, cv2.LINE_AA)
    cv2.imwrite(f'{save_folder}/{image_name}_with_value.png', image_masked)
    print("Save image.")
    return None


def save_image_without_value(image_name, image, save_folder='./result'):
    """
    get 'mask_of_all' & 'coordinates_of_wells' from folder
    :param image_name:
    :param value:
    :param image:
    :return None:
    """
    cv2.imwrite(f'{save_folder}/{image_name}.png', image)
    print("Save image.")
    return None


def write_to_csv(filename, data):
    """

    :param filename:
    :param data: data should be list
    :return None:
    """
    if 'coordinate' in filename:
        with open(filename, mode='w') as csv_file:
            csv_file_writer = csv.writer(csv_file, delimiter=',')
            csv_file_writer.writerow(['well1', 'well2', 'well3', 'well4', 'well5', 'well6', 'well7', 'well8',
                                      'well9', 'well10', 'well11', 'well12', 'well13', 'well14', 'well15', 'well16'])
            csv_file_writer.writerow(data)

    elif 'detection' in filename or 'calibration' in filename:
        with open(filename, mode='a') as csv_file:
            fields = ['time', 'well1', 'well2', 'well3', 'well4', 'well5', 'well6', 'well7', 'well8', 'well9', 'well10', 'well11', 'well12', 'well13', 'well14', 'well15', 'well16', 'shutter_speed', 'ISO']
            dictWriter = csv.DictWriter(csv_file, fieldnames=fields)
            if os.path.getsize(filename) == 0:
                dictWriter.writeheader()
            dictdata = {'time':datetime.now().strftime("%H:%M:%S"), 'well1':data[0], 'well2':data[1], 'well3':data[2], 'well4':data[3], 'well5':data[4], 'well6':data[5], 'well7':data[6], 'well8':  data[7], 'well9':data[8], 'well10':data[9], 'well11':data[10], 'well12':data[11], 'well13':data[12], 'well14':data[13], 'well15':data[14], 'well16':data[15], 'shutter_speed':data[16], 'ISO':data[17]}
            dictWriter.writerow(dictdata)
    return None


def read_from_csv(filename):
    """

    :param filename:
    :return data which is dictionary:
    """
    data = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                data = row
    return data


def str_to_list(string):
    string = string[1:]
    string = string[:-1]
    res = list(map(int, string.split(', ')))
    res = res[::-1]
    return res

def crop(image):
    crop_point = (int(image.shape[0] / 6), int(image.shape[1] / 6))
    crop_height = int(2 * image.shape[0] / 3)
    crop_width = int(2 * image.shape[1] / 3)
    image_crop = image[crop_point[0]:crop_point[0] + crop_height, crop_point[1]:crop_point[1] + crop_width]
    return image_crop

