# 🎬 KẾ HOẠCH NÂNG CẤP - AI WHITEBOARD VIDEO STUDIO 2.0

> **Ngày khởi tạo:** 2026-10-20
> **Trạng thái:** Đang lập kế hoạch
> **Repository:** https://github.com/NHH-031/tool_AI
> **Phiên bản hiện tại:** 1.0 (MVP hoàn chỉnh)

---

## 📊 TỔNG QUAN HIỆN TRẠNG

### ✅ Những gì đã hoàn thành tốt
- Quy trình 4 bước chuẩn mực: Kịch bản → Storyboard → Giọng đọc → Kết xuất video MP4
- Phong cách mỹ thuật 2D Comic / Graphic Novel trên nền giấy kem ấm `#F5EBD7` (tuân thủ SKILL.md)
- Bộ render stream whiteboard: Bàn tay cầm bút vẽ liên tục theo nét thực tế
- SQLite Job Store + SSE theo dõi tiến độ thời gian thực
- Hệ thống TTS EdgeTTS miễn phí chất lượng cao (có trích xuất WordBoundary)
- Sinh ảnh qua Pollinations.ai (miễn phí, không cần API key)
- Đạo diễn kịch bản AI qua Gemini (GeminiScriptDirector)

### ❌ Các lỗ hổng cần xử lý

| # | Vấn đề | Mức độ | File liên quan |
|---|--------|--------|----------------|
| 1 | Nhạc nền BGM chỉ là metadata giả, chưa có file âm thanh thật | 🔴 Nghiêm trọng | `apps/api/routers/music.py`, `export.py` |
| 2 | Pipeline export bỏ qua hoàn toàn `music_id` và `music_volume` | 🔴 Nghiêm trọng | `apps/api/routers/export.py:260-270` |
| 3 | WordBoundary timing từ EdgeTTS bị bỏ rơi, không sinh phụ đề | 🟡 Quan trọng | `core/tts/edge.py:99-127` |
| 4 | Mỗi cảnh chỉ có 1 vùng vẽ toàn màn hình (single-region) | 🟡 Quan trọng | `apps/api/routers/export.py:145-173` |
| 5 | Cố định 16:9, chưa hỗ trợ video dọc 9:16 cho TikTok/Shorts | 🟡 Quan trọng | `core/artwork/pollinations.py`, `export.py` |
| 6 | Chỉ có 1 bàn tay duy nhất, không có tùy chọn bút/tay khác | 🟢 Cải thiện | `assets/drawing-hand.png` |
| 7 | Render tuần tự từng cảnh, chậm 3-5 phút cho 5-6 cảnh | 🟢 Cải thiện | `apps/api/routers/export.py:198-269` |
| 8 | Không có xem trước hoạt họa từng cảnh (quick preview) | 🟢 Cải thiện | `apps/web/app/components/steps/` |
| 9 | Dịch kịch bản phụ thuộc GEMINI_API_KEY hoặc từ điển thủ công | 🟢 Cải thiện | `core/artwork/translations/vi_to_en.json` |
| 10 | Không có Auto-save dự án trên trình duyệt | 🟢 Cải thiện | `apps/web/app/page.tsx` |

---

## 🗺️ LỘ TRÌNH THEO PHASE

---

## PHASE 1: HỆ THỐNG ÂM THANH CHUYÊN NGHIỆP
> **Mục tiêu:** Video xuất ra có nhạc nền, âm thanh bút vẽ sống động, không còn im lặng đơn điệu
> **Thời gian ước tính:** 2-3 ngày
> **Mức ưu tiên:** 🔴 CAO NHẤT

### Task 1.1: Tích hợp kho nhạc nền BGM thật
- **Mô tả:** Bổ sung các file nhạc nền bản quyền miễn phí vào thư mục `assets/audio/music/`
- **Chi tiết thực hiện:**
  - [x] Tạo thư mục `assets/audio/music/`
  - [x] Thu thập/sinh 5 bản nhạc nền miễn phí (lofi, acoustic, cinematic, playful, ambient)
  - [x] Cập nhật `MUSIC_CATALOG` trong `apps/api/routers/music.py`: thêm `preview_url` trỏ đến file thật
  - [x] Thêm API endpoint `GET /music/{music_id}/preview` để phát nhạc thử trên web
  - [x] Cập nhật `apps/web/app/components/MusicView.tsx`: nút Play/Pause nghe thử từng bản nhạc với HTML5 Audio
  - [x] Cập nhật `VoiceStep.tsx`: Thêm nút nghe thử BGM tức thì ngay cạnh thanh chọn nhạc
