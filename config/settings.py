"""
应用程序配置文件
"""

# 应用程序信息
APP_NAME = "竣工图编制系统"
VERSION = "1.0.0"

# 默认参数
DEFAULT_CIRCLE_RADIUS = 30.0
DEFAULT_LINE_WIDTH = 0.8
DEFAULT_TEXT_SIZE = 2.5
DEFAULT_MAX_DISTANCE = 30.0

# 可视化参数
VISUAL_CONFIG = {
    'text_scale': 0.8,  # 主文本大小比例
    'axis_scale': 2.5,  # 坐标轴长度比例
    'arrow_scale': 0.3,  # 箭头大小比例
    'label_scale': 0.6,  # 坐标轴标签比例
    'text_offset': 1.2,  # 文本偏移比例
}

# 颜色配置
COLORS = {
    'design': 1,  # 红色
    'actual': 2,  # 黄色
    'deviation': 3,  # 绿色
    'success': 4,  # 青色
    'warning': 5,  # 蓝色
    'error': 6,  # 品红
    'info': 7  # 白色
}

# 文件类型
FILE_TYPES = {
    'cad': ['.dwg', '.dxf'],
    'excel': ['.xlsx', '.xls'],
    'csv': ['.csv'],
    'cass': ['.dat', '.cass']
}

# 日志配置
LOG_CONFIG = {
    'filename': 'logs/app.log',
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# UI配置
UI_CONFIG = {
    'window_size': '1024x768',
    'window_title': APP_NAME,
    'font_family': 'Microsoft YaHei',
    'font_size': 10,
    'default_max_distance': DEFAULT_MAX_DISTANCE,
    'version': VERSION
} 