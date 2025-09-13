"""
API主入口文件
"""
import uvicorn
from .endpoints import app
from .config import API_HOST, API_PORT

def main():
    """启动API服务"""
    print(f"启动猪只检测API服务...")
    print(f"服务地址: http://{API_HOST}:{API_PORT}")
    print(f"API文档: http://{API_HOST}:{API_PORT}/docs")
    print(f"按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "api.endpoints:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()