# api/fsljxs.py
import os
import time
import random
import requests
import re
import base64
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

# 确保目录存在
os.makedirs("fsljxsfont/font/woff2", exist_ok=True)

def generate_filename(chapter: str) -> str:
    timestamp = int(time.time())
    random_number = random.randint(1000, 9999)
    woff2_filename = f"{chapter}_{timestamp}_{random_number}.woff2"
    return woff2_filename

def delete_old_files():
    current_time = time.time()
    for root, dirs, files in os.walk("fsljxsfont/font"):
        for file in files:
            file_path = os.path.join(root, file)
            file_time = os.path.getmtime(file_path)
            if current_time - file_time > 30:
                os.remove(file_path)
                print(f"删除文件: {file_path}")

@router.get("/content2")
async def get_woff2_font(chapter: str = Query(..., description="章节名称")):
    try:
        # 构建URL
        url = f"https://m.feibzw.com/{chapter}/"
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 EdgA/130.0.0.0",
        }

        # 发起请求
        response = requests.get(url, headers=headers)

        # 检查请求是否成功
        if response.status_code == 200:
            # 使用正则表达式匹配<link>标签中的href属性
            pattern = r'<link.*type="text/css" href="(.*\.css)"/>'
            match = re.search(pattern, response.text)
            
            if match:
                # 提取匹配到的内容
                css_url = "https://m.feibzw.com" + match.group(1)
                print("匹配到的CSS文件路径为:", css_url)
                
                # 发起请求获取CSS文件内容
                css_response = requests.get(css_url)
                
                # 检查请求是否成功
                if css_response.status_code == 200:
                    # 使用正则表达式匹配@font-face规则中的woff2字体文件的Base64编码
                    font_pattern = r'base64,(.*?)\) '
                    font_match = re.search(font_pattern, css_response.text)
                    
                    if font_match:
                        # 提取匹配到的Base64编码
                        font_base64 = font_match.group(1)
                        print("找到字体文件的Base64编码:", font_base64)
                        
                        # 生成文件名
                        woff2_filename = generate_filename(chapter)
                        
                        # 保存为woff2文件
                        woff2_file_path = os.path.join("fsljxsfont/font/woff2", woff2_filename)
                        
                        # 将Base64编码解码为二进制数据
                        font_data = base64.b64decode(font_base64)
                        
                        with open(woff2_file_path, "wb") as font_file:
                            font_file.write(font_data)
                        
                        print(f"woff2字体文件已保存到 {woff2_file_path}")
                        
                        # 删除旧文件
                        delete_old_files()
                        
                        return JSONResponse(content={"message": "字体文件已保存", "woff2_file_path": woff2_file_path}, status_code=200)
                    else:
                        return JSONResponse(content={"message": "未找到匹配的@font-face规则"}, status_code=404)
                else:
                    return JSONResponse(content={"message": f"下载CSS文件失败，状态码: {css_response.status_code}"}, status_code=css_response.status_code)
            else:
                return JSONResponse(content={"message": "未找到匹配的<link>标签"}, status_code=404)
        else:
            return JSONResponse(content={"message": f"请求失败，状态码: {response.status_code}"}, status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)
