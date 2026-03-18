# Hệ thống quản lý GPT Team & Mã đổi tự động mời

Một hệ thống quản lý tài khoản ChatGPT Team dựa trên FastAPI, hỗ trợ quản trị viên quản lý hàng loạt tài khoản Team, người dùng có thể dùng mã đổi để tự động tham gia Team.

## 🚀 Docker triển khai & cập nhật một lệnh

### Triển khai nhanh
```bash
git clone https://github.com/tibbar213/team-manage.git
cd team-manage
cp .env.example .env
docker compose up -d
```

### Cập nhật nhanh
```bash
git pull && docker compose down && docker compose up -d --build
```

## ✨ Tính năng chính

### Chức năng cho quản trị viên
- **Quản lý tài khoản Team**
  - Nhập từng Team hoặc nhập hàng loạt (hỗ trợ mọi định dạng AT Token)
  - Tự động nhận diện & trích xuất AT Token, email, Account ID
  - Tự động đồng bộ thông tin Team (tên, gói đăng ký, thời gian hết hạn, số lượng thành viên)
  - Quản lý thành viên Team (xem, thêm, xóa thành viên)
  - Giám sát trạng thái Team (có sẵn / đã đầy / hết hạn / lỗi)

- **Quản lý mã đổi**
  - Tạo mã đổi đơn lẻ / hàng loạt
  - Tùy chỉnh chuỗi mã đổi và thời hạn hiệu lực
  - Lọc theo trạng thái mã đổi (chưa dùng / đã dùng / hết hạn)
  - Xuất mã đổi ra file văn bản
  - Xóa mã đổi chưa sử dụng

- **Tra cứu lịch sử sử dụng**
  - Lọc đa chiều (email, mã đổi, Team ID, khoảng thời gian)
  - Phân trang (20 bản ghi mỗi trang)
  - Thống kê (tổng số, hôm nay, tuần này, tháng này)

- **Cài đặt hệ thống**
  - Cấu hình proxy (HTTP/SOCKS5)
  - Đổi mật khẩu quản trị viên
  - Điều chỉnh cấp độ log động
  - **Webhook cảnh báo tồn kho** (khi mã đổi sắp hết có thể tự động gọi hệ thống bên ngoài để bổ sung)

### Tự động hóa & tích hợp
- **Cảnh báo tồn kho & tự động nhập Team**
  - Khi số mã đổi khả dụng thấp hơn ngưỡng cấu hình, tự động gọi Webhook cảnh báo
  - Hỗ trợ chương trình bên thứ ba gọi API để tự động nhập thêm tài khoản Team mới
  - Hướng dẫn tích hợp chi tiết xem tại [integration_docs.md](integration_docs.md)

### Chức năng cho người dùng cuối
- **Quy trình đổi mã**
  - Nhập email và mã đổi
  - Tự động kiểm tra hiệu lực mã đổi
  - Hiển thị danh sách Team khả dụng
  - Cho phép chọn Team thủ công hoặc tự động phân bổ
  - Tự động gửi lời mời Team tới email của người dùng

## 🛠️ Ngăn xếp kỹ thuật

- **Backend**: FastAPI 0.109+
- **Web server**: Uvicorn
- **Cơ sở dữ liệu**: SQLite + SQLAlchemy 2.0 + aiosqlite
- **Template engine**: Jinja2
- **HTTP client**: curl-cffi (mô phỏng fingerprint trình duyệt, vượt Cloudflare)
- **Xác thực**: Session-based (hash mật khẩu bằng bcrypt)
- **Mã hóa**: cryptography (AES-256-GCM)
- **Giải mã JWT**: PyJWT
- **Frontend**: HTML + CSS + JavaScript thuần

## 📋 Yêu cầu hệ thống

- Python 3.10+
- pip (trình quản lý gói Python)
- Hệ điều hành: Windows / Linux / macOS

## 🚀 Bắt đầu nhanh

### 1. Clone dự án

```bash
git clone https://github.com/tibbar213/team-manage.git
cd team-manage
```

### 2. Tạo môi trường ảo

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Sao chép `.env.example` thành `.env` và chỉnh sửa cấu hình:

```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:

```env
# Cấu hình ứng dụng
APP_NAME=Hệ thống Quản lý GPT Team
APP_VERSION=0.1.0
APP_HOST=0.0.0.0
APP_PORT=8008
DEBUG=True

# Cấu hình cơ sở dữ liệu (mặc định dùng SQLite)
DATABASE_URL=sqlite+aiosqlite:///team_manage.db

# Cấu hình bảo mật (bắt buộc đổi khi chạy production)
SECRET_KEY=your-secret-key-here-change-in-production
ADMIN_PASSWORD=admin123

