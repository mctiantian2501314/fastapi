#!/usr/bin/env python3
from public.usage import USAGE as html
from api.bqxs520 import router as bqxs520_router
from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()



app.include_router(bqxs520_router, prefix="/bqxs520")


@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
