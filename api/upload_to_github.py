from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
import requests
import base64
import os
import random
import string
import json
from datetime import datetime

router = APIRouter()

@router.post("/upload", description="上传本地文件到GitHub仓库，并随机命名文件（包含时间戳），返回原始下载链接")
async def upload_file_to_github(
    repo_name: str = Form(..., description="仓库名称（格式为'用户名/仓库名'）"),
    branch: str = Form(..., description="分支名称"),
    commit_message: str = Form(..., description="提交信息"),
    access_token: str = Form(..., description="GitHub个人访问令牌"),
    file: UploadFile = File(..., description="要上传的文件")
):
    """
    上传文件到GitHub仓库

    :param repo_name: 仓库名称（格式为'用户名/仓库名'）
    :param branch: 分支名称
    :param commit_message: 提交信息
    :param access_token: GitHub个人访问令牌
    :param file: 要上传的文件
    :return: 包含原始下载链接的JSON数据
    """
    # 读取文件内容
    file_content = await file.read()

    # 获取当前时间的时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 随机生成文件名（包含时间戳）
    random_filename = ''.join(random.choices(string.ascii_letters, k=4)) + timestamp
    file_extension = os.path.splitext(file.filename)[1]
    random_file_path = f"{random_filename}{file_extension}"

    # GitHub API的基础URL
    base_url = f"https://api.github.com/repos/{repo_name}/contents/{random_file_path}"

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
        download_url = f"https://raw.githubusercontent.com/{repo_name}/refs/heads/{branch}/SY/{random_file_path}"
        #https://raw.githubusercontent.com/{repo_name}/refs/heads/{branch}/SY/{random_file_path}
        return {"download_url": download_url}
    else:
        raise HTTPException(status_code=400, detail=f"文件上传失败，错误信息：{response.json()}")
