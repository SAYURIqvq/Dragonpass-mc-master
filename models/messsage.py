import enum


class MessageType(enum.Enum):
    """
    MessageType enum class
    """
    success = "success"
    unparseed_error = "未能解析上传文件，请传pdf, docx, pptx, xlsx, doc, ppt, xls格式文件"

