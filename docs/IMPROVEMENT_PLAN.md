# 🎬 KẾ HOẠCH NÂNG CẤP - AI WHITEBOARD VIDEO STUDIO 2.0

> **Ngày khởi tạo:** 2026-10-20
> **Trạng thái:** Đã hoàn thành 5/5 Phase (100% Production Ready)
> **Repository:** https://github.com/NHH-031/tool_AI
> **Phiên bản hiện tại:** 2.0 (Toàn diện, đa tính năng)

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
  - [x] Cập nhật `CreateVideoView.tsx`: thêm bộ chọn tỉ lệ khung hình (16:9, 9:16, 1:1) trực quan
  - [x] Cập nhật `ScriptStep.tsx`: thêm card chọn tỷ lệ khung hình Video (16:9 Ngang vs 9:16 Dọc)
  - [x] Truyền `aspect_ratio` qua toàn bộ pipeline (từ ScriptStep → StoryboardStep → ExportStep)
  - [x] Cập nhật `apps/web/app/types.ts`: thêm field `aspectRatio` vào `ProjectWorkflow`
  - [x] Cập nhật `apps/web/app/api-client.ts`: truyền `aspect_ratio` vào `generateStoryboardImage` và `renderExport`
  - [x] Cập nhật `ExportStep.tsx`: video preview hiển thị dynamic container (`aspect-[9/16]` khi dọc 9:16)
