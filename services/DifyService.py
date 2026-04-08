import httpx
import json
from typing import AsyncGenerator, Dict, Any
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from config.settings import DIFY_URL, DIFY_API_KEY, DIFY_STREAMING
from utils.logger import logger


class DifyService:
    def __init__(self):
        self.api_key = DIFY_API_KEY
        self.url = DIFY_URL
        self.streaming = DIFY_STREAMING
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def send_message(
        self, 
        query: str, 
        inputs: Dict[str, Any] = None, 
        user: str = "default-user",
        conversation_id: str = "",
        response_mode: str = "blocking"
    ) -> Dict[str, Any]:
        """
        发送消息到Dify API
        
        Args:
            query: 用户查询内容
            inputs: 输入参数
            user: 用户标识
            conversation_id: 对话ID
            
        Returns:
            Dify API 响应
        """
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": response_mode,
            "user": user,
            "conversation_id": conversation_id
        }

        logger.info(f"Sending message to Dify API: {query}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Dify API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Dify API error: {response.text}"
                    )
                    
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Request to Dify API failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Dify API: {str(e)}"
            )

    async def send_message_streaming(
        self,
        query: str,
        inputs: Dict[str, Any] = None,
        user: str = "default-user",
        conversation_id: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        流式发送消息到Dify API
        
        Args:
            query: 用户查询内容
            inputs: 输入参数
            user: 用户标识
            conversation_id: 对话ID
            
        Yields:
            流式响应数据
        """
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user,
            "conversation_id": conversation_id
        }

        logger.info(f"Sending streaming message to Dify API: {query}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    self.url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Dify API error: {response.status_code} - {error_text}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Dify API error: {error_text.decode()}"
                        )
                        
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            yield line + "\n\n"
                            
        except httpx.RequestError as e:
            logger.error(f"Request to Dify API failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Dify API: {str(e)}"
            )
