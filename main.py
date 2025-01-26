#!/usr/bin/env python3
# main.py
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from public.usage import USAGE as html
from api.hello import router as hello_router
from api.bqxs520 import router as bqxs520_router
from api.six_nine_hsz import router as hsz_router


app = FastAPI()


app.include_router(hello_router, prefix="/hello")
app.include_router(bqxs520_router, prefix="/bqxs520")
app.include_router(hsz_router, prefix="/69hsz")

@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
