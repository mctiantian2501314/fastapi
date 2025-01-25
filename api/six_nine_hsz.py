#天天的鸟蛋蛋 fastapi 69书吧搜索69hsz
from fastapi import APIRouter, Query, HTTPException
import requests
from bs4 import BeautifulSoup
from fastapi.responses import JSONResponse
import json
import re

router = APIRouter()

@router.get("/search")
async def search_novels(keyword: str = Query(..., description="搜索关键词")):
    if not keyword:
        raise HTTPException(status_code=400, detail="请输入关键词")
    
    url = "https://www.69hsz.com/ss/"
    params = {
        'searchkey': keyword
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFJM10 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.260 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua': "\"Android WebView\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-platform': "\"Android\"",
        'upgrade-insecure-requests': "1",
        'x-requested-with': "cn.mujiankeji.mbrowser",
        'sec-fetch-site': "none",
        'sec-fetch-mode': "navigate",
        'sec-fetch-user': "?1",
        'sec-fetch-dest': "document",
        'referer': "https://www.69hsz.com/",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 检查请求是否成功，失败则抛出异常
        soup = BeautifulSoup(response.text, 'html.parser')

        data_list = []
        items = soup.select('.item:nth-child(n+1)')
        for item in items:
            name = item.select_one('dt > a').text if item.select_one('dt > a') else ""
            author = item.select_one('.btm > a').text if item.select_one('.btm > a') else ""
            intro = item.select_one('dd').text if item.select_one('dd') else ""
            img = item.select_one('img')['data-original'] if item.select_one('img') else ""
            url_value = item.select_one('dt > a')['href'] if item.select_one('dt > a') else ""
            wordcount = item.select_one('.btm > em').text if item.select_one('.btm > em') else ""
            
            # 更通用的根据url匹配id的正则表达式
            id_match = re.search(r'\/(\d+)(\/|$)', url_value)
            id_value = id_match.group(1) if id_match else ""

            data_list.append({
                "name": name,
                "author": author,
                "intro": intro,
                "wordcount": wordcount,
                "img": img,
                "url": url_value,
                "id": id_value
            })

        result = {
            "c": 200,
            "m": "请求成功",
            "data": data_list
        }

        return JSONResponse(content=result, media_type="application/json")

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"请求出错: {e}")
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"其他错误: {ex}")