- **Files đã chỉnh sửa / tạo mới:**
  - `apps/api/routers/music.py`
  - `apps/web/app/components/MusicView.tsx`
  - `apps/web/app/components/steps/VoiceStep.tsx`
  - `apps/web/app/api-client.ts`
  - `scripts/generate_audio_assets.py`

### Task 1.2: Trộn nhạc BGM vào pipeline kết xuất video
- **Mô tả:** Sửa pipeline export để trộn nhạc nền BGM cùng giọng đọc vào video thành phẩm
- **Chi tiết thực hiện:**
  - [x] Tạo module `core/audio/mixer.py`: hàm `mix_audio_with_bgm()` và `AudioMixer.mix_multi_track()`
  - [x] Áp dụng kỹ thuật **Auto-Ducking**: nhạc nền tự hạ ~35% khi có giọng đọc, tự nâng về 100% khi ngắt câu / khoảng lặng
  - [x] Cập nhật `_run_export_pipeline()` trong `apps/api/routers/export.py`:
    - Sau bước render video các cảnh, tiến hành hòa âm đa luồng
    - Đọc `req.music_id` để nạp bản nhạc BGM tương ứng
    - Đọc `req.music_volume` để điều chỉnh âm lượng
  - [x] BGM tự động loop nếu video dài hơn bản nhạc, tự fade-out 2s cuối video
- **Files đã tạo mới:**
  - `core/audio/__init__.py`
  - `core/audio/mixer.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`

### Task 1.3: Hiệu ứng âm thanh cọ bút vẽ (Drawing Scratch SFX)
- **Mô tả:** Lồng âm thanh bút chì/bút lông cọ lên giấy, đồng bộ với thời gian bàn tay vẽ
- **Chi tiết thực hiện:**
  - [x] Tạo 3 mẫu âm thanh SFX bút vẽ (marker draw, pencil sketch, chalk board) lưu tại `assets/audio/sfx/`
  - [x] Tạo module `core/audio/sfx_sync.py`: chồng âm SFX vào khoảng thời gian bàn tay đang vẽ (85% thời lượng thoại)
  - [x] SFX tự tắt khi bàn tay rời đi (15% cuối mỗi cảnh giữ tranh tĩnh cho khán giả quan sát)
  - [x] Tích hợp vào pipeline export cùng BGM và giọng đọc với Limiter chống rè
- **Files đã tạo mới:**
  - `core/audio/sfx_sync.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/types.ts`
  - `tests/test_audio_engine.py`

### 📋 Checklist hoàn thành Phase 1:
- [x] Video xuất ra có nhạc nền BGM thật, âm lượng tự động hạ khi giọng đọc cất tiếng
- [x] Video có tiếng bút vẽ sột soạt đồng bộ với bàn tay
- [x] Người dùng nghe thử được nhạc nền trên giao diện web
- [x] Đã kiểm thử tự động toàn diện qua `pytest tests/test_audio_engine.py` (4/4 tests passed)
- [x] Commit & push lên GitHub (Commit `159ff0f`)

---

## PHASE 2: PHỤ ĐỀ TỰ ĐỘNG & XUẤT FILE SRT
> **Mục tiêu:** Video có phụ đề chạy chữ chuyên nghiệp, xuất kèm file .srt để tải lên YouTube/TikTok
> **Thời gian ước tính:** 2 ngày
> **Mức ưu tiên:** 🟡 CAO

### Task 2.1: Sinh file phụ đề .srt từ WordBoundary timing
- **Mô tả:** Tận dụng mốc thời gian `WordBoundary` từ EdgeTTS để sinh file `.srt` chuẩn
- **Chi tiết thực hiện:**
  - [x] Tạo module `core/subtitles/__init__.py`
  - [x] Tạo module `core/subtitles/srt_generator.py`:
    - Hàm `generate_project_subtitles()`, `create_segments_from_scene()`
    - Phân tách và nhóm từ đồng bộ theo WordBoundary từ TTS hoặc phân bổ đều
    - Xuất chuẩn SRT format: `index`, `timestamp --> timestamp`, `text`
  - [x] Xuất định dạng WebVTT qua `to_vtt()` (cho YouTube / Web player)
  - [x] Cập nhật pipeline export: sau khi render xong, tạo file `.srt` và `.vtt` tổng
  - [x] Thêm API endpoint `GET /export/{job_id}/subtitle` để tải file `.srt` hoặc `.vtt`
