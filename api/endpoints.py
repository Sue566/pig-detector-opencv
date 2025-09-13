"""
API端点定义
"""
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.logging_utils import setup_logging
from scripts.predict import load_model, predict_image_with_model
from .config import CFG_PATH, WEIGHTS_PATH, API_TITLE, API_VERSION, TEMP_DIR
from .models import (
    PredictRequest, PredictImageRequest, PredictResponse, 
    HealthResponse, DetectionResult, MeasurementResult
)
from .utils import (
    generate_result_filename, generate_result_url, read_image_from_source,
    calculate_pig_length_from_ruler, calculate_pig_length_from_base,
    estimate_pig_weight, get_class_name, choose_largest_box,
    draw_advanced_visualization, upload_image_to_minio, load_minio_config
)

# 设置日志
logger = setup_logging("pig_detector_api")

# 创建FastAPI应用
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="猪只检测与测量API - 支持长度和重量计算"
)

# 全局变量存储模型
MODEL = None
MODEL_META = {}

@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    global MODEL, MODEL_META
    logger.info("正在加载模型: %s", WEIGHTS_PATH)
    try:
        MODEL, MODEL_META = load_model(str(CFG_PATH), str(WEIGHTS_PATH))
        logger.info("模型加载成功")
    except Exception as e:
        logger.error("模型加载失败: %s", e)
        raise e


@app.get("/", response_class=HTMLResponse)
def root():
    """根路径 - 显示完整的项目说明页面"""
    logger.info("根路径访问，显示项目说明页面")
    
    # 读取HTML模板文件
    template_path = Path(__file__).parent / "templates" / "index.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.warning("HTML模板文件未找到，重定向到API文档")
        return RedirectResponse(url="/docs")
    except Exception as e:
        logger.error("读取HTML模板失败: %s", e)
        return RedirectResponse(url="/docs")

@app.get("/home", response_class=HTMLResponse)
def home():
    """主页 - 显示完整的项目说明页面"""
    return root()


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """健康检查"""
    logger.info("健康检查")
    return HealthResponse(
        status="healthy",
        version=MODEL_META.get("version", "unknown"),
        trained_at=MODEL_META.get("trained_at", "unknown")
    )

@app.get("/info", response_model=HealthResponse)
def get_info():
    """获取API信息"""
    logger.info("API信息查询")
    return HealthResponse(
        status="running",
        version=MODEL_META.get("version", "unknown"),
        trained_at=MODEL_META.get("trained_at", "unknown")
    )


