"""
系統配置文件
定義所有硬編碼常數和配置參數
"""
from pathlib import Path

# ============================================================================
# 目錄配置
# ============================================================================
BASE_DIR = Path(__file__).parent.parent
PARA_DIR = BASE_DIR / 'para'
ROI_DIR = PARA_DIR / 'ROIs'
TMP_DIR = PARA_DIR / 'tmp'
RESULT_DIR = BASE_DIR / 'result'

# ============================================================================
# 相機配置
# ============================================================================
CAMERA_WIDTH = 800
CAMERA_HEIGHT = 480
CAMERA_DEFAULT_FRAMERATE = 2
CAMERA_DEFAULT_ISO = 200
CAMERA_SENSOR_MODE = 3
CAMERA_AWB_MODE = 'incandescent'
CAMERA_DRC_STRENGTH = 'off'
CAMERA_VFLIP = False
CAMERA_HFLIP = True
CAMERA_WARMUP_TIME = 5  # seconds

# ============================================================================
# qPCR 檢測參數
# ============================================================================
WELL_COUNT = 16
THRESHOLDING_OFFSET = 25  # 用於移除陰影區域
HISTOGRAM_BINS = 256
HISTOGRAM_RANGE = [0, 256]

# ============================================================================
# Socket 通信配置
# ============================================================================
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 8888
SOCKET_BUFFER_SIZE = 1024
SOCKET_RECEIVE_TIMEOUT = 1
SOCKET_CONNECTION_RETRY_DELAY = 1  # seconds
SOCKET_HEARTBEAT_INTERVAL = 1  # seconds

# ============================================================================
# 協議定義
# ============================================================================
PROTOCOL_COMMANDS = {
    'SET:01': 'detection',
    'SET:02-1': 'calibrate_dye',
    'SET:02-2': 'calibrate_water',
    'SET:03': 'ct_calculation',
    'SET:00': 'set_camera_params',
}

# ============================================================================
# Ct 值計算配置
# ============================================================================
DEFAULT_CT_THRESHOLD = 0.4584
CT_THRESHOLD_MULTIPLIER = 10  # threshold = 10 * StdDev + Avg
CT_MAX_VALUE = 99.99
CT_UNAVAILABLE_VALUE = 99.99
MOVING_AVERAGE_WINDOW = 5

# ============================================================================
# 文件名和格式
# ============================================================================
DETECTION_CSV_FILE = RESULT_DIR / 'detection.csv'
CALIBRATION_CSV_FILE = RESULT_DIR / 'calibration.csv'
NORMALIZATION_CSV_FILE = RESULT_DIR / 'normalization.csv'
COORDINATES_CSV_FILE = TMP_DIR / 'coordinates.csv'

CSV_DATETIME_FORMAT = "%H:%M:%S"
CSV_FIELDS = [
    'time', 'well1', 'well2', 'well3', 'well4', 'well5', 'well6', 'well7', 'well8',
    'well9', 'well10', 'well11', 'well12', 'well13', 'well14', 'well15', 'well16',
    'shutter_speed', 'ISO'
]

# ============================================================================
# 圖像處理配置
# ============================================================================
MORPH_KERNEL_SIZE = 3
MORPH_ITERATIONS = 1
GAUSSIAN_BLUR_SIGMA = 100
UNSHARP_ALPHA = 2
UNSHARP_BETA = -25
UNSHARP_GAMMA = 0

# ============================================================================
# 合併圖像配置
# ============================================================================
MERGE_ALPHA = 0.7
MERGE_BETA = 1 - MERGE_ALPHA
MERGE_GAMMA = 3
MERGE_THRESHOLD = 70

# ============================================================================
# 日誌配置
# ============================================================================
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = RESULT_DIR / 'system.log'

# ============================================================================
# 性能配置
# ============================================================================
ENABLE_PROFILING = False
PROFILING_OUTPUT_FILE = RESULT_DIR / 'profiling.txt'
