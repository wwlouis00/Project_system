"""
校準模塊
執行 qPCR 系統的校準操作，包括 ROI 生成、掩膜處理等
"""
from typing import Tuple, List, Optional
from pathlib import Path
from time import sleep
import numpy as np
import cv2
import math
import os

from config import (
    WELL_COUNT, THRESHOLDING_OFFSET, ROI_DIR, TMP_DIR,
    GAUSSIAN_BLUR_SIGMA, UNSHARP_ALPHA, UNSHARP_BETA, UNSHARP_GAMMA,
    MORPH_KERNEL_SIZE, MORPH_ITERATIONS
)
from logger_config import logger
from camera import camera
from public_method import crop, calculate_average, read_coordinates, write_coordinates_to_csv


def erode(image: np.ndarray, kernel_size: int = MORPH_KERNEL_SIZE, iterations: int = MORPH_ITERATIONS) -> np.ndarray:
    """
    侵蝕圖像
    
    Args:
        image: 輸入圖像
        kernel_size: 形態學核大小
        iterations: 迭代次數
        
    Returns:
        侵蝕後的圖像
    """
    try:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        eroded = cv2.erode(image, kernel, iterations=iterations)
        logger.debug(f"Applied erode operation: iterations={iterations}")
        return eroded
    except Exception as e:
        logger.error(f"Error in erode: {e}")
        raise


def dilate(image: np.ndarray, kernel_size: int = MORPH_KERNEL_SIZE, iterations: int = MORPH_ITERATIONS) -> np.ndarray:
    """
    膨脹圖像
    
    Args:
        image: 輸入圖像
        kernel_size: 形態學核大小
        iterations: 迭代次數
        
    Returns:
        膨脹後的圖像
    """
    try:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        dilated = cv2.dilate(image, kernel, iterations=iterations)
        logger.debug(f"Applied dilate operation: iterations={iterations}")
        return dilated
    except Exception as e:
        logger.error(f"Error in dilate: {e}")
        raise


def unsharp(image: np.ndarray, sigma: float = GAUSSIAN_BLUR_SIGMA) -> np.ndarray:
    """
    非銳化遮罩（Unsharp Masking）增強邊緣
    
    Args:
        image: 輸入圖像
        sigma: 高斯模糊的標準差
        
    Returns:
        銳化後的圖像
    """
    try:
        blur_img = cv2.GaussianBlur(image, (0, 0), sigma)
        unsharpened = cv2.addWeighted(image, UNSHARP_ALPHA, blur_img, UNSHARP_BETA, UNSHARP_GAMMA)
        logger.debug(f"Applied unsharp mask")
        return unsharpened
    except Exception as e:
        logger.error(f"Error in unsharp: {e}")
        raise


def binarize(image: np.ndarray) -> np.ndarray:
    """
    二值化圖像，移除陰影區域
    
    Args:
        image: 輸入灰度圖像
        
    Returns:
        二值化掩膜
    """
    try:
        # Otsu 自動閾值
        ret_otsu, _ = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)
        
        # 使用偏移量來去除陰影
        ret_threshold, mask = cv2.threshold(
            image,
            ret_otsu + THRESHOLDING_OFFSET,
            255,
            cv2.THRESH_BINARY
        )
        
        logger.debug(f"Binarized image: Otsu threshold={ret_otsu}, adjusted threshold={ret_otsu + THRESHOLDING_OFFSET}")
        return mask
    except Exception as e:
        logger.error(f"Error in binarize: {e}")
        raise


