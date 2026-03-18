"""
Hệ thống Quản lý GPT Team và Mã đổi Tự động Mời
File khởi động ứng dụng FastAPI
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import logging
from pathlib import Path
from datetime import datetime

from contextlib import asynccontextmanager
# Nhập các route
from app.routes import redeem, auth, admin, api, user, warranty
from app.config import settings
from app.database import init_db, close_db, AsyncSessionLocal
from app.services.auth import auth_service

# Lấy thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"

from starlette.exceptions import HTTPException as StarletteHTTPException

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời ứng dụng
    Khởi tạo database khi bật, giải phóng tài nguyên khi tắt
    """
    logger.info("Hệ thống đang khởi động, đang khởi tạo database...")
    try:
        # 0. Đảm bảo thư mục database tồn tại
        db_file = settings.database_url.split("///")[-1]
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Tạo bảng database
        await init_db()
        
        # 2. Chạy migration database tự động
        from app.db_migrations import run_auto_migration
        run_auto_migration()
        
        # 3. Khởi tạo mật khẩu admin (nếu chưa tồn tại)
        async with AsyncSessionLocal() as session:
            await auth_service.initialize_admin_password(session)
        logger.info("Khởi tạo database hoàn tất")
    except Exception as e:
        logger.error(f"Khởi tạo database thất bại: {e}")
    
    yield
    
    # Đóng kết nối
    await close_db()
    logger.info("Hệ thống đang tắt, đã giải phóng kết nối database")


# Tạo instance ứng dụng FastAPI
app = FastAPI(
    title="Hệ thống Quản lý GPT Team",
    description="Hệ thống quản lý tài khoản ChatGPT Team và mã đổi tự động mời",
    version="0.1.0",
    lifespan=lifespan
)

# Xử lý ngoại lệ toàn cục
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """ Xử lý ngoại lệ HTTP """
    if exc.status_code in [401, 403]:
        # Kiểm tra xem có phải yêu cầu HTML không
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/login")
    
    # Trả về JSON mặc định (hành vi mặc định của FastAPI)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Cấu hình middleware Session
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=14 * 24 * 60 * 60,  # 14 ngày
    same_site="lax",
    https_only=False  # Môi trường dev đặt False, production nên đặt True
)

# Cấu hình file tĩnh
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# Cấu hình template engine
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Thêm bộ lọc template
def format_datetime(dt):
    """Định dạng ngày giờ"""
    if not dt:
        return "-"
    if isinstance(dt, str):
        try:
            # Tương thích với chuỗi có thông tin múi giờ
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except:
            return dt
    
    # Chuyển đổi sang múi giờ cài đặt để hiển thị (nếu là aware datetime)
    import pytz
    from app.config import settings
    if dt.tzinfo is None:
        # Nếu là naive datetime, giả sử là múi giờ địa phương
        pass
    else:
        # Nếu là aware datetime, chuyển sang múi giờ mục tiêu
        tz = pytz.timezone(settings.timezone)
        dt = dt.astimezone(tz)
        
    return dt.strftime("%Y-%m-%d %H:%M")

def escape_js(value):
    """Escape chuỗi để dùng trong JavaScript"""
    if not value:
        return ""
    return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")

templates.env.filters["format_datetime"] = format_datetime
templates.env.filters["escape_js"] = escape_js

# Cấu hình logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Đăng ký các route
app.include_router(user.router)  # Route người dùng (root path)
app.include_router(redeem.router)
app.include_router(warranty.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Trang đăng nhập"""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "user": None}
    )


@app.get("/health")
async def health_check():
    """Endpoint kiểm tra trạng thái hệ thống"""
    return {"status": "healthy"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """ Route favicon.ico """
    return FileResponse(APP_DIR / "static" / "favicon.png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
