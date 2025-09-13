#!/usr/bin/env python3
"""
启动新的猪只检测API服务
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import main

if __name__ == "__main__":
    main()