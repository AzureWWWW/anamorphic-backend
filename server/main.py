import uvicorn
from fastapi import FastAPI
from sqlalchemy import text
from api_router import api_router

from models import Base
from database import engine

app = FastAPI(title="E2E Chat Server")

# Include routers
app.include_router(api_router)

# Create tables and set SQLite pragmas on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Better concurrency for many readers/writers
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
