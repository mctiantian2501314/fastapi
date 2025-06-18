from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx
import json
import logging
import os
import subprocess
import tempfile
import time
import shutil

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/to")
async def convert_avif_to_png(
    url: str = Query(..., description="AVIF图片URL"),
    options: str = Query(None, description="自定义请求头JSON")
):
    
    headers = {}
    if options:
        try:
            headers = json.loads(options)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in options, using empty headers")
    

    start_time = time.time()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=15.0)
            resp.raise_for_status()
            
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"服务器返回错误状态码: {resp.status_code}"
                )
                
            logger.info(f"下载完成: {len(resp.content)} bytes in {time.time()-start_time:.2f}s")
                
        except httpx.HTTPError as e:
            logger.error(f"下载失败: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"下载失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"请求异常: {str(e)}"
            )
    

    avif_path = None
    png_path = None
    try:
        start_time = time.time()
        

        temp_dir = tempfile.mkdtemp()
        

        avif_path = os.path.join(temp_dir, "input.avif")
        with open(avif_path, "wb") as f:
            f.write(resp.content)
        

        png_path = os.path.join(temp_dir, "output.png")
        
        
        cmd = [
            "ffmpeg",
            "-y",  
            "-i", avif_path,
            "-frames:v", "1",  
            png_path
        ]
        
        #  FFmpeg 
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10  
        )
        
        # 检查转换结果
        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="ignore")
            logger.error(f"FFmpeg 转换失败: {error_msg}")
            raise RuntimeError(f"FFmpeg 错误: {error_msg}")
        
        # 读取 PNG 文件
        with open(png_path, "rb") as f:
            png_data = f.read()
        
        logger.info(f"转换完成: {len(png_data)} bytes in {time.time()-start_time:.2f}s")
        
    except Exception as e:
        logger.error(f"转换失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"转换失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    return Response(content=png_data, media_type="image/png")

@router.get("/ffmpeg-version")
async def get_ffmpeg_version():
    """检查 FFmpeg 是否可用及其版本"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        version_output = result.stdout.decode("utf-8", errors="ignore").split("\n")[0]
        return {"version": version_output}
    except Exception as e:
        return {"error": str(e)}