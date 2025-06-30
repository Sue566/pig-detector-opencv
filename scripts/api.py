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
WEIGHTS_PATH = Path(os.environ.get("WEIGHTS_PATH", ROOT / "models" / "best_model.pth")).resolve()

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
    result_type = "pig" if results else "other"
    logger.info("Prediction done, type=%s, count=%d", result_type, len(results))
    return {"type": result_type, "results": results}


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
    port = 8000
    logger.info("Starting API on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)

