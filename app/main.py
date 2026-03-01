from fastapi import FastAPI
from app.routes import diagram
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CodeFlow AI")

app.include_router(diagram.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hobby-nextjs.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

