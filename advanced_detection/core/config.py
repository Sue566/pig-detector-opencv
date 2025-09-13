"""
高级检测配置文件
定义颜色、类别、测量参数等常量
"""

# 检测类别定义
CLASS_DEFINITIONS = {
    0: {
        "name": "Pig",
        "name_cn": "猪",
        "color_rgb": (255, 0, 0),      # 红色 - 猪
        "color_bgr": (0, 0, 255),      # OpenCV BGR格式
        "color_hex": "#FF0000"
    },
    1: {
        "name": "Ruler", 
        "name_cn": "尺子",
        "color_rgb": (0, 100, 255),    # 蓝色 - 尺子
        "color_bgr": (255, 100, 0),    # OpenCV BGR格式
        "color_hex": "#0064FF"
    },
    2: {
        "name": "Base",
        "name_cn": "底座", 
        "color_rgb": (0, 200, 0),      # 绿色 - 底座
        "color_bgr": (0, 200, 0),      # OpenCV BGR格式
        "color_hex": "#00C800"
    }
}

# 测量参数
MEASUREMENT_CONFIG = {
    "ruler": {
        "default_length_cm": 30.0,
        "min_length_cm": 10.0,
        "max_length_cm": 100.0
    },
    "base": {
        "default_length_cm": 60.0,
        "default_width_cm": 40.0,
        "min_size_cm": 20.0,
        "max_size_cm": 200.0
    },
    "weight": {
        "formula_coefficient": 0.0015,  # 调整系数，使重量更合理
        "formula_exponent": 2.3,        # 调整指数
        "range_percentage": 0.25        # ±25% 重量范围
    }
}

# 可视化配置
VISUALIZATION_CONFIG = {
    "box": {
        "line_width": 3,
        "corner_radius": 0
    },
    "text": {
        "font_size_large": 18,
        "font_size_small": 14,
        "line_height": 22,
        "padding": 8,
        "background_alpha": 0.8
    },
    "fonts": {
        "primary": [
            "/System/Library/Fonts/Arial.ttf",           # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf"                 # Windows
        ],
        "fallback": "default"
    }
}

# 长度标注配置
LENGTH_ANNOTATION_CONFIG = {
    "show_length_line": True,      # 是否显示长度标注线
    "line_color": (255, 255, 0),   # 黄色标注线
    "line_width": 2,
    "arrow_size": 8,
    "text_offset": 10,
    "precision": 1                 # 小数点精度
}

def get_class_info(class_id):
    """获取类别信息"""
    return CLASS_DEFINITIONS.get(class_id, {
        "name": f"Class_{class_id}",
        "name_cn": f"类别_{class_id}",
        "color_rgb": (128, 128, 128),
        "color_bgr": (128, 128, 128),
        "color_hex": "#808080"
    })

def get_class_color(class_id, format="rgb"):
    """获取类别颜色"""
    # 强制定义颜色，确保正确性
    colors = {
        0: {  # 猪
            "rgb": (255, 0, 0),      # 纯红色
            "bgr": (0, 0, 255),
            "hex": "#FF0000"
        },
        1: {  # 尺子
            "rgb": (0, 100, 255),    # 蓝色
            "bgr": (255, 100, 0),
            "hex": "#0064FF"
        },
        2: {  # 底座
            "rgb": (0, 200, 0),      # 绿色
            "bgr": (0, 200, 0),
            "hex": "#00C800"
        }
    }
    
    if class_id in colors:
        if format == "rgb":
            return colors[class_id]["rgb"]
        elif format == "bgr":
            return colors[class_id]["bgr"]
        elif format == "hex":
            return colors[class_id]["hex"]
        else:
            return colors[class_id]["rgb"]
    else:
        # 默认灰色
        if format == "rgb":
            return (128, 128, 128)
        elif format == "bgr":
            return (128, 128, 128)
        elif format == "hex":
            return "#808080"
        else:
            return (128, 128, 128)