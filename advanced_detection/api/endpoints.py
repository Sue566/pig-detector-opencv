"""
高级检测API端点
提供FastAPI集成接口
"""

import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..core.detector import AdvancedPigDetector


class AdvancedPredictRequest(BaseModel):
    """高级预测请求模型"""
    image_path: str
    conf: float = 0.5
    top_k: int = 10
    return_visualization: bool = True
    return_summary: bool = False
    ruler_length_cm: float = 30.0
    base_length_cm: float = 60.0
    base_width_cm: float = 40.0
    output_format: str = "url"  # "url", "base64", "path"


class AdvancedPredictResponse(BaseModel):
    """高级预测响应模型"""
    code: int
    msg: str
    data: Optional[Dict[str, Any]] = None


def create_advanced_endpoints(app: FastAPI, model, predict_func, 
                            minio_config=None, minio_client=None, logger=None):
    """创建高级检测API端点"""
    
    detector = AdvancedPigDetector()
    
    @app.post("/api/predict_advanced", response_model=AdvancedPredictResponse)
    def predict_advanced(req: AdvancedPredictRequest):
        """高级预测接口 - 包含精确测量和可视化"""
        if logger:
            logger.info("/api/predict_advanced called with %s", req.image_path)
        
        try:
            if not req.image_path:
                return AdvancedPredictResponse(
                    code=400,
                    msg="图片路径不能为空",
                    data=None
                )
            
            # 执行基础检测
            raw_results = predict_func(model, req.image_path, conf=req.conf, top_k=req.top_k)
            
            if not raw_results or len(raw_results) == 0:
                return AdvancedPredictResponse(
                    code=500,
                    msg="检测失败或无检测结果",
                    data=None
                )
            
            # 获取图片尺寸（这里需要根据实际情况调整）
            try:
                from PIL import Image
                import requests
                from io import BytesIO
                
                if req.image_path.startswith("http"):
                    response = requests.get(req.image_path, timeout=10)
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(req.image_path)
                
                img_width, img_height = img.size
            except Exception as e:
                # 如果无法获取图片尺寸，使用默认值
                img_width, img_height = 1920, 1080
                if logger:
                    logger.warning(f"无法获取图片尺寸，使用默认值: {e}")
            
            # 处理检测结果
            detections, measurements = detector.process_detection_results(
                raw_results, img_width, img_height
            )
            
            # 更新测量参数
            if req.ruler_length_cm != 30.0 or req.base_length_cm != 60.0 or req.base_width_cm != 40.0:
                # 重新计算测量结果
                pig_box = None
                ruler_box = None
                base_box = None
                
                for detection in detections:
                    class_id = detection['class_id']
                    if class_id == 0:
                        pig_box = detection['box']
                    elif class_id == 1:
                        ruler_box = detection['box']
                    elif class_id == 2:
                        base_box = detection['box']
                
                measurements = detector.measurement_calculator.calculate_comprehensive_measurements(
                    pig_box, ruler_box, base_box,
                    ruler_length_cm=req.ruler_length_cm,
                    base_length_cm=req.base_length_cm,
                    base_width_cm=req.base_width_cm,
                    img_width=img_width, img_height=img_height
                )
            
            # 准备响应数据
            response_data = {
                'type': 'advanced_detection',
                'detections': detections,
                'measurements': measurements,
                'statistics': detector.get_detection_statistics(detections),
                'image_info': {
                    'width': img_width,
                    'height': img_height,
                    'source': req.image_path
                }
            }
            
            # 处理可视化
            if req.return_visualization:
                try:
                    # 确定输出目录和文件名
                    today = datetime.now()
                    date_path = f"{today.year:04d}/{today.month:02d}/{today.day:02d}"
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    if minio_config and minio_client:
                        # 使用Minio存储
                        filename = f"advanced_detection_{timestamp}.jpg"
                        object_name = f"media/pigdata/pig/{date_path}/{filename}"
                        
                        # 创建临时文件
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                            temp_path = tmp_file.name
                        
                        try:
                            # 创建可视化
                            detector.create_advanced_visualization(
                                req.image_path, detections, measurements, temp_path
                            )
                            
                            # 上传到Minio
                            client, secure = minio_client
                            bucket = minio_config["bucket"]
                            
                            with open(temp_path, 'rb') as f:
                                client.put_object(
                                    bucket_name=bucket,
                                    object_name=object_name,
                                    data=f,
                                    length=os.path.getsize(temp_path),
                                    content_type="image/jpeg",
                                )
                            
                            # 生成URL
                            base_url = minio_config["url"].rstrip("/")
                            result_url = f"{base_url}/{bucket}/{object_name}"
                            response_data['result_image_url'] = result_url
                            
                            if logger:
                                logger.info(f"高级可视化图片已保存: {result_url}")
                        
                        finally:
                            # 清理临时文件
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                    
                    else:
                        # 本地存储
                        output_dir = f"media/pigdata/pig/{date_path}"
                        os.makedirs(output_dir, exist_ok=True)
                        
                        filename = f"advanced_detection_{timestamp}.jpg"
                        output_path = os.path.join(output_dir, filename)
                        
                        detector.create_advanced_visualization(
                            req.image_path, detections, measurements, output_path
                        )
                        response_data['result_image_path'] = output_path
                        response_data['result_image_filename'] = filename
                
                except Exception as viz_error:
                    if logger:
                        logger.error(f"可视化生成失败: {viz_error}")
                    response_data['visualization_error'] = str(viz_error)
            
            # 处理摘要图片
            if req.return_summary and measurements.get('length_cm') is not None:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    summary_filename = f"measurement_summary_{timestamp}.jpg"
                    
                    if minio_config and minio_client:
                        # Minio存储摘要
                        object_name = f"media/pigdata/pig/{date_path}/{summary_filename}"
                        
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                            temp_path = tmp_file.name
                        
                        try:
                            detector.create_measurement_summary(measurements, temp_path)
                            
                            client, secure = minio_client
                            bucket = minio_config["bucket"]
                            
                            with open(temp_path, 'rb') as f:
                                client.put_object(
                                    bucket_name=bucket,
                                    object_name=object_name,
                                    data=f,
                                    length=os.path.getsize(temp_path),
                                    content_type="image/jpeg",
                                )
                            
                            base_url = minio_config["url"].rstrip("/")
                            summary_url = f"{base_url}/{bucket}/{object_name}"
                            response_data['summary_image_url'] = summary_url
                        
                        finally:
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                    
                    else:
                        # 本地存储摘要
                        output_dir = f"media/pigdata/pig/{date_path}"
                        os.makedirs(output_dir, exist_ok=True)
                        
                        summary_path = os.path.join(output_dir, summary_filename)
                        detector.create_measurement_summary(measurements, summary_path)
                        response_data['summary_image_path'] = summary_path
                
                except Exception as summary_error:
                    if logger:
                        logger.error(f"摘要生成失败: {summary_error}")
                    response_data['summary_error'] = str(summary_error)
            
            return AdvancedPredictResponse(
                code=200,
                msg="高级检测成功",
                data=response_data
            )
            
        except Exception as e:
            if logger:
                logger.error(f"高级预测失败: {e}")
            return AdvancedPredictResponse(
                code=500,
                msg=f"服务器内部错误: {str(e)}",
                data=None
            )
    
    @app.post("/api/calculate_measurements_only")
    def calculate_measurements_only(req: AdvancedPredictRequest):
        """仅计算测量结果，不生成可视化"""
        if logger:
            logger.info("/api/calculate_measurements_only called with %s", req.image_path)
        
        try:
            if not req.image_path:
                return AdvancedPredictResponse(
                    code=400,
                    msg="图片路径不能为空",
                    data=None
                )
            
            # 执行检测（不生成可视化）
            raw_results = predict_func(model, req.image_path, conf=req.conf, top_k=req.top_k)
            
            if not raw_results or len(raw_results) == 0:
                return AdvancedPredictResponse(
                    code=500,
                    msg="检测失败或无检测结果",
                    data=None
                )
            
            # 获取图片尺寸
            try:
                from PIL import Image
                import requests
                from io import BytesIO
                
                if req.image_path.startswith("http"):
                    response = requests.get(req.image_path, timeout=10)
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(req.image_path)
                
                img_width, img_height = img.size
            except Exception:
                img_width, img_height = 1920, 1080
            
            # 处理检测结果
            detections, measurements = detector.process_detection_results(
                raw_results, img_width, img_height
            )
            
            response_data = {
                'type': 'measurements_only',
                'measurements': measurements,
                'statistics': detector.get_detection_statistics(detections),
                'detections_count': len(detections),
                'image_info': {
                    'width': img_width,
                    'height': img_height,
                    'source': req.image_path
                }
            }
            
            return AdvancedPredictResponse(
                code=200,
                msg="测量计算成功",
                data=response_data
            )
            
        except Exception as e:
            if logger:
                logger.error(f"测量计算失败: {e}")
            return AdvancedPredictResponse(
                code=500,
                msg=f"服务器内部错误: {str(e)}",
                data=None
            )
    
    return app