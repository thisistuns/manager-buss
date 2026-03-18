"""
Định nghĩa mô hình cơ sở dữ liệu (Database Models)
Định nghĩa tất cả các bảng SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.utils.time_utils import get_now


class Team(Base):
    """Bảng thông tin Team"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, comment="Email của admin Team")
    access_token_encrypted = Column(Text, nullable=False, comment="Access Token đã mã hóa")
    refresh_token_encrypted = Column(Text, comment="Refresh Token đã mã hóa")
    session_token_encrypted = Column(Text, comment="Session Token đã mã hóa")
    client_id = Column(String(100), comment="OAuth Client ID")
    encryption_key_id = Column(String(50), comment="ID khóa mã hóa")
    account_id = Column(String(100), comment="account-id đang sử dụng")
    team_name = Column(String(255), comment="Tên Team")
    plan_type = Column(String(50), comment="Loại gói (plan)")
    subscription_plan = Column(String(100), comment="Gói đăng ký")
    expires_at = Column(DateTime, comment="Thời gian hết hạn đăng ký")
    current_members = Column(Integer, default=0, comment="Số thành viên hiện tại")
    max_members = Column(Integer, default=6, comment="Số thành viên tối đa")
    status = Column(String(20), default="active", comment="Trạng thái: active/full/expired/error/banned")
    account_role = Column(String(50), comment="Vai trò tài khoản: account-owner/standard-user v.v.")
    device_code_auth_enabled = Column(Boolean, default=False, comment="Đã bật xác thực danh tính thiết bị hay chưa")
    error_count = Column(Integer, default=0, comment="Số lần báo lỗi liên tiếp")
    last_sync = Column(DateTime, comment="Thời gian đồng bộ cuối")
    created_at = Column(DateTime, default=get_now, comment="Thời gian tạo")

    # Mối quan hệ (Relationships)
    team_accounts = relationship("TeamAccount", back_populates="team", cascade="all, delete-orphan")
    redemption_records = relationship("RedemptionRecord", back_populates="team", cascade="all, delete-orphan")

    # Chỉ mục (Indexes)
    __table_args__ = (
        Index("idx_status", "status"),
    )


class TeamAccount(Base):
    """Bảng liên kết Team Account"""
    __tablename__ = "team_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(String(100), nullable=False, comment="Account ID")
    account_name = Column(String(255), comment="Tên Account")
    is_primary = Column(Boolean, default=False, comment="Có phải Account chính không")
    created_at = Column(DateTime, default=get_now, comment="Thời gian tạo")

    # Mối quan hệ
    team = relationship("Team", back_populates="team_accounts")

    # Ràng buộc duy nhất
    __table_args__ = (
        Index("idx_team_account", "team_id", "account_id", unique=True),
    )


class RedemptionCode(Base):
    """Bảng mã đổi (Redemption codes)"""
    __tablename__ = "redemption_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, comment="Mã đổi")
    status = Column(String(20), default="unused", comment="Trạng thái: unused/used/expired/warranty_active")
    created_at = Column(DateTime, default=get_now, comment="Thời gian tạo")
    expires_at = Column(DateTime, comment="Thời gian hết hạn")
    used_by_email = Column(String(255), comment="Email người sử dụng")
    used_team_id = Column(Integer, ForeignKey("teams.id"), comment="Team ID đã sử dụng")
    used_at = Column(DateTime, comment="Thời gian sử dụng")
    has_warranty = Column(Boolean, default=False, comment="Có phải mã bảo hành không")
    warranty_days = Column(Integer, default=30, comment="Thời hạn bảo hành (ngày)")
    warranty_expires_at = Column(DateTime, comment="Thời gian hết hạn bảo hành (tính theo ngày bảo hành sau lần dùng đầu)")

    # Mối quan hệ
    redemption_records = relationship("RedemptionRecord", back_populates="redemption_code")

    # Chỉ mục
    __table_args__ = (
        Index("idx_code_status", "code", "status"),
    )


class RedemptionRecord(Base):
    """Bảng lịch sử sử dụng (Redemption records)"""
    __tablename__ = "redemption_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, comment="Email người dùng")
    code = Column(String(32), ForeignKey("redemption_codes.code"), nullable=False, comment="Mã đổi")
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, comment="Team ID")
    account_id = Column(String(100), nullable=False, comment="Account ID")
    redeemed_at = Column(DateTime, default=get_now, comment="Thời gian đổi")
    is_warranty_redemption = Column(Boolean, default=False, comment="Có phải đổi bảo hành không")

    # Mối quan hệ
    team = relationship("Team", back_populates="redemption_records")
    redemption_code = relationship("RedemptionCode", back_populates="redemption_records")

    # Chỉ mục
    __table_args__ = (
        Index("idx_email", "email"),
    )


class Setting(Base):
    """Bảng cấu hình hệ thống (Settings)"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment="Tên cấu hình")
    value = Column(Text, comment="Giá trị cấu hình")
    description = Column(String(255), comment="Mô tả cấu hình")
    created_at = Column(DateTime, default=get_now, comment="Thời gian tạo")
    updated_at = Column(DateTime, default=get_now, onupdate=get_now, comment="Thời gian cập nhật")

    # Chỉ mục
    __table_args__ = (
        Index("idx_key", "key"),
    )
