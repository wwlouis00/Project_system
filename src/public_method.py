"""
公共方法模塊
提供圖像處理、CSV I/O、初始化等通用功能
"""
from typing import List, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
import numpy as np
import cv2
import csv
import os

from config import (
    WELL_COUNT, PARA_DIR, ROI_DIR, TMP_DIR, RESULT_DIR,
    CAMERA_WIDTH, CAMERA_HEIGHT, CSV_DATETIME_FORMAT, CSV_FIELDS,
    HISTOGRAM_BINS, HISTOGRAM_RANGE
)
from logger_config import logger


def initialize() -> None:
    """
    初始化系統目錄結構
    建立必需的所有目錄
    """
    directories = [PARA_DIR, ROI_DIR, TMP_DIR, RESULT_DIR]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory initialized: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise


def create_image_windows() -> None:
    """
    創建空白 OpenCV 窗口用於顯示
    
    Note:
        此功能已廢棄，保留用於向後兼容性
    """
    logger.warning("create_image_windows() is deprecated")
    zeros = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH), dtype='uint8')
    cv2.imshow('image', zeros)


def calculate_average(image: np.ndarray, roi_dir: Path = ROI_DIR) -> List[float]:
    """
    計算每個井的平均灰度值
    統一的計算函數，取代 calibration.py 和 public_method.py 的重複定義
    
    Args:
        image: 灰度圖像 (ndarray)
        roi_dir: ROI 文件目錄
        
    Returns:
        16 個井的平均值列表
        
    Raises:
        FileNotFoundError: 如果 ROI 文件不存在
    """
    averages: List[float] = []
    
    try:
        for i in range(WELL_COUNT):
            roi_file = roi_dir / f'ROI_{i+1}.bmp'
            
            if not roi_file.exists():
                logger.warning(f"ROI file not found: {roi_file}")
                averages.append(0)
                continue
            
            roi_mask = cv2.imread(str(roi_file), cv2.IMREAD_GRAYSCALE)
            
            # 計算直方圖
            hist = cv2.calcHist(
                [image], [0], roi_mask,
                histSize=[HISTOGRAM_BINS],
                ranges=HISTOGRAM_RANGE
            )
            
            # 計算加權平均
            total_val = 0.0
            pixel_count = 0
            
            for intensity, count in enumerate(hist):
                count_val = int(count[0])
                total_val += intensity * count_val
                pixel_count += count_val
            
            average = int(total_val / pixel_count) if pixel_count > 0 else 0
            averages.append(average)
            
        logger.debug(f"Calculated averages for all wells: {averages}")
        return averages
    except Exception as e:
        logger.error(f"Error calculating average: {e}")
        raise
        


def calculate_average_mode(image: np.ndarray, roi_dir: Path = ROI_DIR) -> List[float]:
    """
    計算每個井的眾數（加權）
    
    Args:
        image: 灰度圖像
        roi_dir: ROI 文件目錄
        
    Returns:
        16 個井的加權眾數列表
    """
    modes: List[float] = []
    
    try:
        for i in range(WELL_COUNT):
            roi_file = roi_dir / f'ROI_{i+1}.bmp'
            
            if not roi_file.exists():
                logger.warning(f"ROI file not found: {roi_file}")
                modes.append(0)
                continue
            
            roi_mask = cv2.imread(str(roi_file), cv2.IMREAD_GRAYSCALE)
            
            hist = cv2.calcHist(
                [image], [0], roi_mask,
                histSize=[HISTOGRAM_BINS],
                ranges=HISTOGRAM_RANGE
            )
            
            # 找出前 5 個最大值
            hist_flat = hist.flatten()
            hist_sorted = np.sort(hist_flat)[::-1]
            
            if hist_sorted[1] <= 3:  # 井中沒有東西
                modes.append(0)
                continue
            
            # 找出對應的灰度值和計數
            peaks = []
            for j in range(min(5, len(hist_sorted))):
                threshold = hist_sorted[j]
                for intensity, count in enumerate(hist):
                    if count[0] == threshold:
                        peaks.append((intensity, int(count[0])))
                        break
            
            # 計算加權平均
            if peaks:
                weighted_sum = sum(intensity * count for intensity, count in peaks)
                total_count = sum(count for _, count in peaks)
                mode = int(weighted_sum / total_count)
                modes.append(mode)
            else:
                modes.append(0)
        
        logger.debug(f"Calculated modes for all wells")
        return modes
        
    except Exception as e:
        logger.error(f"Error calculating mode: {e}")
        raise


def save_image_with_values(
    image_name: str,
    image: np.ndarray,
    values: List[float],
    save_folder: Path = RESULT_DIR
) -> None:
    """
    保存帶有文字標籤的圖像
    
    Args:
        image_name: 圖像基礎名稱
        image: 待保存的圖像
        values: 每個井的數值列表
        save_folder: 保存目錄
    """
    try:
        save_folder = Path(save_folder)
        save_folder.mkdir(parents=True, exist_ok=True)
        
        roi_all_file = ROI_DIR / 'ROI_of_all.bmp'
        if not roi_all_file.exists():
            logger.warning(f"ROI mask not found: {roi_all_file}")
            return
        
        mask = cv2.imread(str(roi_all_file), cv2.IMREAD_GRAYSCALE)
        image_masked = cv2.bitwise_and(image, image, mask=mask)
        
        # 讀取坐標
        coordinates = read_coordinates()
        
        # 在圖像上添加文字
        for i, coord in enumerate(coordinates):
            if i < len(values):
                cv2.putText(
                    image_masked,
                    str(int(values[i])),
                    (coord[1], coord[0] - 10),
                    cv2.FONT_HERSHEY_TRIPLEX,
                    0.5,
                    (66, 211, 249),
                    1,
                    cv2.LINE_AA
                )
        
        output_path = save_folder / f'{image_name}_with_value.png'
        cv2.imwrite(str(output_path), image_masked)
        logger.info(f"Saved annotated image: {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving annotated image: {e}")
        raise