- **Files đã chỉnh sửa:**
  - `apps/web/app/components/CreateVideoView.tsx`
  - `apps/web/app/components/steps/ScriptStep.tsx`
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/types.ts`
  - `apps/web/app/api-client.ts`
  - `apps/web/app/page.tsx`

### Task 3.2: Điều chỉnh sinh ảnh và render theo tỷ lệ mới
- **Mô tả:** Khi chọn 9:16, toàn bộ pipeline từ sinh ảnh đến render video phải dùng kích thước dọc
- **Chi tiết thực hiện:**
  - [x] Cập nhật `core/artwork/prompt_builder.py`: thêm `aspect_ratio` vào `StructuredIllustrationPrompt`
  - [x] Cập nhật `core/artwork/pollinations.py`: nếu `aspect_ratio == "9:16"` → dùng kích thước `720x1280` và bổ sung từ khóa định hướng dọc mobile
  - [x] Cập nhật `apps/api/routers/storyboard.py`: nhận `aspect_ratio` từ request và cấu hình prompt chuẩn định dạng dọc
  - [x] Cập nhật `apps/api/routers/export.py`:
    - Annotation canvas sử dụng tỷ lệ dọc `1080x1920` (hoặc `720x1280`)
    - Vị trí đường đi bàn tay vẽ (handPath) điều chỉnh cho khung hình dọc (tránh lệch ngoài rìa)
    - Truyền `aspect_ratio` cho toàn bộ quá trình render phân cảnh
  - [x] Cập nhật `core/subtitles/burner.py`:
    - Safe-zone cho video dọc 9:16: nâng lề đáy lên `margin_ratio = 0.16` (thay vì 0.08) để tránh bị che bởi thanh điều hướng và caption TikTok / Reels / Shorts
    - Nhóm từ ngắn hơn (`max_words_per_segment = 4`) để phụ đề dọc không bị tràn dòng
  - [x] Cập nhật `engines/whiteboard/adapter.py`: `WhiteboardRenderConfig` hỗ trợ tham số `aspect_ratio`
  - [x] Cập nhật `scripts/render_stream_whiteboard.py`: output video co giãn tỷ lệ chuẩn theo `cap_long_edge` cho video dọc
- **Files đã tạo mới:**
  - `tests/test_aspect_ratio.py`
- **Files đã chỉnh sửa:**
  - `core/artwork/prompt_builder.py`
  - `core/artwork/pollinations.py`
  - `apps/api/routers/storyboard.py`
  - `apps/api/routers/export.py`
  - `core/subtitles/burner.py`
  - `engines/whiteboard/adapter.py`

### 📋 Checklist hoàn thành Phase 3:
- [x] Người dùng chọn được 16:9 (YouTube) hoặc 9:16 (TikTok/Shorts/Reels) từ giao diện
- [x] Ảnh sinh ra đúng tỷ lệ dọc/ngang tương ứng
- [x] Video kết xuất ra đúng kích thước dọc 720x1280 / 1080x1920 khi chọn 9:16
- [x] Lề an toàn phụ đề (Safe Zone) được bảo vệ, tránh bị che khuất bởi UI TikTok/Shorts
- [x] Đã kiểm thử tự động toàn diện qua `pytest tests/test_aspect_ratio.py` (7/7 tests passed)
- [x] Commit & push lên GitHub (Phase 3)

---

## PHASE 4: HOẠT HỌA PHÂN VÙNG NGỮ NGHĨA & ĐA DẠNG BÚT VẼ
> **Mục tiêu:** Nâng tầm chất lượng hoạt họa: vẽ theo thứ tự kể chuyện, đa dạng công cụ vẽ
> **Thời gian ước tính:** 3-4 ngày
> **Mức ưu tiên:** 🔵 TRUNG BÌNH

### Task 4.1: Bóc tách phân vùng vẽ tự động (Multi-Region Reveal)
- **Mô tả:** Thay thế single-region (1 vùng toàn màn hình) bằng 2-3 vùng vẽ theo ngữ nghĩa
- **Chi tiết thực hiện:**
  - [x] Tạo module `core/annotation/auto_segment.py`:
    - Phân tích ảnh bằng OpenCV (edge detection + contour grouping)
    - Chia tranh thành 2-3 khối lớn (vùng nền, vùng nhân vật chính, vùng chi tiết phụ)
    - Tạo annotation JSON với nhiều `elements` thay vì 1 element
  - [x] Cập nhật `_create_scene_annotation()` trong `apps/api/routers/export.py`:
    - Gọi `auto_segment` để phân vùng thay vì tạo 1 vùng toàn cảnh
    - Gán `startMs` tuần tự theo quy tắc: nền → nhân vật → chi tiết
    - Áp dụng `protectedRegions` cho các vùng chồng lấn
  - [x] Kết nối với `core/pipeline/semantic_planner.py` để lấy thông tin ngữ nghĩa (nếu có)
- **Files đã tạo mới:**
  - `core/annotation/__init__.py`
  - `core/annotation/auto_segment.py`
  - `tests/test_multi_region_drawing.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`

### Task 4.2: Bộ sưu tập bàn tay & bút vẽ (Custom Drawing Tools)
- **Mô tả:** Cho người dùng chọn kiểu bàn tay/bút vẽ hoặc ẩn bàn tay
- **Chi tiết thực hiện:**
  - [x] Tạo thư mục `assets/drawing-tools/`:
    - `hand-pen-modern.png` (bút dạ đen - mặc định hiện tại)
    - `hand-quill-vintage.png` (bút lông ngỗng chấm mực - phong cách cổ điển)
    - `hand-calligraphy.png` (bút thư pháp - phong cách Á Đông)
    - `hand-marker.png` (bút viết bảng - phong cách whiteboard hiện đại)
  - [x] Thêm API catalog bút vẽ: `GET /assets/drawing-tools`
  - [x] Cập nhật frontend: selector chọn kiểu bút vẽ tại ExportStep
  - [x] Truyền `hand_tool_id` vào `RenderExportRequest` và pipeline render
  - [x] Hỗ trợ chế độ `no_hand` (ẩn bàn tay, nét vẽ tự hiện)
- **Files đã tạo mới:**
  - `assets/drawing-tools/hand-pen-modern.png`
  - `assets/drawing-tools/hand-marker.png`
  - `assets/drawing-tools/hand-quill-vintage.png`
  - `assets/drawing-tools/hand-calligraphy.png`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/assets.py` (bổ sung endpoint drawing-tools)
  - `apps/api/routers/export.py`
  - `engines/whiteboard/adapter.py`
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/api-client.ts`
  - `apps/web/app/types.ts`
  - `apps/web/app/page.tsx`

### 📋 Checklist hoàn thành Phase 4:
- [x] Video được vẽ theo thứ tự: bối cảnh → nhân vật → chi tiết (không còn quét 1 vùng toàn màn hình)
- [x] Người dùng chọn được ít nhất 3 kiểu bút vẽ/bàn tay hoặc ẩn bàn tay
- [x] Đã kiểm thử tự động toàn diện qua `pytest tests/test_multi_region_drawing.py` (8/8 tests passed)
- [x] Commit & push lên GitHub (Phase 4)

---

## PHASE 5: TỐI ƯU HIỆU NĂNG & TRẢI NGHIỆM STUDIO
> **Mục tiêu:** Tăng tốc render, thêm tính năng tiện ích, nâng cấp UX
> **Thời gian ước tính:** 2-3 ngày
> **Mức ưu tiên:** 🔵 TRUNG BÌNH (Đã hoàn thành 100%)

### Task 5.1: Render song song đa tiến trình (Parallel Multi-Scene Rendering)
- **Mô tả:** Tận dụng nhiều lõi CPU để render đồng thời nhiều cảnh, tăng tốc gấp 2.5-3 lần
- **Chi tiết thực hiện:**
  - [x] Đóng gói bước render và muxing mỗi cảnh vào hàm con không nghẽn luồng
  - [x] Sử dụng `asyncio.Semaphore(max_workers)` kết hợp `asyncio.to_thread` tối ưu trên cả Windows và Linux (tránh vấn đề pickle của ProcessPoolExecutor)
  - [x] Quản lý tiến trình SSE: báo tiến độ render từng cảnh theo thời gian thực tới web client
  - [x] Tự động tính toán số worker: `min(4, total_scenes, max(1, os.cpu_count() - 1))`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/export.py`

