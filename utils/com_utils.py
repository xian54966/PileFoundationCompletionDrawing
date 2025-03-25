"""
COM工具模块
"""
import pythoncom
import win32com.client
import win32gui
import win32con
import ctypes
from typing import Any, Callable
from utils.logger import get_logger

# 创建模块的logger
logger = get_logger(__name__)

def initialize_com():
    """
    初始化COM环境
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        pythoncom.CoInitialize()
        logger.info("COM环境初始化成功")
        return True
    except Exception as e:
        logger.error(f"COM环境初始化失败: {e}")
        return False

def uninitialize_com():
    """
    释放COM环境
    """
    try:
        pythoncom.CoUninitialize()
        logger.info("COM环境已释放")
    except Exception as e:
        logger.error(f"COM环境释放失败: {e}")

def ensure_com_initialized(func: Callable) -> Callable:
    """确保COM接口已初始化的装饰器
    
    Args:
        func: 需要装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs) -> Any:
        try:
            # 初始化COM
            pythoncom.CoInitialize()
            # 执行原函数
            result = func(*args, **kwargs)
            # 清理COM
            pythoncom.CoUninitialize()
            return result
        except Exception as e:
            logger.error(f"COM操作失败: {e}")
            raise
    return wrapper 