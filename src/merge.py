"""
圖像合併模塊
將 ROI 掩膜與原始圖像疊加用於可視化
"""
from pathlib import Path
from typing import Dict, List
import cv2
import numpy as np

from config import ROI_DIR, TMP_DIR, MERGE_ALPHA, MERGE_BETA, MERGE_GAMMA, MERGE_THRESHOLD
from logger_config import logger


def _gray2rgb(gray_image: np.ndarray, color_dict: Dict[str, List[int]]) -> np.ndarray:
    """
    將灰度圖像轉換為 RGB，根據像素值上色
    
    Args:
        gray_image: 灰度圖像
        color_dict: 顏色映射字典
        
    Returns:
        RGB 圖像
    """
    try:
        rgb_image = np.zeros((*gray_image.shape, 3), dtype=np.uint8)
        
        for i in range(rgb_image.shape[0]):
            for j in range(rgb_image.shape[1]):
                if gray_image[i, j] < 127:
                    rgb_image[i, j, :] = color_dict.get("black", [0, 0, 0])
                else:
                    rgb_image[i, j, :] = color_dict.get("red", [0, 0, 255])
        
        logger.debug(f"Converted grayscale to RGB: {rgb_image.shape}")
        return rgb_image
        
    except Exception as e:
        logger.error(f"Error in gray2rgb: {e}")
        raise


def add_images() -> None:
    """
    合併兩個圖像：原始圖像 + ROI 掩膜
    使用加權平均方法
    """
    try:
        dye_path = TMP_DIR / 'dye.png'
        roi_image_path = TMP_DIR / 'ROI_image_new.png'
        
        if not dye_path.exists() or not roi_image_path.exists():
            logger.warning(f"Missing input images for merging")
            return
        
        img1 = cv2.imread(str(dye_path))
        src = cv2.imread(str(roi_image_path))
        
        h, w, _ = img1.shape
        img2 = cv2.resize(src, (w, h))
        
        # 加權合併
        merged = cv2.addWeighted(img1, MERGE_ALPHA, img2, MERGE_BETA, MERGE_GAMMA)
        
        output_path = TMP_DIR / 'merged_image.png'
        cv2.imwrite(str(output_path), merged)
        
        logger.info(f"Images merged successfully: {output_path}")
        
    except Exception as e:
        logger.error(f"Error adding images: {e}")
        raise


def merge() -> None:
    """
    執行完整的圖像合併流程
    1. 讀取 ROI 掩膜
    2. 二值化
    3. 轉換為 RGB
    4. 與原始圖像合併
    """
    try:
        logger.info("Starting image merge process...")
        
        # 讀取 ROI 掩膜
        roi_all_path = TMP_DIR / 'ROI_of_all.bmp'
        if not roi_all_path.exists():
            logger.warning(f"ROI_of_all.bmp not found at {roi_all_path}")
            return
        
        roi_all = cv2.imread(str(roi_all_path), cv2.IMREAD_GRAYSCALE)
        
        # 二值化
        ret, th2 = cv2.threshold(roi_all, MERGE_THRESHOLD, 255, cv2.THRESH_BINARY)
        logger.debug(f"Applied threshold: {MERGE_THRESHOLD}")
        
        # 定義顏色
        color_dict = {
            "black": [0, 0, 0],
            "red": [0, 0, 255]
        }
        
        # 轉換為 RGB
        img_new = _gray2rgb(th2, color_dict)
        
        roi_image_new_path = TMP_DIR / 'ROI_image_new.png'
        cv2.imwrite(str(roi_image_new_path), img_new)
        logger.debug(f"Saved ROI image: {roi_image_new_path}")
        
        # 合併圖像
        add_images()
        
        logger.info("Image merge process completed")
        
    except Exception as e:
        logger.error(f"Error in merge process: {e}")
        raise
