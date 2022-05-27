from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from tgbot.config import Settings

settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db.user}:{settings.db.password}@{settings.db.host}/{settings.db.name}"

Base = declarative_base()


def create_engine(database_url: str):
    engine = create_async_engine(database_url)
    return engine


def create_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory


async def init_models(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
