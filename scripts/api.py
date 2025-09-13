from pathlib import Path
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import os
import sys
import requests
import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.logging_utils import setup_logging

from scripts.predict import load_model, predict_image_with_model

logger = setup_logging("api")
app = FastAPI(title="Pig Detector API")

# Use project root for default config and weights paths
CFG_PATH = Path(os.environ.get("CFG_PATH", ROOT / "config.yaml")).resolve()
WEIGHTS_PATH = Path(os.environ.get("WEIGHTS_PATH", ROOT / "models" / "v1_model.pth")).resolve()

# Load the model once at startup
logger.info("Loading model from %s", WEIGHTS_PATH)
MODEL, MODEL_META = load_model(str(CFG_PATH), str(WEIGHTS_PATH))
logger.info("Model loaded")


class PredictRequest(BaseModel):
    image_path: str
    conf: float = 0.5
    top_k: int | None = 10


@app.post("/api/predict")
def predict(req: PredictRequest):
    logger.info("/predict called with %s", req.image_path)
    try:
        results = predict_image_with_model(
            MODEL, req.image_path, conf=req.conf, top_k=req.top_k
        )
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Image not found: {req.image_path}")
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(status_code=500, detail="Prediction failed")
    
    # 分析检测结果，统计各类型数量
    detection_summary = {"pig": 0, "ruler": 0, "scale": 0, "total": len(results)}
    
    # 假设results中包含class_id或class_name字段
    # 如果没有，我们需要修改predict_image_with_model函数
    for result in results:
        # 这里需要根据实际的结果格式来判断类型
        # 暂时基于检测框的特征来推断类型
        box = result.get('box', [])
        if len(box) == 4:
            width = abs(box[2] - box[0])
            height = abs(box[3] - box[1])
            aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1
            
            # 简单的类型推断逻辑（需要根据实际模型输出调整）
            if aspect_ratio > 5:  # 长条形，可能是尺子
                detection_summary["ruler"] += 1
            elif aspect_ratio < 2 and width * height > 10000:  # 较大的方形区域，可能是秤
                detection_summary["scale"] += 1
            else:  # 其他情况认为是猪
                detection_summary["pig"] += 1
    
    # 确定主要检测类型
    if detection_summary["pig"] > 0:
        primary_type = "pig"
    elif detection_summary["ruler"] > 0:
        primary_type = "ruler"
    elif detection_summary["scale"] > 0:
        primary_type = "scale"
    else:
        primary_type = "other"
    
    logger.info("Prediction done, primary_type=%s, summary=%s", primary_type, detection_summary)
    
    return {
        "type": primary_type,
        "detection_summary": detection_summary,
        "results": results
    }


@app.get("/")
def root():
    """Return model version at root path"""
    logger.info("/ called")
    return {
        "version": MODEL_META.get("version", "unknown"),
        "trained_at": MODEL_META.get("trained_at", "unknown"),
    }


def _read_image_any(image_path: str) -> np.ndarray:
    # 支持本地文件和 http/https
    if image_path.startswith("http://") or image_path.startswith("https://"):
        r = requests.get(image_path, timeout=10)
        r.raise_for_status()
        data = np.frombuffer(r.content, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法解码远程图片")
        return img
    else:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法读取本地图片")
        return img


def _draw_results_on_image(img: np.ndarray, results):
    out = img.copy()
    for det in results or []:
        box = det.get("box") if isinstance(det, dict) else None
        if not box or len(box) != 4:
            continue
        try:
            x1, y1, x2, y2 = [int(round(float(v))) for v in box]
        except Exception:
            continue

        cls_name = None
        score = None
        if isinstance(det, dict):
            cls_name = det.get("class_name") or det.get("label") or det.get("name") or "object"
            score = det.get("score") or det.get("confidence")

        color = (0, 255, 0)  # 绿色框
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        text = cls_name or "object"
        try:
            if score is not None:
                text = f"{text} {float(score):.2f}"
        except Exception:
            pass

        (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        y_text = max(y1 - 10, th + 4)
        cv2.rectangle(out, (x1, y_text - th - 4), (x1 + tw + 4, y_text + baseline - 2), (0, 255, 0), -1)
        cv2.putText(out, text, (x1 + 2, y_text - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    return out


class PredictImageRequest(BaseModel):
    image_path: str
    conf: float = 0.5
    top_k: int | None = 10
    format: str = "jpeg"  # "jpeg" 或 "png"


@app.post("/api/predict_image")
def predict_image(req: PredictImageRequest):
    logger.info("/api/predict_image called with %s", req.image_path)
    try:
        # 1) 读取图像
        img = _read_image_any(req.image_path)

        # 2) 推理（沿用原有推理函数，确保与 /api/predict 一致）
        results = predict_image_with_model(MODEL, req.image_path, conf=req.conf, top_k=req.top_k)

        # 3) 绘制
        vis = _draw_results_on_image(img, results)

        # 4) 编码并返回
        fmt = (req.format or "jpeg").lower()
        fmt = "jpeg" if fmt in ("jpg", "jpeg") else "png"
        ext = ".jpg" if fmt == "jpeg" else ".png"
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 92] if fmt == "jpeg" else []
        ok, buf = cv2.imencode(ext, vis, encode_params)
        if not ok:
            raise ValueError("图像编码失败")

        media_type = "image/jpeg" if fmt == "jpeg" else "image/png"
        return Response(content=buf.tobytes(), media_type=media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Image not found: {req.image_path}")
    except requests.RequestException as e:
        logger.exception("下载远程图片失败: %s", e)
        raise HTTPException(status_code=400, detail="无法下载远程图片")
    except Exception as e:
        logger.exception("predict_image 失败: %s", e)
        raise HTTPException(status_code=500, detail="Prediction image failed")


@app.get("/api/version")
def version():
    """Return model version and training time if available."""
    logger.info("/version called")
    return {
        "version": MODEL_META.get("version", "unknown"),
        "trained_at": MODEL_META.get("trained_at", "unknown"),
    }

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = 8092
    logger.info("Starting API on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)

