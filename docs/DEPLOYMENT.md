# 🚀 HƯỚNG DẪN TRIỂN KHAI VÀ TỰ LƯU TRỮ (DEPLOYMENT & SELF-HOSTING GUIDE)

Tài liệu hướng dẫn chi tiết cách triển khai nền tảng **AI Whiteboard Video Production Studio** trên môi trường máy chủ cá nhân (Self-hosted), VPS Cloud (AWS, DigitalOcean, Google Cloud, Hetzner, Vultr) hoặc Docker Compose chỉ với 1 lệnh duy nhất.

---

## 🏗️ 1. KIẾN TRÚC HỆ THỐNG DOCKER

Hệ thống được đóng gói thành cụm microservices tách rời bằng Docker Compose:

```
                      [ Người dùng / Trình duyệt ]
                                   │
                      (HTTP / WebSocket :3000)
                                   ▼
                   ┌───────────────────────────────┐
                   │    whiteboard-web (Node.js)   │
                   │   Next.js 15 Studio Frontend  │
                   └───────────────┬───────────────┘
                                   │
                                   │ (REST API / SSE :8000)
                                   ▼
                   ┌───────────────────────────────┐
                   │    whiteboard-api (Python)    │
                   │   FastAPI + Hardware Engine   │
                   └───────┬───────────────┬───────┘
                           │               │
                 (Hàng đợi tác vụ)   (Lưu trữ video)
                           ▼               ▼
                 ┌──────────────────┐  ┌──────────────────┐
                 │ whiteboard-redis │  │  Thư mục output/ │
                 │ Redis 7 Broker   │  │  (Mount Volume)  │
                 └──────────────────┘  └──────────────────┘
```

---

## 💻 2. YÊU CẦU HỆ THỐNG

### Cấu hình tối thiểu (CPU Mode):
- **CPU:** 4 Cores (Intel / AMD / ARM64).
- **RAM:** 8 GB.
- **Dung lượng đĩa:** Tối thiểu 15 GB trống (cho Docker images và video xuất ra).
- **Hệ điều hành:** Ubuntu 22.04 LTS+, Debian 12+, CentOS Stream 9+, macOS Sonoma+, Windows 11 với WSL2.

### Cấu hình khuyến nghị (GPU Acceleration Mode):
- **CPU:** 8 Cores trở lên.
- **RAM:** 16 GB+.
- **GPU:** NVIDIA GeForce RTX 3050, 3060, 4060, A10G, T4, hoặc Apple Silicon M1/M2/M3/M4.
- **Driver:** NVIDIA Driver >= 525 + `nvidia-container-toolkit`.

---

## ⚡ 3. TRIỂN KHAI 1-CLICK VỚI DOCKER COMPOSE

### Bước 1: Clone kho lưu trữ
```bash
git clone https://github.com/NHH-031/tool_AI.git
cd tool_AI
```

### Bước 2: Tạo file biến môi trường (Tùy chọn)
Tạo file `.env` nếu bạn muốn cấu hình thêm API key cho các nhà cung cấp bên ngoài:
```bash
# Cấu hình API Server
APP_ENV=production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Sinh ảnh minh họa
IMAGE_GENERATOR_PROVIDER=pollinations

# Giọng đọc cao cấp (Không bắt buộc, mặc định dùng EdgeTTS miễn phí)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Bước 3: Khởi động toàn bộ Studio
```bash
docker compose up -d --build
```

### Bước 4: Kiểm tra trạng thái
```bash
# Xem trạng thái các container
docker compose ps

# Xem nhật ký hoạt động
docker compose logs -f api
```

Khi thấy thông báo:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```
Bạn đã triển khai thành công! Hãy mở trình duyệt và truy cập:
- **Giao diện Studio:** `http://localhost:3000`
- **Tài liệu API Swagger:** `http://localhost:8000/docs`
- **Kiểm tra phần cứng GPU:** `http://localhost:8000/system/hardware`

---

## 🎮 4. CẤU HÌNH TĂNG TỐC GPU (NVIDIA GPU PASSTHROUGH)

Nếu máy chủ của bạn có card màn hình NVIDIA, hãy cài đặt **NVIDIA Container Toolkit** để container nhận diện và tăng tốc render qua NVENC:

### Trên Ubuntu/Debian:
```bash
# 1. Thêm kho lưu trữ NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Cài đặt và khởi động lại Docker daemon
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 3. Kiểm tra container nhận diện GPU
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

File `docker-compose.yml` đã được định cấu hình sẵn khối `deploy.resources.reservations.devices` để tự động kích hoạt GPU NVENC khi có sẵn.

---

## 💾 5. QUẢN LÝ DỮ LIỆU & SAO LƯU (DATA PERSISTENCE)

Toàn bộ dữ liệu của bạn được ánh xạ an toàn ra ngoài ổ cứng máy chủ:
- `./output/storyboard/`: Toàn bộ các cảnh vẽ và ảnh phác thảo của các dự án.
- `./output/export/`: Các video MP4 hoàn tất, file phụ đề `.srt`, `.vtt`, ảnh động `.gif` và WebM trong suốt.
- `./output/archive/`: Kho video đã lưu trữ vĩnh viễn kèm cơ sở dữ liệu `archive_db.sqlite`.
- `./output/packages/`: Các file đóng gói dự án di động `.whiteboard`.

### Lệnh sao lưu định kỳ:
```bash
# Sao lưu toàn bộ thư mục output thành file nén tar
tar -czvf whiteboard_backup_$(date +%Y%m%d).tar.gz ./output
```

---

## 🛠️ 6. CẬP NHẬT PHIÊN BẢN MỚI (UPGRADE)

Khi có bản cập nhật mới trên kho mã nguồn:
```bash
git pull origin main
docker compose build --no-cache
docker compose up -d
```

---

## ❓ 7. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Vấn đề | Nguyên nhân | Cách khắc phục |
|--------|-------------|----------------|
| **Cổng 8000 hoặc 3000 đã bị chiếm dụng** | Một dịch vụ khác đang chạy trên cổng này | Đổi cổng ánh xạ trong `docker-compose.yml` (ví dụ: `"8080:8000"`, `"3001:3000"`). |
| **Video render dùng CPU thay vì GPU** | Chưa cài đặt NVIDIA Container Toolkit | Cài đặt theo mục 4 ở trên và kiểm tra bằng lệnh `docker compose exec api nvidia-smi`. |
| **Không tải được âm thanh TTS** | Lỗi kết nối mạng đến máy chủ Microsoft EdgeTTS | Kiểm tra DNS và kết nối internet quốc tế của máy chủ. |
| **Không thể tải lên file .whiteboard lớn** | Giới hạn kích thước upload của Reverse Proxy / Nginx | Thêm cấu hình `client_max_body_size 100M;` trong cấu hình Nginx phía trước. |

---

*AI Whiteboard Video Production Studio · Bản quyền thuộc về đội ngũ phát triển.*
