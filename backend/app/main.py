import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import api_router
from app.db.database import init_db

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("eatfit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EatFit AI API starting up...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("EatFit AI API shutting down...")


app = FastAPI(
    title="EatFit AI API",
    description="外食健康饮食 Agent - AI diet advisor for eating out",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": "EatFit AI",
        "version": "1.0.0",
        "description": "外食健康饮食 Agent API"
    }