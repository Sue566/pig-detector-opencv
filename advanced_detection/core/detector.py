"""
高级猪检测器
整合检测、测量和可视化功能
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .measurement import MeasurementCalculator
from ..visualization.renderer import AdvancedRenderer


class AdvancedPigDetector:
    """高级猪检测器"""
    
    def __init__(self):
        self.measurement_calculator = MeasurementCalculator()
        self.renderer = AdvancedRenderer()
    
    def process_detection_results(self, raw_results: List[Dict[str, Any]], 
                                img_width: int, img_height: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """处理原始检测结果，转换为像素坐标并分类"""
        
        processed_detections = []
        pig_box = None
        ruler_box = None
        base_box = None
        
        for result in raw_results:
            if not isinstance(result, dict):
                continue
            
            class_id = result.get('class_id', 0)
            confidence = result.get('confidence', result.get('score', 0.0))
            bbox = result.get('bbox', result.get('box'))
            
            if not bbox or len(bbox) != 4:
                continue
            
            # 检查是否需要坐标转换
            if all(v <= 1.0 for v in bbox):
                # YOLO格式，需要转换为像素坐标
                pixel_box, width_px, height_px = self.measurement_calculator.yolo_to_pixel(
                    bbox, img_width, img_height
                )
            else:
                # 已经是像素坐标
                pixel_box = bbox
                width_px = abs(bbox[2] - bbox[0])
                height_px = abs(bbox[3] - bbox[1])
            
            processed_detection = {
                'class_id': class_id,
                'confidence': confidence,
                'box': pixel_box,
                'width_px': width_px,
                'height_px': height_px
            }
            
            processed_detections.append(processed_detection)
            
            # 保存特定对象的边界框用于测量
            if class_id == 0:  # pig
                pig_box = pixel_box
            elif class_id == 1:  # ruler
                ruler_box = pixel_box
            elif class_id == 2:  # base
                base_box = pixel_box
        
        # 计算综合测量结果
        measurements = self.measurement_calculator.calculate_comprehensive_measurements(
            pig_box, ruler_box, base_box,
            img_width=img_width, img_height=img_height
        )
        
        return processed_detections, measurements
    
    def create_advanced_visualization(self, image_path: str, detections: List[Dict[str, Any]], 
                                    measurements: Dict[str, Any], output_path: str = None) -> str:
        """创建高级可视化图片"""
        
        if output_path is None:
            # 生成默认输出路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"advanced_detection_{timestamp}.jpg"
        
        return self.renderer.render_advanced_detection(image_path, detections, measurements, output_path)
    
    def create_measurement_summary(self, measurements: Dict[str, Any], output_path: str = None) -> str:
        """创建测量结果摘要图片"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"measurement_summary_{timestamp}.jpg"
        
        return self.renderer.create_measurement_summary_image(measurements, output_path)
    
    def process_complete_detection(self, image_path: str, raw_results: List[Dict[str, Any]], 
                                 img_width: int, img_height: int,
                                 create_visualization: bool = True,
                                 output_dir: str = None) -> Dict[str, Any]:
        """完整的检测处理流程"""
        
        # 处理检测结果
        detections, measurements = self.process_detection_results(raw_results, img_width, img_height)
        
        result = {
            'detections': detections,
            'measurements': measurements,
            'image_info': {
                'width': img_width,
                'height': img_height,
                'source': image_path
            }
        }
        
        # 创建可视化
        if create_visualization:
            try:
                # 确定输出目录
                if output_dir is None:
                    output_dir = "temp"
                
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                viz_filename = f"advanced_detection_{timestamp}.jpg"
                viz_path = os.path.join(output_dir, viz_filename)
                
                # 创建可视化
                self.create_advanced_visualization(image_path, detections, measurements, viz_path)
                result['visualization_path'] = viz_path
                result['visualization_filename'] = viz_filename
                
                # 如果有测量结果，也创建摘要图片
                if measurements.get('length_cm') is not None:
                    summary_filename = f"measurement_summary_{timestamp}.jpg"
                    summary_path = os.path.join(output_dir, summary_filename)
                    self.create_measurement_summary(measurements, summary_path)
                    result['summary_path'] = summary_path
                    result['summary_filename'] = summary_filename
                
            except Exception as e:
                result['visualization_error'] = str(e)
        
        return result
    
    def get_detection_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取检测统计信息"""
        stats = {
            'total_detections': len(detections),
            'pig_count': 0,
            'ruler_count': 0,
            'base_count': 0,
            'confidence_scores': []
        }
        
        for detection in detections:
            class_id = detection.get('class_id', 0)
            confidence = detection.get('confidence', 0.0)
            
            stats['confidence_scores'].append(confidence)
            
            if class_id == 0:
                stats['pig_count'] += 1
            elif class_id == 1:
                stats['ruler_count'] += 1
            elif class_id == 2:
                stats['base_count'] += 1
        
        if stats['confidence_scores']:
            stats['avg_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
            stats['min_confidence'] = min(stats['confidence_scores'])
            stats['max_confidence'] = max(stats['confidence_scores'])
        
        return stats