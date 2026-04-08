import os
from pathlib import Path


# Base directory
BASE_DIR = Path(__file__).parent.parent


# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH = BASE_DIR / "logs" / "flight_api.log"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "False").lower() == "true"

MODEL_URL = os.environ.get(
    "MODEL_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-68763db8f6254eefa4c61fa0d0d131a1")
IMAGES_SAVE_DIR = os.environ.get("IMAGES_SAVE_DIR", "./data/images")
VLM_MODEL = os.environ.get("VLM_MODEL", "qwen-vl-max-latest")
MAX_RETRIES = os.environ.get("MAX_RETRIES", 1)

ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xlsx", ".xls"}
CHANGE_TO_PDF_FILE_TYPE = {".ppt", ".pptx", ".doc", ".docx", ".xlsx", ".xls"}
TEMPERATURE = os.environ.get("TEMPERATURE", 0.7)

DIFY_URL = os.environ.get("DIFY_URL", "http://192.168.25.247") + "/v1/chat-messages"
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-7KL3WfxSuM09l6CVIxgdiAwk")

ITINERARY_URL = os.environ.get("ITINERARY_URL", "https://wxbot.dragonpass.com.cn")
ITINERARY_API = os.environ.get("ITINERARY_API", "/v1/chat/itinerary/hybrid")

# Dify streaming settings
DIFY_STREAMING = os.getenv("DIFY_STREAMING", "True").lower() == "true"

SYSTEM_PROMPT = """
你是一个助手，需要根据图片或文本内容，提取信息。
这些图片和文字中的内容有关出行规划。

###任务###
1.请严格根据图片或文字中的内容，提取信息。
2.你需要提取规划的行程中的POI信息。
3.请严格依据输出格式示例，返回一个JSON格式的结果。
4.请将POI按照行程顺序返回。
5.同一天内请不要重复输出相同的POI。
6.如果图片中没有一个具体的行程计划，那么你就充当一个助手，请根据图片给出的POI信息，进行规划，并最后按示例格式输出结果。
7.还需要再结果中添加一个"city"字段，用于记录图片中的城市名称。 （若有多个城市，按顺序返回多个）
8.最大的规划天数小于等于14天。
9.如果图片和文本中内容如出行旅游无关则返回空格式。如果与旅游相关，但没有行程规划内容，也返回空格式。
10.输出的内容都使用城市名称。如果是外文，则翻译成中文后输出。

###POI信息解释###
POI（Point of Interest）是地理信息系统中的核心数据类型，指地理空间中具有明确名称、类别和坐标的实体。
简单理解，POI就是景点。

###输出格式示例###
{
    "city": "城市1|城市2",
    "day1": "POI1|POI2|POI3"
    "day2": "POI1|POI2|POI3"
}
空格式返回：
{
    "city": "",
    "day1": ""
}
"""

USER_PROMPT = """
这是一些图片：
"""
REWRITE_PROMPT = """
你返回的 JSON 格式不正确。请严格按照以下格式示例返回结果：\n{\n    \"day1\": \"POI1|POI2|POI3\"\n    \"day2\": \"POI1|POI2|POI3\"\n}\n请确保返回的是有效的 JSON 格式，并且每天的行程作为一个键值对，按顺序排列。
"""
