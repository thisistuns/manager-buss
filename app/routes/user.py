"""
Route người dùng
Xử lý hiển thị trang đổi mã của người dùng
"""
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

logger = logging.getLogger(__name__)

# Tạo router
router = APIRouter(
    tags=["user"]
)


@router.get("/", response_class=HTMLResponse)
async def redeem_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Trang đổi mã của người dùng

    Args:
        request: Đối tượng Request FastAPI
        db: Phiên truy cập cơ sở dữ liệu

    Returns:
        HTML trang đổi mã
    """
    try:
        from app.main import templates
        from app.services.team import TeamService
        
        team_service = TeamService()
        remaining_spots = await team_service.get_total_available_seats(db)

        logger.info(f"Người dùng truy cập trang đổi mã, số chỗ còn lại: {remaining_spots}")

        return templates.TemplateResponse(
            "user/redeem.html",
            {
                "request": request,
                "remaining_spots": remaining_spots
            }
        )

    except Exception as e:
        logger.error(f"Hiển thị trang đổi mã thất bại: {e}")
        return HTMLResponse(
            content=f"<h1>Tải trang thất bại</h1><p>{str(e)}</p>",
            status_code=500
        )
