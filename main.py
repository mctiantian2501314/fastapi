from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from public.usage import USAGE as html
from api.hello import router as hello_router
from api.bqxs520 import router as bqxs520_router
from api.avif_converter import router as avif_router

from api.upload_to_github import router as upload_router
import httpx

app = FastAPI()

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

app.include_router(hello_router, prefix="/hello")
app.include_router(bqxs520_router, prefix="/bqxs520")
app.
app.include_router(avif_router, prefix="/aviftonpng")
app.include_router(upload_router, prefix="/github")

@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")

@app.get("/proxy")
async def proxy(request: Request):
    target_url = "https://ttdndd.serv00.net/cf.php"
    async with httpx.AsyncClient() as client:
        response = await client.get(target_url)
        return JSONResponse(content=response.json(), media_type="application/json")
