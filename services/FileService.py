import asyncio
import functools
import os
import subprocess
from fastapi import UploadFile
import tempfile
from fastapi.responses import JSONResponse
from typing import List
import PIL.Image as Image
import httpx
import urllib.parse
from models.parse_file import ParseFileRequest, ParseTextRequest


from config.settings import (
    API_HOST,
    API_PORT,
    API_RELOAD,
    CHANGE_TO_PDF_FILE_TYPE,
    ALLOWED_EXTENSIONS,
    REWRITE_PROMPT,
)
from config.settings import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    IMAGES_SAVE_DIR,
    VLM_MODEL,
    MAX_RETRIES,
    TEMPERATURE,
)
from utils.file_utils import FileUtils
from utils.images_utils import img_b64
from utils.json_utils import ResultProcessor
from utils.logger import logger
from models.messsage import MessageType

class FileService:
    def __init__(self, client):
        self.client = client

    async def process_file(self, file_url: str, client):
        """
        Process uploaded file: convert to PDF if needed, then to images,
        and finally extract information using VLM
        """
        logger.info(f"Processing file from URL: {file_url}")
        
        # Validate URL
        parsed_url = urllib.parse.urlparse(file_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return JSONResponse(
                content={
                    "code": "400",
                    "msg": "Invalid file URL provided",
                    "data": {},
                },
                status_code=400,
            )
        
        file_path = parsed_url.path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 如果文件类型不在允许的范围内，则返回错误信息
        if file_ext.lower() not in ALLOWED_EXTENSIONS:
            return JSONResponse(
                content={
                    "code": "400",  # 错误码code
                    "msg": MessageType.unparseed_error.value ,  # 错误码信息
                    "data": {},
                },
                status_code=400,
            )

        # Download file with retry mechanism
        async with httpx.AsyncClient() as http_client:
            max_download_retries = 3  # Maximum number of download retries
            retry_count = 0
            download_success = False
            file_content = None
            
            while retry_count < max_download_retries and not download_success:
                try:
                    response = await http_client.get(file_url)
                    response.raise_for_status()
                    file_content = response.content
                    download_success = True
                    logger.info(f"File downloaded successfully after {retry_count} retries")
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Download attempt {retry_count} failed: {str(e)}")
                    if retry_count >= max_download_retries:
                        return JSONResponse(
                            content={
                                "code": "500",
                                "msg": f"Failed to download file after {max_download_retries} attempts: {str(e)}",
                                "data": {},
                            },
                            status_code=500,
                        )
                    # Wait before retrying
                    await asyncio.sleep(1)

        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            input_path = tmp_file.name

            pdf_file = None
            output_dir = None
            # 如果是office文件 转成PDF文件
            if file_ext.lower() in CHANGE_TO_PDF_FILE_TYPE:
                output_dir = tempfile.mkdtemp()
                command = [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    output_dir,
                    input_path,
                ]
                # 使用 asyncio 的方式运行 subprocess，避免阻塞 FastAPI 事件循环
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, functools.partial(subprocess.run, command, check=True))
                output_pdf_path = os.path.join(
                    output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
                )
                input_pdf_path = output_pdf_path
                pdf_file = input_pdf_path
            else:
                pdf_file = input_path

            # PDF文件转成图片
            images: List = FileUtils.pdf_to_images(pdf_file)
            file_names_list = FileUtils.save_images(images, IMAGES_SAVE_DIR)
            images_list = []
            for file_name in file_names_list:
                item = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64(file_name)}"},
                }
                images_list.append(item)
            images_list.append({"type": "text", "text": USER_PROMPT})

            message_list = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": images_list,
                },
            ]
            result = await self.request_vlm(client, message_list, MAX_RETRIES)
            logger.info(f"Result: {result}")
            # 删除output_dir 下的文件
            if output_dir:
                FileUtils.delete_files_in_dir(output_dir)

        return JSONResponse(
            content={
                "code": "200",  
                "msg": MessageType.success.value, 
                "data": {
                    "message": result  # 结果
                },
            },
            status_code=200,
        )


    async def process_uploadfile(self, file: UploadFile,  client):
        """
        Process uploaded file: convert to PDF if needed, then to images,
        and finally extract information using VLM
        """
        logger.info(f"Processing file: {file.filename}")
        file_ext = os.path.splitext(file.filename)[1]
        # 如果文件类型不在允许的范围内，则返回错误信息
        if file_ext.lower() not in ALLOWED_EXTENSIONS:
            return JSONResponse(
                content={
                    "code": "400",  # 错误码code
                    "msg": MessageType.unparseed_error.value ,  # 错误码信息
                    "data": {},
                },
                status_code=400,
            )


        
        # 如果文件类型不在允许的范围内，则返回错误信息
        if file_ext.lower() not in ALLOWED_EXTENSIONS:
            return JSONResponse(
                content={
                    "code": "400",  # 错误码code
                    "msg": MessageType.unparseed_error.value ,  # 错误码信息
                    "data": {},
                },
                status_code=400,
            )
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(await file.read())
            tmp_file.flush()
            input_path = tmp_file.name

            pdf_file = None
            output_dir = None
            # 如果是office文件 转成PDF文件
            if file_ext.lower() in CHANGE_TO_PDF_FILE_TYPE:
                output_dir = tempfile.mkdtemp()
                command = [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    output_dir,
                    input_path,
                ]
                # subprocess.run(command, check=True)
                # 使用 asyncio 的方式运行 subprocess，避免阻塞 FastAPI 事件循环
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, functools.partial(subprocess.run, command, check=True))
                
                output_pdf_path = os.path.join(
                    output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
                )
                input_pdf_path = output_pdf_path
                pdf_file = input_pdf_path
            else:
                pdf_file = input_path

            # PDF文件转成图片
            images: List = FileUtils.pdf_to_images(pdf_file)
            file_names_list = FileUtils.save_images(images, IMAGES_SAVE_DIR)
            images_list = []
            for file_name in file_names_list:
                item = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64(file_name)}"},
                }
                images_list.append(item)
            images_list.append({"type": "text", "text": USER_PROMPT})

            message_list = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": images_list,
                },
            ]
            logger.info("vlm request")
            result = await self.request_vlm(client, message_list, MAX_RETRIES)
            logger.info(f"Result: {result}")
            # 删除output_dir 下的文件
            if output_dir:
                FileUtils.delete_files_in_dir(output_dir)

        return JSONResponse(
            content={
                "code": "200",  
                "msg": MessageType.success.value, 
                "data": {
                    "message": result  # 结果
                },
            },
            status_code=200,
        )

    async def process_text(self, request: ParseTextRequest, client):
        try: 
            images_list = []
            images_list.append({"type": "text", "text": request.travelPlan})
            message_list = [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": SYSTEM_PROMPT}],
                    },
                    {
                        "role": "user",
                        "content": images_list,
                    },
                ]
            logger.info("vlm request")
            result = await self.request_vlm(client, message_list, MAX_RETRIES)
            logger.info(f"Result: {result}")


            return JSONResponse(
                content={
                    "code": "200",  
                    "msg": MessageType.success.value, 
                    "data": {
                        "message": result  # 结果
                    },
                },
                status_code=200,
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "code": "500",
                    "msg": str(e),
                    "data": {},
                },
                status_code=500,
            )


    async def request_vlm(self, client, message_list: List[dict], max_retries: int):
        # 请求VLM 提取图片中信息
        completion = await client.chat.completions.create(
            model=VLM_MODEL,
            messages=message_list,
            temperature=TEMPERATURE

        )
        result = completion.choices[0].message.content
        json_obj = ResultProcessor.extract_json(result)

        retries = 0
        while retries < max_retries and not self.check_json_format(json_obj):
            retries += 1
            # 构造新的提示信息，要求模型修正格式
            new_message_list = message_list + [
                {"role": "assistant", "content": result},
                {
                    "role": "user",
                    "content": REWRITE_PROMPT,
                },
            ]

            completion = await client.chat.completions.create(
                model=VLM_MODEL,
                messages=new_message_list,
            )
            result = completion.choices[0].message.content
            json_obj = ResultProcessor.extract_json(result)

        new_result = {}
        for key, value in json_obj.items():
            split_result = value.split("|")
            if len(split_result) == 1 and split_result[0] == "":
                new_result[key] = []
            else:
                new_result[key] = split_result
            # new_result[key] = value.split("|")
        return new_result

    def check_json_format(self, json_obj):
        """
        检查 JSON 格式是否符合要求
        格式示例: {"day1": "POI1|POI2|POI3", "day2": "POI1|POI2|POI3"}
        """
        # 检查是否为字典类型
        if not isinstance(json_obj, dict):
            return False

        # 检查是否为空字典
        if not json_obj:
            return False

        # 检查每个键值对
        for key, value in json_obj.items():
            # 检查键是否以"day"开头并跟数字
            if not key.startswith("day") and not key.startswith("city"):
                return False

            if key.startswith("day"):
                try:
                    day_num = int(key[3:])
                    if day_num <= 0:
                        return False
                except ValueError:
                    return False

            # 检查值是否为字符串类型
            if not isinstance(value, str):
                return False

            # 检查值是否包含"|"分隔符或者为空
            if value and "|" not in value and value != "":
                # 单个 POI 是允许的
                pass

        return True