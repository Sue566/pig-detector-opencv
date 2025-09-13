from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys


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

