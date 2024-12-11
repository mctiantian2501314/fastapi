#!/usr/bin/env python3
from public.usage import USAGE as html
from api.bqxs520 import router as bqxs520_router
from api.hello import router as hello_router
from api.random import router as random_router
from api.v1.groq import router as groq_router
from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()

app.include_router(hello_router, prefix="/hello")
app.include_router(random_router, prefix="/random")
app.include_router(groq_router, prefix="/v1/groq")
app.include_router(bqxs520_router, prefix="/bqxs520")


@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
