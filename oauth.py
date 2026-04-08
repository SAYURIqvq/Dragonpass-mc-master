from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import json
import os
from typing import List



# 加载配置文件
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在！")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
ALLOWED_KEYS = set(config.get("allowed_keys", []))
PROTECTED_ROUTES = set(config.get("protected_routes", []))
KEY_PREFIX = config.get("prefix", "sk-")

app = FastAPI(title="FastAPI with sk- Key Auth")

# 认证中间件
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    path = request.url.path

    # 如果路径在受保护列表中，进行认证
    if any(path.startswith(route) for route in PROTECTED_ROUTES):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "缺少 Authorization 头"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authorization 格式错误，应为 'Bearer sk-xxx'"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[7:]  # 去掉 "Bearer "

        if not token.startswith(KEY_PREFIX):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": f"密钥必须以 '{KEY_PREFIX}' 开头"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token not in ALLOWED_KEYS:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "无效的 API 密钥"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 通过认证，继续处理请求
    response = await call_next(request)
    return response

# 示例公开接口（无需认证）
@app.get("/public/hello")
async def public_hello():
    return {"message": "Hello, this is public!"}

# 示例受保护接口
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    return {"message": "聊天完成！", "model": "gpt-4"}

@app.get("/v1/models")
async def list_models():
    return {"models": ["gpt-4", "gpt-3.5-turbo"]}

@app.get("/api/user/profile")
async def user_profile():
    return {"user": "authenticated_user", "role": "admin"}

# 用于测试当前配置
@app.get("/config/debug")
async def debug_config():
    return {
        "protected_routes": list(PROTECTED_ROUTES),
        "allowed_keys_count": len(ALLOWED_KEYS),
        "prefix": KEY_PREFIX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)