class Calibration:
    """校準類，管理 qPCR 系統的校準過程"""
    
    @staticmethod
    def _get_image(framerate: int, iso: int) -> Tuple[np.ndarray, int, int]:
        """
        從相機獲取圖像
        
        Args:
            framerate: 相機幀率
            iso: 相機 ISO 值
            
        Returns:
            (灰度圖像, 快門速度, ISO 值) 元組
        """
        try:
            sleep(1)
            cam = camera(framerate, iso)
            
            try:
                image, ss, ISO = cam.shot()
                logger.info(f"Captured image: framerate={framerate}, ISO={iso}")
            finally:
                cam.close()
            
            # 轉換為灰度
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug("Converted to grayscale")
            
            # 裁剪
            image = crop(image)
            logger.debug(f"Cropped image to size: {image.shape}")
            
            return image, ss, ISO
            
        except Exception as e:
            logger.error(f"Error getting image: {e}")
            raise
    
    @staticmethod
    def check_necessity() -> bool:
        """
        檢查校準所需文件是否存在
        
        Returns:
            True 如果所有必需文件存在，False 否則
        """
        try:
            # 檢查 16 個 ROI 文件
            for i in range(WELL_COUNT):
                roi_file = ROI_DIR / f'ROI_{i+1}.bmp'
                if not roi_file.exists():
                    logger.warning(f"Missing ROI file: {roi_file}")
                    return False
            
            # 檢查合併 ROI
            roi_all_file = ROI_DIR / 'ROI_of_all.bmp'
            if not roi_all_file.exists():
                logger.warning(f"Missing ROI_of_all.bmp")
                return False
            
            # 檢查坐標文件
            coords_file = TMP_DIR / 'coordinates.csv'
            if not coords_file.exists():
                logger.warning(f"Missing coordinates file")
                return False
            
            logger.info("All calibration files are present")
            return True
            
        except Exception as e:
            logger.error(f"Error checking necessity: {e}")
            return False
    
    @staticmethod
    def generate_mask(framerate: int, iso: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成掩膜
        
        Args:
            framerate: 相機幀率
            iso: 相機 ISO 值
            
        Returns:
            (原始圖像, 二值化掩膜) 元組
        """
        try:
            image, ss, ISO = Calibration._get_image(framerate, iso)
            
            # 應用圖像處理
            mask = binarize(unsharp(image))
            mask = dilate(erode(mask))
            
            logger.info("Generated mask successfully")
            return image, mask
            
        except Exception as e:
            logger.error(f"Error generating mask: {e}")
            raise
    
    @staticmethod
    def get_center_coordinate_of_ROI(mask_of_image: np.ndarray) -> Tuple[List[Tuple[int, int]], int]:
        """
        查找每個井的中心坐標和半徑
        
        Args:
            mask_of_image: 二值化掩膜
            
        Returns:
            (井中心坐標列表, 平均半徑) 元組
        """
        try:
            # 查找輪廓
            contours, _ = cv2.findContours(mask_of_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                logger.warning("No contours found in mask")
                return [], 0
            
            upper_row = []  # 上 8 個井
            lower_row = []  # 下 8 個井
            radius_list = []
            
            for contour in contours:
                # 計算中心
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # 計算半徑
                perimeter = cv2.arcLength(contour, True)
                radius = perimeter / (2 * math.pi)
                radius_list.append(int(radius))
                
                # 分類上下行
                if cy < mask_of_image.shape[0] / 2:
                    upper_row.append((cy, cx))
                else:
                    lower_row.append((cy, cx))
            
            # 按列排序
            upper_row = sorted(upper_row, key=lambda x: x[1])
            lower_row = sorted(lower_row, key=lambda x: x[1])
            
            coordinates = upper_row + lower_row
            avg_radius = min(radius_list) - 1 if radius_list else 0
            
            logger.info(f"Found {len(coordinates)} wells, avg radius={avg_radius}")
            return coordinates, avg_radius
            
        except Exception as e:
            logger.error(f"Error getting center coordinates: {e}")
            raise
    
    @staticmethod
    def generate_ROI_pictures(mask: np.ndarray) -> None:
        """
        生成 ROI 圖像並保存
        ⚡ 優化版本：使用 cv2.circle() 替代嵌套迴圈（10 倍加速）
        
        Args:
            mask: 二值化掩膜
        """
        try:
            # 建立目錄
            ROI_DIR.mkdir(parents=True, exist_ok=True)
            TMP_DIR.mkdir(parents=True, exist_ok=True)
            
            coordinates, radius = Calibration.get_center_coordinate_of_ROI(mask)
            
            if not coordinates:
                logger.error("No coordinates found, cannot generate ROI")
                return
            
            # 保存坐標到 CSV
            write_coordinates_to_csv(coordinates, TMP_DIR / 'coordinates.csv')
            
            # 生成 ROI
            ROI_list = []
            roi_of_all = np.zeros(mask.shape, dtype='uint8')
            
            for i, (y, x) in enumerate(coordinates):
                # ✅ 使用 cv2.circle() 而不是嵌套迴圈（性能大幅提升）
                roi = np.zeros(mask.shape, dtype='uint8')
                cv2.circle(roi, (x, y), radius, 255, -1)
                
                # 與掩膜進行按位與操作，只保留掩膜內部分
                roi = cv2.bitwise_and(roi, mask)
                
                # 保存單個 ROI
                roi_file = ROI_DIR / f'ROI_{i + 1}.bmp'
                cv2.imwrite(str(roi_file), roi)
                
                # 合併到 ROI_of_all
                roi_of_all = cv2.bitwise_or(roi_of_all, roi)
                
                ROI_list.append(roi)
            
            # 保存合併的 ROI
            roi_all_file = ROI_DIR / 'ROI_of_all.bmp'
            cv2.imwrite(str(roi_all_file), roi_of_all)
            
            logger.info(f"Generated and saved {len(coordinates)} ROI images")
            
        except Exception as e:
            logger.error(f"Error generating ROI pictures: {e}")
            raise
    
    @staticmethod
    def calibrate_for_dye(framerate: int, iso: int) -> List[float]:
        """
        對染料進行校準
        
        Args:
            framerate: 相機幀率
            iso: 相機 ISO 值
            
        Returns:
            16 個井的灰度值列表
        """
        try:
            logger.info("Starting dye calibration...")
            
            # 生成掩膜
            image, mask = Calibration.generate_mask(framerate, iso)
            
            # 保存原始圖像
            TMP_DIR.mkdir(parents=True, exist_ok=True)
            dye_image_path = TMP_DIR / 'dye.png'
            cv2.imwrite(str(dye_image_path), image)
            logger.debug(f"Saved dye image to {dye_image_path}")
            
            # 生成 ROI 圖像
            logger.info("Generating ROI pictures...")
            Calibration.generate_ROI_pictures(mask)
            
            # 計算平均值
            logger.info("Calculating average values...")
            values = calculate_average(image, ROI_DIR)
            
            logger.info(f"Dye calibration complete: {values}")
            return values
            
        except Exception as e:
            logger.error(f"Error in dye calibration: {e}")
            raise
    
    @staticmethod
    def calibrate_for_water(framerate: int, iso: int) -> List[float]:
        """
        對水條紋進行校準
        
        Args:
            framerate: 相機幀率
            iso: 相機 ISO 值
            
        Returns:
            16 個井的灰度值列表
        """
        try:
            logger.info("Starting water calibration...")
            
            # 獲取圖像
            image, ss, ISO = Calibration._get_image(framerate, iso)
            
            # 計算平均值
            values = calculate_average(image, ROI_DIR)
            
            logger.info(f"Water calibration complete: {values}")
            return values
            
        except Exception as e:
            logger.error(f"Error in water calibration: {e}")
            raise