### Task 5.2: Nút xem trước hoạt họa từng cảnh (Single-Scene Quick Preview)
- **Mô tả:** Thêm nút "🎬 Xem trước (3s)" trên mỗi cảnh để dựng nhanh đoạn hoạt họa 3 giây (15fps/480p)
- **Chi tiết thực hiện:**
  - [x] Thêm API endpoint `POST /export/preview-scene`:
    - Nhận `scene_index`, `image_url`, `text`, `aspect_ratio`, `drawing_tool`
    - Render nhanh đoạn hoạt họa 3 giây ở 15fps, kích thước tối ưu
    - Trả về URL video preview MP4 tức thì
  - [x] Cập nhật `StoryboardStep.tsx`: thêm nút "🎬 Xem trước (3s)" ngay trên từng thẻ cảnh
  - [x] Hộp thoại xem trước video modal popup có thanh điều khiển HTML5 Video và nút đóng trực quan
- **Files đã tạo mới / chỉnh sửa:**
  - `apps/api/routers/export.py`
  - `apps/web/app/components/steps/StoryboardStep.tsx`
  - `apps/web/app/api-client.ts`

### Task 5.3: Auto-save dự án & Khôi phục phiên làm việc
- **Mô tả:** Tự động lưu trạng thái dự án vào localStorage, không mất dữ liệu khi reload trang
- **Chi tiết thực hiện:**
  - [x] Tạo hook `useAutoSave()` trong frontend:
    - Debounce 1.5 giây, lưu tự động `scenes`, `workflow`, `step`, `subtitles`, `drawing_tool` vào `localStorage`
    - Khi tải trang, kiểm tra bản nháp và hiển thị thanh thông báo nổi bật cho phép "Khôi phục bản nháp" hoặc "Bỏ qua / Xóa nháp"
  - [x] Lưu kèm timestamp định dạng tiếng Việt để người dùng biết thời điểm lưu
  - [x] Cung cấp hàm `discardDraft()` để xóa sạch bản nháp khi cần bắt đầu mới
- **Files đã tạo mới:**
  - `apps/web/app/hooks/useAutoSave.ts`
