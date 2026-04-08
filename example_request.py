import requests
import json

def upload_file_to_parse(file_path, api_url):
    """
    向/parse_file接口发送文件上传请求的示例
    
    Args:
        file_path (str): 要上传的文件路径
        api_url (str): API的URL，例如 "http://localhost:8000/parse_file"
    
    Returns:
        dict: API响应结果
    """
    # 打开文件准备上传
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(api_url, files=files)
    
    # 返回响应结果
    return response.json()

def upload_file_with_custom_name(file_path, api_url, upload_filename=None):
    """
    向/parse_file接口发送文件上传请求，可自定义上传文件名
    
    Args:
        file_path (str): 要上传的本地文件路径
        api_url (str): API的URL，例如 "http://localhost:8000/parse_file"
        upload_filename (str, optional): 上传时使用的文件名，默认为原文件名
    
    Returns:
        dict: API响应结果
    """
    if upload_filename is None:
        upload_filename = file_path.split('/')[-1]  # 获取文件名
    
    # 打开文件准备上传
    with open(file_path, 'rb') as file:
        files = {'file': (upload_filename, file)}
        response = requests.post(api_url, files=files)
    
    # 返回响应结果
    return response.json()

# 示例用法
if __name__ == "__main__":
    # 基本用法
    api_url = "http://localhost:8000/parse_file"
    file_path = "example.pdf"
    
    # 发送请求
    try:
        result = upload_file_to_parse(file_path, api_url)
        print("API响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到")
    except Exception as e:
        print(f"请求失败: {e}")