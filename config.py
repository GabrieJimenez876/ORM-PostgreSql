import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "orm_db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    MAX_CONTENT_LENGTH = 16 * 1024
