"""
Module kết nối cơ sở dữ liệu
Cấu hình kết nối bất đồng bộ SQLite và quản lý phiên (session)
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Tạo engine bất đồng bộ
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,  # Kiểm soát việc in SQL
    future=True,
    connect_args={"timeout": 60},  # Tăng thời gian chờ (timeout) kết nối
    pool_size=50,                  # Kích thước cơ bản của connection pool
    max_overflow=100,              # Số lượng connection vượt quá tối đa cho phép
    pool_recycle=3600,             # Tái chế connection mỗi giờ để tránh lỗi hết hạn
    pool_pre_ping=True             # Kiểm tra tính hoạt động (ping) trước khi dùng connection
)

# Tạo factory cho session bất đồng bộ
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Tạo lớp Base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Lấy phiên (session) kết nối cơ sở dữ liệu
    Dùng cho fastapi dependency injection
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Khởi tạo cơ sở dữ liệu
    Tạo tất cả các bảng
    """
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Đóng kết nối cơ sở dữ liệu
    """
    await engine.dispose()
