"""
檢測模塊
執行 qPCR 檢測並記錄結果
"""
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from time import sleep
import cv2
import os

from config import WELL_COUNT, RESULT_DIR, TMP_DIR, ROI_DIR
from logger_config import logger
from camera import camera
from public_method import crop, calculate_average, save_image_with_values, write_detection_data_to_csv


class Detection:
    """檢測類，管理 qPCR 檢測流程"""
    
    @staticmethod
    def get_detect_image(framerate: int, iso: int) -> tuple:
        """
        獲取檢測圖像
        
        Args:
            framerate: 相機幀率
            iso: ISO 值
            
        Returns:
            (灰度圖像, 快門速度, ISO) 元組
        """
        try:
            sleep(1)
            cam = camera(framerate, iso)
            
            try:
                image, ss, ISO = cam.shot()
                logger.info(f"Detection image captured: ss={ss}, ISO={ISO}")
            finally:
                cam.close()
            
            # 轉換為灰度
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug("Converted image to grayscale")
            
            # 裁剪
            image = crop(image)
            logger.debug(f"Cropped image to {image.shape}")
            
            return image, ss, ISO
            
        except Exception as e:
            logger.error(f"Error getting detection image: {e}")
            raise
    
    @staticmethod
    def check_necessity() -> bool:
        """
        檢查檢測所需文件是否存在
        
        Returns:
            True 如果所有必需文件存在
        """
        try:
            # 檢查 ROI 文件
            for i in range(WELL_COUNT):
                roi_file = ROI_DIR / f'ROI_{i+1}.bmp'
                if not roi_file.exists():
                    logger.warning(f"Missing ROI file: {roi_file}")
                    return False
            
            # 檢查合併 ROI
            roi_all_file = ROI_DIR / 'ROI_of_all.bmp'
            if not roi_all_file.exists():
                logger.warning("Missing ROI_of_all.bmp")
                return False
            
            # 檢查坐標文件
            coords_file = TMP_DIR / 'coordinates.csv'
            if not coords_file.exists():
                logger.warning("Missing coordinates file")
                return False
            
            logger.info("All detection prerequisites are met")
            return True
            
        except Exception as e:
            logger.error(f"Error checking detection necessity: {e}")
            return False
    
    @staticmethod
    def detect(
        framerate: int,
        iso: int,
        image_file_name: Optional[str] = None,
        save_folder: Path = RESULT_DIR
    ) -> List[float]:
        """
        執行檢測
        
        Args:
            framerate: 相機幀率
            iso: ISO 值
            image_file_name: 可選的圖像文件名
            save_folder: 保存目錄
            
        Returns:
            16 個井的灰度值列表
        """
        try:
            logger.info("Starting detection...")
            
            # 獲取圖像
            detect_image, ss, ISO = Detection.get_detect_image(framerate, iso)
            
            # 計算平均值
            values = calculate_average(detect_image, ROI_DIR)
            logger.info(f"Detection values calculated: {values}")
            
            # 保存帶標籤的圖像
            if image_file_name is None:
                image_file_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                save_image_with_values(image_file_name, detect_image, values, save_folder)
            except Exception as e:
                logger.warning(f"Failed to save annotated image: {e}")
            
            # 寫入 CSV
            csv_data = values + [ss, ISO]
            write_detection_data_to_csv(csv_data, Path(RESULT_DIR) / "detection.csv")
            
            logger.info("Detection completed successfully")
            return values
            
        except Exception as e:
            logger.error(f"Error in detection: {e}")
            raise
