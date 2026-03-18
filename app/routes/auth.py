"""
Route xác thực
Xử lý đăng nhập và đăng xuất của quản trị viên
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import auth_service
from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

# Tạo router
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


# Model yêu cầu
class LoginRequest(BaseModel):
    """Yêu cầu đăng nhập"""
    password: str = Field(..., description="Mật khẩu quản trị viên", min_length=1)


class ChangePasswordRequest(BaseModel):
    """Yêu cầu đổi mật khẩu"""
    old_password: str = Field(..., description="Mật khẩu cũ", min_length=1)
    new_password: str = Field(..., description="Mật khẩu mới", min_length=6)


# Model phản hồi
class LoginResponse(BaseModel):
    """Phản hồi đăng nhập"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class LogoutResponse(BaseModel):
    """Phản hồi đăng xuất"""
    success: bool
    message: str


class ChangePasswordResponse(BaseModel):
    """Phản hồi đổi mật khẩu"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng nhập quản trị viên

    Args:
        request: Đối tượng Request của FastAPI
        login_data: Dữ liệu đăng nhập
        db: Phiên kết nối database

    Returns:
        Kết quả đăng nhập
    """
    try:
        logger.info("Yêu cầu đăng nhập quản trị viên")

        # Xác minh mật khẩu
        result = await auth_service.verify_admin_login(
            login_data.password,
            db
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )

        # Thiết lập Session
        request.session["user"] = {
            "username": "admin",
            "is_admin": True
        }

        logger.info("Đăng nhập quản trị viên thành công, Session đã được tạo")

        return LoginResponse(
            success=True,
            message="Đăng nhập thành công",
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Đăng nhập thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đăng nhập thất bại: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request):
    """
    Đăng xuất quản trị viên

    Args:
        request: Đối tượng Request của FastAPI

    Returns:
        Kết quả đăng xuất
    """
    try:
        # Xóa Session
        request.session.clear()

        logger.info("Đăng xuất quản trị viên thành công")

        return LogoutResponse(
            success=True,
            message="Đăng xuất thành công"
        )

    except Exception as e:
        logger.error(f"Đăng xuất thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đăng xuất thất bại: {str(e)}"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Đổi mật khẩu quản trị viên

    Args:
        request: Đối tượng Request của FastAPI
        password_data: Dữ liệu mật khẩu
        db: Phiên kết nối database
        current_user: Người dùng hiện tại (cần đăng nhập)

    Returns:
        Kết quả đổi mật khẩu
    """
    try:
        logger.info("Quản trị viên yêu cầu đổi mật khẩu")

        # Đổi mật khẩu
        result = await auth_service.change_admin_password(
            password_data.old_password,
            password_data.new_password,
            db
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        # Xóa Session, yêu cầu đăng nhập lại
        request.session.clear()

        logger.info("Đổi mật khẩu quản trị viên thành công")

        return ChangePasswordResponse(
            success=True,
            message="Đổi mật khẩu thành công, vui lòng đăng nhập lại",
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Đổi mật khẩu thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đổi mật khẩu thất bại: {str(e)}"
        )


@router.get("/status")
async def get_auth_status(request: Request):
    """
    Lấy trạng thái xác thực

    Args:
        request: Đối tượng Request của FastAPI

    Returns:
        Trạng thái xác thực
    """
    user = request.session.get("user")

    return {
        "authenticated": user is not None,
        "user": user
    }
