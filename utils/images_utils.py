import base64

# 把本地图片读成 base64
def img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')