- **Files đã tạo mới:**
  - `core/subtitles/__init__.py`
  - `core/subtitles/models.py`
  - `core/subtitles/srt_generator.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `apps/api/routers/voices.py` (lưu timing vào metadata)

### Task 2.2: Burn-in phụ đề trực tiếp lên video
- **Mô tả:** Vẽ phụ đề đè lên video trong quá trình render (tùy chọn bật/tắt)
- **Chi tiết thực hiện:**
  - [x] Tạo module `core/subtitles/burner.py`:
    - Lớp `SubtitleBurner` dùng Pillow (hỗ trợ font Segoe UI / Arial tiếng Việt có dấu)
    - Giải mã và tái nén video chất lượng cao qua PyAV
  - [x] Hỗ trợ 2 kiểu phụ đề:
    - **Classic**: Chữ trắng viền đen nét đậm, nền kính bo góc mờ tối chống chói
    - **Karaoke**: Highlight từ đang đọc màu vàng kim `#FACC15` phong cách TikTok
  - [x] Thêm tùy chọn `subtitle_style` vào `RenderExportRequest` (none / classic / karaoke)
  - [x] Cập nhật frontend `ExportStep.tsx`: bộ chọn 3 kiểu phụ đề trực quan
  - [x] Nút tải file phụ đề `.SRT` và `.VTT` bên cạnh nút tải MP4
- **Files đã tạo mới:**
  - `core/subtitles/burner.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/api-client.ts`
  - `apps/web/app/types.ts`
  - `apps/web/app/page.tsx`
  - `tests/test_subtitles.py`

### 📋 Checklist hoàn thành Phase 2:
- [x] Video kết xuất ra có phụ đề chữ chạy theo nhịp giọng đọc (Classic hoặc TikTok Karaoke)
- [x] Người dùng chọn được kiểu phụ đề (Không phụ đề / Classic / Karaoke)
- [x] Nút "Tải file phụ đề (.SRT)" xuất hiện bên cạnh nút "Tải xuống MP4"
- [x] Đã kiểm thử tự động toàn diện qua `pytest tests/test_subtitles.py` (4/4 tests passed)
- [x] Commit & push lên GitHub (Phase 2)

---

## PHASE 3: HỖ TRỢ VIDEO DỌC 9:16 (TIKTOK / SHORTS / REELS)
> **Mục tiêu:** Nhà sáng tạo có thể chọn xuất video dọc 9:16 cho nền tảng video ngắn
> **Thời gian ước tính:** 2 ngày
> **Mức ưu tiên:** 🟡 CAO

### Task 3.1: Bộ chọn tỷ lệ khung hình trên giao diện web
- **Mô tả:** Thêm bộ chọn aspect ratio (16:9 hoặc 9:16) tại bước đầu tiên
- **Chi tiết thực hiện:**
  - [ ] Cập nhật `CreateVideoView.tsx`: thêm 2 nút radio/toggle chọn `16:9` hoặc `9:16`
  - [ ] Truyền `aspect_ratio` qua toàn bộ pipeline (từ ScriptStep → StoryboardStep → ExportStep)
  - [ ] Cập nhật `apps/web/app/types.ts`: thêm field `aspect_ratio` vào `ProjectWorkflow`
- **Files cần chỉnh sửa:**
  - `apps/web/app/components/CreateVideoView.tsx`
  - `apps/web/app/types.ts`
  - `apps/web/app/page.tsx`

### Task 3.2: Điều chỉnh sinh ảnh và render theo tỷ lệ mới
- **Mô tả:** Khi chọn 9:16, toàn bộ pipeline từ sinh ảnh đến render video phải dùng kích thước dọc
- **Chi tiết thực hiện:**
  - [ ] Cập nhật `core/artwork/pollinations.py`: nếu `aspect_ratio == "9:16"` → dùng `width=720&height=1280`
  - [ ] Cập nhật `apps/api/routers/storyboard.py`: truyền aspect ratio vào prompt
  - [ ] Cập nhật `apps/api/routers/export.py`:
    - Annotation canvas sử dụng `1080x1920` thay vì `1920x1080`
    - Vị trí bàn tay vẽ điều chỉnh cho khung hình dọc
  - [ ] Cập nhật `engines/whiteboard/adapter.py`: `WhiteboardRenderConfig` hỗ trợ tham số `aspect_ratio`
  - [ ] Cập nhật `scripts/render_stream_whiteboard.py`: output video kích thước dọc
