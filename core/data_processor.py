"""
数据处理模块
"""
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from utils.logger import get_logger

# 创建模块的logger
logger = get_logger(__name__)

class DataProcessor:
    """数据处理类"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.design_points = []  # [(x, y), ...]
        self.design_point_numbers = []  # [point_number, ...]
        self.measured_points = []  # [(x, y), ...]
        self.measured_point_numbers = []  # [point_number, ...]
        self.matched_points = []  # [(design_point, measured_point), ...]
        self.deviations = []  # 偏差值列表
        self.arrow_scale = 0.5  # 默认箭头比例
        
    def load_cass_data(self, file_path: str, is_design: bool = False) -> Tuple[bool, str]:
        """加载Cass格式数据
        
        Args:
            file_path: 数据文件路径
            is_design: 是否为设计点位数据
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # CASS格式：点号,编码,Y坐标,X坐标,高程
            df = pd.read_csv(file_path, header=None, names=['point_number', 'code', 'y', 'x', 'elevation'])
            
            if is_design:
                # 设计数据不需要交换XY，直接使用CASS格式的坐标
                points = list(zip(df['y'], df['x']))  # Y作为X，X作为Y
                logger.info("加载设计数据：保持CASS格式坐标")
            else:
                # 实测数据需要交换XY
                points = list(zip(df['x'], df['y']))  # X作为Y，Y作为X
                logger.info("加载实测数据：交换XY坐标")
            
            point_numbers = df['point_number'].tolist()
            
            if is_design:
                self.design_points = points
                self.design_point_numbers = point_numbers
            else:
                self.measured_points = points
                self.measured_point_numbers = point_numbers
            
            logger.info(f"成功加载CASS数据，共{len(points)}个点")
            if len(points) > 0:
                first_point = points[0]
                if is_design:
                    logger.info(f"第一个设计点坐标：X={first_point[0]:.3f}, Y={first_point[1]:.3f}")
                else:
                    logger.info(f"第一个实测点坐标：X={first_point[0]:.3f}, Y={first_point[1]:.3f}")
            
            return True, ""
        except Exception as e:
            logger.error(f"加载Cass格式数据失败: {e}")
            return False, str(e)
            
    def load_custom_data(self, file_path: str, column_format: str) -> Tuple[bool, str]:
        """加载自定义格式数据
        
        Args:
            file_path: 数据文件路径
            column_format: 列格式，如"x,y,z"或"x,y"
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            columns = [col.strip() for col in column_format.split(',')]
            df = pd.read_csv(file_path, usecols=columns)
            self.measured_points = list(zip(df[columns[0]], df[columns[1]]))
            return True, ""
        except Exception as e:
            logger.error(f"加载自定义格式数据失败: {e}")
            return False, str(e)
            
    def get_measured_points(self) -> List[Tuple[float, float]]:
        """获取实测点位列表
        
        Returns:
            List[Tuple[float, float]]: 实测点位坐标列表
        """
        return self.measured_points
        
    def match_by_point_number(self) -> bool:
        """按点号匹配点位
        
        Returns:
            bool: 是否成功
        """
        try:
            if not self.design_points or not self.measured_points:
                logger.error("设计点位或实测点位数据为空")
                return False
                
            # 创建点号到坐标的映射
            design_dict = dict(zip(self.design_point_numbers, self.design_points))
            measured_dict = dict(zip(self.measured_point_numbers, self.measured_points))
            
            # 找到共同的点号
            common_numbers = set(self.design_point_numbers) & set(self.measured_point_numbers)
            
            if not common_numbers:
                logger.error("未找到匹配的点号")
                return False
                
            # 按点号匹配点位
            self.matched_points = [
                (design_dict[num], measured_dict[num])
                for num in common_numbers
            ]
            
            logger.info(f"按点号匹配成功，共匹配{len(self.matched_points)}个点")
            return True
        except Exception as e:
            logger.error(f"按点号匹配点位失败: {e}")
            return False
            
    def match_by_sequence(self) -> bool:
        """按顺序匹配点位
        
        Returns:
            bool: 是否成功
        """
        try:
            if not self.design_points or not self.measured_points:
                logger.error("设计点位或实测点位数据为空")
                return False
                
            if len(self.design_points) != len(self.measured_points):
                logger.error("设计点位和实测点位数量不一致")
                return False
                
            # 直接按顺序匹配
            self.matched_points = list(zip(self.design_points, self.measured_points))
            
            logger.info(f"按顺序匹配成功，共匹配{len(self.matched_points)}个点")
            return True
        except Exception as e:
            logger.error(f"按顺序匹配点位失败: {e}")
            return False
            
    def match_by_distance(self, max_distance: float) -> bool:
        """按距离匹配点位
        
        Args:
            max_distance: 最大匹配距离
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.design_points or not self.measured_points:
                logger.error("设计点位或实测点位数据为空")
                return False
                
            matched = []
            used_measured = set()
            
            # 对每个设计点位
            for i, design_point in enumerate(self.design_points):
                min_dist = float('inf')
                best_match = None
                best_index = None
                
                # 寻找最近的实测点位
                for j, measured_point in enumerate(self.measured_points):
                    if j in used_measured:
                        continue
                        
                    dist = np.sqrt(
                        (design_point[0] - measured_point[0])**2 + 
                        (design_point[1] - measured_point[1])**2
                    )
                    
                    if dist < min_dist and dist <= max_distance:
                        min_dist = dist
                        best_match = measured_point
                        best_index = j
                        
                if best_match is not None:
                    matched.append((design_point, best_match))
                    used_measured.add(best_index)
                    logger.debug(f"点位{i+1}匹配成功，距离={min_dist:.2f}")
                else:
                    logger.warning(f"点位{i+1}未找到匹配点")
                    
            self.matched_points = matched
            
            if matched:
                logger.info(f"按距离匹配成功，共匹配{len(matched)}个点")
                return True
            else:
                logger.error("未找到任何匹配点")
                return False
        except Exception as e:
            logger.error(f"按距离匹配点位失败: {e}")
            return False
            
    def get_matched_points(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """获取匹配后的点位列表
        
        Returns:
            List[Tuple[Tuple[float, float], Tuple[float, float]]]: 匹配后的点位列表
        """
        return self.matched_points
        
    def calculate_statistics(self) -> Optional[Dict]:
        """计算偏差统计信息
        
        Returns:
            Optional[Dict]: 统计信息字典
        """
        try:
            if not self.matched_points:
                return None
                
            deviations = []
            for design_point, measured_point in self.matched_points:
                deviation = np.sqrt(
                    (design_point[0] - measured_point[0])**2 + 
                    (design_point[1] - measured_point[1])**2
                )
                deviations.append(deviation * 1000)  # 转换为毫米
                
            deviations = np.array(deviations)
            
            return {
                'total_points': len(deviations),
                'max_deviation': np.max(deviations),
                'min_deviation': np.min(deviations),
                'mean_deviation': np.mean(deviations),
                'std_deviation': np.std(deviations),
                'exceeded_points': np.sum(deviations > 30.0)  # 30mm为限差
            }
        except Exception as e:
            logger.error(f"计算偏差统计信息失败: {e}")
            return None
            
    def export_statistics(self, file_path: str) -> bool:
        """导出统计数据
        
        Args:
            file_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.matched_points:
                return False
                
            # 创建数据框
            data = []
            for i, (design_point, measured_point) in enumerate(self.matched_points, 1):
                deviation = np.sqrt(
                    (design_point[0] - measured_point[0])**2 + 
                    (design_point[1] - measured_point[1])**2
                )
                data.append({
                    '点号': i,
                    '设计X(m)': design_point[0],
                    '设计Y(m)': design_point[1],
                    '实测X(m)': measured_point[0],
                    '实测Y(m)': measured_point[1],
                    '偏差(mm)': deviation * 1000  # 转换为毫米
                })
                
            df = pd.DataFrame(data)
            
            # 导出到Excel
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            logger.error(f"导出统计数据失败: {e}")
            return False
            
    def calculate_deviations(self) -> bool:
        """计算所有匹配点位的偏差，并计算合适的箭头比例
        
        Returns:
            bool: 计算是否成功
        """
        try:
            if not self.matched_points:
                logger.warning("没有匹配的点位数据，无法计算偏差")
                return False
                
            # 计算每个点位的偏差
            self.deviations = []
            for design_point, measured_point in self.matched_points:
                dx = measured_point[0] - design_point[0]
                dy = measured_point[1] - design_point[1]
                deviation = (dx**2 + dy**2)**0.5 * 1000  # 转换为毫米
                self.deviations.append(deviation)
                
            # 计算统计值
            max_dev = max(self.deviations)
            min_dev = min(self.deviations)
            avg_dev = sum(self.deviations) / len(self.deviations)
            
            logger.info(f"偏差统计: 最大值={max_dev:.2f}mm, 最小值={min_dev:.2f}mm, 平均值={avg_dev:.2f}mm")
            
            # 计算建议的箭头比例
            self.arrow_scale = self.calculate_arrow_scale(pile_diameter=1000)  # 使用默认桩径
            
            logger.info(f"计算得到建议的箭头比例: {self.arrow_scale:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"计算偏差失败: {e}", exc_info=True)
            return False
            
    def calculate_arrow_scale(self, pile_diameter: float,
                            min_scale: float = 0,  # 最小箭头长度（相对于半径）
                            avg_scale: float = 2,  # 平均箭头长度（相对于半径）
                            max_scale: float = 3   # 最大箭头长度（相对于半径）
                            ) -> float:
        """计算合适的箭头比例
        
        Args:
            pile_diameter: 桩基直径
            min_scale: 最小箭头长度（相对于半径）
            avg_scale: 平均箭头长度（相对于半径）
            max_scale: 最大箭头长度（相对于半径）
            
        Returns:
            float: 建议的箭头比例
        """
        if not self.deviations:
            return avg_scale
            
        radius = pile_diameter / 2
        max_dev = max(self.deviations)
        min_dev = min(self.deviations)
        avg_dev = sum(self.deviations) / len(self.deviations)
        
        logger.info(f"计算箭头比例 - 最大偏差: {max_dev:.2f}mm, 最小偏差: {min_dev:.2f}mm, 平均偏差: {avg_dev:.2f}mm")
        
        # 处理特殊情况
        if min_dev == 0:
            min_dev = max_dev * 0.1  # 将最小偏差设为最大偏差的10%
            logger.info(f"最小偏差为0，调整为最大偏差的10%: {min_dev:.2f}mm")
        
        if max_dev == 0:  # 所有偏差都为0的情况
            logger.info("所有偏差都为0，使用默认箭头比例")
            return avg_scale
            
        # 计算期望的箭头长度（相对于桩基半径）
        target_min_length = radius * min_scale  # 最小箭头期望长度
        target_avg_length = radius * avg_scale  # 平均箭头期望长度
        target_max_length = radius * max_scale  # 最大箭头期望长度
        
        logger.info(f"目标箭头长度 - 最小: {target_min_length:.2f}mm, 平均: {target_avg_length:.2f}mm, 最大: {target_max_length:.2f}mm")
        
        # 计算比例（箭头长度 = 偏差值 * 比例）
        scale_by_min = target_min_length / min_dev  # 使最小偏差显示为最小目标长度
        scale_by_avg = target_avg_length / avg_dev  # 使平均偏差显示为平均目标长度
        scale_by_max = target_max_length / max_dev  # 使最大偏差显示为最大目标长度
        
        logger.info(f"候选比例 - 最小: {scale_by_min:.3f}, 平均: {scale_by_avg:.3f}, 最大: {scale_by_max:.3f}")
        
        # 取合适的比例（偏向于平均值）
        arrow_scale = scale_by_avg
        
        # 确保箭头比例在合理范围内
        arrow_scale = max(1.0, min(arrow_scale, 10.0))  # 限制在1.0到10.0之间
        
        logger.info(f"最终箭头比例: {arrow_scale:.3f}")
        return arrow_scale
        
    def get_deviations(self) -> List[float]:
        """获取偏差值列表"""
        return self.deviations
        
    def get_arrow_scale(self) -> float:
        """获取建议的箭头比例"""
        return self.arrow_scale 