"""
日誌系統配置
提供統一的日誌記錄功能
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, RESULT_DIR


class LoggerConfig:
    """日誌配置管理器"""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def setup_logger(cls, name: str = 'qPCR_System') -> logging.Logger:
        """
        配置並返回全局日誌記錄器
        
        Args:
            name: 日誌記錄器名稱
            
        Returns:
            配置好的日誌記錄器實例
        """
        if cls._instance is not None:
            return cls._instance
        
        # 建立日誌目錄
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # 格式化器
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件處理器（使用 RotatingFileHandler 防止日誌文件過大）
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        cls._instance = logger
        return logger
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """獲取已配置的日誌記錄器"""
        if cls._instance is None:
            return cls.setup_logger()
        return cls._instance


# 全局日誌記錄器實例
logger = LoggerConfig.setup_logger()
