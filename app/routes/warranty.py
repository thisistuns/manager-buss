"""
Các route liên quan đến bảo hành
Xử lý các yêu cầu tra cứu bảo hành của người dùng
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.warranty import warranty_service

router = APIRouter(
    prefix="/warranty",
    tags=["warranty"]
)


class WarrantyCheckRequest(BaseModel):
    """Yêu cầu tra cứu bảo hành"""
    email: Optional[EmailStr] = None
    code: Optional[str] = None


class WarrantyCheckRecord(BaseModel):
    """Bản ghi đơn lẻ khi tra cứu bảo hành"""
    code: str
    has_warranty: bool
    warranty_valid: bool
    warranty_expires_at: Optional[str]
    status: str
    used_at: Optional[str]
    team_id: Optional[int]
    team_name: Optional[str]
    team_status: Optional[str]
    team_expires_at: Optional[str]
    email: Optional[str] = None
    device_code_auth_enabled: bool = False


class WarrantyCheckResponse(BaseModel):
    """Phản hồi tra cứu bảo hành"""
    success: bool
    has_warranty: bool
    warranty_valid: bool
    warranty_expires_at: Optional[str]
    banned_teams: list
    can_reuse: bool
    original_code: Optional[str]
    records: list[WarrantyCheckRecord] = []
    message: Optional[str]
    error: Optional[str]


@router.post("/check", response_model=WarrantyCheckResponse)
async def check_warranty(
    request: WarrantyCheckRequest,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Kiểm tra trạng thái bảo hành
    
    Người dùng có thể tra cứu trạng thái bảo hành qua email hoặc mã đổi
    """
    try:
        # Xác minh ít nhất một tham số được cung cấp
        if not request.email and not request.code:
            raise HTTPException(
                status_code=400,
                detail="Phải cung cấp email hoặc mã đổi"
            )
        
        # Gọi dịch vụ bảo hành
        result = await warranty_service.check_warranty_status(
            db_session,
            email=request.email,
            code=request.code
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Tra cứu thất bại")
            )
        
        return WarrantyCheckResponse(
            success=True,
            has_warranty=result.get("has_warranty", False),
            warranty_valid=result.get("warranty_valid", False),
            warranty_expires_at=result.get("warranty_expires_at"),
            banned_teams=result.get("banned_teams", []),
            can_reuse=result.get("can_reuse", False),
            original_code=result.get("original_code"),
            records=result.get("records", []),
            message=result.get("message"),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kiểm tra trạng thái bảo hành thất bại: {str(e)}"
        )


class EnableDeviceAuthRequest(BaseModel):
    """Yêu cầu bật xác thực danh tính thiết bị"""
    code: str
    email: str
    team_id: int


@router.post("/enable-device-auth")
async def enable_device_auth(
    request: EnableDeviceAuthRequest,
    db_session: AsyncSession = Depends(get_db)
):
    """
    Bật xác thực danh tính thiết bị bằng một click
    """
    from app.services.team import team_service
    from sqlalchemy import select
    from app.models import RedemptionRecord

    try:
        # 1. Xác minh có ghi nhận người dùng trong Team hay không
        stmt = select(RedemptionRecord).where(
            RedemptionRecord.code == request.code,
            RedemptionRecord.email == request.email,
            RedemptionRecord.team_id == request.team_id
        )
        result = await db_session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(
                status_code=403,
                detail="Không tìm thấy bản ghi đổi mã liên quan, không thể thực hiện thao tác"
            )
            
        # 2. Gọi TeamService để bật
        # Lưu ý: ở đây chúng ta dùng enable_device_code_auth đã được implement
        res = await team_service.enable_device_code_auth(request.team_id, db_session)
        
        if not res.get("success"):
            raise HTTPException(
                status_code=500,
                detail=res.get("error", "Bật tính năng thất bại")
            )
            
        return {"success": True, "message": "Bật xác thực thiết bị thành công"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bật tính năng thất bại: {str(e)}"
        )