# 向後兼容性別名
def save_image_with_value(image_name: str, image: np.ndarray, value: List[float], save_folder: str = './result') -> None:
    """向後兼容性包裝"""
    save_image_with_values(image_name, image, value, Path(save_folder))


def save_image_without_value(image_name: str, image: np.ndarray, save_folder: str = './result') -> None:
    """
    保存原始圖像
    
    Args:
        image_name: 圖像基礎名稱
        image: 待保存的圖像
        save_folder: 保存目錄
    """
    try:
        save_folder = Path(save_folder)
        save_folder.mkdir(parents=True, exist_ok=True)
        
        output_path = save_folder / f'{image_name}.png'
        cv2.imwrite(str(output_path), image)
        logger.info(f"Saved image: {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise


def write_coordinates_to_csv(
    coordinates: List[Tuple[int, int]],
    filepath: Path = TMP_DIR / 'coordinates.csv'
) -> None:
    """
    保存井坐標到 CSV 文件
    
    Args:
        coordinates: 坐標列表
        filepath: 保存路徑
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # 寫入頭行
            headers = [f'well{i+1}' for i in range(WELL_COUNT)]
            writer.writerow(headers)
            # 寫入數據行
            writer.writerow(coordinates)
        
        logger.info(f"Saved coordinates to: {filepath}")
        
    except Exception as e:
        logger.error(f"Error writing coordinates: {e}")
        raise


def read_coordinates(filepath: Path = TMP_DIR / 'coordinates.csv') -> List[Tuple[int, int]]:
    """
    從 CSV 文件讀取井坐標
    
    Args:
        filepath: 坐標文件路徑
        
    Returns:
        坐標列表
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Coordinates file not found: {filepath}")
            return []
        
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # 跳過頭行
            data_row = next(reader)
            
            # 解析坐標字符串
            coordinates = []
            for coord_str in data_row:
                # 移除括號並解析
                coord_str = coord_str.strip('()')
                y, x = map(int, coord_str.split(', '))
                coordinates.append((y, x))
            
            logger.debug(f"Read {len(coordinates)} coordinates")
            return coordinates
            
    except Exception as e:
        logger.error(f"Error reading coordinates: {e}")
        return []


def write_to_csv(filename: str, data: List[float]) -> None:
    """
    將數據寫入 CSV（向後兼容性包裝）
    
    Args:
        filename: 文件名
        data: 數據列表
    """
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if 'coordinate' in filename:
            write_coordinates_to_csv(data, filepath)
        elif 'detection' in filename or 'calibration' in filename:
            write_detection_data_to_csv(data, filepath)
        else:
            logger.warning(f"Unknown CSV type: {filename}")
    except Exception as e:
        logger.error(f"Error writing CSV: {e}")
        raise


def write_detection_data_to_csv(
    data: List[float],
    filepath: Path = RESULT_DIR / 'detection.csv'
) -> None:
    """
    將檢測數據寫入 CSV
    
    Args:
        data: 包含 16 個井值 + shutter_speed + ISO 的數據列表
        filepath: 保存路徑
    """
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            
            # 如果文件為空，寫入頭行
            if filepath.stat().st_size == 0:
                writer.writeheader()
            
            # 構建數據字典
            row_data = {
                'time': datetime.now().strftime(CSV_DATETIME_FORMAT),
            }
            
            for i in range(WELL_COUNT):
                row_data[f'well{i+1}'] = data[i] if i < len(data) else 0
            
            if len(data) > WELL_COUNT:
                row_data['shutter_speed'] = data[WELL_COUNT]
                row_data['ISO'] = data[WELL_COUNT + 1]
            
            writer.writerow(row_data)
        
        logger.debug(f"Wrote detection data to: {filepath}")
        
    except Exception as e:
        logger.error(f"Error writing detection data: {e}")
        raise


def read_from_csv(filename: str) -> List[str]:
    """
    從 CSV 文件讀取數據
    
    Args:
        filename: 文件路徑
        
    Returns:
        數據行列表
    """
    try:
        data = []
        filepath = Path(filename)
        
        if not filepath.exists():
            logger.warning(f"CSV file not found: {filepath}")
            return data
        
        with open(filepath) as f:
            reader = csv.reader(f, delimiter=',')
            next(reader)  # 跳過頭行
            for row in reader:
                data = row
        
        return data
        
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return []


def str_to_list(string: str) -> List[int]:
    """
    將字符串表示的列表轉換為實際列表
    
    Args:
        string: 格式如 '(y, x)' 的字符串
        
    Returns:
        整數列表
    """
    try:
        string = string.strip('()')
        res = list(map(int, string.split(', ')))
        return list(reversed(res))
    except Exception as e:
        logger.error(f"Error parsing coordinate string: {e}")
        return []


def crop(image: np.ndarray) -> np.ndarray:
    """
    裁剪圖像中心部分
    移除邊界以減少噪聲
    
    Args:
        image: 原始圖像
        
    Returns:
        裁剪後的圖像
    """
    try:
        crop_offset = (int(image.shape[0] / 6), int(image.shape[1] / 6))
        crop_size = (int(2 * image.shape[0] / 3), int(2 * image.shape[1] / 3))
        
        cropped = image[
            crop_offset[0] : crop_offset[0] + crop_size[0],
            crop_offset[1] : crop_offset[1] + crop_size[1]
        ]
        
        logger.debug(f"Cropped image from {image.shape} to {cropped.shape}")
        return cropped
        
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        raise


