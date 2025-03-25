"""
文件工具模块
"""
import os
from config.settings import FILE_TYPES
from utils.logger import logger

def is_cass_file(file_path):
    """
    判断是否为CASS格式文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 是否为CASS格式文件
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline().strip() for _ in range(3)]
            for line in first_lines:
                if line.startswith('CASS') or line.startswith('*FPH') or line.startswith('*ZD'):
                    return True
        return False
    except Exception as e:
        logger.error(f"检查CASS文件格式失败: {e}")
        return False

def get_file_type(file_path):
    """
    获取文件类型
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 文件类型（'CAD', 'EXCEL', 'CSV', 'CASS'）
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    for file_type, extensions in FILE_TYPES.items():
        if ext in extensions:
            return file_type
            
    if is_cass_file(file_path):
        return 'CASS'
        
    return None

def ensure_file_exists(file_path):
    """
    确保文件存在
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False
    return True

def create_directory_if_not_exists(directory):
    """
    如果目录不存在则创建
    
    Args:
        directory (str): 目录路径
        
    Returns:
        bool: 是否成功创建目录
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"创建目录: {directory}")
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        return False 