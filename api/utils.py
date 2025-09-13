"""
API工具函数
"""
import os
import time
import hashlib
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import requests
import cv2
import numpy as np
import yaml
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from minio import Minio
from minio.error import S3Error

from .config import MEDIA_BASE_URL, DETECTION_CLASSES, VISUALIZATION_CONFIG, CFG_PATH


def generate_result_filename(original_path: str, detection_type: str = "detection") -> str:
    """
    生成结果文件名
    格式: media/pigdata/pig/detection_results/年/月/日/原文件名_hash.jpg
    """
    # 解析原始文件名
    if original_path.startswith("http://") or original_path.startswith("https://"):
        parsed = urllib.parse.urlparse(original_path)
        q = urllib.parse.parse_qs(parsed.query)
        prefix_vals = q.get("prefix") or []
        if prefix_vals:
            decoded = urllib.parse.unquote(prefix_vals[0])
            original_name = decoded.split("/")[-1]
        else:
            original_name = os.path.basename(parsed.path) or "image.jpg"
    else:
        original_name = os.path.basename(original_path)
    
    # 去掉扩展名
    name_without_ext = os.path.splitext(original_name)[0]
    
    # 生成唯一hash
    timestamp = str(int(time.time()))
    hash_input = f"{original_path}_{timestamp}"
    file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    # 获取当前日期
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    # 构建文件路径
    filename = f"{name_without_ext}_{file_hash}.jpg"
    relative_path = f"media/pigdata/pig/{detection_type}/{year}/{month}/{day}/{filename}"
    
    return relative_path


def generate_result_url(relative_path: str) -> str:
    """
    生成结果图片URL
    格式: http://119.96.28.202:8094/huangshi-mini/media/pigdata/pig/detection_results/年/月/日/xxx.jpg
    """
    # 移除开头的 media/pigdata/pig/ 部分，因为MEDIA_BASE_URL已经包含了
    if relative_path.startswith("media/pigdata/pig/"):
        path_suffix = relative_path[len("media/pigdata/pig/"):]
    else:
        path_suffix = relative_path
    
    return f"{MEDIA_BASE_URL}/{path_suffix}"


def load_minio_config(cfg_path: Path) -> Optional[Dict[str, str]]:
    """加载MinIO配置"""
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        minio_cfg = (cfg.get("minio") or {}) if isinstance(cfg, dict) else {}
        url = str(minio_cfg.get("url") or "").rstrip("/")
        access_key = minio_cfg.get("accessKey")
        secret_key = minio_cfg.get("secretKey")
        bucket = minio_cfg.get("bucketName")
        if not (url and access_key and secret_key and bucket):
            print(f"⚠️ MinIO配置不完整: {cfg_path}")
            return None
        return {
            "url": url,
            "access_key": access_key,
            "secret_key": secret_key,
            "bucket": bucket,
        }
    except Exception as e:
        print(f"⚠️ 加载MinIO配置失败: {e}")
        return None


def create_minio_client(cfg: Dict[str, str]) -> Optional[Tuple[Minio, bool]]:
    """创建MinIO客户端"""
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
        print(f"⚠️ 创建MinIO客户端失败: {e}")
        return None


def upload_image_to_minio(image_data: bytes, object_name: str, 
                         minio_config: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
    """
    上传图片到MinIO
    返回: (是否成功, 实际URL)
    """
    if not minio_config:
        minio_config = load_minio_config(CFG_PATH)
    
    if not minio_config:
        print("⚠️ MinIO配置不可用，跳过上传")
        # 返回预期的URL格式，即使没有实际上传
        relative_path = f"media/pigdata/pig/{object_name}"
        return False, generate_result_url(relative_path)
    
    client_info = create_minio_client(minio_config)
    if not client_info:
        print("⚠️ MinIO客户端创建失败")
        relative_path = f"media/pigdata/pig/{object_name}"
        return False, generate_result_url(relative_path)
    
    client, secure = client_info
    bucket = minio_config["bucket"]
    
    try:
        # 确保bucket存在
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"✅ 创建MinIO bucket: {bucket}")
        
        # 上传文件
        data_stream = BytesIO(image_data)
        data_stream.seek(0)
        
        client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=data_stream,
            length=len(image_data),
            content_type="image/jpeg",
        )
        
        # 生成访问URL
        relative_path = f"media/pigdata/pig/{object_name}"
        result_url = generate_result_url(relative_path)
        
        print(f"✅ 图片上传成功: {object_name}")
        return True, result_url
        
    except S3Error as e:
        print(f"❌ MinIO上传失败: {e}")
        relative_path = f"media/pigdata/pig/{object_name}"
        return False, generate_result_url(relative_path)
    except Exception as e:
        print(f"❌ 上传过程出错: {e}")
        relative_path = f"media/pigdata/pig/{object_name}"
        return False, generate_result_url(relative_path)


def read_image_from_source(image_path: str) -> np.ndarray:
    """从本地或URL读取图片，返回OpenCV格式"""
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


def calculate_pig_length_from_ruler(pig_box: List[float], ruler_box: List[float], 
                                  ruler_length_cm: float = 30.0) -> Optional[float]:
    """根据尺子像素长度计算猪的长度（cm）"""
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


