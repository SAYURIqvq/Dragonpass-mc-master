"""
Main FastAPI application for flight search API
"""

import os
import tempfile
import subprocess
from fastapi import (
    FastAPI,
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
    Request,
    status,
    Response,
)
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import httpx
from typing import Dict, Any, Optional
from typing import List
from openai import OpenAI, AsyncOpenAI
import json
from utils.file_utils import FileUtils
from utils.json_utils import ResultProcessor
from utils.images_utils import img_b64
from services.FileService import FileService
from services.DifyService import DifyService
from utils.logger import logger
from config.settings import (
    API_HOST,
    API_PORT,
    API_RELOAD,
    CHANGE_TO_PDF_FILE_TYPE,
    ALLOWED_EXTENSIONS,
    DASHSCOPE_API_KEY,
    MODEL_URL,
    SYSTEM_PROMPT,
    USER_PROMPT,
    IMAGES_SAVE_DIR,
    VLM_MODEL,
    DIFY_URL,
    DIFY_API_KEY,
    ITINERARY_URL,
    ITINERARY_API,
)
from models.dify import DifyRequest
from models.parse_file import ParseFileRequest, ParseTextRequest


client = None
file_service = None
dify_service = None

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Flight Search API...")
    global client, file_service, dify_service
    client = AsyncOpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=DASHSCOPE_API_KEY,
        base_url=MODEL_URL,
    )
    file_service = FileService(client=client)
    dify_service = DifyService()
    yield
    # Shutdown
    logger.info("Shutting down Flight Search API...")


# Create FastAPI application
app = FastAPI(
    title="Flight Search API",
    description="MC - 文件转图片 pdf, docx, excel -> jpg",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "message": "MC API",
            "description": "MC - 文件转图片 pdf, docx, excel -> jpg",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        },
    }


@app.post("/parse_file")
async def download_data(request: ParseFileRequest):
    """
    Reload data from the specified file URL
    """
    return await file_service.process_file(request.file_url, client)


@app.post("/parse_text")
async def upload_text(request: ParseTextRequest):
    """
    Reload data from the specified file URL
    """
    return await file_service.process_text(request, client)


@app.post("/parse_upload_file")
async def upload_data(file: UploadFile = File(...)):
    """
    Reload data from the specified file URL
    """
    return await file_service.process_uploadfile(file, client)


@app.post("/v1/chat/itinerary/hybrid")
async def hybrid_chat(request: Request):
    """
    请求转发到 ITINERARY_URL + /v1/chat/itinerary/hybrid
    """
    # Get the body and headers from the incoming request
    body = await request.body()
    headers = dict(request.headers)
    headers["host"] = "wxbot.dragonpass.com.cn"
    # Create an HTTP client
    async with httpx.AsyncClient() as client:
        # Forward the request to the itinerary service
        itinerary_url = ITINERARY_URL + ITINERARY_API
        response = await client.post(
            itinerary_url, content=body, headers=headers, timeout=600
        )

        # Return the response from the itinerary service

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


@app.post("/df/chat")
async def dify_chat(request: DifyRequest):
    """
    与Dify进行对话

    Args:
        request: Dify请求参数
    """
    if not DIFY_URL or not DIFY_API_KEY:
        return JSONResponse(
            content={
                "code": "500",
                "msg": "Dify API URL or API Key not configured",
                "data": {},
            },
            status_code=500,
        )

    # 转换inputs为字典格式
    inputs_dict = request.inputs.dict()

    # 检查function_name是否为支持的值
    supported_functions = ["faq", "intention", "poi"]
    if request.inputs.function_name not in supported_functions:
        return JSONResponse(
            content={
                "code": "400",
                "msg": f"function_name must be one of {supported_functions}",
                "data": {},
            },
            status_code=400,
        )

    # 如果function_name为poi，则city和names为必填
    if request.inputs.function_name == "poi":
        if not request.inputs.city:
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "city is required when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )
        if not request.inputs.names:
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "names is required when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )
        if not request.query.strip():
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "query cannot be empty when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )

    try:
        result = await dify_service.send_message(
            query=request.query,
            inputs=inputs_dict,
            user=request.user,
            conversation_id=request.conversation_id,
            response_mode=request.response_mode,
        )
        return JSONResponse(
            content={"code": "200", "msg": "success", "data": result}, status_code=200
        )
    except HTTPException as e:
        return JSONResponse(
            content={"code": str(e.status_code), "msg": e.detail, "data": {}},
            status_code=e.status_code,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "code": "500",
                "msg": f"Failed to connect to Dify API: {str(e)}",
                "data": {},
            },
            status_code=500,
        )


# @app.post("/dify/chat-stream")
async def dify_chat_stream(request: DifyRequest):
    """
    流式与Dify进行对话

    Args:
        request: Dify请求参数
    """
    if not DIFY_URL or not DIFY_API_KEY:
        return JSONResponse(
            content={
                "code": "500",
                "msg": "Dify API URL or API Key not configured",
                "data": {},
            },
            status_code=500,
        )

    # 转换inputs为字典格式
    inputs_dict = request.inputs.model_dump()

    # 检查function_name是否为支持的值
    supported_functions = ["faq", "intention", "poi"]
    if request.inputs.function_name not in supported_functions:
        return JSONResponse(
            content={
                "code": "400",
                "msg": f"function_name must be one of {supported_functions}",
                "data": {},
            },
            status_code=400,
        )

    # 如果function_name为poi，则city和names为必填
    if request.inputs.function_name == "poi":
        if not request.inputs.city:
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "city is required when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )
        if not request.inputs.names:
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "names is required when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )
        if not request.query.strip():
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "query cannot be empty when function_name is poi",
                    "data": {},
                },
                status_code=400,
            )

    # 强制设置response_mode为streaming
    return StreamingResponse(
        dify_service.send_message_streaming(
            query=request.query,
            inputs=inputs_dict,
            user=request.user,
            conversation_id=request.conversation_id,
        ),
        media_type="text/event-stream",
    )


@app.get("/api/health")
async def health():
    """
    Health check endpoint
    """
    return {"code": "200", "msg": "success", "data": {"status": "ok"}}


if __name__ == "__main__":
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD, log_level="info"
    )