# Cấu hình log
LOG_LEVEL=INFO

# Cấu hình proxy (tùy chọn)
PROXY_ENABLED=False
PROXY=

# Cấu hình JWT
JWT_VERIFY_SIGNATURE=False
```

### 5. Khởi tạo cơ sở dữ liệu

```bash
python init_db.py
```

### 6. Khởi động ứng dụng

```bash
# Chế độ phát triển (tự reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8008

# Hoặc chạy trực tiếp
python app/main.py
```

### 7. Truy cập ứng dụng

- **Trang đổi mã cho người dùng**: http://localhost:8008/
- **Trang đăng nhập quản trị**: http://localhost:8008/login
- **Bảng điều khiển quản trị**: http://localhost:8008/admin

**Tài khoản quản trị mặc định**:
- Tên đăng nhập: `admin`
- Mật khẩu: `admin123` (nên đổi ngay sau lần đăng nhập đầu tiên)

---

## 🐳 Triển khai bằng Docker (khuyến nghị)

Dự án hỗ trợ triển khai nhanh bằng Docker để đảm bảo môi trường đồng nhất và đơn giản cấu hình.

### 1. Chuẩn bị

Đảm bảo hệ thống đã cài:
- Docker
- Docker Compose

### 2. Khởi động nhanh

1.  Clone dự án và vào thư mục.
2.  Cấu hình file `.env` (tham khảo mục "Cấu hình biến môi trường" ở trên).
3.  Chạy lệnh Docker Compose:

```bash
# 构建并启动容器
docker compose up -d
```

### 3. Lưu trữ dữ liệu (persist)

Trong cấu hình Docker đã map file `team_manage.db` của host vào trong container, nên dữ liệu sẽ được lưu ở thư mục gốc dự án, kể cả khi xóa container thì dữ liệu vẫn còn.

### 4. Một số lệnh thường dùng

```bash
# 查看日志
docker compose logs -f

# 停止并移除容器
docker compose down

# 重新构建镜像
docker compose build --no-cache
```

## 📁 Cấu trúc dự án

```
team-manage/
├── app/                        # Thư mục chính của ứng dụng
│   ├── main.py                 # Entry FastAPI
│   ├── config.py               # Quản lý cấu hình
│   ├── database.py             # Kết nối CSDL
│   ├── models.py               # Các model SQLAlchemy
│   ├── routes/                 # Module route
│   │   ├── admin.py            # Route cho admin
│   │   ├── user.py             # Route cho người dùng
│   │   ├── api.py              # API endpoint
│   │   ├── auth.py             # Route xác thực
│   │   └── redeem.py           # Route đổi mã
│   ├── services/               # Các service nghiệp vụ
│   │   ├── auth.py             # Service xác thực
│   │   ├── chatgpt.py          # Tích hợp ChatGPT API
│   │   ├── encryption.py       # Service mã hóa
│   │   ├── redeem_flow.py      # Service quy trình đổi mã
│   │   ├── redemption.py       # Service quản lý mã đổi
│   │   ├── settings.py         # Service cài đặt hệ thống
│   │   └── team.py             # Service quản lý Team
│   ├── utils/                  # Các tiện ích
│   │   ├── jwt_parser.py       # Phân tích JWT Token
│   │   └── token_parser.py     # Regex bắt token
│   ├── dependencies/           # Dependency cho FastAPI
│   │   └── auth.py             # Dependency xác thực
│   ├── templates/              # Template Jinja2
│   │   ├── base.html           # Layout cơ bản
│   │   ├── auth/               # Trang xác thực
│   │   ├── admin/              # Trang quản trị
│   │   └── user/               # Trang người dùng
│   └── static/                 # Static files
│       ├── css/                # File CSS
│       └── js/                 # File JavaScript
├── init_db.py                  # Script khởi tạo DB
├── requirements.txt            # Dependencies Python
├── Dockerfile                  # File build Docker image
├── docker-compose.yml          # Orchestrator Docker
├── .dockerignore               # File ignore cho Docker
├── .env.example                # Ví dụ file biến môi trường
├── CLAUDE.md                   # Hướng dẫn cho Claude Code
├── 需求.md                     # Tài liệu yêu cầu dự án (Tiếng Trung)
├── 任务.md                     # Tài liệu theo dõi task (Tiếng Trung)
├── 接口.md                     # Tài liệu API (Tiếng Trung)
└── README.md                   # Tài liệu giới thiệu dự án (file này)
```

## 🔧 Ghi chú cấu hình

### Cấu hình cơ sở dữ liệu

Mặc định dùng SQLite với file `team_manage.db`. Nếu muốn dùng CSDL khác, hãy chỉnh `DATABASE_URL`.

### Cấu hình proxy

Nếu cần đi qua proxy để truy cập ChatGPT API, có thể cấu hình trong trang "Cài đặt Hệ thống" của admin:

- Hỗ trợ proxy HTTP: `http://proxy.example.com:8080`
- Hỗ trợ proxy SOCKS5: `socks5://proxy.example.com:1080`

