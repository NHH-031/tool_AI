# AI Whiteboard Studio — UI Architecture & Design System

Tài liệu thiết kế kiến trúc và quy chuẩn giao diện người dùng cho **AI Whiteboard Video Production Studio**.

---

## 1. Tổng Quan Kiến Trúc Giao Diện

Giao diện Studio được xây dựng dựa trên Next.js 15 (React 19) và Tailwind CSS, tích hợp đồng bộ với Backend Orchestrator API (FastAPI) tại cổng 8000:

```text
[ Browser Client (Next.js 15) ]
              │
              ├── Navbar (Tab routing, System Telemetry, Health Badge)
              ├── Dashboard View (Overview Metrics, Presets, Recent Projects)
              ├── Create Video Flow (10-step wizard: Idea → Language → Voice → Speed → Music → Volume → Style → Ratio → Generate)
              ├── Review & Editor Screen (Script, Entities, Narration Timing, Timeline, Video Player, QA Certificate)
              ├── Regenerate Toolbar & Modal (Script, Scene, Asset, Voice, Drawing)
              ├── Templates View (Catalog of visual styles and paper backgrounds)
              ├── Assets View (SVG Vector asset library with dynamic pose inspection)
              ├── Voices View (TTS voice catalog with waveform sample preview)
              ├── Music View (Royalty-free BGM library with mood & volume presets)
              └── Production Jobs View (8-stage pipeline execution monitor)
              │
              ▼
[ Orchestrator API (FastAPI @ :8000) ]
  ├── /health (Service status)
  ├── /templates (VideoTemplate catalog)
  ├── /assets (Vector SVG manifest)
  ├── /voices (TTS Voice catalog)
  ├── /music (Royalty-free BGM catalog)
  ├── /projects (Studio projects CRUD)
  ├── /jobs (Production jobs lifecycle & auto-runner)
  ├── /jobs/{id}/review (Review screen data)
  ├── /jobs/{id}/regenerate (Granular component regeneration)
  └── /media (StaticFiles streaming for MP4 and PNG artifacts)
```

---

## 2. Quy Chuẩn Thẩm Mỹ & Trải Nghiệm Người Dùng (Rich Aesthetics)

Giao diện tuân thủ các nguyên tắc thiết kế cao cấp:
- **Dark Theme sang trọng**: Sử dụng nền tối sâu thẳm (`bg-slate-950`, `bg-slate-900/50`) kết hợp với hiệu ứng kính mờ `backdrop-blur-xl`.
- **Bảng màu Tailored Gradient**: Điểm nhấn chuyển sắc (`from-indigo-500 via-violet-600 to-amber-500`), tạo cảm giác hiện đại và ấn tượng ngay từ cái nhìn đầu tiên.
- **Trạng thái trực quan sống động (Dynamic States)**:
  - Nút bấm có hiệu ứng hover glow và active scale (`active:scale-95`).
  - Đèn tín hiệu API Health đập nhẹ theo nhịp (`animate-pulse`).
  - Thanh tiến trình 8 giai đoạn có ký hiệu hoàn thành `✓ Done` rõ ràng.

---

## 3. Các Phân Hệ Giao Diện (Studio Views)

### 3.1. Dashboard View
- **Hero Banner**: Cho phép người dùng nhập nhanh ý tưởng video hoặc chọn các kịch bản mẫu ("Con khỉ trèo cây lấy chuối", "Giải thích lạm phát", "Vòng tuần hoàn nước").
- **Thống kê (Metrics Cards)**: Hiển thị tổng số dự án, tiêu chuẩn chất lượng (1080p Full HD), số lượng tư thế vector (35+ Poses), và tỷ lệ kiểm thử thành công (100%).
- **Dự án gần đây**: Danh sách card dự án kèm ảnh thu nhỏ (thumbnail), thời lượng, trạng thái và nút mở thẳng vào màn hình Review.

