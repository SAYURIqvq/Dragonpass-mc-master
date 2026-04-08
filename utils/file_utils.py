import os
import pdf2image
from typing import List
import PIL.Image as Image
import logging


class FileUtils:
    """
    文件工具类
    """
    @staticmethod
    def delete_files_in_dir(dir_path: str):
        """
        删除指定目录下的所有文件
        :param dir_path: 目录路径
        """
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # 删除目录
        if os.path.exists(dir_path):
            os.rmdir(dir_path)
    @staticmethod
    def pdf_to_images(pdf_file_path: str) -> List[Image.Image]:
        """
        将pdf文件转换为图片列表
        :param pdf_file_path: pdf文件路径
        :return: 图片列表
        """
        images = pdf2image.convert_from_path(pdf_file_path)
        return images
    
    @staticmethod
    def save_images(images: List[Image.Image], save_dir: str) -> List[str]:
        """
        保存图片列表
        :param images: 图片列表
        :param save_dir: 保存目录
        """
        file_names = []
        max_size = 10 * 1024 * 1024  # 10MB
        
        for i, image in enumerate(images):
            file_path = os.path.join(save_dir, f"{i}.jpg")
            
            # 先以基础质量保存
            image.save(file_path, "JPEG", quality=95, optimize=True)
            
            # 检查文件大小是否超过10MB，如果超过则进行压缩
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                # logging.info(f"图片文件 {file_path} 大小为 {file_size} 字节，超过10MB限制，开始压缩")
                
                # 通过调整图片质量来压缩文件大小
                quality = 90
                while file_size > max_size and quality > 10:
                    image.save(file_path, "JPEG", quality=quality, optimize=True)
                    file_size = os.path.getsize(file_path)
                    quality -= 10
                    
                # 如果质量降低后仍然太大，尝试降低图片尺寸
                if file_size > max_size:
                    # 逐步缩小尺寸直到满足大小要求
                    scale = 0.9
                    while file_size > max_size and scale > 0.1:
                        new_width = int(image.width * scale)
                        new_height = int(image.height * scale)
                        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        resized_image.save(file_path, "JPEG", quality=85, optimize=True)
                        file_size = os.path.getsize(file_path)
                        scale -= 0.1
                    # logging.info(f"已调整图片尺寸，当前大小: {file_size} 字节")
                    
            file_names.append(file_path)
        return file_names

    @staticmethod
    def open_image(file_name: str) -> Image.Image:
        """
        打开图片
        :param file_name: 图片文件名
        """
        return Image.open(file_name)
    
if __name__ == '__main__':
    images = FileUtils.pdf_to_images("data/test1.pdf")
    # 保存图片
    FileUtils.save_images(images, "data/pictures")