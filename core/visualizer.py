"""
可视化模块
"""
import os
import win32com.client
import win32gui
import win32con
import ctypes
from typing import List, Tuple, Dict, Any, Optional
from utils.logger import get_logger
from utils.com_utils import ensure_com_initialized
from config.settings import COLORS
from functools import wraps
import numpy as np
import time
import pythoncom
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPainterPath
import math

# 创建模块的logger
logger = get_logger(__name__)

def ensure_com_initialized(func):
    """确保COM环境已初始化的装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.ensure_com_initialized():
            return False, "COM环境初始化失败"
        return func(self, *args, **kwargs)
    return wrapper

class Visualizer:
    """可视化类"""
    
    def __init__(self):
        """初始化可视化器"""
        self.app = None
        self.doc = None
        self.modelspace = None
        self.style = {
            'pile_diameter': 10000,      # 桩基直径（mm）
            'axis_scale': 1.5,          # 坐标轴比例
            'arrow_scale': 0.3,         # 箭头比例
            'main_text_scale': 0.5,     # 主文本比例
            'axis_label_scale': 0.6,   # 坐标轴标签比例
            'angle_text_scale': 0.5      # 角度文本比例
        }
        self._com_initialized = False
        self._max_retries = 3
        self._retry_delay = 1  # 秒
        
    def ensure_com_initialized(self) -> bool:
        """确保COM环境已初始化
        
        Returns:
            bool: 是否成功初始化
        """
        if not self._com_initialized:
            for attempt in range(self._max_retries):
                try:
                    # 尝试获取已存在的CAD应用程序实例
                    self.app = win32com.client.GetActiveObject("AutoCAD.Application")
                except:
                    try:
                        # 如果没有运行中的实例，创建新的
                        self.app = win32com.client.Dispatch("AutoCAD.Application")
                    except Exception as e:
                        logger.error(f"CAD COM环境初始化失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                        if attempt < self._max_retries - 1:
                            time.sleep(self._retry_delay)
                            continue
                        return False
                
                try:
                    self.app.Visible = True
                    # 获取当前活动文档
                    if self.app.Documents.Count > 0:
                        self.doc = self.app.ActiveDocument
                        self.modelspace = self.doc.ModelSpace
                    else:
                        logger.error("没有打开的CAD文档")
                        return False
                        
                    self._com_initialized = True
                    logger.info("CAD COM环境初始化成功")
                    return True
                except Exception as e:
                    logger.error(f"设置CAD可见性或获取文档失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay)
                        continue
                return False
        return True
    
    def open_drawing(self, file_path: str) -> Tuple[bool, str]:
        """
        打开CAD图纸
        
        Args:
            file_path (str): 图纸文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            self.doc = self.app.Documents.Open(file_path)
            self.modelspace = self.doc.ModelSpace
            logger.info(f"成功打开CAD图纸: {file_path}")
            return True, "打开成功"
        except Exception as e:
            error_msg = f"打开CAD图纸失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def draw_deviation(self, matched_points: List[Tuple[Tuple[float, float], Tuple[float, float]]], 
                      pile_diameter: float, axis_scale: float, arrow_scale: float,
                      main_text_scale: float = 0.2, axis_label_scale: float = 0.15,
                      angle_text_scale: float = 0.5) -> bool:
        """绘制偏差数据
        
        Args:
            matched_points: 匹配后的点位列表
            pile_diameter: 桩基直径
            axis_scale: 坐标轴比例
            arrow_scale: 箭头比例
            main_text_scale: 主文本比例
            axis_label_scale: 坐标轴标签比例
            angle_text_scale: 角度文本比例
            
        Returns:
            bool: 是否成功
        """
        try:
            if not matched_points:
                logger.error("没有匹配的点位数据")
                return False
                
            # 确保CAD环境已初始化
            if not self.ensure_com_initialized():
                logger.error("CAD环境初始化失败")
                return False
                
            # 更新样式
            self.style.update({
                'pile_diameter': pile_diameter,
                'axis_scale': axis_scale,
                'arrow_scale': arrow_scale,
                'main_text_scale': main_text_scale,
                'axis_label_scale': axis_label_scale,
                'angle_text_scale': angle_text_scale
            })
            
            # 创建偏差图层
            try:
                deviation_layer = self.doc.Layers.Add("偏差分析")
                deviation_layer.Color = 1  # 红色
            except Exception as e:
                logger.warning(f"创建图层失败（可能已存在）: {e}")
                try:
                    deviation_layer = self.doc.Layers.Item("偏差分析")
                except:
                    logger.error("无法创建或获取偏差分析图层")
                    return False
            
            # 设置当前图层
            self.doc.ActiveLayer = deviation_layer
            
            # 转换为VBA数组格式的点
            def to_vba_point(x: float, y: float) -> Any:
                return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (x, y, 0.0))
            
            success_count = 0
            # 绘制每个点的偏差
            for design_point, measured_point in matched_points:
                try:
                    # 计算偏差
                    dx = float(measured_point[0]) - float(design_point[0])  # 确保是浮点数
                    dy = float(measured_point[1]) - float(design_point[1])  # 确保是浮点数
                    # 计算偏差并转换为毫米（坐标值可能是以米为单位）
                    deviation = math.sqrt(dx**2 + dy**2) * 1000  # 转换为毫米
                    deviation_mm = deviation  # 毫米单位
                    
                    # 计算偏差角度（与X轴的夹角，逆时针为正）
                    # 使用数学坐标系，y轴向上为正，角度从x轴正向开始逆时针为正
                    angle = math.degrees(math.atan2(dy, dx))  # 转换为度，逆时针方向为正
                    if angle < 0:  # 确保角度为正值
                        angle += 360
                    
                    # 转换坐标点为VBA格式（已经是毫米）
                    center_point = to_vba_point(design_point[0], design_point[1])
                    
                    # 绘制桩基圆
                    circle = self.modelspace.AddCircle(center_point, pile_diameter/2)  # 桩基直径已经是毫米
                    circle.Layer = "偏差分析"
                    circle.Color = 5  # 蓝色
                    
                    # 绘制坐标轴
                    axis_length = pile_diameter * axis_scale  # 桩基直径已经是毫米
                    # X轴
                    x_axis = self.modelspace.AddLine(
                        to_vba_point(design_point[0] - axis_length, design_point[1]),
                        to_vba_point(design_point[0] + axis_length, design_point[1])
                    )
                    x_axis.Layer = "偏差分析"
                    x_axis.Color = 0  # 黑色
                    
                    # Y轴
                    y_axis = self.modelspace.AddLine(
                        to_vba_point(design_point[0], design_point[1] - axis_length),
                        to_vba_point(design_point[0], design_point[1] + axis_length)
                    )
                    y_axis.Layer = "偏差分析"
                    y_axis.Color = 0  # 黑色
                    
                    # 绘制坐标轴箭头
                    arrow_size = axis_length * 0.1  # 箭头大小为轴长的10%
                    arrow_angle = math.pi / 6  # 30度
                    
                    # X轴箭头
                    x_arrow_p1 = to_vba_point(
                        design_point[0] + axis_length - arrow_size * math.cos(arrow_angle),
                        design_point[1] - arrow_size * math.sin(arrow_angle)
                    )
                    x_arrow_p2 = to_vba_point(
                        design_point[0] + axis_length - arrow_size * math.cos(-arrow_angle),
                        design_point[1] - arrow_size * math.sin(-arrow_angle)
                    )
                    x_arrow_end = to_vba_point(design_point[0] + axis_length, design_point[1])
                    self.modelspace.AddLine(x_arrow_end, x_arrow_p1).Color = 0
                    self.modelspace.AddLine(x_arrow_end, x_arrow_p2).Color = 0
                    
                    # Y轴箭头
                    y_arrow_p1 = to_vba_point(
                        design_point[0] - arrow_size * math.sin(arrow_angle),
                        design_point[1] + axis_length - arrow_size * math.cos(arrow_angle)
                    )
                    y_arrow_p2 = to_vba_point(
                        design_point[0] + arrow_size * math.sin(arrow_angle),
                        design_point[1] + axis_length - arrow_size * math.cos(arrow_angle)
                    )
                    y_arrow_end = to_vba_point(design_point[0], design_point[1] + axis_length)
                    self.modelspace.AddLine(y_arrow_end, y_arrow_p1).Color = 0
                    self.modelspace.AddLine(y_arrow_end, y_arrow_p2).Color = 0
                    
                    # 绘制坐标轴标签
                    # X轴标签
                    x_label_size = pile_diameter * self.style['axis_label_scale']
                    x_label_offset = 10 * x_label_size / 100  # 调整偏移量，避免与箭头重叠
                    x_label_point = to_vba_point(
                        design_point[0] + axis_length + x_label_offset,
                        design_point[1]
                    )
                    x_label_obj = self.modelspace.AddText("X", x_label_point, x_label_size)
                    x_label_obj.Color = 0  # 黑色
                    
                    # Y轴标签
                    y_label_size = pile_diameter * self.style['axis_label_scale']
                    y_label_offset = 10 * y_label_size / 100  # 调整偏移量，避免与箭头重叠
                    y_label_point = to_vba_point(
                        design_point[0],
                        design_point[1] + axis_length + y_label_offset
                    )
                    y_label_obj = self.modelspace.AddText("Y", y_label_point, y_label_size)
                    y_label_obj.Color = 0  # 黑色
                    
                    # 绘制偏差箭头
                    # 箭头长度使用桩基直径作为基准尺寸，但不对偏差值本身再乘以1000
                    arrow_length = deviation_mm * arrow_scale  # 偏差值(mm) * 比例因子
                    
                    # 如果箭头长度太小，则设置一个最小值以确保可见性
                    min_arrow_length = pile_diameter * 0.25  # 最小箭头长度为桩基直径的25%
                    if arrow_length < min_arrow_length:
                        arrow_length = min_arrow_length
                        
                    end_point = to_vba_point(
                        design_point[0] + arrow_length * math.cos(math.radians(angle)),
                        design_point[1] + arrow_length * math.sin(math.radians(angle))
                    )
                    arrow_line = self.modelspace.AddLine(center_point, end_point)
                    arrow_line.Layer = "偏差分析"
                    arrow_line.Color = 1  # 红色
                    
                    # 绘制箭头头部
                    head_size = arrow_length * 0.2
                    head_angle = math.pi / 6  # 30度
                    angle_rad = math.radians(angle)
                    
                    arrow_p1 = to_vba_point(
                        design_point[0] + arrow_length * math.cos(angle_rad) - head_size * math.cos(angle_rad + head_angle),
                        design_point[1] + arrow_length * math.sin(angle_rad) - head_size * math.sin(angle_rad + head_angle)  # 注意这里是减号，为箭头方向计算
                    )
                    arrow_p2 = to_vba_point(
                        design_point[0] + arrow_length * math.cos(angle_rad) - head_size * math.cos(angle_rad - head_angle),
                        design_point[1] + arrow_length * math.sin(angle_rad) - head_size * math.sin(angle_rad - head_angle)  # 注意这里是减号，为箭头方向计算
                    )
                    
                    self.modelspace.AddLine(end_point, arrow_p1).Color = 1  # 红色
                    self.modelspace.AddLine(end_point, arrow_p2).Color = 1  # 红色
                    
                    # 绘制角度圆弧
                    # 圆弧半径应该适中，既不太大也不太小
                    arc_radius = min(arrow_length * 0.3, pile_diameter * 0.2)  # 选择合适的圆弧大小
                    # 确保圆弧半径不会太小而无法看清
                    min_arc_radius = pile_diameter * 0.1  # 最小圆弧半径为桩基直径的10%
                    if arc_radius < min_arc_radius:
                        arc_radius = min_arc_radius
                        
                    # 逆时针方向绘制圆弧
                    start_angle = 0  # 起始角度（水平向右）
                    end_angle = angle  # 终止角度（逆时针方向）
                    # 在CAD中，AutoCAD API的AddArc方法中，正角度表示逆时针，负角度表示顺时针
                    arc = self.modelspace.AddArc(
                        center_point,
                        arc_radius,
                        math.radians(0),  # 起始角度（水平向右）
                        math.radians(angle)  # 终止角度（正值表示逆时针方向）
                    )
                    arc.Color = 3  # 绿色
                    
                    # 绘制角度文本
                    angle_text = f"{angle:.0f}°"  # 使用实际计算的角度
                    # 计算文本位置，放在圆弧中间位置
                    mid_angle = angle / 2  # 角度的一半
                    mid_angle_rad = math.radians(mid_angle)  # 转换为弧度
                    # 文本距离中心点的距离，比圆弧稍微大一点
                    text_radius = arc_radius * 1.3  # 增加文本半径，避免与圆弧重叠
                    # 计算文本位置坐标，使用数学坐标系计算（y轴向上为正）
                    text_point = to_vba_point(
                        design_point[0] + text_radius * math.cos(mid_angle_rad),
                        design_point[1] + text_radius * math.sin(mid_angle_rad)  # 使用加号表示逆时针方向
                    )
                    # 使用angle_text_scale参数来控制文本大小
                    angle_text_size = pile_diameter * self.style['angle_text_scale']
                    angle_text_obj = self.modelspace.AddText(angle_text, text_point, angle_text_size)
                    angle_text_obj.Color = 3  # 绿色
                    
                    # 绘制偏差值文本
                    # 将文本放在箭头末端稍微偏移的位置，确保不与箭头重叠
                    offset_distance = pile_diameter * 0.05  # 偏移距离
                    text_point = to_vba_point(
                        design_point[0] + (arrow_length + offset_distance) * math.cos(angle_rad),
                        design_point[1] + (arrow_length + offset_distance) * math.sin(angle_rad)  # 使用加号表示逆时针方向
                    )
                    # 使用main_text_scale参数来控制偏差值文本大小
                    deviation_text_size = pile_diameter * self.style['main_text_scale']
                    text = self.modelspace.AddText(
                        f"{deviation_mm:.0f}mm",
                        text_point,
                        deviation_text_size
                    )
                    text.Color = 0  # 黑色
                    
                    success_count += 1
                except Exception as e:
                    logger.error(f"绘制点位失败: {e}")
                    continue
            
            if success_count > 0:
                logger.info(f"成功绘制 {success_count}/{len(matched_points)} 个点的偏差")
                return True
            else:
                logger.error("所有点位绘制失败")
                return False
                
        except Exception as e:
            logger.error(f"绘制偏差数据失败: {e}")
            return False
            
    def update_style(self, pile_diameter: float = 10000, axis_scale: float = 1.5, 
                    arrow_scale: float = 0.3, main_text_scale: float = 0.5,
                    axis_label_scale: float = 0.6, angle_text_scale: float = 0.5) -> bool:
        """更新可视化样式
        
        Args:
            pile_diameter: 桩基直径
            axis_scale: 坐标轴比例
            arrow_scale: 箭头比例
            main_text_scale: 主文本比例
            axis_label_scale: 坐标轴标签比例
            angle_text_scale: 角度文本比例
            
        Returns:
            bool: 是否成功
        """
        try:
            self.style.update({
                'pile_diameter': pile_diameter,
                'axis_scale': axis_scale,
                'arrow_scale': arrow_scale,
                'main_text_scale': main_text_scale,
                'axis_label_scale': axis_label_scale,
                'angle_text_scale': angle_text_scale
            })
            logger.info("可视化样式更新成功")
            return True
        except Exception as e:
            logger.error(f"更新可视化样式失败: {e}")
            return False
            
    def _draw_circle(self, center: Tuple[float, float], radius: float):
        """绘制圆
        
        Args:
            center: 圆心坐标
            radius: 半径
        """
        try:
            circle = self.modelspace.AddCircle(center, radius)
            circle.Color = 1  # 红色
        except Exception as e:
            logger.error(f"绘制圆失败: {e}")
            
    def _draw_arrow(self, start: Tuple[float, float], end: Tuple[float, float]):
        """绘制箭头
        
        Args:
            start: 起点坐标
            end: 终点坐标
        """
        try:
            # 计算箭头方向
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = (dx**2 + dy**2)**0.5
            
            # 计算箭头大小
            arrow_size = length * self.style['arrow_scale']
            
            # 计算箭头端点
            angle = np.arctan2(dy, dx)
            arrow_angle = np.pi/6  # 30度
            
            arrow1 = (
                end[0] - arrow_size * np.cos(angle + arrow_angle),
                end[1] - arrow_size * np.sin(angle + arrow_angle)
            )
            arrow2 = (
                end[0] - arrow_size * np.cos(angle - arrow_angle),
                end[1] - arrow_size * np.sin(angle - arrow_angle)
            )
            
            # 绘制箭头
            self.modelspace.AddLine(start, end)
            self.modelspace.AddLine(end, arrow1)
            self.modelspace.AddLine(end, arrow2)
        except Exception as e:
            logger.error(f"绘制箭头失败: {e}")
            
    def _draw_text(self, position: Tuple[float, float], text: str):
        """绘制文本
        
        Args:
            position: 位置坐标
            text: 文本内容
        """
        try:
            # 计算文本位置（偏移一点，避免重叠）
            offset = self.style['pile_diameter'] * 0.2
            text_pos = (position[0] + offset, position[1] + offset)
            
            # 绘制文本
            text_obj = self.modelspace.AddText(text, text_pos, 2.5)
            text_obj.Color = 1  # 红色
        except Exception as e:
            logger.error(f"绘制文本失败: {e}")
    
    def highlight_entities(self, entities: List[Any], highlight: bool = True, color: int = 1) -> bool:
        """
        高亮显示实体
        
        Args:
            entities (List[Any]): 实体列表
            highlight (bool): 是否高亮
            color (int): 高亮颜色
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.doc:
                return False
                
            for entity in entities:
                if hasattr(entity, 'Color'):
                    entity.Color = color if highlight else 0
            return True
        except Exception as e:
            logger.error(f"高亮显示实体失败: {e}")
            return False
    
    def zoom_to_entities(self, entities: List[Any]) -> bool:
        """
        缩放视图以显示指定实体
        
        Args:
            entities (List[Any]): 实体列表
            
        Returns:
            bool: 是否成功
        """
        if not self.ensure_com_initialized():
            return False
            
        try:
            if not self.doc or not entities:
                return False
                
            # 计算边界框
            min_x = min_y = min_z = float('inf')
            max_x = max_y = max_z = float('-inf')
            
            for entity in entities:
                if hasattr(entity, 'Coordinates'):
                    coords = entity.Coordinates
                    min_x = min(min_x, coords[0])
                    min_y = min(min_y, coords[1])
                    min_z = min(min_z, coords[2])
                    max_x = max(max_x, coords[0])
                    max_y = max(max_y, coords[1])
                    max_z = max(max_z, coords[2])
                    
            # 设置视图范围
            self.app.ZoomExtents()
            
            logger.info("成功调整视图范围")
            return True
            
        except Exception as e:
            logger.error(f"调整视图范围失败: {e}")
            return False
    
    def create_deviation_report(self, analysis: Dict[str, Any], output_path: str) -> bool:
        """
        创建偏差报告
        
        Args:
            analysis (Dict[str, Any]): 偏差分析结果
            output_path (str): 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.doc:
                return False
                
            # 创建报告图层
            report_layer = self.doc.Layers.Add("偏差报告")
            report_layer.Color = COLORS['report']
            
            # 添加报告标题
            title = f"偏差分析报告 (总点数: {analysis['total_points']})"
            title_point = (0, 0, 0)
            title_text = self.doc.ModelSpace.AddText(
                title,
                title_point,
                2.0
            )
            title_text.Layer = "偏差报告"
            
            # 添加统计信息
            stats = [
                f"正常点数: {analysis['normal_points']}",
                f"超限点数: {analysis['exceeded_points']}",
                f"平均偏差: {analysis['deviation_stats']['mean']:.3f}",
                f"最大偏差: {analysis['deviation_stats']['max']:.3f}",
                f"最小偏差: {analysis['deviation_stats']['min']:.3f}",
                f"标准差: {analysis['deviation_stats']['std']:.3f}"
            ]
            
            for i, stat in enumerate(stats):
                stat_point = (0, -2 * (i + 1), 0)
                stat_text = self.doc.ModelSpace.AddText(
                    stat,
                    stat_point,
                    1.0
                )
                stat_text.Layer = "偏差报告"
            
            # 保存图纸
            self.doc.SaveAs(output_path)
            return True
        except Exception as e:
            logger.error(f"创建偏差报告失败: {e}")
            return False
    
    def reset_visualization(self) -> bool:
        """
        重置可视化状态
        
        Returns:
            bool: 是否成功
        """
        if not self.ensure_com_initialized():
            return False
            
        try:
            if not self.doc:
                return False
                
            # 清除所有颜色
            for entity in self.doc.ModelSpace:
                if hasattr(entity, 'Color'):
                    entity.Color = 0
                    
            logger.info("成功重置可视化状态")
            return True
            
        except Exception as e:
            logger.error(f"重置可视化状态失败: {e}")
            return False

