from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class DifyRequestInputs(BaseModel):
    """
    Dify请求输入参数模型
    """
    function_name: str  # 必填且仅支持faq/intention/poi
    city: Optional[str] = None  # 若function_name为poi则此参数必填
    names: Optional[str] = None  # 若function_name为poi则此参数必填
    lang: Optional[str] = None  # 选填，zh或en


class DifyRequest(BaseModel):
    """
    Dify请求模型，用于聊天和流式聊天接口
    """
    inputs: DifyRequestInputs
    query: str
    response_mode: str  # 必填
    conversation_id: Optional[str] = ""  # 选填，如无则传空字符串即可，同一通会话传相同的id
    user: str  # 必填