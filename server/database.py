from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SQLite file in project root (./chat.db)
    DATABASE_URL: str = "sqlite+aiosqlite:///./chat.db"
    JWT_SECRET_KEY: str = "Thanhbjim@$@&^@&%^&RFghgjSachin"
    JWT_ALG: str = "HS256"


settings = Settings()

# For SQLite concurrency, aiosqlite is required
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)