def calculate_pig_length_from_base(pig_box: List[float], base_box: List[float], 
                                 base_length_cm: float = 60.0, base_width_cm: float = 40.0) -> Optional[float]:
    """根据底座尺寸估算猪的长度（cm）"""
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


def estimate_pig_weight(length_cm: Optional[float], k: float = 0.002, 
                       error_pct: float = 0.20) -> Tuple[Optional[float], Optional[Tuple[float, float]]]:
    """估计重量：weight (kg) = k * length(cm) ** 2.5"""
    if length_cm is None:
        return None, None
    est = k * (length_cm ** 2.5)
    return est, (est * (1 - error_pct), est * (1 + error_pct))


def get_class_name(class_id: int) -> str:
    """获取类别名称"""
    return DETECTION_CLASSES.get(class_id, f"class_{class_id}")


def choose_largest_box(boxes: List[List[float]]) -> Optional[List[float]]:
    """选择面积最大的框"""
    if not boxes:
        return None
    
    def area(box):
        return abs(box[2] - box[0]) * abs(box[3] - box[1])
    
    return max(boxes, key=area)


def to_pixel_box(box: List[float], img_w: int, img_h: int) -> List[float]:
    """
    将box转为像素坐标 [x1,y1,x2,y2]
    支持YOLO归一化格式或像素坐标
    """
    try:
        arr = [float(v) for v in box]
    except Exception:
        return box
    
    if max(arr) <= 1.0:
        # YOLO格式 (x_center, y_center, w, h)
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
        return arr


def draw_advanced_visualization(img: np.ndarray, results: List[Dict[str, Any]], 
                              measurements: List[Dict[str, Any]]) -> np.ndarray:
    """
    绘制高级可视化结果，参考advanced_visualize.py的实现
    """
    # 转换为PIL图像
    if isinstance(img, np.ndarray):
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    else:
        pil_img = img.convert("RGB")

    draw = ImageDraw.Draw(pil_img)
    img_w, img_h = pil_img.size

    # 加载字体
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", VISUALIZATION_CONFIG["font_size"])
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", VISUALIZATION_CONFIG["font_size_small"])
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", VISUALIZATION_CONFIG["font_size"])
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", VISUALIZATION_CONFIG["font_size_small"])
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

    # 绘制检测框
    for det in results or []:
        box = det.get("box")
        if not box or len(box) != 4:
            continue
            
        pix = to_pixel_box(box, img_w, img_h)
        x1, y1, x2, y2 = [int(round(v)) for v in pix]
        
        class_id = det.get("class_id", 0)
        class_name = get_class_name(class_id)
        score = det.get("score") or det.get("confidence") or 0.0
        
        # 获取颜色
        color_name = DETECTION_CLASSES.get(class_id, "pig")
        color = VISUALIZATION_CONFIG["colors"].get(color_name, (255, 255, 0))
        
        # 绘制矩形框
        draw.rectangle([x1, y1, x2, y2], outline=color, width=VISUALIZATION_CONFIG["line_width"])
        
        # 绘制基础标签
        if class_id == 0:  # 猪
            # 查找对应的测量数据
            pig_measurement = None
            for m in measurements:
                if m.get("pig_box") == box:
                    pig_measurement = m
                    break
            
            if pig_measurement:
                # 绘制详细信息
                texts = [f"猪: {score:.2f}"]
                
                if pig_measurement.get("length_cm"):
                    texts.append(f"长度: {pig_measurement['length_cm']:.1f}cm")
                
                if pig_measurement.get("estimated_weight_kg"):
                    weight = pig_measurement["estimated_weight_kg"]
                    weight_range = pig_measurement.get("weight_range_kg")
                    if weight_range:
                        texts.append(f"重量: {weight:.1f}kg ({weight_range[0]:.1f}-{weight_range[1]:.1f}kg)")
                    else:
                        texts.append(f"重量: {weight:.1f}kg")
                
                if pig_measurement.get("length_method"):
                    texts.append(f"方法: {pig_measurement['length_method']}")
                
                # 绘制多行文本背景
                max_w = 0
                total_h = 0
                bboxes = []
                for t in texts:
                    tb = draw.textbbox((0, 0), t, font=small_font)
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
                draw.rectangle([bx, by, bx + bg_w, by + bg_h], fill=color)

                y_cursor = by + 4
                for i, t in enumerate(texts):
                    draw.text((bx + 5, y_cursor), t, fill="white", font=small_font)
                    y_cursor += bboxes[i][1] + 4
            else:
                # 简单标签
                label = f"猪: {score:.2f}"
                tb = draw.textbbox((0, 0), label, font=font)
                text_w = tb[2] - tb[0]
                text_h = tb[3] - tb[1]
                draw.rectangle([x1, y1 - text_h - 6, x1 + text_w + 6, y1], fill=color)
                draw.text((x1 + 3, y1 - text_h - 3), label, fill="white", font=font)
        else:
            # 其他对象的简单标签
            label = f"{class_name}: {score:.2f}"
            tb = draw.textbbox((0, 0), label, font=font)
            text_w = tb[2] - tb[0]
            text_h = tb[3] - tb[1]
            draw.rectangle([x1, y1 - text_h - 6, x1 + text_w + 6, y1], fill=color)
            draw.text((x1 + 3, y1 - text_h - 3), label, fill="white", font=font)

    # 转换回OpenCV格式
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)