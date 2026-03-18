"""
Module tự động di chuyển dữ liệu (Migrations)
Tự động phát hiện và thực thi các thay đổi cấu trúc database cần thiết khi ứng dụng khởi động
"""
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def get_db_path():
    """Lấy đường dẫn file database"""
    from app.config import settings
    db_file = settings.database_url.split("///")[-1]
    return Path(db_file)


def column_exists(cursor, table_name, column_name):
    """Kiểm tra cột được chỉ định có tồn tại trong bảng không"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def run_auto_migration():
    """
    Chạy tự động quá trình migrate database
    Phát hiện các cột còn thiếu và tự động thêm vào
    """
    db_path = get_db_path()
    
    if not db_path.exists():
        logger.info("File database chưa tồn tại, bỏ qua migration")
        return
    
    logger.info("Bắt đầu kiểm tra cấu trúc database (migration)...")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        migrations_applied = []
        
        # Kiểm tra và thêm cột liên quan bảo hành
        if not column_exists(cursor, "redemption_codes", "has_warranty"):
            logger.info("Thêm trường redemption_codes.has_warranty")
            cursor.execute("""
                ALTER TABLE redemption_codes 
                ADD COLUMN has_warranty BOOLEAN DEFAULT 0
            """)
            migrations_applied.append("redemption_codes.has_warranty")
        
        if not column_exists(cursor, "redemption_codes", "warranty_expires_at"):
            logger.info("Thêm trường redemption_codes.warranty_expires_at")
            cursor.execute("""
                ALTER TABLE redemption_codes 
                ADD COLUMN warranty_expires_at DATETIME
            """)
            migrations_applied.append("redemption_codes.warranty_expires_at")
        
        if not column_exists(cursor, "redemption_codes", "warranty_days"):
            logger.info("Thêm trường redemption_codes.warranty_days")
            cursor.execute("""
                ALTER TABLE redemption_codes 
                ADD COLUMN warranty_days INTEGER DEFAULT 30
            """)
            migrations_applied.append("redemption_codes.warranty_days")
        
        if not column_exists(cursor, "redemption_records", "is_warranty_redemption"):
            logger.info("Thêm trường redemption_records.is_warranty_redemption")
            cursor.execute("""
                ALTER TABLE redemption_records 
                ADD COLUMN is_warranty_redemption BOOLEAN DEFAULT 0
            """)
            migrations_applied.append("redemption_records.is_warranty_redemption")

        # Kiểm tra và thêm trường Token refresh
        if not column_exists(cursor, "teams", "refresh_token_encrypted"):
            logger.info("Thêm trường teams.refresh_token_encrypted")
            cursor.execute("ALTER TABLE teams ADD COLUMN refresh_token_encrypted TEXT")
            migrations_applied.append("teams.refresh_token_encrypted")

        if not column_exists(cursor, "teams", "session_token_encrypted"):
            logger.info("Thêm trường teams.session_token_encrypted")
            cursor.execute("ALTER TABLE teams ADD COLUMN session_token_encrypted TEXT")
            migrations_applied.append("teams.session_token_encrypted")

        if not column_exists(cursor, "teams", "client_id"):
            logger.info("Thêm trường teams.client_id")
            cursor.execute("ALTER TABLE teams ADD COLUMN client_id VARCHAR(100)")
            migrations_applied.append("teams.client_id")

        if not column_exists(cursor, "teams", "error_count"):
            logger.info("Thêm trường teams.error_count")
            cursor.execute("ALTER TABLE teams ADD COLUMN error_count INTEGER DEFAULT 0")
            migrations_applied.append("teams.error_count")

        if not column_exists(cursor, "teams", "account_role"):
            logger.info("Thêm trường teams.account_role")
            cursor.execute("ALTER TABLE teams ADD COLUMN account_role VARCHAR(50)")
            migrations_applied.append("teams.account_role")

        if not column_exists(cursor, "teams", "device_code_auth_enabled"):
            logger.info("Thêm trường teams.device_code_auth_enabled")
            cursor.execute("ALTER TABLE teams ADD COLUMN device_code_auth_enabled BOOLEAN DEFAULT 0")
            migrations_applied.append("teams.device_code_auth_enabled")
        
        # Commit thay đổi
        conn.commit()
        
        if migrations_applied:
            logger.info(f"Hoàn thành quá trình (migration), đã áp dụng {len(migrations_applied)} cập nhật: {', '.join(migrations_applied)}")
        else:
            logger.info("Database đã ở version mới nhất, không cần thực hiện migration")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Migration database thất bại: {e}")
        raise


if __name__ == "__main__":
    # Cho phép chạy script này trực tiếp để migrate dữ liệu thủ công
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_auto_migration()
    print("Migration hoàn tất")
