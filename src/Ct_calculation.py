"""
Ct 值計算模塊
計算定量 PCR 的 Ct 值
"""
import pandas as pd
from pathlib import Path
from typing import List, Tuple
import os

from config import (
    DEFAULT_CT_THRESHOLD, CT_THRESHOLD_MULTIPLIER,
    CT_MAX_VALUE, CT_UNAVAILABLE_VALUE, MOVING_AVERAGE_WINDOW,
    RESULT_DIR, CSV_DATETIME_FORMAT, WELL_COUNT
)
from logger_config import logger


class CtCalculator:
    """Ct 值計算器 - 消除全局變數，使用類封裝"""
    
    def __init__(self, raw_file_path: str = None):
        """
        初始化計算器
        
        Args:
            raw_file_path: 原始檢測 CSV 文件路徑
        """
        if raw_file_path is None:
            raw_file_path = str(RESULT_DIR / "detection.csv")
        
        self.raw_file_path = raw_file_path
        self.df_raw = None
        self.df_normalization = None
        self.ct_values = []
        
        logger.info(f"CtCalculator initialized with file: {raw_file_path}")
    
    def _load_data(self) -> bool:
        """
        讀取原始 CSV 文件
        
        Returns:
            成功讀取返回 True
        """
        try:
            if not os.path.exists(self.raw_file_path):
                logger.error(f"File not found: {self.raw_file_path}")
                return False
            
            self.df_raw = pd.read_csv(self.raw_file_path)
            self.df_normalization = self.df_raw.copy()
            
            logger.info(f"Loaded data from {self.raw_file_path}: {self.df_raw.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def _add_accumulation_time(self) -> None:
        """
        添加累積時間列
        將時間戳轉換為分鐘
        """
        try:
            if 'time' not in self.df_normalization.columns:
                logger.warning("No 'time' column found")
                return
            
            df_time = self.df_normalization['time']
            from datetime import datetime
            
            time_ori = datetime.strptime(df_time.iloc[0], CSV_DATETIME_FORMAT)
            time_delta = []
            
            for time_str in df_time:
                time_now = datetime.strptime(time_str, CSV_DATETIME_FORMAT)
                delta_minutes = (time_now - time_ori).total_seconds() / 60
                time_delta.append(delta_minutes)
            
            self.df_normalization.insert(1, 'accumulation', time_delta)
            logger.debug(f"Added accumulation time column")
            
        except Exception as e:
            logger.error(f"Error adding accumulation time: {e}")
    
    def _normalize(self, baseline_begin: int, baseline_end: int) -> None:
        """
        標準化數據：(IF(t) - IF(b)) / IF(b)
        
        Args:
            baseline_begin: 基線起始索引
            baseline_end: 基線終止索引
        """
        try:
            for i in range(WELL_COUNT):
                well_name = f'well{i+1}'
                
                if well_name not in self.df_normalization.columns:
                    continue
                
                # 計算基線平均值
                baseline_values = self.df_raw[well_name].iloc[baseline_begin:baseline_end+2]
                baseline_avg = baseline_values.mean()
                
                if baseline_avg == 0:
                    logger.warning(f"Baseline average is 0 for {well_name}")
                    continue
                
                # 標準化
                self.df_normalization[well_name] = (
                    (self.df_raw[well_name] - baseline_avg) / baseline_avg
                )
            
            logger.debug("Data normalization completed")
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise
    
    def _get_ct_threshold(self, baseline_begin: int, baseline_end: int) -> List[float]:
        """
        計算 Ct 閾值
        
        Args:
            baseline_begin: 基線起始索引
            baseline_end: 基線終止索引
            
        Returns:
            16 個井的閾值列表
        """
        try:
            threshold_values = []
            
            for i in range(WELL_COUNT):
                well_name = f'well{i+1}'
                
                if well_name not in self.df_normalization.columns:
                    threshold_values.append(DEFAULT_CT_THRESHOLD)
                    continue
                
                baseline_data = self.df_normalization[well_name].iloc[baseline_begin:baseline_end+2]
                std_dev = baseline_data.std()
                avg = baseline_data.mean()
                
                logger.debug(f"{well_name}: StdDev={std_dev:.4f}, Avg={avg:.4f}")
                
                # 如果標準差為 0，使用默認閾值
                if std_dev == 0:
                    threshold = DEFAULT_CT_THRESHOLD
                    logger.warning(f"{well_name}: Using default threshold")
                else:
                    threshold = CT_THRESHOLD_MULTIPLIER * std_dev + avg
                
                threshold_values.append(threshold)
                logger.debug(f"{well_name}: Threshold={threshold:.4f}")
            
            return threshold_values
            
        except Exception as e:
            logger.error(f"Error calculating threshold: {e}")
            raise
    
    def _get_ct_values(self, threshold_values: List[float], baseline_begin: int) -> List[float]:
        """
        計算 Ct 值使用線性插值
        
        Args:
            threshold_values: 閾值列表
            baseline_begin: 基線起始索引
            
        Returns:
            Ct 值列表
        """
        try:
            ct_values = []
            
            for i in range(WELL_COUNT):
                well_name = f'well{i+1}'
                
                if well_name not in self.df_normalization.columns:
                    ct_values.append(CT_UNAVAILABLE_VALUE)
                    continue
                
                well_data = self.df_normalization[well_name]
                acc_time = self.df_normalization.get('accumulation', pd.Series())
                
                ct_found = False
                
                # 查找第一個超過閾值的點
                for j in range(len(well_data)):
                    if well_data.iloc[j] >= threshold_values[i] and j > baseline_begin:
                        # 線性插值
                        if j > 0:
                            x1 = acc_time.iloc[j-1] if len(acc_time) > j-1 else j-1
                            y1 = well_data.iloc[j-1]
                            x2 = acc_time.iloc[j] if len(acc_time) > j else j
                            y2 = well_data.iloc[j]
                            
                            y = threshold_values[i]
                            x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
                            
                            ct_values.append(round(x, 2))
                            logger.debug(f"{well_name}: Ct={round(x, 2)}")
                            ct_found = True
                            break
                
                if not ct_found:
                    ct_values.append(CT_UNAVAILABLE_VALUE)
                    logger.warning(f"{well_name}: Ct value not available")
            
            return ct_values
            
        except Exception as e:
            logger.error(f"Error calculating Ct values: {e}")
            raise
    
    def _apply_moving_average(self) -> pd.DataFrame:
        """
        應用移動平均平滑曲線
        
        Returns:
            平滑後的數據框
        """
        try:
            smoothed_wells = []
            
            for i in range(WELL_COUNT):
                well_name = f'well{i+1}'
                
                if well_name not in self.df_normalization.columns:
                    continue
                
                # 移動平均
                well_smooth = self.df_normalization[well_name].rolling(
                    window=MOVING_AVERAGE_WINDOW
                ).mean()
                
                # 填充 NaN 值
                filling_value = self.df_normalization[well_name].iloc[MOVING_AVERAGE_WINDOW]
                well_smooth = well_smooth.fillna(filling_value).round(2)
                
                smoothed_wells.append(well_smooth)
            
            logger.debug("Applied moving average")
            return pd.DataFrame(smoothed_wells).T
            
        except Exception as e:
            logger.error(f"Error applying moving average: {e}")
            raise
    
    def calculate(self, baseline_begin: int, baseline_end: int) -> List[float]:
        """
        執行完整的 Ct 值計算
        
        Args:
            baseline_begin: 基線起始索引
            baseline_end: 基線終止索引
            
        Returns:
            Ct 值列表
        """
        try:
            logger.info(f"Starting Ct calculation: baseline [{baseline_begin}, {baseline_end}]")
            
            # 讀取數據
            if not self._load_data():
                logger.error("Failed to load data")
                return []
            
            # 添加累積時間
            self._add_accumulation_time()
            
            # 標準化
            self._normalize(baseline_begin, baseline_end)
            
            # 保存標準化數據
            norm_file = Path(RESULT_DIR) / "normalization.csv"
            self.df_normalization.to_csv(norm_file, index=False)
            logger.info(f"Saved normalization data to {norm_file}")
            
            # 計算閾值
            threshold_values = self._get_ct_threshold(baseline_begin, baseline_end)
            
            # 計算 Ct 值
            ct_values = self._get_ct_values(threshold_values, baseline_begin)
            
            # 應用移動平均（可選）
            smoothed_df = self._apply_moving_average()
            
            self.ct_values = ct_values
            logger.info(f"Ct calculation completed: {ct_values}")
            
            return ct_values
            
        except Exception as e:
            logger.error(f"Error in ct_calculation: {e}")
            raise


# 保留向後相容性的函數
def ct_calculation(baseline_begin: int, baseline_end: int) -> List[float]:
    """
    向後相容性包裝函數
    
    Args:
        baseline_begin: 基線起始索引
        baseline_end: 基線終止索引
        
    Returns:
        Ct 值列表
    """
    calculator = CtCalculator()
    return calculator.calculate(baseline_begin, baseline_end)
