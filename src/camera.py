"""
相機控制模塊
管理 Raspberry Pi 相機的初始化和拍攝
"""
from picamera import PiCamera
from time import sleep
from typing import Tuple
import numpy as np
import cv2

from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_SENSOR_MODE,
    CAMERA_AWB_MODE, CAMERA_DRC_STRENGTH, CAMERA_VFLIP,
    CAMERA_HFLIP, CAMERA_WARMUP_TIME
)
from logger_config import logger


class camera(PiCamera):
    """Raspberry Pi 相機控制類"""
    
    width = CAMERA_WIDTH
    height = CAMERA_HEIGHT
    
    def __init__(self, framerate: int, iso: int):
        """
        初始化相機
        
        Args:
            framerate: 幀率（快門速度 = 1/framerate）
            iso: ISO 值
        """
        try:
            super().__init__()
            
            self.resolution = (self.width, self.height)
            self.framerate = framerate
            self.sensor_mode = CAMERA_SENSOR_MODE
            self.shutter_speed = int((1 / framerate) * (10 ** 6))  # 微秒
            self.iso = iso
            self.awb_mode = CAMERA_AWB_MODE
            self.drc_strength = CAMERA_DRC_STRENGTH
            self.led = False
            self.vflip = CAMERA_VFLIP
            self.hflip = CAMERA_HFLIP
            
            logger.info(f"Camera initialized: framerate={framerate}, iso={iso}, "
                       f"shutter_speed={self.shutter_speed}μs")
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            raise
    
    def shot(self) -> Tuple[np.ndarray, int, int]:
        """
        拍攝圖像
        
        Returns:
            (RGB 圖像, 快門速度, ISO) 元組
            
        Raises:
            Exception: 如果拍攝失敗
        """
        try:
            logger.debug(f"Taking shot: framerate={self.framerate}, "
                        f"shutter_speed={self.shutter_speed}μs, ISO={self.iso}")
            
            # 預熱
            sleep(CAMERA_WARMUP_TIME)
            
            # 關閉自動曝光
            self.exposure_mode = 'off'
            
            # 拍攝圖像
            image_data = np.zeros((self.height * self.width * 3), dtype=np.uint8)
            self.capture(image_data, 'bgr')
            
            # 重塑為圖像格式
            image = image_data.astype('uint8').reshape((self.height, self.width, 3))
            
            logger.info(f"Shot taken successfully: size={image.shape}")
            return image, self.shutter_speed, self.iso
            
        except Exception as e:
            logger.error(f"Error taking shot: {e}")
            raise
