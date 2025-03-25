"""
主窗口模块
"""
import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QGraphicsScene, 
    QGraphicsView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from .Ui_Mainwindow import Ui_MainWindow
from core.cad_handler import CADHandler
from core.data_processor import DataProcessor
from core.visualizer import Visualizer, PreviewScene
from utils.logger import get_logger

# 创建模块的logger
logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        # 创建UI对象
        self.ui = Ui_MainWindow()
        # 设置UI
        self.ui.setupUi(self)
        
        # 设置窗口标题
        self.setWindowTitle("桩基偏差分析系统")
        
        # 初始化核心组件
        self.cad_handler = CADHandler()
        self.data_processor = DataProcessor()
        self.visualizer = Visualizer()
        
        # 初始化预览场景
        self.preview_scene = PreviewScene()
        self.ui.preview_view.setScene(self.preview_scene)
        
        # 打印预览视图的信息
        logger.info(f"预览视图尺寸: {self.ui.preview_view.size()}")
        logger.info(f"预览视图可见性: {self.ui.preview_view.isVisible()}")
        logger.info(f"预览视图父控件: {self.ui.preview_view.parent().objectName()}")
        
        # 初始化变量
        self.cad_file = None
        self.measured_file = None
        self.design_points = []
        self.measured_points = []
        
        # 连接信号和槽
        self.connect_signals()
        
        # 初始化UI状态
        self.init_ui_state()
        
    def connect_signals(self):
        """连接信号和槽"""
        # 文件操作
        self.ui.browse_cad_btn.clicked.connect(self.browse_cad_file)
        self.ui.open_cad_btn.clicked.connect(self.open_cad_file)
        self.ui.open_measured_btn.clicked.connect(self.browse_measured_file)
        
        # 图层操作
        self.ui.refresh_layer_btn.clicked.connect(self.refresh_layers)
        
        # 点位提取
        self.ui.select_circle_btn.clicked.connect(self.select_circle)
        self.ui.extract_cass_btn.clicked.connect(self.extract_cass)
        self.ui.load_design_points_btn.clicked.connect(self.load_design_points)
        
        # 数据加载
        self.ui.load_measured_btn.clicked.connect(self.load_measured_data)
        
        # 点位匹配
        self.ui.match_points_btn.clicked.connect(self.match_points)
        
        # 偏差绘制和导出
        self.ui.calculate_deviation_btn.clicked.connect(self.calculate_deviation)
        self.ui.draw_deviation_btn.clicked.connect(self.draw_deviation)
        self.ui.statistics_btn.clicked.connect(self.statistics_deviation)
        self.ui.export_statistics_btn.clicked.connect(self.export_statistics)
        
        # 样式设置
        self.ui.reset_style_btn.clicked.connect(self.reset_style)
        self.ui.apply_style_btn.clicked.connect(self.apply_style)
        
    def init_ui_state(self):
        """初始化UI状态"""
        # 设置默认值
        self.ui.cad_file_path.setText("D:/Project/竣工图编制/test/test2.dwg")
        self.ui.axis_scale_edit.setText("1.5")          # 坐标轴比例
        self.ui.main_text_scale_edit.setText("1.0")     # 主文本比例
        self.ui.axis_label_scale_edit.setText("1.0")    # 坐标轴标签比例
        self.ui.angle_text_scale_edit.setText("1.0")    # 角度文本比例
        self.ui.arrow_scale_edit.setText("1.0")        # 箭头比例
        
        # 设置箭头比例编辑框提示信息
        #self.ui.arrow_scale_edit.setPlaceholderText("可手动调整")
        
        # 设置圆信息编辑框
        self.ui.circle_diameter_edit.setPlaceholderText("可手动调整")
        self.ui.circle_count_edit.setReadOnly(True)
        
        # 设置单选按钮默认状态
        self.ui.point_number_radio.setChecked(True)
        
        # 初始化进度条
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setVisible(False)  # 默认隐藏进度条
        
        # 设置预览视图
        self.ui.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        self.ui.preview_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.ui.preview_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.preview_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.preview_view.setMinimumSize(400, 300)  # 设置最小尺寸
        
        # 立即显示默认样式预览
        self.apply_style()
        
        # 记录初始化完成
        self.log_message("程序初始化完成")
        
    def browse_cad_file(self):
        """浏览CAD文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择CAD文件",
            "",
            "CAD文件 (*.dwg *.dxf);;所有文件 (*.*)"
        )
        if file_path:
            self.ui.cad_file_path.setText(file_path)
            
    def open_cad_file(self):
        """打开CAD文件"""
        file_path = self.ui.cad_file_path.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择CAD文件！")
            return
            
        try:
            # 初始化进度条
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)
            
            # 确保CAD应用程序已初始化
            self.log_message("正在初始化CAD应用程序，请稍候...")
            if not self.cad_handler.ensure_com_initialized():
                self.log_message("CAD应用程序初始化失败", "ERROR")
                QMessageBox.critical(self, "错误", "CAD应用程序初始化失败")
                self.ui.progressBar.setVisible(False)
                return
                
            self.ui.progressBar.setValue(50)
            
            # 打开CAD文件
            self.log_message(f"正在打开CAD文件：{file_path}")
            success, msg = self.cad_handler.open_drawing(file_path)
            if success:
                self.cad_file = file_path
                self.log_message(f"成功打开CAD文件：{file_path}")
                
                self.ui.progressBar.setValue(80)
                
                # 刷新图层列表
                self.log_message("正在刷新图层列表，请稍候...")
                self.refresh_layers()
                
                self.ui.progressBar.setValue(100)
            else:
                self.log_message(f"打开CAD文件失败：{msg}", "ERROR")
                QMessageBox.critical(self, "错误", msg)
                
            # 完成后隐藏进度条
            self.ui.progressBar.setVisible(False)
                
        except Exception as e:
            error_msg = f"打开CAD文件失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            # 发生错误时隐藏进度条
            self.ui.progressBar.setVisible(False)
            
    def browse_measured_file(self):
        """浏览实测数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择实测数据文件",
            "",
            "文本文件 (*.txt *.csv);;所有文件 (*.*)"
        )
        if file_path:
            self.ui.measured_data_path.setText(file_path)
            
    def refresh_layers(self):
        """刷新图层列表"""
        if not self.cad_file:
            QMessageBox.warning(self, "警告", "请先打开CAD文件！")
            return
            
        try:
            layers = self.cad_handler.get_layer_names()
            self.ui.layer_combo.clear()
            self.ui.layer_combo.addItems(layers)
            if layers:
                self.ui.layer_combo.setCurrentIndex(0)
            self.log_message("刷新图层列表")
        except Exception as e:
            logger.error(f"刷新图层失败: {e}")
            QMessageBox.critical(self, "错误", f"刷新图层失败：{str(e)}")
            
    def select_circle(self):
        """选择桩基圆"""
        if not self.cad_file:
            QMessageBox.warning(self, "警告", "请先打开CAD文件！")
            return
            
        try:
            # 初始化进度条
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)
            
            # 提示用户选择桩基圆
            self.log_message("请在CAD图纸中选择一个桩基圆...")
            entities = self.cad_handler.get_selected_entities()
            
            if not entities:
                self.log_message("未选择任何实体", "WARNING")
                QMessageBox.warning(self, "警告", "未选择任何实体！")
                self.ui.progressBar.setVisible(False)
                return
                
            self.ui.progressBar.setValue(30)
            
            # 查找相似圆
            self.log_message("正在查找相似桩基圆...")
            circles = self.cad_handler.find_similar_circles(entities[0])
            
            self.ui.progressBar.setValue(60)
            
            if circles:
                self.log_message(f"找到 {len(circles)} 个相似桩基圆")
                
                # 更新圆信息显示
                self.ui.circle_count_edit.setText(str(len(circles)))
                if hasattr(entities[0], 'Radius'):
                    diameter = entities[0].Radius * 2
                    self.ui.circle_diameter_edit.setText(f"{diameter:.2f}")
                
                # 提取圆心坐标
                self.log_message("正在提取圆心坐标...")
                points = self.cad_handler.extract_points_from_circles(circles)
                
                self.ui.progressBar.setValue(80)
                
                # 高亮显示
                self.log_message("正在高亮显示相似桩基圆...")
                self.cad_handler.highlight_entities(circles)
                
                # 保存为设计点位
                self.design_points = points
                self.log_message(f"已保存 {len(points)} 个设计点位")
                
                # 弹出文件选择对话框
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "导出CASS格式文件",
                    "",
                    "CASS文件 (*.dat);;所有文件 (*.*)"
                )
                
                if file_path:
                    # 导出为CASS格式
                    success = self.cad_handler.export_cass_format(points, file_path)
                    if success:
                        self.log_message(f"成功导出CASS格式文件：{file_path}")
                        QMessageBox.information(self, "成功", "已成功导出CASS格式文件！")
                    else:
                        self.log_message("导出CASS格式失败", "ERROR")
                        QMessageBox.warning(self, "警告", "导出CASS格式失败")
            else:
                self.log_message("未找到相似桩基圆", "WARNING")
                QMessageBox.warning(self, "警告", "未找到相似桩基圆")
            
            # 完成后隐藏进度条
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.setVisible(False)
                
        except Exception as e:
            error_msg = f"选择桩基圆失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            # 发生错误时隐藏进度条
            self.ui.progressBar.setVisible(False)
            
    def extract_cass(self):
        """提取为Cass格式"""
        if not self.cad_file:
            QMessageBox.warning(self, "警告", "请先打开CAD文件！")
            return
            
        layer = self.ui.layer_combo.currentText()
        if not layer:
            QMessageBox.warning(self, "警告", "请先选择图层！")
            return
            
        try:
            # 初始化进度条
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)
            
            # 选择桩基圆
            self.log_message(f"正在图层 {layer} 中查找桩基圆...")
            circles = self.cad_handler.select_circles(layer)
            if not circles:
                self.log_message(f"当前图层 {layer} 未找到桩基圆", "WARNING")
                QMessageBox.warning(self, "警告", "当前图层未找到桩基圆！")
                self.ui.progressBar.setVisible(False)
                return
                
            self.ui.progressBar.setValue(40)
            self.log_message(f"在图层 {layer} 中找到 {len(circles)} 个桩基圆")
            
            # 分析圆的信息
            stats = self.cad_handler.analyze_circles(layer)
            if stats:
                # 更新UI显示
                self.ui.circle_count_edit.setText(str(stats['count']))
                if 'avg_radius' in stats:
                    diameter = stats['avg_radius'] * 2
                    self.ui.circle_diameter_edit.setText(f"{diameter:.2f}")
            
            # 提取圆心坐标
            self.log_message("正在提取圆心坐标...")
            points = self.cad_handler.extract_points_from_circles(circles)
            if not points:
                self.log_message("提取圆心坐标失败", "ERROR")
                QMessageBox.warning(self, "警告", "提取圆心坐标失败！")
                self.ui.progressBar.setVisible(False)
                return
                
            self.ui.progressBar.setValue(70)
            self.log_message(f"成功提取 {len(points)} 个圆心坐标")
            
            # 高亮显示选中的圆
            self.log_message("正在高亮显示选中的圆...")
            self.cad_handler.highlight_entities(circles, highlight=True, color=1)
            
            self.ui.progressBar.setValue(80)
            
            # 保存为Cass格式
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存Cass格式文件",
                "",
                "Cass文件 (*.dat);;所有文件 (*.*)"
            )
            
            if file_path:
                self.log_message(f"正在导出CASS格式文件：{file_path}")
                success = self.cad_handler.export_cass_format(points, file_path)
                if success:
                    self.log_message(f"成功导出CASS格式文件：{file_path}")
                    QMessageBox.information(self, "成功", "已成功导出CASS格式文件！")
                else:
                    self.log_message("导出CASS格式失败", "ERROR")
                    QMessageBox.warning(self, "警告", "导出CASS格式失败")
            
            # 完成后隐藏进度条
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.setVisible(False)
                
        except Exception as e:
            error_msg = f"导出CASS格式失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            # 发生错误时隐藏进度条
            self.ui.progressBar.setVisible(False)
            
    def load_measured_data(self):
        """加载实测数据"""
        # 检查是否选择了文件
        file_path = self.ui.measured_data_path.text()
        if not file_path:
            self.log_message("未选择实测数据文件", "WARNING")
            QMessageBox.warning(self, "警告", "请先选择实测数据文件！")
            return
            
        try:
            # 初始化进度条
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)
            
            # 根据选择的格式加载数据
            if self.ui.cass_format_radio.isChecked():
                # CASS格式
                self.log_message(f"正在加载CASS格式文件：{file_path}")
                success, msg = self.data_processor.load_cass_data(file_path, is_design=False)
            else:
                # 自定义格式
                column_format = self.ui.column_format_edit.text()
                if not column_format:
                    self.log_message("未指定自定义格式的列定义", "WARNING")
                    QMessageBox.warning(self, "警告", "请先在列定义框中指定数据格式！")
                    self.ui.progressBar.setVisible(False)
                return
                    
                self.log_message(f"正在加载自定义格式文件：{file_path}")
                self.log_message(f"使用列定义：{column_format}")
                success, msg = self.data_processor.load_custom_data(file_path, column_format)
                
            self.ui.progressBar.setValue(50)
            
            # 处理加载结果
            if success:
                self.measured_file = file_path
                self.measured_points = self.data_processor.measured_points
                point_count = len(self.measured_points)
                self.log_message(f"成功加载实测点位：共 {point_count} 个点")
                
                # 显示点位信息
                if point_count > 0:
                    first_point = self.measured_points[0]
                    self.log_message(f"第一个点位坐标：X={first_point[0]:.3f}, Y={first_point[1]:.3f}")
                    last_point = self.measured_points[-1]
                    self.log_message(f"最后一个点位坐标：X={last_point[0]:.3f}, Y={last_point[1]:.3f}")
            else:
                self.log_message(f"加载数据失败：{msg}", "ERROR")
                QMessageBox.warning(self, "警告", msg)
                
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.setVisible(False)
                
        except Exception as e:
            error_msg = f"加载实测数据失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            self.ui.progressBar.setVisible(False)
            
    def match_points(self):
        """匹配点位"""
        # 分别检查设计点位和实测点位
        if not self.design_points:
            self.log_message("未加载设计点位数据", "WARNING")
            QMessageBox.warning(self, "警告", "请先提取设计点位数据！")
            return
            
        if not self.measured_points:
            self.log_message("未加载实测点位数据", "WARNING")
            QMessageBox.warning(self, "警告", "请先加载实测点位数据！")
            return
            
        try:
            success = False
            if self.ui.point_number_radio.isChecked():
                # 按点号匹配
                self.log_message("正在按点号匹配点位...")
                success = self.data_processor.match_by_point_number()
            elif self.ui.order_radio.isChecked():
                # 按顺序匹配
                self.log_message("正在按顺序匹配点位...")
                success = self.data_processor.match_by_sequence()
            elif self.ui.distance_radio.isChecked():
                # 按距离匹配
                try:
                    distance = float(self.ui.distance_threshold.text())
                    if distance <= 0:
                        self.log_message("距离阈值必须大于0", "ERROR")
                        QMessageBox.warning(self, "警告", "请输入大于0的距离阈值！")
                        return
                        
                    self.log_message(f"正在按距离匹配点位（阈值：{distance}mm）...")
                    success = self.data_processor.match_by_distance(distance)
                except ValueError:
                    self.log_message("距离阈值格式错误", "ERROR")
                    QMessageBox.warning(self, "警告", "请输入有效的距离阈值！")
                    return
            else:
                self.log_message("未选择匹配方式", "WARNING")
                QMessageBox.warning(self, "警告", "请选择匹配方式！")
                return
                
            if success:
                matched_count = len(self.data_processor.get_matched_points())
                self.log_message(f"点位匹配完成，共匹配 {matched_count} 个点")
                QMessageBox.information(self, "成功", f"点位匹配完成，共匹配 {matched_count} 个点！")
            else:
                self.log_message("点位匹配失败", "ERROR")
                QMessageBox.warning(self, "警告", "点位匹配失败，请检查匹配方式和数据！")
        except Exception as e:
            error_msg = f"匹配点位失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            
    def calculate_deviation(self):
        """计算偏差并获取建议的箭头比例"""
        try:
            # 检查是否已匹配点位
            if not self.data_processor.get_matched_points():
                self.log_message("请先匹配点位", "WARNING")
                QMessageBox.warning(self, "警告", "请先执行点位匹配！")
                return
                
            # 计算偏差
            if not self.data_processor.calculate_deviations():
                self.log_message("计算偏差失败", "ERROR")
                QMessageBox.critical(self, "错误", "计算偏差失败！")
                return
                
            # 获取建议的箭头比例
            arrow_scale = self.data_processor.get_arrow_scale()
            
            # 更新界面上的箭头比例
            self.ui.arrow_scale_edit.setText(f"{arrow_scale:.3f}")
            
            # 更新预览
            self.apply_style()
            
            self.log_message("偏差计算完成，已更新建议的箭头比例")
            
        except Exception as e:
            logger.error(f"计算偏差失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"计算偏差失败：{str(e)}")
            
    def draw_deviation(self):
        """绘制偏差数据"""
        try:
            # 检查是否已计算偏差
            if not self.data_processor.get_deviations():
                self.log_message("请先计算偏差", "WARNING")
                QMessageBox.warning(self, "警告", "请先计算偏差！")
                return
                
            # 获取当前样式设置
            try:
                # 使用circle_diameter_edit中的值作为桩基直径
                pile_diameter = float(self.ui.circle_diameter_edit.text())
                axis_scale = float(self.ui.axis_scale_edit.text())
                arrow_scale = float(self.ui.arrow_scale_edit.text())
                main_text_scale = float(self.ui.main_text_scale_edit.text())
                axis_label_scale = float(self.ui.axis_label_scale_edit.text())
                angle_text_scale = float(self.ui.angle_text_scale_edit.text())
            except ValueError:
                self.log_message("样式参数格式错误，将使用默认值", "WARNING")
                # 如果转换失败，使用默认值
                pile_diameter = 1000
                axis_scale = 0.5
                arrow_scale = self.data_processor.get_arrow_scale()  # 使用计算得到的箭头比例
                main_text_scale = 1.0
                axis_label_scale = 1.0
                angle_text_scale = 1.0
                
            # 更新可视化器样式
            success = self.visualizer.update_style(
                pile_diameter=pile_diameter,
                axis_scale=axis_scale,
                arrow_scale=arrow_scale,
                main_text_scale=main_text_scale,
                axis_label_scale=axis_label_scale,
                angle_text_scale=angle_text_scale
            )
            
            if not success:
                self.log_message("更新样式失败", "ERROR")
                return
                
            # 绘制偏差
            matched_points = self.data_processor.get_matched_points()
            # 获取高程信息
            matched_elevations = self.data_processor.get_matched_elevations()
            
            self.log_message(f"正在绘制偏差，共 {len(matched_points)} 个点...")
            if matched_elevations:
                self.log_message(f"包含高程信息，将绘制桩基标高")
            
            if self.visualizer.draw_deviation(
                matched_points, 
                pile_diameter, 
                axis_scale, 
                arrow_scale,
                main_text_scale,
                axis_label_scale,
                angle_text_scale,
                elevations=matched_elevations  # 传递高程信息
            ):
                self.log_message("偏差绘制完成")
                QMessageBox.information(self, "完成", "偏差数据绘制完成！")
            else:
                self.log_message("偏差绘制失败", "ERROR")
                QMessageBox.critical(self, "错误", "偏差数据绘制失败！")
        except Exception as e:
            error_msg = f"绘制偏差失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            
    def statistics_deviation(self):
        """统计偏差数据"""
        if not self.design_points or not self.measured_points:
            QMessageBox.warning(self, "警告", "请先完成点位匹配！")
            return
            
        try:
            stats = self.data_processor.calculate_statistics()
            msg = f"偏差统计结果：\n"
            msg += f"总点数：{stats['total_points']}\n"
            msg += f"最大偏差：{stats['max_deviation']:.2f}mm\n"
            msg += f"最小偏差：{stats['min_deviation']:.2f}mm\n"
            msg += f"平均偏差：{stats['mean_deviation']:.2f}mm\n"
            msg += f"标准差：{stats['std_deviation']:.2f}mm\n"
            msg += f"超限点数：{stats['exceeded_points']}"
            
            QMessageBox.information(self, "统计结果", msg)
            self.log_message("偏差数据统计完成")
        except Exception as e:
            logger.error(f"统计偏差数据失败: {e}")
            QMessageBox.critical(self, "错误", f"统计偏差数据失败：{str(e)}")
            
    def export_statistics(self):
        """导出统计数据"""
        if not self.design_points or not self.measured_points:
            QMessageBox.warning(self, "警告", "请先完成点位匹配！")
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出统计数据",
                "",
                "Excel文件 (*.xlsx);;所有文件 (*.*)"
            )
            if file_path:
                success = self.data_processor.export_statistics(file_path)
                if success:
                    self.log_message(f"成功导出统计数据：{file_path}")
                else:
                    QMessageBox.warning(self, "警告", "导出统计数据失败")
        except Exception as e:
            logger.error(f"导出统计数据失败: {e}")
            QMessageBox.critical(self, "错误", f"导出统计数据失败：{str(e)}")
            
    def reset_style(self):
        """重置样式设置"""
        self.init_ui_state()
        self.log_message("重置样式设置为默认值")
        
    def apply_style(self):
        """应用样式设置"""
        try:
            # 获取样式参数
            try:
                pile_diameter = float(self.ui.circle_diameter_edit.text()) if self.ui.circle_diameter_edit.text() else 1000
                axis_scale = float(self.ui.axis_scale_edit.text())
                arrow_scale = float(self.ui.arrow_scale_edit.text())  # 使用用户输入的箭头比例
                main_text_scale = float(self.ui.main_text_scale_edit.text())
                axis_label_scale = float(self.ui.axis_label_scale_edit.text())
                angle_text_scale = float(self.ui.angle_text_scale_edit.text())
            except ValueError as e:
                self.log_message("样式参数格式错误", "ERROR")
                QMessageBox.warning(self, "警告", "请输入有效的数值！")
                return
            
            # 检查参数有效性
            if pile_diameter <= 0 or axis_scale <= 0 or arrow_scale <= 0 or \
               main_text_scale <= 0 or axis_label_scale <= 0 or angle_text_scale <= 0:
                self.log_message("样式参数必须大于0", "ERROR")
                QMessageBox.warning(self, "警告", "所有样式参数必须大于0！")
                return
            
            # 更新预览
            logger.info(f"开始更新样式预览... 桩基直径: {pile_diameter}, 箭头比例: {arrow_scale}")
            self.preview_scene.draw_deviation(
                pile_diameter,
                axis_scale,
                arrow_scale,
                main_text_scale,
                axis_label_scale,
                angle_text_scale
            )
            
            # 保存样式设置到可视化器
            success = self.visualizer.update_style(
                pile_diameter=pile_diameter,
                axis_scale=axis_scale,
                arrow_scale=arrow_scale,
                main_text_scale=main_text_scale,
                axis_label_scale=axis_label_scale,
                angle_text_scale=angle_text_scale
            )
            
            if success:
                self.log_message(f"样式设置已更新 - 桩基直径: {pile_diameter}mm, 箭头比例: {arrow_scale}")
            else:
                self.log_message("样式设置保存失败", "WARNING")
                
        except Exception as e:
            logger.error(f"应用样式设置失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"应用样式设置失败：{str(e)}")
            
    def log_message(self, message, level="INFO"):
        """记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别，可选值：INFO, WARNING, ERROR
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据日志级别设置不同的前缀和颜色
        if level == "WARNING":
            prefix = "警告"
            color = "orange"
        elif level == "ERROR":
            prefix = "错误"
            color = "red"
        else:  # INFO
            prefix = "信息"
            color = "black"
            
        # 格式化日志消息
        formatted_msg = f'<div style="color: {color}">[{timestamp}] [{prefix}] {message}</div>'
        
        # 添加到日志控件
        self.ui.log_text.append(formatted_msg)
        
        # 根据级别调用logger
        if level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)
            
    def load_design_points(self):
        """加载设计点位数据（CASS格式）"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择设计点位文件",
            "",
            "CASS文件 (*.dat);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            # 初始化进度条
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setVisible(True)
            
            # 开始加载数据
            self.log_message(f"正在加载设计点位文件：{file_path}")
            
            # 使用数据处理器加载CASS格式数据
            success, msg = self.data_processor.load_cass_data(file_path, is_design=True)
            
            self.ui.progressBar.setValue(50)
            
            if success:
                # 获取点位数据
                self.design_points = self.data_processor.design_points
                point_count = len(self.design_points)
                self.log_message(f"成功加载设计点位：共 {point_count} 个点")
                
                # 显示点位信息
                if point_count > 0:
                    first_point = self.design_points[0]
                    self.log_message(f"第一个点位坐标：X={first_point[0]:.3f}, Y={first_point[1]:.3f}")
                    last_point = self.design_points[-1]
                    self.log_message(f"最后一个点位坐标：X={last_point[0]:.3f}, Y={last_point[1]:.3f}")
                    
                    # 更新UI状态
                    QMessageBox.information(self, "成功", f"已成功加载 {point_count} 个设计点位！")
            else:
                self.log_message(f"加载设计点位失败：{msg}", "ERROR")
                QMessageBox.warning(self, "警告", f"加载设计点位失败：{msg}")
                
            self.ui.progressBar.setValue(100)
            self.ui.progressBar.setVisible(False)
                
        except Exception as e:
            error_msg = f"加载设计点位失败：{str(e)}"
            self.log_message(error_msg, "ERROR")
            QMessageBox.critical(self, "错误", error_msg)
            self.ui.progressBar.setVisible(False)
            
    def extract_by_layer(self):
        """按图层提取设计点位"""
        try:
            layer_name = self.ui.layer_name_edit.text().strip()
            if not layer_name:
                self.log_message("请输入图层名称", "WARNING")
                QMessageBox.warning(self, "警告", "请输入图层名称！")
                return
                
            # 提取点位
            success, circles = self.cad_handler.extract_circles_by_layer(layer_name)
            if not success:
                self.log_message("按图层提取点位失败", "ERROR")
                QMessageBox.critical(self, "错误", "提取点位失败！")
                return
                
            # 更新圆信息显示
            if circles:
                diameter = circles[0].get('diameter', 0)  # 获取第一个圆的直径
                self.ui.circle_diameter_edit.setText(f"{diameter:.2f}")
                self.ui.circle_count_edit.setText(str(len(circles)))
                self.ui.pile_diameter_edit.setText(f"{diameter:.2f}")  # 同步更新样式设置中的桩基直径
                
            # 提取坐标点
            points = [(circle['center'].x, circle['center'].y) for circle in circles]
            self.data_processor.design_points = points
            
            self.log_message(f"按图层提取点位成功，共{len(points)}个点")
            QMessageBox.information(self, "成功", f"成功提取{len(points)}个点！")
            
        except Exception as e:
            self.log_message(f"按图层提取点位失败: {e}", "ERROR")
            QMessageBox.critical(self, "错误", f"提取点位失败：{str(e)}")
            
    def extract_by_select(self):
        """按选择提取设计点位"""
        try:
            # 提取点位
            success, circles = self.cad_handler.extract_circles_by_select()
            if not success:
                self.log_message("按选择提取点位失败", "ERROR")
                QMessageBox.critical(self, "错误", "提取点位失败！")
                return
                
            # 更新圆信息显示
            if circles:
                diameter = circles[0].get('diameter', 0)  # 获取第一个圆的直径
                self.ui.circle_diameter_edit.setText(f"{diameter:.2f}")
                self.ui.circle_count_edit.setText(str(len(circles)))
                self.ui.pile_diameter_edit.setText(f"{diameter:.2f}")  # 同步更新样式设置中的桩基直径
                
            # 提取坐标点
            points = [(circle['center'].x, circle['center'].y) for circle in circles]
            self.data_processor.design_points = points
            
            self.log_message(f"按选择提取点位成功，共{len(points)}个点")
            QMessageBox.information(self, "成功", f"成功提取{len(points)}个点！")
            
        except Exception as e:
            self.log_message(f"按选择提取点位失败: {e}", "ERROR")
            QMessageBox.critical(self, "错误", f"提取点位失败：{str(e)}") 