# api/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1) ให้สิทธิ์ override ด้วย DATABASE_URL ก่อน (เช่น sqlite:///./data.db)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # 2) ถ้าไม่ตั้ง DATABASE_URL ไว้ ให้ประกอบจาก POSTGRES_* ตามเดิม
    DB_USER = os.getenv("POSTGRES_USER", "thai_lpr_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "thai_lpr_pass")
    DB_HOST = os.getenv("POSTGRES_HOST", "db")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "thai_lpr")
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3) สร้าง engine + session ให้รองรับทั้ง Postgres/SQLite
engine_kwargs = dict(pool_pre_ping=True)

# กรณี SQLite ให้ใส่ connect_args เพิ่ม (กัน thread issue)
if DATABASE_URL.startswith("sqlite:///") or DATABASE_URL.startswith("sqlite://"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
