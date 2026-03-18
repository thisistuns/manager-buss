"""
Module cấu hình ứng dụng
Sử dụng Pydantic Settings để quản lý cấu hình
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


# Thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Cấu hình ứng dụng"""

    # Cấu hình ứng dụng
    app_name: str = "Hệ thống Quản lý GPT Team"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8008
    debug: bool = True

    # Cấu hình database
    # Khuyến nghị dùng thư mục data khi chạy Docker để tránh lỗi quyền truy cập
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/team_manage.db"

    # Cấu hình bảo mật
    secret_key: str = "your-secret-key-here-change-in-production"
    admin_password: str = "admin123"

    # Cấu hình logging
    log_level: str = "INFO"
    database_echo: bool = False

    # Cấu hình proxy
    proxy: str = ""
    proxy_enabled: bool = False

    # Cấu hình JWT
    jwt_verify_signature: bool = False

    # Cấu hình múi giờ
    timezone: str = "Asia/Ho_Chi_Minh"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Tạo instance cấu hình toàn cục
settings = Settings()
