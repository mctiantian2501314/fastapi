from fastapi import APIRouter, Query, Request
import json
from bs4 import BeautifulSoup
from fastapi.responses import JSONResponse
import httpx
from lxml import etree
import re
import asyncio
from urllib.parse import quote
from playwright.async_api import async_playwright

# 创建一个APIRouter实例
router = APIRouter()

# 搜索功能
@router.get("/search")
async def search(query: str, request: Request):
    headers = {
        "User-Agent": request.headers.get("User-Agent", "Mobile")
    }
    """
    根据输入的关键词在指定网站上进行书籍搜索，并返回搜索结果。

    参数:
    - query: 搜索关键词字符串

    返回:
    - JSONResponse: 包含搜索状态码、消息以及搜索到的书籍相关信息列表的JSON响应
    """
    if not query:
        return JSONResponse(content={"c": "400", "m": "请输入搜索关键词", "data": []})

    async with httpx.AsyncClient() as client:
        encoded_query = quote(query)
        search_url = f"https://www.bqxs520.com/search.shtml?key={encoded_query}"
        response = await client.get(search_url, headers=headers)

        if response.status_code!= 200:
            return JSONResponse(content={"c": "500", "m": "请求失败", "data": []})

        soup = BeautifulSoup(response.text, 'html.parser')
        entries = soup.select("dd ul li")
        results = []

        for entry in entries:
            title = entry.find('span').get('title') if entry.find('span') else None
            href = entry.find('a').get('href') if entry.find('a') else None
            src = entry.find('img').get('src') if entry.find('img') else 'https://s2.loli.net/2024/11/10/RFcln7Wz2Y145VZ.jpg'

            desc_div = entry.select_one(".desc")
            desc_text = desc_div.get_text(strip=True) if desc_div else '暂无简介'

            # 提取ID
            id_match = re.search(r'/book/(\d+)_(\d+)_(\d+)\.shtml', href)
            if id_match:
                id1, id2, id3 = id_match.groups()
                book_id = f"{id1}_{id2}_{id3}"
            else:
                id1 = id2 = id3 = book_id = None

            # 使用CSS选择器提取标签
            itags = []
            tag_spans = entry.select('.tags > span > a')
            for tag_span in tag_spans:
                itags.append(tag_span.text)

            results.append({
                "book_name": title,
                "img": src,
                "text": desc_text,
                "itag": ", ".join(itags),
                "id": {
                    "id1": id1,
                    "id2": id2,
                    "id3": id3,
                    "book_id": book_id
                },
                "url": href
            })

        return JSONResponse(content={"c": "200", "m": "成功响应", "data": results})


