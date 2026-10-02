# Phase 02 — Architecture & Project Skeleton

## Objective
Xây dựng nền tảng kiến trúc phần mềm (Software Architecture Foundation) và Project Skeleton cho dự án **AI Whiteboard Video Production Studio**. Đảm bảo phân tách rạch ròi giữa UI, Backend API, AI Agents, Provider Abstractions và Whiteboard Media Engine; thiết lập hệ thống kiểm thử tự động cho Backend, Core và Frontend trước khi tiến hành triển khai chi tiết các AI Agent.

---

## Architecture implemented
Hệ thống được tổ chức theo kiến trúc Clean Architecture đa tầng:
- **Tầng Giao diện (Presentation Layer)**: `apps/web/` — Ứng dụng Next.js 15 (App Router), TypeScript, Tailwind CSS.
- **Tầng Ứng dụng & Dịch vụ (Application Layer)**: `apps/api/` — FastAPI REST API cung cấp healthcheck, quản lý job sản xuất và điều phối.
- **Tầng Nghiệp vụ cốt lõi (Core Domain Layer)**: `core/` — Chứa schemas Pydantic (Annotation, Script, Storyboard), Job State Machine, Template Prompts, Asset Management.
- **Tầng Trừu tượng hóa Nhà cung cấp (Provider Abstraction Layer)**: `core/providers/` — Định nghĩa interface trừu tượng cho `LLMProvider`, `TTSProvider`, `ImageProvider`, `StorageProvider` kèm bản mock in-memory, chống vendor lock-in.
- **Tầng Tác tử Chuyên biệt (Specialized Agent Layer)**: `agents/` — Gồm 7 Agent: `script`, `narration`, `visual_planner`, `asset`, `drawing`, `timeline`, `qa`.
- **Tầng Động cơ Hoạt họa (Media Engine Layer)**: `engines/whiteboard/` — Lớp adapter bọc ngoài script render cốt lõi (`render_stream_whiteboard.py`, `merge_scenes.py`), giữ nguyên 100% logic đã được nghiệm thu ở Phase 01.
- **Tầng Hậu kỳ Âm thanh & Ghép kênh (Audio & Compositor)**: `audio/` và `compositor/` — Xử lý giọng đọc, đo duration, pad silence và multiplexing video + voice + BGM.

---

## Modules created
1. `apps/api/`:
   - `main.py`: Entrypoint FastAPI, CORS setup.
   - `config.py`: Tải cấu hình từ môi trường bằng `pydantic-settings`.
   - `routers/health.py`: `GET /health` trả về trạng thái service.
   - `routers/jobs.py`: REST endpoints tạo và truy vấn `ProductionJob`.
2. `apps/web/`:
   - `package.json`, `tsconfig.json`, `next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`.
   - `app/layout.tsx`, `app/globals.css`, `app/page.tsx`: Giao diện studio skeleton tối thiểu.
3. `core/`:
   - `schemas/annotation.py`: Mô hình Pydantic cho Canvas, Region, Reveal, HandPath, Element, Annotation.
   - `schemas/script.py`: Mô hình Pydantic cho SubtitleCue, SceneScript, ProductionScript.
   - `jobs/models.py`: `JobStatus`, `JobStage`, `ProductionJob`.
   - `providers/base.py`: Abstract Base Classes cho LLM, TTS, Image, Storage.
   - `providers/mock.py`: Mock implementation cho toàn bộ providers phục vụ test cục bộ.
   - `templates/prompts.py`: System prompt phong cách phác thảo Notion và kịch bản phân cảnh.
   - `assets/manager.py`: Điều phối lưu trữ tài nguyên dự án.
4. `engines/whiteboard/`:
   - `adapter.py`: `WhiteboardEngineAdapter` và `WhiteboardRenderConfig`.
5. `agents/`:
   - `base.py`: `BaseProductionAgent`, `AgentContext`, `AgentResult`.
   - `script/`, `narration/`, `visual_planner/`, `asset/`, `drawing/`, `timeline/`, `qa/`: Skeletons cho từng agent.
6. `audio/`:
   - `processor.py`: Trừu tượng hóa xử lý audio.
7. `compositor/`:
   - `muxer.py`: Trừu tượng hóa ghép kênh âm thanh & video.
8. `tests/`:
   - `backend/test_health.py`, `backend/test_config.py`, `backend/test_jobs_api.py`.
   - `core/test_imports.py`, `core/test_providers.py`, `core/test_jobs.py`, `core/test_schemas.py`.
   - `engines/test_whiteboard_adapter.py`.
9. `docs/`:
   - `ARCHITECTURE.md`: Tài liệu kiến trúc toàn diện 7 phần kèm Mermaid diagrams.
   - `progress/PHASE-02.md`: (File này) Báo cáo tiến độ Phase 02.
10. `.env.example`: Mẫu biến môi trường an toàn, không chứa secret thật.

---

## Backend status
- **Framework**: FastAPI + Uvicorn + Pydantic v2.
- **Endpoint `/health`**:
  ```json
  {
    "status": "ok",
    "service": "AI Whiteboard Video Production Studio API",
    "version": "0.1.0",
    "timestamp": "2026-10-02T09:52:55.770780Z",
    "environment": "development"
  }
  ```