### Cấu hình bảo mật

**Trước khi triển khai production, bắt buộc chỉnh các cấu hình sau**:

1. `SECRET_KEY`: dùng để ký Session, hãy dùng chuỗi ngẫu nhiên mạnh
2. `ADMIN_PASSWORD`: mật khẩu admin ban đầu, nên đổi ngay sau khi đăng nhập
3. `DEBUG`: trong production phải đặt `False`

## 📖 Hướng dẫn sử dụng

### Quy trình thao tác cho quản trị viên

1. **Đăng nhập trang quản trị**
   - Truy cập http://localhost:8008/login
   - Đăng nhập bằng tài khoản mặc định (admin/admin123)
   - Nên đổi mật khẩu sau lần đăng nhập đầu tiên

2. **Nhập tài khoản Team**
   - Vào "Quản lý Team" → "Nhập Team"
   - Nhập từng Team: điền AT Token, email (tùy chọn), Account ID (tùy chọn)
   - Nhập hàng loạt: dán nội dung có chứa nhiều AT Token (hỗ trợ nhiều định dạng)
   - Hệ thống sẽ tự động nhận diện và trích xuất thông tin

3. **Tạo mã đổi**
   - Vào "Quản lý Mã đổi" → "Tạo Mã đổi"
   - Tạo đơn lẻ: có thể tự đặt mã và thời hạn
   - Tạo hàng loạt: đặt số lượng và thời hạn
   - Sau khi tạo có thể sao chép hoặc tải về

4. **Xem lịch sử sử dụng**
   - Vào "Lịch sử sử dụng"
   - Lọc theo email, mã đổi, Team ID, khoảng thời gian
   - Xem thống kê (tổng, hôm nay, tuần này, tháng này)

5. **Cài đặt hệ thống**
   - Vào "Cài đặt Hệ thống"
   - Cấu hình proxy (nếu cần)
   - Đổi mật khẩu admin
   - Điều chỉnh cấp độ log

### Quy trình đổi mã cho người dùng

1. **Vào trang đổi mã**
   - Truy cập http://localhost:8008/

2. **Nhập thông tin**
   - Điền địa chỉ email
   - Nhập mã đổi

3. **Chọn Team**
   - Hệ thống hiển thị danh sách Team khả dụng
   - Người dùng có thể chọn Team thủ công hoặc bấm "Tự động chọn"

4. **Hoàn tất đổi mã**
   - Hệ thống sẽ gửi lời mời tới email
   - Người dùng xem lại kết quả đổi (tên Team, thời gian hết hạn)

5. **Chấp nhận lời mời**
   - Mở email chứa thư mời ChatGPT Team
   - Bấm vào link trong email để chấp nhận

## 🔌 API

Tài liệu API chi tiết xem tại [接口.md](接口.md) (tiếng Trung).

Một số endpoint chính:

- `POST /auth/login` - Đăng nhập quản trị viên
- `POST /auth/logout` - Đăng xuất quản trị viên
- `POST /redeem/verify` - Xác minh mã đổi
- `POST /redeem/confirm` - Xác nhận đổi mã
- `GET /admin` - Bảng điều khiển admin
- `GET /admin/teams/import` - Trang nhập Team
- `GET /admin/codes` - Danh sách mã đổi
- `GET /admin/records` - Lịch sử sử dụng

## 🐛 Xử lý sự cố

### Khởi tạo cơ sở dữ liệu thất bại

```bash
# 删除旧数据库文件
rm team_manage.db

# 重新初始化
python init_db.py
```

### Không thể gọi được ChatGPT API

1. Kiểm tra kết nối mạng
2. Cấu hình proxy (nếu cần)
3. Kiểm tra AT Token còn hiệu lực không
4. Xem log để tìm lỗi chi tiết

### Nhập Team thất bại

1. Đảm bảo định dạng AT Token đúng
2. Kiểm tra Token đã hết hạn chưa
3. Xác minh Token có quyền quản lý Team hay không

## 📄 Giấy phép

Dự án này chỉ dùng cho mục đích học tập và nghiên cứu.

## 🤝 Đóng góp

Hoan nghênh mọi Issue và Pull Request!

---

**Lưu ý**: Hệ thống này chỉ dùng để quản lý hợp pháp các tài khoản ChatGPT Team, vui lòng tuân thủ Điều khoản dịch vụ của OpenAI.
