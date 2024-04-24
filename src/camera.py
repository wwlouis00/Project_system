from picamera import PiCamera
from time import sleep
import numpy as np
import cv2
class camera(PiCamera):
    width = 800
    height = 480

    def __init__(self, framerate, iso):
        super().__init__()
        self.resolution = (self.width, self.height)
        self.framerate = framerate # shutter speed = 1/framerate, the higher framerate is, the faster shutter speed will be
        self.sensor_mode = 3
        self.shutter_speed = int((1/self.framerate) * (10 ** 6))  # microseconds, 0 means auto
        self.iso = iso
        # self.exposure_mode =  'off'
        # g = self.awb_gains
        self.awb_mode = 'incandescent'
        # self.awb_gains = g
        self.drc_strength = 'off'
        self.led = False
        self.vflip = False
        self.hflip = True

    def shot(self):
        print("Shot...")
        print(f"Framerate: {self.framerate}")
        print(f"Shutter_speed: {self.shutter_speed}")
        print(f"ISO: {self.iso}")
        sleep(5)
        self.exposure_mode =  'off'
        image = np.zeros((self.height * self.width * 3), dtype=np.uint8)
        self.capture(image, 'bgr')
        image = image.astype('uint8')
        image = image.reshape((self.height, self.width, 3))
        print("Shoted!")
        return image, self.shutter_speed, self.iso
