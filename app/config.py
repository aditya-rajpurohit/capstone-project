import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(str(DATABASE_URL), echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
