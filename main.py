"""
桩基偏差分析系统主程序
"""
import os
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import get_logger

# 创建模块的logger
logger = get_logger(__name__)

def main():
    """主程序入口"""
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 记录程序启动信息
        logger.info("程序启动成功")
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        # 记录异常信息
        logger.critical(f"程序发生严重错误: {str(e)}")
        logger.exception("详细错误信息:")
        
        # 显示错误对话框
        from PyQt6.QtWidgets import QMessageBox
        error_msg = f"程序发生严重错误:\n{str(e)}\n\n详细错误信息已记录到日志文件。"
        QMessageBox.critical(None, "错误", error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main() 