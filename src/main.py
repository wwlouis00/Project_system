#!/usr/bin/python3
"""
主控制程序
管理 Socket 通信和 qPCR 系統的命令分派
"""
import socket
import time
from time import sleep
from typing import Callable, Dict, Optional, Tuple

from config import SOCKET_HOST, SOCKET_PORT, SOCKET_BUFFER_SIZE, SOCKET_RECEIVE_TIMEOUT
from logger_config import logger
from public_method import initialize
from calibration import Calibration
from detection import Detection
from Ct_calculation import ct_calculation
from merge import merge
from utils import (
    format_values_for_protocol, parse_camera_params_command,
    parse_ct_calculation_command, ensure_directories_exist
)


class QPCRServer:
    """qPCR 系統服務器"""
    
    def __init__(self, host: str = SOCKET_HOST, port: int = SOCKET_PORT):
        """
        初始化服務器
        
        Args:
            host: Socket 主機地址
            port: Socket 端口
        """
        self.host = host
        self.port = port
        self.framerate = 2
        self.iso = 200
        self.socket = None
        
        # 命令處理器映射表
        self.command_handlers: Dict[str, Callable] = {
            'SET:01': self._handle_detection,
            'SET:02-1': self._handle_calibrate_dye,
            'SET:02-2': self._handle_calibrate_water,
            'SET:03': self._handle_ct_calculation,
            'SET:00': self._handle_camera_params,
        }
        
        logger.info(f"QPCRServer initialized: {host}:{port}")
    
    def _handle_detection(self, command: str) -> str:
        """
        處理檢測命令
        
        Args:
            command: 原始命令字符串
            
        Returns:
            應答字符串
        """
        try:
            logger.info("Handling detection command...")
            
            if not Detection.check_necessity():
                logger.error("Detection prerequisites not met")
                return "CT:ERROR"
            
            values = Detection.detect(self.framerate, self.iso)
            msg = format_values_for_protocol(values)
            
            logger.info(f"Detection complete: {msg}")
            return f"CT:{msg}"
            
        except Exception as e:
            logger.error(f"Error in detection: {e}")
            return "CT:ERROR"
    
    def _handle_calibrate_dye(self, command: str) -> str:
        """
        處理染料校準命令
        
        Args:
            command: 原始命令字符串
            
        Returns:
            應答字符串
        """
        try:
            logger.info("Handling dye calibration command...")
            
            values = Calibration.calibrate_for_dye(self.framerate, self.iso)
            msg = format_values_for_protocol(values)
            
            logger.info(f"Dye calibration complete: {msg}")
            return f"CA:{msg}"
            
        except Exception as e:
            logger.error(f"Error in dye calibration: {e}")
            return "CA:ERROR"
    
    def _handle_calibrate_water(self, command: str) -> str:
        """
        處理水條紋校準命令
        
        Args:
            command: 原始命令字符串
            
        Returns:
            應答字符串
        """
        try:
            logger.info("Handling water calibration command...")
            
            if not Calibration.check_necessity():
                logger.error("Water calibration prerequisites not met")
                return "CT:ERROR"
            
            values = Calibration.calibrate_for_water(self.framerate, self.iso)
            msg = format_values_for_protocol(values)
            
            # 合併圖像
            try:
                merge()
                logger.info("ROI merge completed")
            except Exception as e:
                logger.warning(f"Failed to merge ROI: {e}")
            
            logger.info(f"Water calibration complete: {msg}")
            return f"CT:{msg}"
            
        except Exception as e:
            logger.error(f"Error in water calibration: {e}")
            return "CT:ERROR"
    
    def _handle_ct_calculation(self, command: str) -> str:
        """
        處理 Ct 計算命令
        格式: SET:03,00035,00320 (基線 3.5-32 分鐘)
        
        Args:
            command: 原始命令字符串
            
        Returns:
            應答字符串
        """
        try:
            logger.info("Handling Ct calculation command...")
            
            baseline_begin, baseline_end = parse_ct_calculation_command(command)
            logger.info(f"Baseline range: [{baseline_begin}, {baseline_end}]")
            
            values = ct_calculation(baseline_begin, baseline_end)
            msg = format_values_for_protocol(values, format_type='ct')
            
            logger.info(f"Ct calculation complete: {msg}")
            return f"CT:{msg}"
            
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid Ct calculation command format: {e}")
            return "CT:ERROR"
        except Exception as e:
            logger.error(f"Error in Ct calculation: {e}")
            return "CT:ERROR"
    
    def _handle_camera_params(self, command: str) -> str:
        """
        處理相機參數設置命令
        格式: SET:00,01,80 (幀率=1, ISO=800)
        
        Args:
            command: 原始命令字符串
            
        Returns:
            應答字符串
        """
        try:
            logger.info("Handling camera parameter command...")
            
            framerate, iso = parse_camera_params_command(command)
            
            self.framerate = framerate
            self.iso = iso
            
            logger.info(f"Camera parameters updated: framerate={framerate}, iso={iso}")
            return f"ISO:0x{int(iso/10):02x}"
            
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid camera parameter format: {e}")
            return "ISO:ERROR"
        except Exception as e:
            logger.error(f"Error setting camera parameters: {e}")
            return "ISO:ERROR"
    
    def _process_command(self, command: str) -> str:
        """
        分派命令到相應的處理器
        
        Args:
            command: 命令字符串
            
        Returns:
            應答字符串
        """
        try:
            command = command.strip()
            logger.info(f"Processing command: {command}")
            
            # 查找匹配的命令處理器
            for cmd_prefix, handler in self.command_handlers.items():
                if cmd_prefix in command:
                    return handler(command)
            
            logger.warning(f"Unknown command format: {command}")
            return "ERROR: Unknown command"
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "ERROR: Internal server error"
    
    def _establish_connection(self) -> bool:
        """
        建立 Socket 連接
        
        Returns:
            連接成功返回 True
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.setblocking(False)
            self.socket.send(b'Hello')
            
            logger.info(f"Connected to server: {self.host}:{self.port}")
            return True
            
        except ConnectionRefusedError:
            logger.error(f"Connection refused by server: {self.host}:{self.port}")
            if self.socket:
                self.socket.close()
            return False
        except Exception as e:
            logger.error(f"Error establishing connection: {e}")
            if self.socket:
                self.socket.close()
            return False
    
    def _receive_command(self) -> Optional[str]:
        """
        接收命令
        
        Returns:
            命令字符串或 None
        """
        try:
            command_bytes = self.socket.recv(SOCKET_BUFFER_SIZE)
            
            if not command_bytes:
                logger.warning("Connection closed by server")
                return None
            
            command = command_bytes.decode('utf-8')
            return command
            
        except socket.timeout:
            return None
        except BlockingIOError:
            return None
        except (ConnectionResetError, BrokenPipeError) as e:
            logger.warning(f"Connection lost: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving command: {e}")
            return None
    
    def _send_response(self, response: str) -> bool:
        """
        發送應答
        
        Args:
            response: 應答字符串
            
        Returns:
            成功返回 True
        """
        try:
            self.socket.sendall(response.encode())
            logger.debug(f"Sent response: {response}")
            return True
            
        except (ConnectionResetError, BrokenPipeError) as e:
            logger.warning(f"Connection lost while sending response: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return False
    
    def run(self) -> None:
        """
        運行服務器主循環
        """
        logger.info("Starting qPCR server...")
        ensure_directories_exist()
        initialize()
        
        while True:
            try:
                # 連接到服務器
                if not self._establish_connection():
                    sleep(SOCKET_RECEIVE_TIMEOUT)
                    continue
                
                # 命令循環
                while True:
                    sleep(SOCKET_RECEIVE_TIMEOUT)
                    
                    # 嘗試接收命令
                    command = self._receive_command()
                    
                    if command is None:
                        logger.debug(f"[{time.ctime()}] Server still connected, waiting for commands...")
                        continue
                    
                    # 處理命令
                    response = self._process_command(command)
                    logger.info(f"Response: {response}")
                    
                    # 發送應答
                    if not self._send_response(response):
                        logger.warning("Failed to send response, reconnecting...")
                        break
                    
            except KeyboardInterrupt:
                logger.info("Server interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                if self.socket:
                    self.socket.close()
                sleep(SOCKET_RECEIVE_TIMEOUT)
            finally:
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
        
        logger.info("Server shutdown complete")


def main() -> None:
    """主函數"""
    server = QPCRServer()
    server.run()


if __name__ == "__main__":
    main()
