"""
对话框模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Callable
from utils.logger import logger
from config.settings import UI_CONFIG

class ProgressDialog:
    """进度对话框"""
    
    def __init__(self, parent: tk.Tk, title: str = "处理中", message: str = "正在处理，请稍候..."):
        """
        初始化进度对话框
        
        Args:
            parent (tk.Tk): 父窗口
            title (str): 对话框标题
            message (str): 提示消息
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(pady=10, padx=20, fill=tk.X)
        
        # 创建消息标签
        self.message_var = tk.StringVar(value=message)
        self.message_label = ttk.Label(
            self.dialog,
            textvariable=self.message_var
        )
        self.message_label.pack(pady=5)
        
        # 更新进度
        self.progress_var.set(0)
        self.dialog.update()
        
    def update_progress(self, value: float, message: Optional[str] = None):
        """
        更新进度
        
        Args:
            value (float): 进度值(0-100)
            message (Optional[str]): 更新消息
        """
        self.progress_var.set(value)
        if message:
            self.message_var.set(message)
        self.dialog.update()
        
    def close(self):
        """关闭对话框"""
        self.dialog.destroy()

class ParameterDialog:
    """参数设置对话框"""
    
    def __init__(self, parent: tk.Tk, title: str = "参数设置"):
        """
        初始化参数设置对话框
        
        Args:
            parent (tk.Tk): 父窗口
            title (str): 对话框标题
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.dialog, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 参数变量
        self.parameters = {}
        
        # 创建参数输入区域
        self._create_parameter_section()
        
        # 创建按钮区域
        self._create_button_section()
        
    def _create_parameter_section(self):
        """创建参数输入区域"""
        # 最大偏差设置
        ttk.Label(self.main_frame, text="最大偏差:").grid(row=0, column=0, sticky=tk.W)
        self.parameters['max_distance'] = tk.StringVar(value=str(UI_CONFIG['default_max_distance']))
        ttk.Entry(self.main_frame, textvariable=self.parameters['max_distance'], width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 圆形半径设置
        ttk.Label(self.main_frame, text="圆形半径:").grid(row=1, column=0, sticky=tk.W)
        self.parameters['circle_radius'] = tk.StringVar(value=str(UI_CONFIG['default_circle_radius']))
        ttk.Entry(self.main_frame, textvariable=self.parameters['circle_radius'], width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # 线宽设置
        ttk.Label(self.main_frame, text="线宽:").grid(row=2, column=0, sticky=tk.W)
        self.parameters['line_width'] = tk.StringVar(value=str(UI_CONFIG['default_line_width']))
        ttk.Entry(self.main_frame, textvariable=self.parameters['line_width'], width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # 文字大小设置
        ttk.Label(self.main_frame, text="文字大小:").grid(row=3, column=0, sticky=tk.W)
        self.parameters['text_size'] = tk.StringVar(value=str(UI_CONFIG['default_text_size']))
        ttk.Entry(self.main_frame, textvariable=self.parameters['text_size'], width=10).grid(row=3, column=1, sticky=tk.W, padx=5)
        
    def _create_button_section(self):
        """创建按钮区域"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(side=tk.LEFT, padx=5)
        
    def _on_ok(self):
        """确定按钮回调"""
        try:
            # 验证参数
            for name, var in self.parameters.items():
                value = float(var.get())
                if value <= 0:
                    raise ValueError(f"{name}必须大于0")
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            
    def _on_cancel(self):
        """取消按钮回调"""
        self.dialog.destroy()
        
    def get_parameters(self) -> Dict[str, float]:
        """
        获取参数值
        
        Returns:
            Dict[str, float]: 参数值字典
        """
        return {name: float(var.get()) for name, var in self.parameters.items()}

class ConfirmationDialog:
    """确认对话框"""
    
    @staticmethod
    def show(parent: tk.Tk, title: str, message: str) -> bool:
        """
        显示确认对话框
        
        Args:
            parent (tk.Tk): 父窗口
            title (str): 对话框标题
            message (str): 提示消息
            
        Returns:
            bool: 是否确认
        """
        return messagebox.askyesno(title, message)

class ErrorDialog:
    """错误对话框"""
    
    @staticmethod
    def show(parent: tk.Tk, title: str, message: str):
        """
        显示错误对话框
        
        Args:
            parent (tk.Tk): 父窗口
            title (str): 对话框标题
            message (str): 错误消息
        """
        messagebox.showerror(title, message)
        logger.error(message)

class InfoDialog:
    """信息对话框"""
    
    @staticmethod
    def show(parent: tk.Tk, title: str, message: str):
        """
        显示信息对话框
        
        Args:
            parent (tk.Tk): 父窗口
            title (str): 对话框标题
            message (str): 提示消息
        """
        messagebox.showinfo(title, message)
        logger.info(message) 