### 3.2. Create Video Flow (Quy Trình 10 Bước)
Thực hiện tuần tự quy trình chuẩn:
1. **Idea / Title**: Nhập tiêu đề và mô tả ý tưởng chi tiết.
2. **Language**: Lựa chọn ngôn ngữ thuyết minh (Tiếng Việt, English, Japanese, French).
3. **Voice**: Lựa chọn giọng đọc truyền cảm (Nam Khánh, Mai Chi, Thảo My, Arthur) kèm nút nghe thử tức thì.
4. **Speed**: Thanh trượt điều chỉnh tốc độ từ $0.8\text{x}$ đến $1.5\text{x}$ (mặc định $1.0\text{x}$).
5. **Music**: Chọn nhạc nền bản quyền phù hợp với tâm trạng (Playful, Acoustic, Lofi, Corporate).
6. **Music Volume**: Thanh trượt âm lượng $0\% - 100\%$ (khuyến nghị $15\%$ để không lấn át lời thoại).
7. **Visual Style**: Chọn phong cách mỹ thuật (Notion Minimalist, Hand-Drawn Sketch, Vibrant Explainer, Blackboard Chalk).
8. **Aspect Ratio**: Tỉ lệ 16:9 (YouTube), 9:16 (TikTok/Reels), 1:1 (Instagram).
9. **Generate Action**: Nút bấm kích hoạt pipeline với vòng quay loading và tự động chuyển tiếp sang màn hình Review.

### 3.3. Review Screen (Màn Hình Duyệt & Tinh Chỉnh)
- **Status Header**: Hiển thị trạng thái phân cảnh (`completed`, `generating`, `loading`, `retrying`, `failed`) và bảng lưới tiến độ của 8 giai đoạn.
- **Cột Trái (Kiểm định dữ liệu)**:
  - *Script Tab*: Hiển thị kịch bản gốc và danh sách phân đoạn ngữ nghĩa, kèm từ khóa và ước tính thời lượng.
  - *Visual Entities Tab*: Liệt kê thực thể đồ họa (Cây, Khỉ, Chuối), tọa độ bounding box, thứ tự lớp (layer) và độ ưu tiên.
  - *Voice Timing Tab*: Thông số giọng đọc và các thẻ từ khóa karaoke (Word-Level Timing).
  - *Drawing Timeline Tab*: Dòng thời gian vẽ chi tiết từng nét, thời điểm bắt đầu/kết thúc và mục đích ngữ nghĩa.
  - *Scenes Graph Tab*: Cấu trúc phân cảnh tổng hợp.
- **Cột Phải (Trình phát & Chứng nhận)**:
  - Trình phát video MP4 kết xuất thực tế 1080p Full HD kèm điều khiển tua, phát, tạm dừng.
  - Bảng chứng nhận kỹ thuật Media & Visual QA (H.264 / AAC, 30fps, 159 frames, độ lệch $\Delta t = 0.118\text{s}$, chống lộ nét sớm).
  - Nút *Re-Render* và *Export MP4*.

### 3.4. Mô-đun Tái Sinh (Regenerate Toolbar)
Cung cấp 5 nút chức năng mở rộng không khóa kiến trúc:
- 🔄 **Regenerate Script**: Viết lại kịch bản với lời nhắc mới.
- 🔄 **Regenerate Scene**: Bố cục lại các phân cảnh.
- 🔄 **Regenerate Asset**: Đổi tạo hình hoặc tư thế nhân vật.
- 🔄 **Regenerate Voice**: Thu âm lại giọng đọc hoặc đổi tốc độ.
- 🔄 **Regenerate Drawing**: Tái lập lộ trình nét vẽ và quỹ đạo di chuyển bút.
Mỗi nút mở một hộp thoại chỉ dẫn (Instructions modal) và cập nhật thông báo Toast khi hoàn tất.

### 3.5. Xử Lý Trạng Thái Lỗi (Error States)
- Hỗ trợ rõ ràng các trạng thái: `loading`, `generating`, `failed`, `retrying`, `completed`.
- Khi API gặp sự cố, hiển thị banner cảnh báo màu đỏ (`rose-500`) kèm thông báo chi tiết và nút **Thử lại (Retry)**, không để UI rơi vào tình trạng im lặng.

---

## 4. Kiểm Thử Trình Duyệt Tự Động (Browser QA)

Kiểm thử tự động bằng Playwright Chromium (`scripts/verify_studio_ui.py`) đã xác nhận:
- Mọi trang tải mượt mà dưới 500ms.
- Số lượng lỗi JavaScript Console: **0 lỗi**.
- Kiểm thử thành công 100% các nút bấm, bộ chọn, thanh trượt, và quy trình kết xuất.
- Bộ 9 ảnh chụp màn hình kiểm định lưu trữ tại `output/ui_screenshots/`.
