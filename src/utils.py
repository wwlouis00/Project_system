"""
通用工具函數
提取重複邏輯和共用功能
"""
from typing import List, Tuple
from logger_config import logger


def format_values_for_protocol(values: List[float], format_type: str = 'standard') -> str:
    """
    格式化數值列表為協議格式字符串
    
    Args:
        values: 待格式化的數值列表
        format_type: 格式類型 - 'standard' (3位) 或 'ct' (ct值特殊格式)
        
    Returns:
        格式化後的字符串
        
    Examples:
        >>> format_values_for_protocol([3, 25, 100])
        '003,025,100'
        >>> format_values_for_protocol([12.34, 45.67], format_type='ct')
        '01234,04567'
    """
    try:
        if format_type == 'standard':
            # 標準格式：每個數字 3 位補零
            return ','.join(f'{int(v):03d}' for v in values)
        elif format_type == 'ct':
            # Ct 值特殊格式：整數部分 2 位，小數部分 2 位，共 5 位
            formatted = []
            for val in values:
                val_str = str(val)
                if len(val_str) == 5:
                    formatted.append(val_str)
                elif len(val_str) == 4:
                    if val > 10:
                        formatted.append(val_str + '0')
                    else:
                        formatted.append('0' + val_str)
                elif len(val_str) == 3:
                    formatted.append('0' + val_str + '0')
            return ','.join(formatted)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    except Exception as e:
        logger.error(f"Error formatting values: {e}")
        raise


def parse_camera_params_command(command: str) -> Tuple[int, int]:
    """
    解析相機參數命令
    
    Args:
        command: 格式 'SET:00,01,80' 表示 framerate=1, ISO=800
        
    Returns:
        (framerate, iso) 元組
        
    Raises:
        ValueError: 如果命令格式不正確
    """
    try:
        parts = command.strip().split(',')
        if len(parts) < 3:
            raise ValueError("Command format should be 'SET:00,framerate,iso_factor'")
        
        framerate = int(parts[1])
        iso = int(parts[2]) * 10
        
        logger.info(f"Parsed camera params: framerate={framerate}, iso={iso}")
        return framerate, iso
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing camera params command: {e}")
        raise


def parse_ct_calculation_command(command: str) -> Tuple[int, int]:
    """
    解析 Ct 計算命令
    
    Args:
        command: 格式 'SET:03,00035,00320' 表示基線範圍 3.5~32 分鐘
        
    Returns:
        (baseline_begin, baseline_end) 元組，已轉換為正確的數組索引
        
    Raises:
        ValueError: 如果命令格式不正確
    """
    try:
        if len(command) < 18:
            raise ValueError("Command too short")
        
        # 提取基線時間值
        baseline_start_time = int(command[7:12])
        baseline_end_time = int(command[13:18])
        
        # 轉換為數組索引（每 5 分鐘一個數據點）
        baseline_begin = int(baseline_start_time / 5) + 1
        baseline_end = int(baseline_end_time / 5) + 1
        
        logger.info(f"Parsed Ct calculation params: baseline {baseline_start_time}-{baseline_end_time} "
                   f"minutes -> indices {baseline_begin}-{baseline_end}")
        return baseline_begin, baseline_end
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing Ct calculation command: {e}")
        raise


def ensure_directories_exist() -> None:
    """
    確保所有必需的目錄存在
    """
    from config import PARA_DIR, ROI_DIR, TMP_DIR, RESULT_DIR
    
    dirs = [PARA_DIR, ROI_DIR, TMP_DIR, RESULT_DIR]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