- **Files đã chỉnh sửa:**
  - `apps/web/app/page.tsx`

### Task 5.4: Dịch kịch bản tự động không cần API key
- **Mô tả:** Bổ sung bộ dịch tự động (deep-translator kết hợp MyMemoryTranslator + GoogleTranslator + Gemini + từ điển) làm fallback khi không có Gemini key
- **Chi tiết thực hiện:**
  - [x] Bổ sung thư viện `deep-translator>=1.11.0` vào `requirements.txt`
  - [x] Tạo module `core/artwork/translator.py`:
    - Hàm `auto_translate_vi_to_en(text: str) -> str` với cơ chế 4 tầng dự phòng
    - Tầng 1: MyMemoryTranslator (ổn định, không bị chặn)
    - Tầng 2: GoogleTranslator
    - Tầng 3: Gemini Generative AI (nếu có API Key)
    - Tầng 4: Bộ từ điển từ khóa tiếng Việt - Anh ngoại tuyến
    - Bộ nhớ đệm (LRU cache) trong bộ nhớ giảm thiểu số lần gọi dịch lặp lại
    - Hàm `create_whiteboard_art_prompt(script_text, aspect_ratio)` sinh prompt chuẩn Comic Line Art
  - [x] Tích hợp vào `apps/api/routers/scripts.py` khi phân rã kịch bản cục bộ không cần key
- **Files đã tạo mới:**
  - `core/artwork/translator.py`
- **Files đã chỉnh sửa:**
  - `apps/api/routers/scripts.py`
  - `requirements.txt`

### Task 5.5: Bảng cài đặt (Settings Modal) trên giao diện web
- **Mô tả:** Cho phép người dùng cấu hình API key, giọng đọc mặc định, tỷ lệ khung hình, công cụ vẽ, kiểu phụ đề ngay trên giao diện web
- **Chi tiết thực hiện:**
  - [x] Tạo component `SettingsModal.tsx`:
    - Ô nhập: Gemini API Key (chế độ ẩn/hiện mật khẩu)
    - Chọn tỷ lệ mặc định: 16:9 Ngang hoặc 9:16 Dọc
    - Chọn giọng đọc mặc định: Nam (NamMinh) / Nữ (HoaiMy)
    - Thanh trượt: Tốc độ đọc mặc định (0.8x - 1.5x)
    - Chọn công cụ vẽ mặc định: Bút hiện đại, bút lông, bút máy cổ điển, bút thư pháp, ẩn bàn tay
    - Bật/tắt phụ đề mặc định và chọn phong cách phụ đề (Cổ điển / Karaoke)
    - Nút xóa cache và đặt lại cấu hình gốc
  - [x] Nút "⚙️ Cài đặt" trực quan trên thanh tiêu đề `StudioHeader.tsx`
  - [x] Tích hợp với `localStorage` và cập nhật state toàn studio trong `apps/web/app/page.tsx`
- **Files đã tạo mới:**
  - `apps/web/app/components/SettingsModal.tsx`
- **Files đã chỉnh sửa:**
  - `apps/web/app/components/StudioHeader.tsx`
  - `apps/web/app/page.tsx`

### 📋 Checklist hoàn thành Phase 5:
- [x] Render video nhanh hơn ít nhất 2x so với hiện tại (xử lý song song đa cảnh)
- [x] Người dùng xem trước được hoạt họa từng cảnh trước khi render toàn bộ (quick preview 3s)
- [x] Dự án tự động lưu nháp, thông báo khôi phục mượt mà không mất dữ liệu khi reload trang
- [x] Dịch kịch bản tự động với 4 tầng dự phòng không cần cấu hình API key
- [x] Đã kiểm thử tự động toàn diện qua `pytest tests/test_phase5_optimizations.py` (4/4 tests passed)
- [x] Toàn bộ hệ thống vượt qua 30/30 unit & integration tests, TypeScript 0 lỗi
- [x] Commit & push lên GitHub (Phase 5)

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
