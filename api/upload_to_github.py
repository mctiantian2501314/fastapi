from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
import requests
import base64
import os
import random
import string
import json
from datetime import datetime

router = APIRouter()

@router.post("/upload", description="上传本地文件到GitHub仓库，并根据文件内容中的bookSourceName生成文件名（包含随机字母和时间戳），返回原始下载链接")
async def upload_file_to_github(
    repo_name: str = Form(..., description="仓库名称（格式为'用户名/仓库/上传到仓库具体目录'）"),
    branch: str = Form(..., description="分支名称"),
    commit_message: str = Form(..., description="提交信息"),
    access_token: str = Form(..., description="GitHub个人访问令牌"),
    file: UploadFile = File(..., description="要上传的文件")
):
    """
    上传文件到GitHub仓库

    :param repo_name: 仓库名称（格式为'用户名/仓库/上传到仓库具体目录'）
    :param branch: 分支名称
    :param commit_message: 提交信息
    :param access_token: GitHub个人访问令牌
    :param file: 要上传的文件
    :return: 包含原始下载链接的JSON数据
    """
    # 读取文件内容
    file_content = await file.read()

    # 确保文件是JSON格式
    try:
        file_json = json.loads(file_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="上传的文件不是有效的JSON格式")

    # 提取bookSourceName字段的值
    book_source_name = None
    if isinstance(file_json, dict):
        book_source_name = file_json.get("bookSourceName")
    elif isinstance(file_json, list) and len(file_json) > 0:
        book_source_name = file_json[0].get("bookSourceName")

    if not book_source_name:
        raise HTTPException(status_code=200, detail="测试成功，但是不支持这个文件上传,文件没有书源特征哦。by天天的鸟蛋蛋的小提醒")

    # 获取当前时间的时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 随机生成文件名（包含bookSourceName、随机字母和时间戳）
    random_letters = ''.join(random.choices(string.ascii_letters, k=4))
    file_extension = os.path.splitext(file.filename)[1]
    random_file_name = f"{book_source_name}{random_letters}{timestamp}{file_extension}"

    # 解析仓库名称和上传路径
    parts = repo_name.split("/")
    if len(parts) > 2:
        # 如果指定了具体目录
        repo_path = "/".join(parts[2:])
        random_file_path = f"{repo_path}/{random_file_name}"
    else:
        # 默认保存在根目录
        random_file_path = random_file_name

    # GitHub API的基础URL
    base_url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}/contents/{random_file_path}"

    # 获取文件的当前状态（如果存在）
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(base_url, headers=headers)

    if response.status_code == 200:
        # 文件已存在，需要更新
        file_info = response.json()
        sha = file_info["sha"]
        data = {
            "message": commit_message,
            "content": base64.b64encode(file_content).decode(),
            "sha": sha,
            "branch": branch
        }
    else:
        # 文件不存在，需要创建
        data = {
            "message": commit_message,
            "content": base64.b64encode(file_content).decode(),
            "branch": branch
        }

    # 发送PUT请求以上传文件
    response = requests.put(base_url, headers=headers, json=data)

    if response.status_code in [201, 200]:
        # 获取原始下载链接
        download_url = f"https://raw.githubusercontent.com/{parts[0]}/{parts[1]}/{branch}/{random_file_path}"
        return {"download_url": download_url}
    else:
        raise HTTPException(status_code=400, detail=f"文件上传失败，错误信息：{response.json()}")