- **Files cần chỉnh sửa:**
  - `core/artwork/pollinations.py`
  - `apps/api/routers/storyboard.py`
  - `apps/api/routers/export.py`
  - `engines/whiteboard/adapter.py`
  - `scripts/render_stream_whiteboard.py`

### 📋 Checklist hoàn thành Phase 3:
- [ ] Người dùng chọn được 16:9 (YouTube) hoặc 9:16 (TikTok/Shorts/Reels) từ giao diện
- [ ] Ảnh sinh ra đúng tỷ lệ dọc/ngang tương ứng
- [ ] Video kết xuất ra đúng kích thước dọc 1080x1920 khi chọn 9:16
- [ ] Commit & push lên GitHub

---

## PHASE 4: HOẠT HỌA PHÂN VÙNG NGỮ NGHĨA & ĐA DẠNG BÚT VẼ
> **Mục tiêu:** Nâng tầm chất lượng hoạt họa: vẽ theo thứ tự kể chuyện, đa dạng công cụ vẽ
> **Thời gian ước tính:** 3-4 ngày
> **Mức ưu tiên:** 🔵 TRUNG BÌNH

### Task 4.1: Bóc tách phân vùng vẽ tự động (Multi-Region Reveal)
- **Mô tả:** Thay thế single-region (1 vùng toàn màn hình) bằng 2-3 vùng vẽ theo ngữ nghĩa
- **Chi tiết thực hiện:**
  - [ ] Tạo module `core/annotation/auto_segment.py`:
    - Phân tích ảnh bằng OpenCV (edge detection + contour grouping)
    - Chia tranh thành 2-3 khối lớn (vùng nền, vùng nhân vật chính, vùng chi tiết phụ)
    - Tạo annotation JSON với nhiều `elements` thay vì 1 element
  - [ ] Cập nhật `_create_scene_annotation()` trong `apps/api/routers/export.py`:
    - Gọi `auto_segment` để phân vùng thay vì tạo 1 vùng toàn cảnh
    - Gán `startMs` tuần tự theo quy tắc: nền → nhân vật → chi tiết
    - Áp dụng `protectedRegions` cho các vùng chồng lấn
  - [ ] Kết nối với `core/pipeline/semantic_planner.py` để lấy thông tin ngữ nghĩa (nếu có)
- **Files cần tạo mới:**
  - `core/annotation/__init__.py`
  - `core/annotation/auto_segment.py`
- **Files cần chỉnh sửa:**
  - `apps/api/routers/export.py`

### Task 4.2: Bộ sưu tập bàn tay & bút vẽ (Custom Drawing Tools)
- **Mô tả:** Cho người dùng chọn kiểu bàn tay/bút vẽ hoặc ẩn bàn tay
- **Chi tiết thực hiện:**
  - [ ] Tạo thư mục `assets/drawing-tools/`:
    - `hand-pen-modern.png` (bút dạ đen - mặc định hiện tại)
    - `hand-quill-vintage.png` (bút lông ngỗng chấm mực - phong cách cổ điển)
    - `hand-calligraphy.png` (bút thư pháp - phong cách Á Đông)
    - `hand-marker.png` (bút viết bảng - phong cách whiteboard hiện đại)
  - [ ] Thêm API catalog bút vẽ: `GET /assets/drawing-tools`
  - [ ] Cập nhật frontend: dropdown chọn kiểu bút vẽ tại ExportStep
  - [ ] Truyền `hand_asset_id` vào `RenderExportRequest` và pipeline render
  - [ ] Hỗ trợ chế độ `no_hand` (ẩn bàn tay, nét vẽ tự hiện)
- **Files cần tạo mới:**
  - `apps/api/routers/assets.py` (bổ sung endpoint drawing-tools)
