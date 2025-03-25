"""
CAD处理模块
"""
import os
import time
import win32com.client
import win32gui
import win32con
import ctypes
from typing import List, Tuple, Optional, Dict, Any
from utils.logger import get_logger
from functools import wraps

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

class CADHandler:
    """CAD处理类"""
    
    def __init__(self):
        """初始化CAD处理器"""
        self.app = None
        self.doc = None
        self.modelspace = None
        self._com_initialized = False
        self._max_retries = 3
        self._retry_delay = 1  # 秒
        
    def ensure_com_initialized(self) -> bool:
        """
        确保COM环境已初始化
        
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
                    self._com_initialized = True
                    logger.info("CAD COM环境初始化成功")
                    return True
                except Exception as e:
                    logger.error(f"设置CAD可见性失败 (尝试 {attempt + 1}/{self._max_retries}): {e}")
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay)
                        continue
                    return False
        return True
    
    def open_drawing(self, file_path: str) -> Tuple[bool, str]:
        """打开CAD文件
        
        Args:
            file_path: CAD文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        if not self.ensure_com_initialized():
            return False, "COM环境初始化失败"
            
        for attempt in range(self._max_retries):
            try:
                if not os.path.exists(file_path):
                    return False, "文件不存在"
                    
                # 检查是否有打开的文档
                if self.app.Documents.Count == 0:
                    # 如果没有打开的文档，创建一个新的
                    self.doc = self.app.Documents.Add()
                    self.modelspace = self.doc.ModelSpace
                    logger.info("创建新的CAD文档")
                
                # 打开指定的文件
                self.doc = self.app.Documents.Open(file_path)
                self.modelspace = self.doc.ModelSpace
                logger.info(f"成功打开CAD图纸: {file_path}")
                return True, "打开成功"
            except Exception as e:
                error_msg = f"打开CAD图纸失败 (尝试 {attempt + 1}/{self._max_retries}): {str(e)}"
                logger.error(error_msg)
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                    continue
                return False, error_msg
    
    def get_layer_names(self) -> List[str]:
        """获取图层名称列表
        
        Returns:
            List[str]: 图层名称列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            if not self.doc:
                return []
                
            layers = []
            for layer in self.doc.Layers:
                layers.append(layer.Name)
            return layers
        except Exception as e:
            logger.error(f"获取图层列表失败: {e}")
            return []
    
    def select_circles(self, layer_name: str) -> List[object]:
        """选择指定图层中的圆
        
        Args:
            layer_name: 图层名称
            
        Returns:
            List[object]: 圆对象列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            if not self.modelspace:
                return []
                
            circles = []
            for entity in self.modelspace:
                if entity.Layer == layer_name and entity.ObjectName == "AcDbCircle":
                    circles.append(entity)
            return circles
        except Exception as e:
            logger.error(f"选择圆失败: {e}")
            return []
    
    def select_points(self, layer_name: Optional[str] = None) -> List[Any]:
        """
        选择指定图层中的点实体
        
        Args:
            layer_name (Optional[str]): 图层名称，None表示所有图层
            
        Returns:
            List[Any]: 选中的点实体列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            if not self.doc:
                return []
                
            points = []
            for entity in self.doc.ModelSpace:
                if hasattr(entity, 'ObjectName') and 'Point' in entity.ObjectName:
                    if layer_name is None or entity.Layer == layer_name:
                        points.append(entity)
            return points
        except Exception as e:
            logger.error(f"选择点实体失败: {e}")
            return []
    
    def extract_points_from_circles(self, circles: List[object]) -> List[Tuple[float, float]]:
        """从圆中提取中心点坐标
        
        Args:
            circles: 圆对象列表
            
        Returns:
            List[Tuple[float, float]]: 中心点坐标列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            points = []
            for circle in circles:
                center = circle.Center
                points.append((center[0], center[1]))
            #print(points)
            return points
        except Exception as e:
            logger.error(f"提取圆心坐标失败: {e}")
            return []
    
    def extract_points_from_points(self, points: List[Any]) -> List[Tuple[float, float, float]]:
        """
        从点实体中提取坐标
        
        Args:
            points (List[Any]): 点实体列表
            
        Returns:
            List[Tuple[float, float, float]]: 点坐标列表
        """
        #暂不需要实现，使用点的图纸不常见
        pass
        # if not self.ensure_com_initialized():
        #     return []
            
        # try:
        #     coords = []
        #     for point in points:
        #         if hasattr(point, 'Coordinates'):
        #             coords.append(tuple(point.Coordinates))
        #     return coords
        # except Exception as e:
        #     logger.error(f"提取点坐标失败: {e}")
        #     return []
    
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
        if not self.ensure_com_initialized():
            return False
            
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
    
    def analyze_layer_entities(self, layer_name: str) -> Dict[str, int]:
        """
        分析指定图层中的实体类型和数量
        
        Args:
            layer_name (str): 图层名称
            
        Returns:
            Dict[str, int]: 实体类型和数量的字典
        """
        if not self.ensure_com_initialized():
            return {}
            
        try:
            if not self.doc:
                return {}
                
            entity_counts = {}
            for entity in self.doc.ModelSpace:
                if entity.Layer == layer_name:
                    entity_type = getattr(entity, 'ObjectName', 'Unknown')
                    entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            return entity_counts
        except Exception as e:
            logger.error(f"分析图层实体失败: {e}")
            return {}
    
    def analyze_circles(self, layer_name: str) -> Dict[str, Any]:
        """
        分析指定图层中的圆形实体
        
        Args:
            layer_name (str): 图层名称
            
        Returns:
            Dict[str, Any]: 圆形实体的统计信息
        """
        try:
            if not self.doc:
                return {}
                
            circles = self.select_circles(layer_name)
            if not circles:
                return {}
                
            stats = {
                'count': len(circles),
                'radii': [],
                'layers': set()
            }
            
            for circle in circles:
                if hasattr(circle, 'Radius'):
                    stats['radii'].append(circle.Radius)
                if hasattr(circle, 'Layer'):
                    stats['layers'].add(circle.Layer)
                    
            stats['layers'] = list(stats['layers'])
            if stats['radii']:
                stats['avg_radius'] = sum(stats['radii']) / len(stats['radii'])
                stats['min_radius'] = min(stats['radii'])
                stats['max_radius'] = max(stats['radii'])
                
            return stats
        except Exception as e:
            logger.error(f"分析圆形实体失败: {e}")
            return {}
    
    # def analyze_points(self, layer_name: str) -> Dict[str, Any]:
    #     """
    #     分析指定图层中的点实体
        
    #     Args:
    #         layer_name (str): 图层名称
            
    #     Returns:
    #         Dict[str, Any]: 点实体的统计信息
    #     """
    #     try:
    #         if not self.doc:
    #             return {}
                
    #         points = self.select_points(layer_name)
    #         if not points:
    #             return {}
                
    #         stats = {
    #             'count': len(points),
    #             'layers': set()
    #         }
            
    #         for point in points:
    #             if hasattr(point, 'Layer'):
    #                 stats['layers'].add(point.Layer)
                    
    #         stats['layers'] = list(stats['layers'])
    #         return stats
    #     except Exception as e:
    #         logger.error(f"分析点实体失败: {e}")
    #         return {}
    
    def export_cass_format(self, points: List[Tuple[float, float]], file_path: str) -> bool:
        """导出为Cass格式
        
        Args:
            points: 点位坐标列表
            file_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, (x, y) in enumerate(points, 1):
                    # CASS格式：点号,编码,Y坐标,X坐标,高程
                    # 编码使用"J"表示桩基点
                    # 高程默认为0
                    f.write(f"{i},J,{x:.3f},{y:.3f},0.000\n")
            logger.info(f"成功导出CASS格式文件：{file_path}")
            return True
        except Exception as e:
            logger.error(f"导出CASS格式失败: {e}")
            return False
    
    def get_selected_entities(self) -> List[Any]:
        """
        获取用户当前选中的实体
        
        Returns:
            List[Any]: 选中的实体列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            if not self.doc:
                return []
                
            # 清空当前选择集
            self.doc.PickfirstSelectionSet.Clear()
            
            # 提示用户选择实体
            self.doc.Utility.Prompt("\n请选择桩基圆...")
            
            # 等待用户选择实体
            try:
                # 使用GetEntity方法等待用户选择
                entity = self.doc.Utility.GetEntity(None, "\n选择桩基圆: ")
                if entity:
                    return [entity[0]]  # GetEntity返回(实体, 点)元组
            except Exception as e:
                logger.error(f"等待用户选择失败: {e}")
                return []
                
            return []
        except Exception as e:
            logger.error(f"获取选中实体失败: {e}")
            return []
            
    def find_similar_circles(self, reference_circle: Any, tolerance: float = 0.1) -> List[Any]:
        """
        查找与参考圆相似的圆形
        
        Args:
            reference_circle: 参考圆实体
            tolerance: 允许的误差范围（相对值）
            
        Returns:
            List[Any]: 相似圆形列表
        """
        if not self.ensure_com_initialized():
            return []
            
        try:
            if not self.modelspace:
                return []
                
            # 获取参考圆的属性
            ref_radius = reference_circle.Radius
            ref_layer = reference_circle.Layer
            
            # 计算允许的半径范围
            min_radius = ref_radius * (1 - tolerance)
            max_radius = ref_radius * (1 + tolerance)
            
            # 查找相似圆
            similar_circles = []
            for entity in self.modelspace:
                if (entity.ObjectName == "AcDbCircle" and 
                    entity.Layer == ref_layer and
                    min_radius <= entity.Radius <= max_radius):
                    similar_circles.append(entity)
                    
            return similar_circles
        except Exception as e:
            logger.error(f"查找相似圆失败: {e}")
            return [] 