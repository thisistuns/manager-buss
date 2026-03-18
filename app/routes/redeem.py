"""
Route đổi mã
Xử lý yêu cầu xác minh mã đổi và tham gia Team của người dùng
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.redeem_flow import redeem_flow_service

logger = logging.getLogger(__name__)

# Tạo router
router = APIRouter(
    prefix="/redeem",
    tags=["redeem"]
)


# Model yêu cầu
class VerifyCodeRequest(BaseModel):
    """Yêu cầu xác minh mã đổi"""
    code: str = Field(..., description="Mã đổi", min_length=1)


class RedeemRequest(BaseModel):
    """Yêu cầu đổi mã"""
    email: EmailStr = Field(..., description="Email người dùng")
    code: str = Field(..., description="Mã đổi", min_length=1)
    team_id: Optional[int] = Field(None, description="Team ID (tùy chọn, không truyền sẽ tự động chọn)")


# Model phản hồi
class TeamInfo(BaseModel):
    """Thông tin Team"""
    id: int
    team_name: str
    current_members: int
    max_members: int
    expires_at: Optional[str]
    subscription_plan: Optional[str]


class VerifyCodeResponse(BaseModel):
    """Phản hồi xác minh mã đổi"""
    success: bool
    valid: bool
    reason: Optional[str] = None
    teams: List[TeamInfo] = []
    error: Optional[str] = None


class RedeemResponse(BaseModel):
    """Phản hồi đổi mã"""
    success: bool
    message: Optional[str] = None
    team_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/verify", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Xác minh mã đổi và trả về danh sách Team khả dụng

    Args:
        request: Yêu cầu xác minh
        db: Phiên kết nối database

    Returns:
        Kết quả xác minh và danh sách Team khả dụng
    """
    try:
        logger.info(f"Yêu cầu xác minh mã đổi: {request.code}")

        result = await redeem_flow_service.verify_code_and_get_teams(
            request.code,
            db
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return VerifyCodeResponse(
            success=result.get("success", False),
            valid=result.get("valid", False),
            reason=result.get("reason"),
            teams=[TeamInfo(**team) for team in result.get("teams", [])],
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Xác minh mã đổi thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Xác minh thất bại: {str(e)}"
        )


@router.post("/confirm", response_model=RedeemResponse)
async def confirm_redeem(
    request: RedeemRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Xác nhận đổi mã và tham gia Team

    Args:
        request: Yêu cầu đổi mã
        db: Phiên kết nối database

    Returns:
        Kết quả đổi mã
    """
    try:
        logger.info(f"Yêu cầu đổi mã: {request.email} -> Team {request.team_id} (mã đổi: {request.code})")

        result = await redeem_flow_service.redeem_and_join_team(
            request.email,
            request.code,
            request.team_id,
            db
        )

        if not result["success"]:
            # Trả về status code tương ứng theo loại lỗi
            error_msg = result.get("error") or "Nguyên nhân không xác định"
            if any(kw in error_msg for kw in ["không tồn tại", "đã sử dụng", "đã hết hạn", "thời hạn", "đã đầy", "chỗ", "bảo hành", "không hợp lệ", "hết hiệu lực", "maximum number of seats"]):
                status_code = status.HTTP_400_BAD_REQUEST
                if any(kw in error_msg for kw in ["đã đầy", "chỗ", "maximum number of seats"]):
                    status_code = status.HTTP_409_CONFLICT
                raise HTTPException(
                    status_code=status_code,
                    detail=error_msg
                )
            else:
                # Lỗi hệ thống mặc định
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )

        return RedeemResponse(
            success=result.get("success", False),
            message=result.get("message"),
            team_info=result.get("team_info"),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Đổi mã thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đổi mã thất bại: {str(e)}"
        )
