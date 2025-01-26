#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from public.usage import USAGE as html
from api.hello import router as hello_router
from api.bqxs520 import router as bqxs520_router
from api.six_nine_hsz import router as hsz_router
from api.fsljxs import router as fsljxs_router  

app = FastAPI()


app.mount("/fsljxsfont", StaticFiles(directory="fsljxsfont"), name="fsljxsfont")

app.include_router(hello_router, prefix="/hello")
app.include_router(bqxs520_router, prefix="/bqxs520")
app.include_router(hsz_router, prefix="/69hsz")
app.include_router(fsljxs_router, prefix="/fsljxs")  

@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