# 书籍详情页功能（提取章节相关逻辑整合到这里）
@router.get("/detail")
async def detail(request: Request, book_id: str = Query(..., description="书籍ID")):
    headers = {
        "User-Agent": request.headers.get("User-Agent", "Mobile")
    }
    """
    根据输入的书籍ID获取对应书籍的详细信息，包括书名、作者、更新时间等内容，同时提取第一个章节的id作为list_id返回，优先使用XPath获取主角信息，失败则用CSS选择器尝试获取。

    参数:
    - request: 用于获取客户端请求相关信息的Request对象，从中获取请求头
    - book_id: 从请求参数中获取的书籍ID字符串（通过Query获取，设置为必传参数）

    返回:
    - JSONResponse: 包含获取详情状态码、消息以及书籍详细信息和以第一个章节id作为list_id的JSON响应
    """
    if not book_id:
        return JSONResponse(content={"c": "400", "m": "请输入书籍ID", "data": {}})

    async with httpx.AsyncClient() as client:
        detail_url = f"https://www.bqxs520.com/book/{book_id}.shtml"
        try:
            response = await client.get(detail_url, headers=headers, timeout=10, follow_redirects=True)
            response.raise_for_status()

            # 等待页面加载完毕
            await asyncio.sleep(1)  # 等待5秒，确保页面加载完毕

            content = response.text
            root = etree.HTML(content)

            # 提取书籍详情信息
            try:
                bookname = root.xpath("string(//h1/span/text())")
                print(f"提取到的bookname原始值: {bookname}")
                if bookname is None or bookname.strip() == "":
                    bookname = None
            except Exception as e:
                print(f"提取书名信息失败: {e}")
                bookname = None

            try:
                author = root.xpath("string(//div[@class='title']/span/a/text())")
                if author is None or author.strip() == "":
                    author = None
            except Exception as e:
                print(f"提取作者信息失败: {e}")
                author = None

            try:
                update_time = root.xpath("string(//p[3]/text())")
                update_time = update_time.strip() if update_time else None
            except Exception as e:
                print(f"提取更新时间信息失败: {e}")
                update_time = None

            try:
                lastest_chapter_name = root.xpath("string(//p[4]/text())")
                if lastest_chapter_name is None or lastest_chapter_name.strip() == "":
                    lastest_chapter_name = None
            except Exception as e:
                print(f"提取最新章节名信息失败: {e}")
                lastest_chapter_name = None

            # 提取描述
            try:
                description_p5 = root.xpath("string(//p[5])")
                description_p5 = description_p5.strip() if description_p5 else ""
            except Exception as e:
                print(f"提取描述信息（p5部分）失败: {e}")
                description_p5 = ""

            try:
                description_p6 = root.xpath("string(//p[6])")
                description_p6 = description_p6.strip() if description_p6 else ""
            except Exception as e:
                print(f"提取描述信息（p6部分）失败: {e}")
                description_p6 = ""

            description = f"{description_p5}\n{description_p6}"
            if description == "\n":
                description = ""

            # 提取图片链接
            try:
                img = root.xpath("string(//img/@src)")
                if img is None or img.strip() == "":
                    img = None
            except Exception as e:
                print(f"提取图片链接信息失败: {e}")
                img = None

            # 提取属性
            property_dict = {}
            try:
                property_dict['book_name'] = root.xpath("string(//meta[@property='og:novel:book_name']/@content)")
                if property_dict['book_name'] is None or property_dict['book_name'].strip() == "":
                    property_dict['book_name'] = None
            except Exception as e:
                print(f"提取属性（book_name）信息失败: {e}")
                property_dict['book_name'] = None

            try:
                property_dict['author'] = root.xpath("string(//meta[@property='og:novel:author']/@content)")
                if property_dict['author'] is None or property_dict['author'].strip() == "":
                    property_dict['author'] = None
            except Exception as e:
                print(f"提取属性（author）信息失败: {e}")
                property_dict['author'] = None

            try:
                property_dict['description'] = root.xpath("string(//meta[@property='og:description']/@content)")
                if property_dict['description'] is None or property_dict['description'].strip() == "":
                    property_dict['description'] = None
            except Exception as e:
                print(f"提取属性（description）信息失败: {e}")
                property_dict['description'] = None

            try:
                property_dict['category'] = root.xpath("string(//meta[@property='og:novel:category']/@content)")
                if property_dict['category'] is None or property_dict['category'].strip() == "":
                    property_dict['category'] = None
            except Exception as e:
                print(f"提取属性（category）信息失败: {e}")
                property_dict['category'] = None

            try:
                property_dict['status'] = root.xpath("string(//meta[@property='og:novel:status']/@content)")
                if property_dict['status'] is None or property_dict['status'].strip() == "":
                    property_dict['status'] = None
            except Exception as e:
                print(f"提取属性（status）信息失败: {e}")
                property_dict['status'] = None

            try:
                property_dict['lastest_chapter_name'] = root.xpath("string(//meta[@property='og:novel:lastest_chapter_name']/@content)")
                if property_dict['lastest_chapter_name'] is None or property_dict['lastest_chapter_name'].strip() == "":
                    property_dict['lastest_chapter_name'] = None
            except Exception as e:
                print(f"提取属性（lastest_chapter_name）信息失败: {e}")
                property_dict['lastest_chapter_name'] = None

            try:
                property_dict['update_time'] = root.xpath("string(//meta[@property='og:novel:update_time']/@content)")
                if property_dict['update_time'] is None or property_dict['update_time'].strip() == "":
                    property_dict['update_time'] = None
            except Exception as e:
                print(f"提取属性（update_time）信息失败: {e}")
                property_dict['update_time'] = None

            # 提取标签
            try:
                itags = root.xpath("//p[@class='itag']/a/text()")
                itags = [tag.strip() for tag in itags] if itags else []
            except Exception as e:
                print(f"提取标签信息失败: {e}")
                itags = []

            # 提取主角，先尝试用XPath，失败则用CSS选择器
            protagonists = []
            try:
                protagonists_elements = root.xpath("//div[@class='info']/p[1]/span")
                if protagonists_elements:
                    for element in protagonists_elements:
                        text = "".join(element.itertext()).strip() if element.itertext() else ""
                        # 去除多余空白字符、换行等，确保文本规范
                        clean_text = " ".join(text.split())
                        if clean_text:
                            protagonists.append(clean_text)
            except etree.XPathEvalError as e:
                print(f"使用XPath提取主角信息失败，尝试使用CSS选择器，错误信息: {e}")
                soup = BeautifulSoup(content, 'html.parser')
                protagonists_span = soup.select('p:nth-child(3) > span:nth-child(n+1)')
                if protagonists_span:
                    for span in protagonists_span:
                        text = span.get_text(strip=True) if span.get_text(strip=True) else ""
                        # 同样进行文本规范处理
                        clean_text = " ".join(text.split())
                        if clean_text:
                            protagonists.append(clean_text)

            # 提取第一个章节的id（这里假设章节链接的onclick属性中有类似read(id)这样的格式来获取id，根据实际页面结构调整）
            chapter_links = root.xpath('//div[@class="chapterlist"]/a')
            first_chapter_id = ""
            if chapter_links:
                first_link = chapter_links[0]
                onclick_attr = first_link.get('onclick')
                if onclick_attr:
                    import re
                    match = re.search(r'read\((\d+)\)', onclick_attr)
                    if match:
                        first_chapter_id = match.group(1)

            detail_results = {
                "id": {
                    "id1": book_id.split('_')[0],
                    "id2": book_id.split('_')[1],
                    "id3": book_id.split('_')[2],
                    "book_id": book_id
                },
                'bookname': bookname,
                'author': author,
                'update_time': update_time,
                'lastest_chapter_name': lastest_chapter_name,
                'description': description,
                'img': img,
                'property': property_dict,
                'itag': ", ".join(itags),
                'protagonist': ", ".join(protagonists),
                "list_id": first_chapter_id
            }

            return JSONResponse(content={"c": "200", "m": "成功响应", "data": detail_results})
        except httpx.RequestError as e:
            print(f"请求发生错误: {e}")
            return JSONResponse(content={"c": "500", "m": "请求失败", "data": {}})
        except etree.XPathEvalError as e:
            print(f"XPath表达式解析出错（非主角提取部分）: {e}")
            return JSONResponse(content={"c": "500", "m": "解析详情页失败", "data": {}})