- **Kiểm thử live server**: Chạy uvicorn thực tế, gọi HTTP GET qua `httpx`, trả về HTTP 200 trong 1.5s.
- **Bảo mật**: Tuyệt đối không hardcode secret; sử dụng file `.env.example` với các biến rỗng.

---

## Frontend status
- **Framework**: Next.js 15.5.27 (App Router), React 19, TypeScript 5, Tailwind CSS 3.
- **Biên dịch (Build)**: `npm run build` chạy thành công 100%, vượt qua toàn bộ kiểm tra type checking và tối ưu hóa static pages (4/4 static pages).
- **Khởi chạy live (Startup)**: Chạy thử `npx next start -p 3001`, gửi yêu cầu HTTP và nhận kết quả phản hồi HTTP Status 200.
- **UI Skeleton**: Thiết kế giao diện hiện đại phong cách tối giản dark-mode, hiển thị trạng thái kết nối backend, thẻ kiến trúc 3 thành phần chính và bảng kiểm định hệ thống.

---

## Provider abstractions
Đã xây dựng 4 interface trừu tượng (`ABC`) cùng các mô hình dữ liệu I/O có kiểu dữ liệu rõ ràng:
1. `LLMProvider`: Hỗ trợ sinh text tự do và trích xuất dữ liệu có cấu trúc qua Pydantic schema (`generate_structured`).
2. `TTSProvider`: Chuyển đổi văn bản thành dữ liệu audio bytes kèm đo lường thời lượng phát âm.
3. `ImageProvider`: Sinh ảnh phác thảo nét vẽ tối giản theo kích thước 1672x941.
4. `StorageProvider`: Quản lý lưu trữ file nhị phân (in-memory dict cho testing, local filesystem cho phát triển).

---

## Job abstractions
- `JobStatus`: `pending`, `running`, `completed`, `failed`, `cancelled`.
- `JobStage`: `queued`, `script_generation`, `narration_synthesis`, `visual_planning`, `asset_generation`, `timeline_annotation`, `whiteboard_rendering`, `audio_compositing`, `quality_assurance`, `completed`.
- `ProductionJob`: Quản lý danh sách các `JobStageProgress`, tự động tính toán tiến độ, thời gian bắt đầu/kết thúc và các file artifact sinh ra.

---

## Tests executed
Toàn bộ 12 test cases tự động trong thư mục `tests/` đều vượt qua (`12 passed in 0.87s`):
1. `tests/backend/test_config.py::test_default_config` — PASSED
2. `tests/backend/test_health.py::test_get_health_endpoint` — PASSED
3. `tests/backend/test_jobs_api.py::test_create_and_get_job` — PASSED
4. `tests/backend/test_jobs_api.py::test_get_nonexistent_job` — PASSED
5. `tests/core/test_imports.py::test_core_imports` — PASSED
6. `tests/core/test_jobs.py::test_production_job_lifecycle` — PASSED
7. `tests/core/test_providers.py::test_mock_llm_provider` — PASSED
8. `tests/core/test_providers.py::test_mock_tts_provider` — PASSED
9. `tests/core/test_providers.py::test_mock_image_provider` — PASSED
10. `tests/core/test_providers.py::test_mock_storage_provider` — PASSED
11. `tests/core/test_schemas.py::test_validate_example_annotation` — PASSED
12. `tests/engines/test_whiteboard_adapter.py::test_whiteboard_adapter_instantiation` — PASSED

Frontend Build Test:
- `npm run build` trong `apps/web`: PASSED (Compiled successfully in 36.0s)

Frontend Live Startup Test:
- `npx next start -p 3001`: PASSED (HTTP 200)

Backend Live Startup Test:
- `uvicorn.run("apps.api.main:app", port=8000)`: PASSED (HTTP 200)

---

## Problems encountered & solutions
1. **Thiếu thư viện `pydantic-settings`**:
   - *Vấn đề*: Khi import `pydantic_settings` trong `apps/api/config.py`, Python báo lỗi `ModuleNotFoundError`.
   - *Khắc phục*: Đã cài đặt `pydantic-settings` vào `.venv`.
2. **Pytest không hỗ trợ native `async def` khi thiếu `pytest-asyncio`**:
   - *Vấn đề*: `pytest` cảnh báo và fail khi gặp hàm `async def test_*` trong `tests/core/test_providers.py`.
   - *Khắc phục*: Tái cấu trúc các test case sang dùng `asyncio.run(_test())` bên trong hàm đồng bộ, giúp test chạy độc lập không phụ thuộc plugin ngoài.

---

## Evidence
- Báo cáo kiểm thử Pytest: `12 passed in 0.87s`.
- Biên dịch Frontend: `apps/web/.next` được tạo thành công với 4/4 route static.
- Tài liệu kiến trúc: [ARCHITECTURE.md](file:///d:/Tool/docs/ARCHITECTURE.md).
- File mẫu biến môi trường: [.env.example](file:///d:/Tool/.env.example).

---

## Phase status
**PASS**
Hệ thống đã đạt đầy đủ 100% tiêu chí nghiệm thu của Phase 02. Nền tảng kiến trúc đã sẵn sàng cho Phase 03.
