"""Mall Backend — FastAPI Application."""
import logging, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mall Backend API",
    description="نظام مول البيت الذكي - Mall MCP System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


@app.get("/")
async def root():
    return {
        "message": f"مرحباً بك في {os.getenv('MALL_NAME', 'مول البيت')} 🏪",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat/query",
            "health": "/api/chat/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mall-backend"}