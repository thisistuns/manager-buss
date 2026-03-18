"""
Route API
Xử lý các endpoint API cho yêu cầu AJAX
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.team import TeamService

logger = logging.getLogger(__name__)

# Tạo router
router = APIRouter(
    prefix="/api",
    tags=["api"]
)

# Instance dịch vụ
team_service = TeamService()


@router.get("/teams/{team_id}/refresh")
async def refresh_team(
    team_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Làm mới thông tin Team

    Args:
        team_id: ID của Team
        force: Có ép buộc làm mới Token hay không
        db: Phiên truy cập database
        current_user: Người dùng hiện tại (yêu cầu đăng nhập)

    Returns:
        Kết quả làm mới
    """
    try:
        logger.info(f"Làm mới thông tin Team {team_id}, force={force}")

        result = await team_service.sync_team_info(team_id, db, force_refresh=force)

        if not result["success"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result
            )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Làm mới Team thất bại: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Làm mới Team thất bại: {str(e)}"
            }
        )
