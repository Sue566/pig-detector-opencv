"""
高级可视化渲染模块
提供丰富的检测结果可视化功能
"""

import os
import math
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

from ..core.config import (
    CLASS_DEFINITIONS, 
    VISUALIZATION_CONFIG, 
    LENGTH_ANNOTATION_CONFIG,
    get_class_info,
    get_class_color
)


class AdvancedRenderer:
    """高级可视化渲染器"""
    
    def __init__(self):
        self.config = VISUALIZATION_CONFIG
        self.length_config = LENGTH_ANNOTATION_CONFIG
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict[str, Any]:
        """加载字体"""
        fonts = {}
        
        # 尝试加载主要字体
        for font_path in self.config["fonts"]["primary"]:
            try:
                fonts["large"] = ImageFont.truetype(font_path, self.config["text"]["font_size_large"])
                fonts["small"] = ImageFont.truetype(font_path, self.config["text"]["font_size_small"])
                break
            except (OSError, IOError):
                continue
        
        # 如果没有找到字体，使用默认字体
        if "large" not in fonts:
            fonts["large"] = ImageFont.load_default()
            fonts["small"] = ImageFont.load_default()
        
        return fonts
    
    def _read_image_from_source(self, image_path: str) -> Image.Image:
        """从本地或URL读取图片"""
        if isinstance(image_path, str) and (image_path.startswith("http://") or image_path.startswith("https://")):
            response = requests.get(image_path, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        else:
            return Image.open(image_path).convert("RGB")
    
    def _draw_detection_box(self, draw: ImageDraw.Draw, detection: Dict[str, Any]) -> None:
        """绘制单个检测框"""
        class_id = detection["class_id"]
        confidence = detection["confidence"]
        box = detection["box"]
        
        x1, y1, x2, y2 = [int(coord) for coord in box]
        
        # 获取类别信息和颜色
        class_info = get_class_info(class_id)
        color = class_info["color_rgb"]
        class_name = class_info["name_cn"]
        
        print(f"绘制检测框 - 类别ID: {class_id}, 类别名: {class_name}, 颜色: {color}")
        
        # 绘制边界框
        draw.rectangle(
            [x1, y1, x2, y2], 
            outline=color, 
            width=self.config["box"]["line_width"]
        )
        
        # 绘制基础标签
        label = f"{class_name}: {confidence:.2f}"
        self._draw_text_with_background(draw, label, (x1, y1), color, self.fonts["large"])
    
    def _draw_pig_with_measurements(self, draw: ImageDraw.Draw, detection: Dict[str, Any], 
                                  measurements: Dict[str, Any]) -> None:
        """绘制带测量信息的猪检测框"""
        class_id = detection["class_id"]
        confidence = detection["confidence"]
        box = detection["box"]
        
        x1, y1, x2, y2 = [int(coord) for coord in box]
        
        # 强制使用红色作为猪的颜色
        color = (255, 0, 0)  # 红色
        class_name = "猪"
        
        print(f"绘制猪检测框 - 类别ID: {class_id}, 颜色: {color}")
        
        # 绘制边界框
        draw.rectangle(
            [x1, y1, x2, y2], 
            outline=color, 
            width=self.config["box"]["line_width"]
        )
        
        # 准备多行文本
        texts = [f"{class_name}: {confidence:.2f}"]
        
        # 添加长度信息
        if measurements.get("length_cm"):
            length_text = f"长度: {measurements['length_cm']:.1f} cm"
            texts.append(length_text)
        
        # 添加重量信息
        if measurements.get("weight_kg"):
            weight_kg = measurements["weight_kg"]
            weight_range = measurements.get("weight_range_kg")
            if weight_range:
                weight_text = f"重量: {weight_kg:.1f}kg ({weight_range[0]:.1f}-{weight_range[1]:.1f}kg)"
            else:
                weight_text = f"重量: {weight_kg:.1f}kg"
            texts.append(weight_text)
        
        # 添加计算方法
        if measurements.get("calculation_method"):
            method_text = f"方法: {measurements['calculation_method']}"
            texts.append(method_text)
        
        # 添加置信度
        if measurements.get("confidence"):
            conf_text = f"精度: {measurements['confidence']}"
            texts.append(conf_text)
        
        # 绘制多行文本背景和文字
        self._draw_multiline_text_with_background(draw, texts, (x1, y1), color, self.fonts["small"])
        
        # 绘制长度标注线
        if self.length_config["show_length_line"] and measurements.get("length_cm"):
            self._draw_length_annotation(draw, box, measurements["length_cm"])
    
    def _draw_pig_basic(self, draw: ImageDraw.Draw, detection: Dict[str, Any]) -> None:
        """绘制基本猪检测框（不含测量信息）"""
        confidence = detection["confidence"]
        box = detection["box"]
        
        x1, y1, x2, y2 = [int(coord) for coord in box]
        
        # 强制使用红色作为猪的颜色
        color = (255, 0, 0)  # 红色
        class_name = "猪"
        
        print(f"绘制基本猪检测框 - 颜色: {color}")
        
        # 绘制边界框
        draw.rectangle(
            [x1, y1, x2, y2], 
            outline=color, 
            width=self.config["box"]["line_width"]
        )
        
        # 绘制基础标签
        label = f"{class_name}: {confidence:.2f}"
        self._draw_text_with_background(draw, label, (x1, y1), color, self.fonts["large"])
    
    def _draw_text_with_background(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int], 
                                 color: Tuple[int, int, int], font: ImageFont.ImageFont) -> None:
        """绘制带背景的文本"""
        x, y = position
        
        # 计算文本尺寸
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        padding = self.config["text"]["padding"]
        bg_width = text_width + padding * 2
        bg_height = text_height + padding * 2
        
        # 绘制背景
        bg_y = max(y - bg_height, 0)
        draw.rectangle(
            [x, bg_y, x + bg_width, bg_y + bg_height], 
            fill=color
        )
        
        # 绘制文本
        draw.text(
            (x + padding, bg_y + padding), 
            text, 
            fill="white", 
            font=font
        )
    
    def _draw_multiline_text_with_background(self, draw: ImageDraw.Draw, texts: List[str], 
                                           position: Tuple[int, int], color: Tuple[int, int, int], 
                                           font: ImageFont.ImageFont) -> None:
        """绘制多行文本背景"""
        x, y = position
        
        # 计算所有文本的最大宽度和总高度
        max_width = 0
        total_height = 0
        line_height = self.config["text"]["line_height"]
        padding = self.config["text"]["padding"]
        
        for text in texts:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            max_width = max(max_width, text_width)
            total_height += line_height
        
        bg_width = max_width + padding * 2
        bg_height = total_height + padding * 2
        
        # 绘制背景
        bg_y = max(y - bg_height, 0)
        draw.rectangle(
            [x, bg_y, x + bg_width, bg_y + bg_height], 
            fill=color
        )
        
        # 绘制每行文本
        current_y = bg_y + padding
        for text in texts:
            draw.text(
                (x + padding, current_y), 
                text, 
                fill="white", 
                font=font
            )
            current_y += line_height
    
    def _draw_length_annotation(self, draw: ImageDraw.Draw, box: List[float], length_cm: float) -> None:
        """绘制长度标注线"""
        if not self.length_config["show_length_line"]:
            return
        
        x1, y1, x2, y2 = [int(coord) for coord in box]
        
        # 计算标注线位置
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        line_color = self.length_config["line_color"]
        line_width = self.length_config["line_width"]
        arrow_size = self.length_config["arrow_size"]
        text_offset = self.length_config["text_offset"]
        
        if width >= height:
            # 水平标注
            line_y = y1 - 30
            start_point = (x1, line_y)
            end_point = (x2, line_y)
            text_pos = ((x1 + x2) // 2, line_y - text_offset)
            
            # 绘制标注线
            draw.line([start_point, end_point], fill=line_color, width=line_width)
            
            # 绘制箭头
            draw.polygon([
                (x1, line_y),
                (x1 + arrow_size, line_y - arrow_size//2),
                (x1 + arrow_size, line_y + arrow_size//2)
            ], fill=line_color)
            
            draw.polygon([
                (x2, line_y),
                (x2 - arrow_size, line_y - arrow_size//2),
                (x2 - arrow_size, line_y + arrow_size//2)
            ], fill=line_color)
            
        else:
            # 垂直标注
            line_x = x1 - 30
            start_point = (line_x, y1)
            end_point = (line_x, y2)
            text_pos = (line_x - text_offset, (y1 + y2) // 2)
            
            # 绘制标注线
            draw.line([start_point, end_point], fill=line_color, width=line_width)
            
            # 绘制箭头
            draw.polygon([
                (line_x, y1),
                (line_x - arrow_size//2, y1 + arrow_size),
                (line_x + arrow_size//2, y1 + arrow_size)
            ], fill=line_color)
            
            draw.polygon([
                (line_x, y2),
                (line_x - arrow_size//2, y2 - arrow_size),
                (line_x + arrow_size//2, y2 - arrow_size)
            ], fill=line_color)
        
        # 绘制长度文本
        length_text = f"{length_cm:.{self.length_config['precision']}f}cm"
        self._draw_text_with_background(draw, length_text, text_pos, line_color, self.fonts["small"])
    
    def render_advanced_detection(self, image_path: str, detections: List[Dict[str, Any]], 
                                measurements: Dict[str, Any], output_path: str) -> str:
        """渲染高级检测结果"""
        try:
            # 读取图片
            img = self._read_image_from_source(image_path)
            draw = ImageDraw.Draw(img)
            
            print(f"开始渲染 {len(detections)} 个检测结果")
            
            # 分类处理检测结果
            pig_detections = []
            other_detections = []
            
            for detection in detections:
                class_id = detection["class_id"]
                print(f"处理检测对象 - 类别ID: {class_id}")
                
                if class_id == 0:  # 猪
                    pig_detections.append(detection)
                else:
                    # 其他对象（尺子、底座）
                    other_detections.append(detection)
            
            # 先绘制其他对象（尺子、底座）
            for detection in other_detections:
                self._draw_detection_box(draw, detection)
            
            # 然后绘制所有猪（带测量信息）
            for i, pig_detection in enumerate(pig_detections):
                if i == 0:
                    # 第一只猪显示测量信息
                    self._draw_pig_with_measurements(draw, pig_detection, measurements)
                else:
                    # 其他猪只显示基本信息
                    self._draw_pig_basic(draw, pig_detection)
            
            # 保存图片
            img.save(output_path, quality=95, optimize=True)
            print(f"✅ 可视化图片已保存: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 渲染错误: {e}")
            raise Exception(f"渲染高级可视化时出错: {str(e)}")
    
    def create_measurement_summary_image(self, measurements: Dict[str, Any], 
                                       output_path: str, width: int = 400, height: int = 300) -> str:
        """创建测量结果摘要图片"""
        # 创建白色背景图片
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # 标题
        title = "猪只测量结果"
        title_font = self.fonts["large"]
        
        # 计算标题位置
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        
        draw.text((title_x, 20), title, fill="black", font=title_font)
        
        # 测量信息
        y_offset = 80
        line_height = 30
        
        info_lines = []
        if measurements.get("length_cm"):
            info_lines.append(f"长度: {measurements['length_cm']:.1f} cm")
        
        if measurements.get("weight_kg"):
            weight_range = measurements.get("weight_range_kg")
            if weight_range:
                info_lines.append(f"重量: {measurements['weight_kg']:.1f} kg")
                info_lines.append(f"范围: {weight_range[0]:.1f} - {weight_range[1]:.1f} kg")
            else:
                info_lines.append(f"重量: {measurements['weight_kg']:.1f} kg")
        
        if measurements.get("calculation_method"):
            info_lines.append(f"方法: {measurements['calculation_method']}")
        
        if measurements.get("confidence"):
            info_lines.append(f"精度: {measurements['confidence']}")
        
        # 绘制信息行
        for line in info_lines:
            draw.text((20, y_offset), line, fill="black", font=self.fonts["small"])
            y_offset += line_height
        
        # 保存图片
        img.save(output_path, quality=95)
        return output_path