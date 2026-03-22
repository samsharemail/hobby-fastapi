import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.routes import diagram
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CodeFlow AI")

app.include_router(diagram.router, prefix="/api")

_cors_origins = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS", "https://hobby-nextjs.onrender.com"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["https://hobby-nextjs.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