@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """
    猪只检测与测量API
    返回检测结果、测量数据和可视化图片URL
    """
    logger.info("预测请求: %s", req.image_path)

    if not req.image_path or req.image_path.strip() == "":
        raise HTTPException(status_code=400, detail="image_path不能为空")

    try:
        # 执行检测
        results = predict_image_with_model(
            MODEL, req.image_path, conf=req.conf, top_k=req.top_k
        )
    except FileNotFoundError as e:
        logger.error("图片未找到: %s", e)
        raise HTTPException(status_code=400, detail=f"图片未找到: {req.image_path}")
    except Exception as e:
        logger.exception("预测失败: %s", e)
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")

    # 统计检测结果
    detection_summary = {"pig": 0, "ruler": 0, "scale": 0, "total": len(results)}
    
    # 分类收集检测框
    pigs = []
    rulers = []
    bases = []

    for det in results or []:
        box = det.get("box")
        if not box or len(box) != 4:
            continue
            
        class_id = det.get("class_id", 0)
        class_name = get_class_name(class_id).lower()
        
        if "pig" in class_name or class_id == 0:
            detection_summary["pig"] += 1
            pigs.append(box)
        elif "ruler" in class_name or class_id == 1:
            detection_summary["ruler"] += 1
            rulers.append(box)
        elif "base" in class_name or "scale" in class_name or class_id == 2:
            detection_summary["scale"] += 1
            bases.append(box)

    # 选择最大的参考对象
    ruler_box = choose_largest_box(rulers)
    base_box = choose_largest_box(bases)

    # 计算每只猪的测量数据
    measurements = []
    for idx, pig_box in enumerate(pigs):
        length_cm = None
        method = None
        used_ref = None
        
        # 优先使用尺子
        if ruler_box is not None:
            length_cm = calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30.0)
            method = "基于尺子(30cm)"
            used_ref = {"type": "ruler", "box": ruler_box}
        # 否则使用底座
        elif base_box is not None:
            length_cm = calculate_pig_length_from_base(pig_box, base_box, base_length_cm=60.0, base_width_cm=40.0)
            method = "基于底座(60x40cm)"
            used_ref = {"type": "base", "box": base_box}

        # 估算重量
        est_weight, weight_range = estimate_pig_weight(length_cm)

        measurements.append({
            "pig_index": idx,
            "pig_box": pig_box,
            "length_cm": length_cm,
            "length_method": method,
            "used_reference": used_ref,
            "estimated_weight_kg": est_weight,
            "weight_range_kg": weight_range,
        })

    # 生成可视化图片并上传到MinIO
    result_image_url = None
    try:
        # 读取原图
        img = read_image_from_source(req.image_path)
        
        # 绘制可视化结果
        vis_img = draw_advanced_visualization(img, results, measurements)
        
        # 编码图片为JPEG格式
        success, buffer = cv2.imencode('.jpg', vis_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not success:
            raise ValueError("图片编码失败")
        
        # 生成对象名称（MinIO中的路径）
        relative_path = generate_result_filename(req.image_path, "detection_results")
        # 提取文件名部分作为对象名
        if relative_path.startswith("media/pigdata/pig/"):
            object_name = relative_path[len("media/pigdata/pig/"):]
        else:
            object_name = relative_path
        
        # 上传到MinIO
        upload_success, result_image_url = upload_image_to_minio(
            buffer.tobytes(), 
            object_name
        )
        
        if upload_success:
            logger.info("✅ 可视化图片已上传到MinIO: %s", result_image_url)
        else:
            logger.warning("⚠️ MinIO上传失败，返回预期URL: %s", result_image_url)
            
        # 同时保存到本地临时目录作为备份
        temp_filename = f"result_{int(time.time())}.jpg"
        temp_path = TEMP_DIR / temp_filename
        cv2.imwrite(str(temp_path), vis_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        logger.info("本地备份已保存: %s", temp_path)
            
    except Exception as e:
        logger.exception("可视化生成失败: %s", e)

    logger.info(
        "预测完成 - 检测摘要: %s, 猪数量: %d, 尺子: %s, 底座: %s",
        detection_summary, len(pigs), bool(ruler_box), bool(base_box)
    )

    return PredictResponse(
        code=0,
        data={
            "detection_summary": detection_summary,
            "measurements": measurements,
            "result_image_url": result_image_url,
        },
        msg="success"
    )


@app.post("/api/predict_image")
def predict_image(req: PredictImageRequest):
    """
    预测并直接返回可视化图片
    """
    logger.info("图片预测请求: %s", req.image_path)
    
    try:
        # 读取图片
        img = read_image_from_source(req.image_path)
        
        # 执行检测
        results = predict_image_with_model(MODEL, req.image_path, conf=req.conf, top_k=req.top_k)

        # 计算测量数据（简化版本）
        pigs = []
        rulers = []
        bases = []

        for det in results or []:
            box = det.get("box")
            if not box or len(box) != 4:
                continue
                
            class_id = det.get("class_id", 0)
            class_name = get_class_name(class_id).lower()
            
            if "pig" in class_name or class_id == 0:
                pigs.append(box)
            elif "ruler" in class_name or class_id == 1:
                rulers.append(box)
            elif "base" in class_name or "scale" in class_name or class_id == 2:
                bases.append(box)

        ruler_box = choose_largest_box(rulers)
        base_box = choose_largest_box(bases)

        measurements = []
        for idx, pig_box in enumerate(pigs):
            length_cm = None
            method = None
            
            if ruler_box is not None:
                length_cm = calculate_pig_length_from_ruler(pig_box, ruler_box, 30.0)
                method = "基于尺子(30cm)"
            elif base_box is not None:
                length_cm = calculate_pig_length_from_base(pig_box, base_box, 60.0)
                method = "基于底座(60x40cm)"
                
            est_weight, weight_range = estimate_pig_weight(length_cm)
            
            measurements.append({
                "pig_index": idx,
                "pig_box": pig_box,
                "length_cm": length_cm,
                "length_method": method,
                "estimated_weight_kg": est_weight,
                "weight_range_kg": weight_range,
            })

        # 绘制可视化
        vis_img = draw_advanced_visualization(img, results, measurements)
        
        # 编码图片
        fmt = (req.format or "jpeg").lower()
        fmt = "jpeg" if fmt in ("jpg", "jpeg") else "png"
        ext = ".jpg" if fmt == "jpeg" else ".png"
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 92] if fmt == "jpeg" else []
        
        success, buffer = cv2.imencode(ext, vis_img, encode_params)
        if not success:
            raise ValueError("图片编码失败")
            
        media_type = "image/jpeg" if fmt == "jpeg" else "image/png"
        return Response(content=buffer.tobytes(), media_type=media_type)
        
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"图片未找到: {req.image_path}")
    except Exception as e:
        logger.exception("图片预测失败: %s", e)
        raise HTTPException(status_code=500, detail="图片预测失败")


@app.get("/api/version")
def get_version():
    """获取API版本信息"""
    logger.info("版本信息请求")
    return {
        "api_version": API_VERSION,
        "model_version": MODEL_META.get("version", "unknown"),
        "trained_at": MODEL_META.get("trained_at", "unknown"),
    }


# 导出app实例
__all__ = ["app"]