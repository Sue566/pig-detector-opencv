#!/usr/bin/env python3
"""
Pig Detector API - 加入改进的长度/重量计算方法（基于尺子或底座）
这个文件在原有基础上将测量逻辑替换为之前提供的更稳健函数：
- calculate_pig_length_from_ruler
- calculate_pig_length_from_base
- estimate_pig_weight
并对每个检测到的猪分别返回长度与估重结果。
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import os
import sys
import time
import urllib.parse
import requests
import cv2
import numpy as np
import yaml
from minio import Minio
from minio.error import S3Error
from PIL import Image, ImageDraw, ImageFont

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

# 读取 Minio 配置（从 config.yaml）
def _load_minio_config(cfg_path: Path):
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        minio_cfg = (cfg.get("minio") or {}) if isinstance(cfg, dict) else {}
        url = str(minio_cfg.get("url") or "").rstrip("/")
        access_key = minio_cfg.get("accessKey")
        secret_key = minio_cfg.get("secretKey")
        bucket = minio_cfg.get("bucketName")
        if not (url and access_key and secret_key and bucket):
            logger.warning("Minio config is incomplete or missing in %s", cfg_path)
            return None
        return {
            "url": url,
            "access_key": access_key,
            "secret_key": secret_key,
            "bucket": bucket,
        }
    except Exception as e:
        logger.warning("Failed to load minio config: %s", e)
        return None

MINIO_CFG = _load_minio_config(CFG_PATH)

def _make_minio_client(cfg):
    if not cfg:
        return None
    try:
        parsed = urllib.parse.urlparse(cfg["url"])
        secure = parsed.scheme == "https"
        endpoint = parsed.netloc
        client = Minio(
            endpoint=endpoint,
            access_key=cfg["access_key"],
            secret_key=cfg["secret_key"],
            secure=secure,
        )
        return client, secure
    except Exception as e:
        logger.warning("Create Minio client failed: %s", e)
        return None

MINIO_CLIENT_SECURE = _make_minio_client(MINIO_CFG)


# ----- 新增/改进的测量函数 (复用之前的实现) -----

def calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30.0):
    """根据尺子像素长度计算猪的长度（cm）。pig_box 和 ruler_box 均为 [x1,y1,x2,y2]（像素）。"""
    try:
        pig_w_px = abs(pig_box[2] - pig_box[0])
        pig_h_px = abs(pig_box[3] - pig_box[1])
        pig_len_px = max(pig_w_px, pig_h_px)

        ruler_w_px = abs(ruler_box[2] - ruler_box[0])
        ruler_h_px = abs(ruler_box[3] - ruler_box[1])
        ruler_len_px = max(ruler_w_px, ruler_h_px)

        if ruler_len_px <= 0:
            return None
        scale_cm_per_px = ruler_length_cm / float(ruler_len_px)
        return pig_len_px * scale_cm_per_px
    except Exception:
        return None


def calculate_pig_length_from_base(pig_box, base_box, base_length_cm=60.0, base_width_cm=40.0):
    """根据底座尺寸估算猪的长度（cm）。
    假定底座的长边为 base_length_cm，短边为 base_width_cm。使用底座长边作为尺度。
    """
    try:
        base_w_px = abs(base_box[2] - base_box[0])
        base_h_px = abs(base_box[3] - base_box[1])
        pig_w_px = abs(pig_box[2] - pig_box[0])
        pig_h_px = abs(pig_box[3] - pig_box[1])
        pig_len_px = max(pig_w_px, pig_h_px)
        if base_w_px >= base_h_px and base_w_px > 0:
            scale = base_length_cm / float(base_w_px)
        elif base_h_px > 0:
            scale = base_length_cm / float(base_h_px)
        else:
            return None
        return pig_len_px * scale
    except Exception:
        return None


def estimate_pig_weight(length_cm: float, k: float = 0.002, error_pct: float = 0.20):
    """估计重量：weight (kg) = k * length(cm) ** 2.5，返回 (est, (min, max)) 或 (None, None)"""
    if length_cm is None:
        return None, None
    est = k * (length_cm ** 2.5)
    return est, (est * (1 - error_pct), est * (1 + error_pct))


# ----- API 与 辅助函数 -----

class PredictRequest(BaseModel):
    image_path: str
    conf: float = 0.5
    top_k: int | None = 10


@app.post("/api/predict")
def predict(req: PredictRequest):
    logger.info("/predict called with %s", req.image_path)

    if not req.image_path or req.image_path.strip() == "":
        raise HTTPException(status_code=400, detail="image_path cannot be empty")

    try:
        results = predict_image_with_model(
            MODEL, req.image_path, conf=req.conf, top_k=req.top_k
        )
    except FileNotFoundError as e:
        logger.error("Image not found: %s", e)
        raise HTTPException(status_code=400, detail=f"Image not found: {req.image_path}")
    except requests.RequestException as e:
        logger.error("Failed to download image: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to download image from URL: {req.image_path}")
    except Exception as e:
        logger.exception("Prediction failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # 统计
    detection_summary = {"pig": 0, "ruler": 0, "scale": 0, "total": len(results)}

    def _cls_name_of(det):
        if isinstance(det, dict):
            name = det.get("class_name") or det.get("label") or det.get("name")
            if name:
                return str(name).lower()
            cid = det.get("class_id")
            if cid is not None:
                m = {0: "pig", 1: "ruler", 2: "base"}
                return m.get(cid, f"class_{cid}")
        return "object"

    # 收集所有关键框（像素坐标）
    pigs = []
    rulers = []
    bases = []

    for det in results or []:
        box = det.get("box") if isinstance(det, dict) else None
        if not box or len(box) != 4:
            continue
        name = _cls_name_of(det)
        if "pig" in name:
            detection_summary["pig"] += 1
            pigs.append(box)
        elif "ruler" in name:
            detection_summary["ruler"] += 1
            rulers.append(box)
        elif "base" in name or "scale" in name:
            detection_summary["scale"] += 1
            bases.append(box)

    # 进行逐只猪的测量（如果有）
    measurements = []

    # 选择参考尺子/底座：如果检测到了多个，优先选择面积最大的（通常更近、更完整）
    def _choose_largest(boxes):
        if not boxes:
            return None
        def area(b):
            return abs(b[2]-b[0]) * abs(b[3]-b[1])
        return max(boxes, key=area)

    ruler_box = _choose_largest(rulers)
    base_box = _choose_largest(bases)

    for idx, pig_box in enumerate(pigs):
        length_cm = None
        method = None
        used_ref = None
        # 优先使用尺子（选择最大的那一根）
        if ruler_box is not None:
            length_cm = calculate_pig_length_from_ruler(pig_box, ruler_box, ruler_length_cm=30.0)
            method = "ruler_30cm"
            used_ref = {
                "type": "ruler",
                "box": ruler_box
            }
        # 否则尝试底座
        if length_cm is None and base_box is not None:
            length_cm = calculate_pig_length_from_base(pig_box, base_box, base_length_cm=60.0, base_width_cm=40.0)
            method = "base_60x40cm"
            used_ref = {
                "type": "base",
                "box": base_box
            }

        est_w, est_range = estimate_pig_weight(length_cm)

        measurements.append({
            "pig_index": idx,
            "pig_box": pig_box,
            "length_cm": length_cm,
            "length_method": method,
            "used_reference": used_ref,
            "estimated_weight_kg": est_w,
            "weight_range_kg": est_range,
        })

    # 日志
    logger.info(
        "Prediction done, summary=%s, pigs=%d, ruler=%s, base=%s",
        detection_summary, len(pigs), bool(ruler_box), bool(base_box)
    )

    # 可视化并尝试上传至 Minio（若配置存在）
    result_image_url = None
    try:
        img = _read_image_any(req.image_path)
        # 这里使用改写的绘图函数，它会对每个猪绘制各自测量信息
        vis = _draw_results_on_image(img, results, measurements)

        # 生成输出名
        parsed_name = None
        if req.image_path.startswith("http://") or req.image_path.startswith("https://"):
            parsed = urllib.parse.urlparse(req.image_path)
            q = urllib.parse.parse_qs(parsed.query)
            prefix_vals = q.get("prefix") or []
            if prefix_vals:
                decoded = urllib.parse.unquote(prefix_vals[0])
                parsed_name = decoded.split("/")[-1]
            if not parsed_name:
                parsed_name = os.path.basename(parsed.path) or "image.jpg"
        else:
            parsed_name = os.path.basename(req.image_path)

        name, ext = os.path.splitext(parsed_name)
        if not ext:
            ext = ".jpg"
        ts = int(time.time())
        out_name = f"{name}_pred_{ts}{ext}"

        # 为了确保返回的 result_image_url 与期望格式一致，我们直接使用 object_name = out_name
        object_name = out_name

        ok, buf = cv2.imencode(".jpg", vis, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise ValueError("图像编码失败")

        # 如果配置了 Minio 并上传成功，则使用真实上传；无论如何都构建出统一格式的 result_image_url
        uploaded = False
        if MINIO_CFG and MINIO_CLIENT_SECURE:
            client, secure = MINIO_CLIENT_SECURE
            bucket = MINIO_CFG["bucket"]
            try:
                if not client.bucket_exists(bucket):
                    client.make_bucket(bucket)
            except S3Error as e:
                logger.info("Bucket check/create: %s", e)

            from io import BytesIO
            data_stream = BytesIO(buf.tobytes())
            data_stream.seek(0)
            try:
                client.put_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    data=data_stream,
                    length=len(data_stream.getbuffer()),
                    content_type="image/jpeg",
                )
                uploaded = True
            except Exception as e:
                logger.warning("Minio upload failed: %s", e)

        # 构造统一的下载 URL（仅字符串格式），无论是否实际上传成功都返回此格式
        if MINIO_CFG:
            base = MINIO_CFG["url"].rstrip("/")
            prefix_q = urllib.parse.quote(object_name, safe="")
            result_image_url = f"{base}/api/v1/buckets/{MINIO_CFG['bucket']}/objects/download?preview=true&prefix={prefix_q}"
        else:
            # 若没有配置 Minio，返回本地推测的文件名路径（仍然保持同样的 query 参数样式）
            result_image_url = f"http://{parsed.hostname if parsed_name and req.image_path.startswith('http') else 'localhost'}/api/v1/buckets/huangshi-mini/objects/download?preview=true&prefix={urllib.parse.quote(object_name, safe='')}"
    except Exception as e:
        logger.warning("Visualization/Upload skipped: %s", e)

    return {
        "code": 0,
        "data": {
            "detection_summary": detection_summary,
            "measurements": measurements,
            "result_image_url": result_image_url,
        },
        "msg": "success"
    }


@app.get("/")
def root():
    logger.info("/ called")
    return {
        "version": MODEL_META.get("version", "unknown"),
        "trained_at": MODEL_META.get("trained_at", "unknown"),
    }


# 读取图片（cv2）
def _read_image_any(image_path: str) -> np.ndarray:
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


# 绘制检测结果并对每只猪显示对应的长度/重量信息
def _draw_results_on_image(img, results, measurements=None):
    """
    在图像上绘制检测结果（使用PIL），兼容：
    - 输入 img 为 numpy.ndarray (BGR) 或 PIL.Image
    - 检测框可以是 YOLO 归一化格式 (x_center,y_center,w,h) 或 像素坐标 (x1,y1,x2,y2)
    - measurements 可选，若提供会为每只猪显示长度/重量信息

    返回：BGR numpy.ndarray（便于后续使用 cv2.imencode）
    """
    # 转换为 PIL.Image（RGB）
    if isinstance(img, np.ndarray):
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    elif isinstance(img, Image.Image):
        pil_img = img.convert("RGB")
    else:
        pil_img = Image.fromarray(np.array(img)).convert("RGB")

    draw = ImageDraw.Draw(pil_img)

    # 字体
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

    img_w, img_h = pil_img.size

    def _to_pixel_box(box):
        """把 box 转为像素坐标 [x1,y1,x2,y2]（浮点），支持 YOLO 归一化或像素坐标。
        规则：若所有值均 <= 1 则认为是 YOLO 格式 (xc,yc,w,h)，否则认为是像素坐标 (x1,y1,x2,y2)。"""
        try:
            arr = [float(v) for v in box]
        except Exception:
            return None
        if max(arr) <= 1.0:
            # YOLO (x_center, y_center, w, h)
            xc, yc, bw, bh = arr
            x_c_px = xc * img_w
            y_c_px = yc * img_h
            bw_px = bw * img_w
            bh_px = bh * img_h
            x1 = x_c_px - bw_px / 2.0
            y1 = y_c_px - bh_px / 2.0
            x2 = x_c_px + bw_px / 2.0
            y2 = y_c_px + bh_px / 2.0
            return [x1, y1, x2, y2]
        else:
            # 像素坐标
            return [arr[0], arr[1], arr[2], arr[3]]

    def _cls_name_of(det):
        if isinstance(det, dict):
            name = det.get("class_name") or det.get("label") or det.get("name")
            if name:
                return str(name).lower()
            cid = det.get("class_id")
            if cid is not None:
                m = {0: "pig", 1: "ruler", 2: "base"}
                return m.get(cid, f"class_{cid}")
        return "object"

    # 颜色映射（按照你的要求：pig / ruler / scale(base) 使用不同颜色）
    color_map = {
        "pig": "red",
        "ruler": "blue",
        "base": "green",
        "scale": "orange",
    }

    # 先画检测框与简单标签
    for det in results or []:
        box = det.get("box") if isinstance(det, dict) else None
        if not box or len(box) != 4:
            continue
        pix = _to_pixel_box(box)
        if pix is None:
            continue
        x1, y1, x2, y2 = [int(round(v)) for v in pix]
        name_low = _cls_name_of(det)
        color = color_map.get(name_low, "yellow")

        # 绘制矩形（PIL 的 outline 接受颜色名）
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # 标签文本
        score = det.get("score") or det.get("confidence") or 0.0
        label = f"{det.get('class_name') or det.get('label') or det.get('name') or name_low}: {float(score):.2f}"
        tb = draw.textbbox((0, 0), label, font=font)
        text_w = tb[2] - tb[0]
        text_h = tb[3] - tb[1]
        # 背景
        draw.rectangle([x1, y1 - text_h - 6, x1 + text_w + 6, y1], fill=color)
        draw.text((x1 + 3, y1 - text_h - 3), label, fill="white", font=font)

    # 如果有 measurements，则为每只猪绘制长度/重量信息
    if measurements:
        for m in measurements:
            pig_box = m.get("pig_box")
            if not pig_box:
                continue
            pix = _to_pixel_box(pig_box)
            if pix is None:
                continue
            x1, y1, x2, y2 = [int(round(v)) for v in pix]

            texts = []
            if m.get("length_cm") is not None:
                texts.append(f"长度: {m['length_cm']:.1f}cm")
            else:
                texts.append("长度: N/A")
            if m.get("estimated_weight_kg") is not None:
                est = m['estimated_weight_kg']
                rng = m.get('weight_range_kg')
                if rng:
                    texts.append(f"重量: {est:.1f}kg ({rng[0]:.1f}-{rng[1]:.1f}kg)")
                else:
                    texts.append(f"重量: {est:.1f}kg")
            else:
                texts.append("重量: N/A")
            texts.append(f"方法: {m.get('length_method') or '-'}")

            # 计算背景大小
            max_w = 0
            total_h = 0
            bboxes = []
            for t in texts:
                tb = draw.textbbox((0, 0), t, font=font)
                w_t = tb[2] - tb[0]
                h_t = tb[3] - tb[1]
                max_w = max(max_w, w_t)
                total_h += h_t + 4
                bboxes.append((w_t, h_t))

            bg_w = max_w + 10
            bg_h = total_h + 6
            bx = x2 + 6
            if bx + bg_w > img_w:
                bx = max(2, x1 - 6 - bg_w)
            by = max(2, y1)
            draw.rectangle([bx, by, bx + bg_w, by + bg_h], fill="black")

            y_cursor = by + 4
            for i, t in enumerate(texts):
                draw.text((bx + 5, y_cursor), t, fill="white", font=font)
                y_cursor += bboxes[i][1] + 4

    # 返回 BGR numpy，便于后续 cv2.imencode
    out_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return out_np


class PredictImageRequest(BaseModel):
    image_path: str
    conf: float = 0.5
    top_k: int | None = 10
    format: str = "jpeg"


@app.post("/api/predict_image")
def predict_image(req: PredictImageRequest):
    logger.info("/api/predict_image called with %s", req.image_path)
    try:
        img = _read_image_any(req.image_path)
        results = predict_image_with_model(MODEL, req.image_path, conf=req.conf, top_k=req.top_k)

        # 为 predict_image 接口也计算 measurements 以便可视化
        # 重用 predict() 中的测量逻辑
        # 为避免重复代码，我们简单地构造一个轻量版本：
        pigs = []
        rulers = []
        bases = []
        def _cls_name_of(det):
            if isinstance(det, dict):
                name = det.get("class_name") or det.get("label") or det.get("name")
                if name:
                    return str(name).lower()
                cid = det.get("class_id")
                if cid is not None:
                    m = {0: "pig", 1: "ruler", 2: "base"}
                    return m.get(cid, f"class_{cid}")
            return "object"

        for det in results or []:
            box = det.get("box") if isinstance(det, dict) else None
            if not box or len(box) != 4:
                continue
            name = _cls_name_of(det)
            if "pig" in name:
                pigs.append(box)
            elif "ruler" in name:
                rulers.append(box)
            elif "base" in name or "scale" in name:
                bases.append(box)

        def _choose_largest(boxes):
            if not boxes:
                return None
            def area(b):
                return abs(b[2]-b[0]) * abs(b[3]-b[1])
            return max(boxes, key=area)

        ruler_box = _choose_largest(rulers)
        base_box = _choose_largest(bases)

        measurements = []
        for idx, pig_box in enumerate(pigs):
            length_cm = None
            method = None
            if ruler_box is not None:
                length_cm = calculate_pig_length_from_ruler(pig_box, ruler_box, 30.0)
                method = "ruler_30cm"
            if length_cm is None and base_box is not None:
                length_cm = calculate_pig_length_from_base(pig_box, base_box, 60.0)
                method = "base_60x40cm"
            est_w, est_range = estimate_pig_weight(length_cm)
            measurements.append({
                "pig_index": idx,
                "pig_box": pig_box,
                "length_cm": length_cm,
                "length_method": method,
                "estimated_weight_kg": est_w,
                "weight_range_kg": est_range,
            })

        vis = _draw_results_on_image(img, results, measurements)
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