class PreviewScene(QGraphicsScene):
    """预览场景类"""
    
    def draw_deviation(self, pile_diameter, axis_scale, arrow_scale, 
                      main_text_scale, axis_label_scale, angle_text_scale):
        """绘制偏差预览
        
        Args:
            pile_diameter: 桩基圆直径（mm）
            axis_scale: 坐标轴长度比例
            arrow_scale: 箭头长度比例
            main_text_scale: 主文本大小比例
            axis_label_scale: 坐标轴标签比例
            angle_text_scale: 角度文本比例
        """
        try:
            # 清空场景
            self.clear()
            
            # 获取视图尺寸
            view = self.views()[0]
            view_width = view.width()
            view_height = view.height()
            
            if view_width <= 0 or view_height <= 0:
                logger.warning("预览视图尺寸无效")
                return
                
            # 计算缩放比例
            scale = min(view_width, view_height) / (pile_diameter * 3)
            
            # 计算中心点
            center_x = view_width / 2
            center_y = view_height / 2
            
            # 绘制桩基圆
            radius = pile_diameter / 2 * scale
            circle = self.addEllipse(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
                QPen(Qt.GlobalColor.blue),
                QBrush(Qt.GlobalColor.transparent)
            )
            
            # 绘制坐标轴
            axis_length = radius * axis_scale
            axis_arrow_size = axis_length * 0.1  # 坐标轴箭头大小为轴长的10%
            axis_arrow_angle = math.pi / 6  # 30度

            # X轴及其箭头
            self.addLine(
                center_x - axis_length,
                center_y,
                center_x + axis_length,
                center_y,
                QPen(Qt.GlobalColor.black)
            )
            # X轴箭头
            x_arrow_p1_x = center_x + axis_length - axis_arrow_size * math.cos(axis_arrow_angle)
            x_arrow_p1_y = center_y - axis_arrow_size * math.sin(axis_arrow_angle)
            x_arrow_p2_x = center_x + axis_length - axis_arrow_size * math.cos(-axis_arrow_angle)
            x_arrow_p2_y = center_y - axis_arrow_size * math.sin(-axis_arrow_angle)
            self.addLine(center_x + axis_length, center_y, x_arrow_p1_x, x_arrow_p1_y, QPen(Qt.GlobalColor.black))
            self.addLine(center_x + axis_length, center_y, x_arrow_p2_x, x_arrow_p2_y, QPen(Qt.GlobalColor.black))

            # Y轴及其箭头
            self.addLine(
                center_x,
                center_y - axis_length,
                center_x,
                center_y + axis_length,
                QPen(Qt.GlobalColor.black)
            )
            # Y轴箭头
            y_arrow_p1_x = center_x - axis_arrow_size * math.sin(axis_arrow_angle)
            y_arrow_p1_y = center_y - axis_length + axis_arrow_size * math.cos(axis_arrow_angle)
            y_arrow_p2_x = center_x + axis_arrow_size * math.sin(axis_arrow_angle)
            y_arrow_p2_y = center_y - axis_length + axis_arrow_size * math.cos(axis_arrow_angle)
            self.addLine(center_x, center_y - axis_length, y_arrow_p1_x, y_arrow_p1_y, QPen(Qt.GlobalColor.black))
            self.addLine(center_x, center_y - axis_length, y_arrow_p2_x, y_arrow_p2_y, QPen(Qt.GlobalColor.black))
            
            # 绘制示例偏差箭头（45度角）
            arrow_length = radius * arrow_scale
            arrow_angle = 45  # 度
            arrow_rad = math.radians(arrow_angle)
            end_x = center_x + arrow_length * math.cos(arrow_rad)
            end_y = center_y - arrow_length * math.sin(arrow_rad)
            
            # 绘制箭头主体
            arrow_line = self.addLine(
                center_x,
                center_y,
                end_x,
                end_y,
                QPen(Qt.GlobalColor.red, 2)
            )
            
            # 绘制箭头头部
            head_size = arrow_length * 0.2
            head_angle = math.pi / 6  # 30度
            angle = math.atan2(center_y - end_y, end_x - center_x)
            
            # 箭头两个翼的端点
            p1_x = end_x - head_size * math.cos(angle - head_angle)
            p1_y = end_y + head_size * math.sin(angle - head_angle)
            p2_x = end_x - head_size * math.cos(angle + head_angle)
            p2_y = end_y + head_size * math.sin(angle + head_angle)
            
            # 绘制箭头翼
            self.addLine(end_x, end_y, p1_x, p1_y, QPen(Qt.GlobalColor.red, 2))
            self.addLine(end_x, end_y, p2_x, p2_y, QPen(Qt.GlobalColor.red, 2))
            
            # 设置基准文本大小（使用固定值）
            base_text_size = 20  # 基准大小设为12pt
            
            # 绘制偏差值文本
            deviation_text = "50mm"
            text_item = self.addText(deviation_text)
            text_item.setDefaultTextColor(Qt.GlobalColor.black)
            font = QFont()
            font.setPointSize(int(base_text_size * main_text_scale))  # 转换为整数
            text_item.setFont(font)
            
            # 将文本放置在箭头末端
            text_width = text_item.boundingRect().width()
            text_height = text_item.boundingRect().height()
            text_item.setPos(end_x - text_width/2, end_y - text_height - 5)
            
            # 绘制角度圆弧
            arc_radius = arrow_length * 0.3  # 圆弧半径为箭头长度的30%
            arc_path = QPainterPath()
            arc_path.moveTo(center_x + arc_radius, center_y)  # 从水平右侧开始
            arc_path.arcTo(
                center_x - arc_radius,
                center_y - arc_radius,
                arc_radius * 2,
                arc_radius * 2,
                0,  # 起始角度（水平向右）
                45  # 顺时针旋转45度（与箭头角度相同）
            )
            self.addPath(arc_path, QPen(Qt.GlobalColor.blue, 1))
            
            # 绘制角度文本
            angle_text = "45°"
            angle_text_item = self.addText(angle_text)
            angle_text_item.setDefaultTextColor(Qt.GlobalColor.blue)
            font = QFont()
            font.setPointSize(int(base_text_size * angle_text_scale))  # 转换为整数
            angle_text_item.setFont(font)
            
            # 将角度文本放置在圆弧中间偏上位置
            mid_angle_rad = math.radians(22.5)  # 圆弧中点的角度（45/2度）
            text_radius = arc_radius * 0.6  # 文本放在圆弧内侧偏上位置
            text_x = center_x + text_radius * math.cos(mid_angle_rad)
            text_y = center_y - text_radius * math.sin(mid_angle_rad)  # 注意这里是减号，因为Qt坐标系Y轴向下
            
            # 调整文本位置，使其居中显示在计算出的位置
            angle_text_width = angle_text_item.boundingRect().width()
            angle_text_height = angle_text_item.boundingRect().height()
            angle_text_item.setPos(
                text_x - angle_text_width/2,
                text_y - angle_text_height/2
            )
            
            # 绘制坐标轴标签
            font = QFont()
            font.setPointSize(int(base_text_size * axis_label_scale))  # 转换为整数
            
            # X轴标签
            x_label = self.addText("X")
            x_label.setFont(font)
            x_label.setDefaultTextColor(Qt.GlobalColor.black)
            x_label.setPos(
                center_x + axis_length + 10,  # 增加一点距离，避免与箭头重叠
                center_y - x_label.boundingRect().height()/2
            )
            
            # Y轴标签
            y_label = self.addText("Y")
            y_label.setFont(font)
            y_label.setDefaultTextColor(Qt.GlobalColor.black)
            y_label.setPos(
                center_x - y_label.boundingRect().width()/2,
                center_y - axis_length - y_label.boundingRect().height() - 10  # 增加一点距离，避免与箭头重叠
            )
            
            # 设置场景矩形
            scene_rect = QRectF(0, 0, view_width, view_height)
            view.setSceneRect(scene_rect)
            
            return True
            
        except Exception as e:
            logger.error(f"绘制偏差预览失败: {e}", exc_info=True)
            return False 