- **Files cần chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `engines/whiteboard/adapter.py`
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/api-client.ts`

### 📋 Checklist hoàn thành Phase 4:
- [ ] Video được vẽ theo thứ tự: bối cảnh → nhân vật → chi tiết (không còn quét 1 vùng toàn màn hình)
- [ ] Người dùng chọn được ít nhất 3 kiểu bút vẽ/bàn tay hoặc ẩn bàn tay
- [ ] Commit & push lên GitHub

---

## PHASE 5: TỐI ƯU HIỆU NĂNG & TRẢI NGHIỆM STUDIO
> **Mục tiêu:** Tăng tốc render, thêm tính năng tiện ích, nâng cấp UX
> **Thời gian ước tính:** 2-3 ngày
> **Mức ưu tiên:** 🔵 TRUNG BÌNH

### Task 5.1: Render song song đa tiến trình (Parallel Multi-Scene Rendering)
- **Mô tả:** Tận dụng nhiều lõi CPU để render đồng thời nhiều cảnh, tăng tốc gấp 2.5-3 lần
- **Chi tiết thực hiện:**
  - [ ] Tách hàm render mỗi cảnh thành hàm thuần (pure function) để chạy trong process riêng
  - [ ] Sử dụng `concurrent.futures.ProcessPoolExecutor` với `max_workers=3-4`
  - [ ] Quản lý tiến trình SSE: báo tiến độ từng cảnh song song
  - [ ] Fallback về tuần tự nếu RAM < 4GB hoặc CPU < 4 core
- **Files cần chỉnh sửa:**
  - `apps/api/routers/export.py`

### Task 5.2: Nút xem trước hoạt họa từng cảnh (Single-Scene Quick Preview)
- **Mô tả:** Thêm nút "🎬 Xem trước" trên mỗi cảnh để dựng nhanh đoạn hoạt họa 3 giây (360p)
- **Chi tiết thực hiện:**
  - [ ] Thêm API endpoint `POST /export/preview-scene`:
    - Nhận `scene_index`, `image_url`, `text`
    - Render nhanh đoạn 3 giây ở 360p/15fps
    - Trả về URL video preview
  - [ ] Cập nhật `StoryboardStep.tsx` hoặc `VoiceStep.tsx`: thêm nút preview icon
  - [ ] Video preview hiển thị trong modal popup hoặc inline player
- **Files cần chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `apps/web/app/components/steps/StoryboardStep.tsx`
  - `apps/web/app/api-client.ts`

### Task 5.3: Auto-save dự án & Khôi phục phiên làm việc
- **Mô tả:** Tự động lưu trạng thái dự án vào localStorage, không mất dữ liệu khi reload trang
- **Chi tiết thực hiện:**
  - [ ] Tạo hook `useAutoSave()` trong frontend:
    - Mỗi 10 giây, lưu `scenes`, `workflow`, `settings` vào `localStorage`
    - Khi load trang, kiểm tra và hiện modal "Khôi phục phiên làm việc trước?"
  - [ ] Lưu kèm timestamp để phân biệt phiên cũ/mới
  - [ ] Nút "Xóa bản nháp" để reset localStorage
- **Files cần tạo mới:**
  - `apps/web/app/hooks/useAutoSave.ts`
- **Files cần chỉnh sửa:**
  - `apps/web/app/page.tsx`

### Task 5.4: Dịch kịch bản tự động không cần API key
- **Mô tả:** Bổ sung bộ dịch tự động (deep-translator hoặc tương đương) làm fallback khi không có Gemini key
- **Chi tiết thực hiện:**
  - [ ] Cài thêm thư viện `deep-translator` vào `requirements.txt`
  - [ ] Tạo module `core/artwork/translator.py`:
    - Hàm `auto_translate_vi_to_en(text: str) -> str`
    - Ưu tiên: Gemini API → deep-translator → từ điển vi_to_en.json
  - [ ] Cập nhật `core/artwork/prompt_builder.py`: gọi `auto_translate` thay vì tra từ điển thủ công
- **Files cần tạo mới:**
  - `core/artwork/translator.py`
- **Files cần chỉnh sửa:**
  - `core/artwork/prompt_builder.py`
  - `requirements.txt`

### Task 5.5: Bảng cài đặt (Settings Modal) trên giao diện web
- **Mô tả:** Cho phép người dùng cấu hình API key, giọng đọc mặc định, v.v. ngay trên web
- **Chi tiết thực hiện:**
  - [ ] Tạo component `SettingsModal.tsx`:
    - Input: Gemini API Key (ẩn mật khẩu)
    - Dropdown: Giọng đọc mặc định
    - Slider: Tốc độ đọc mặc định
    - Toggle: Bật/tắt phụ đề mặc định
  - [ ] Lưu settings vào localStorage
  - [ ] Thêm icon ⚙️ trên Navbar để mở Settings
- **Files cần tạo mới:**
  - `apps/web/app/components/SettingsModal.tsx`
- **Files cần chỉnh sửa:**
  - `apps/web/app/components/Navbar.tsx`
  - `apps/web/app/page.tsx`

### 📋 Checklist hoàn thành Phase 5:
- [ ] Render video nhanh hơn ít nhất 2x so với hiện tại
- [ ] Người dùng xem trước được hoạt họa từng cảnh trước khi render toàn bộ
- [ ] Dự án tự động lưu nháp, không mất khi reload trang
- [ ] Dịch kịch bản tự động mà không cần cấu hình API key
- [ ] Commit & push lên GitHub

---

## 📐 SƠ ĐỒ KIẾN TRÚC SAU NÂNG CẤP

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI WHITEBOARD VIDEO STUDIO 2.0                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │  Bước 1      │  │  Bước 2       │  │  Bước 3      │  │  Bước 4       │ │
│  │  Kịch bản    │→│  Storyboard   │→│  Giọng đọc   │→│  Kết xuất     │ │
│  │  + Tỷ lệ     │  │  + Preview    │  │  + Timing    │  │  + Phụ đề     │ │
│  │  + Dịch AI   │  │  + Auto-seg   │  │  + SRT gen   │  │  + BGM mix    │ │
│  └─────────────┘  └──────────────┘  └─────────────┘  │  + SFX sync   │ │
│                                                         │  + 9:16/16:9  │ │
│                                                         │  + Parallel   │ │
│                                                         └──────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CORE MODULES (Backend)                        │   │
│  │                                                                  │   │
│  │  core/audio/           core/subtitles/         core/annotation/  │   │
│  │  ├── mixer.py          ├── srt_generator.py    ├── auto_segment  │   │
│  │  ├── sfx_sync.py       ├── vtt_generator.py    └── __init__.py   │   │
│  │  └── __init__.py       ├── burner.py                             │   │
│  │                        └── __init__.py                            │   │
│  │                                                                  │   │
│  │  core/artwork/         core/tts/               engines/          │   │
│  │  ├── translator.py     ├── edge.py (timing)    ├── adapter.py    │   │
│  │  ├── pollinations.py   └── ...                 └── ...           │   │
│  │  └── ...                                                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    ASSETS (Media Resources)                      │   │
│  │  assets/audio/music/   → 5 bản BGM miễn phí                     │   │
│  │  assets/audio/sfx/     → 3-4 mẫu âm thanh bút vẽ               │   │
│  │  assets/drawing-tools/ → 4 kiểu bàn tay/bút vẽ                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 TỔNG KẾT SỐ LIỆU

| Chỉ số | Trước nâng cấp | Sau nâng cấp (dự kiến) |
|--------|-----------------|------------------------|
| Âm thanh video | Chỉ giọng đọc | Giọng đọc + BGM + SFX bút vẽ |
| Phụ đề | Không có | Auto-burn (Classic/Karaoke) + Xuất .SRT |
| Tỷ lệ khung hình | Chỉ 16:9 | 16:9 + 9:16 (TikTok/Shorts) |
| Phân vùng vẽ | 1 vùng toàn màn hình | 2-3 vùng ngữ nghĩa |
| Công cụ vẽ | 1 bàn tay duy nhất | 4 kiểu + ẩn bàn tay |
| Tốc độ render (5 cảnh) | ~3-5 phút | ~1-2 phút (song song) |
| Auto-save dự án | Không | Tự lưu mỗi 10 giây |
| Dịch kịch bản không key | Từ điển thủ công (hạn chế) | AI dịch tự động |

---

## 📝 GHI CHÚ QUAN TRỌNG

1. **Tuân thủ SKILL.md:** Mọi thay đổi đều phải giữ nguyên phong cách mỹ thuật 2D Comic/Graphic Novel trên nền giấy kem ấm `#F5EBD7`. Tuyệt đối không tạo ra hiệu ứng 3D hoặc thay đổi bản sắc mỹ thuật.
2. **Tương thích ngược:** Tất cả API endpoint hiện có phải giữ nguyên giao diện (interface), chỉ bổ sung tham số mới ở dạng optional với giá trị mặc định hợp lý.
3. **Thứ tự Phase:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 (có thể song song Phase 4 và Phase 5).
4. **Kiểm thử:** Sau mỗi Phase, chạy `pytest` đảm bảo 100% test pass trước khi commit.
5. **Commit convention:** Mỗi Phase hoàn thành → 1 commit rõ ràng với message dạng `feat(phase-X): [mô tả ngắn]`.

---

> **Cập nhật lần cuối:** 2026-10-20 | **Người lập:** AI Whiteboard Studio Team
