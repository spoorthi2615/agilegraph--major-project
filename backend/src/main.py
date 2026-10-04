from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import router
from src.core.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AgileGraph application startup.")
    yield

app = FastAPI(title="AgileGraph API", description="Graph-Learned Crypto-Agility Risk Scoring", lifespan=lifespan)

app.include_router(router, prefix="/api/v1")

from src.api.product_routes import router as product_router
app.include_router(product_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to AgileGraph API"}
