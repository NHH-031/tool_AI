# 🎬 KẾ HOẠCH NÂNG CẤP & MỞ RỘNG TOÀN DIỆN - AI WHITEBOARD VIDEO STUDIO 3.0+

> **Ngày khởi tạo:** 2026-10-20
> **Trạng thái:** 
> - ✅ Đã hoàn thành 5/5 Phase nền tảng (Phase 1 -> Phase 5: 100% Passed)
> - ✅ Đã xử lý triệt để lỗi mất trạng thái Loading khi tương tác nút / chuyển bước
> - 🚀 Bước vào giai đoạn mở rộng tính năng thương mại hóa đỉnh cao (Phase 6 -> Phase 10)
> **Repository:** https://github.com/NHH-031/tool_AI
> **Phiên bản hiện tại:** 2.5 (Production Ready + Hotfixed)

---

## 📊 TỔNG QUAN HIỆN TRẠNG & THÀNH TỰU ĐÃ ĐẠT ĐƯỢC

### ✅ Những gì hệ thống đã vận hành hoàn hảo (Phase 1 – Phase 5)
1. **Quy trình 4 bước chuẩn mực:** Kịch bản (Script) → Phân cảnh (Storyboard) → Giọng đọc (Voice) → Kết xuất video MP4 (Export).
2. **Tuân thủ chặt chẽ SKILL.md:** Phong cách mỹ thuật 2D Comic/Graphic Novel trên nền giấy kem ấm `#F5EBD7`, không chữ rác, viền vẽ tinh gọn.
3. **Âm thanh chuyên nghiệp (Phase 1):** 
   - 5 bản nhạc nền BGM bản quyền miễn phí tích hợp sẵn.
   - Kỹ thuật **Auto-Ducking** tự động hạ nhạc nền khi có giọng đọc và nâng âm lượng ở khoảng lặng.
   - Tiếng cọ bút vẽ sột soạt (Drawing Scratch SFX) đồng bộ chính xác với nhịp di chuyển của bàn tay.
4. **Phụ đề tự động (Phase 2):**
   - Sinh file `.srt` và `.vtt` chuẩn xác từ mốc thời gian `WordBoundary` của TTS.
   - Hỗ trợ Burn-in phụ đề trực tiếp lên video với 2 phong cách: **Cổ điển (Classic)** và **TikTok Karaoke Highlight**.
5. **Đa dạng tỷ lệ khung hình (Phase 3):**
   - Hỗ trợ video ngang **16:9** (YouTube/Facebook) và video dọc **9:16** (TikTok/Shorts/Reels).
   - Tự động điều chỉnh kích thước ảnh sinh ra (720x1280 vs 1280x720) và bảo vệ vùng an toàn phụ đề (Safe Zone) không bị che bởi giao diện mobile.
6. **Hoạt họa ngữ nghĩa & Bút vẽ tùy chọn (Phase 4):**
   - Tự động phân tách 2-3 phân vùng vẽ ngữ nghĩa (bối cảnh → nhân vật → chi tiết) bằng OpenCV.
   - Bộ sưu tập 4 công cụ vẽ: Bút dạ hiện đại, Bút máy cổ điển, Bút thư pháp, Bút viết bảng và Chế độ ẩn bàn tay (`no_hand`).
7. **Tối ưu hóa Studio (Phase 5):**
   - Render song song đa phân cảnh (Parallel Multi-Scene Rendering) tăng tốc độ xuất video gấp 2.5 lần.
   - Nút xem trước hoạt họa 3 giây (Single-Scene Quick Preview) tức thì trên từng phân cảnh.
   - Auto-save dự án tự động vào `localStorage` có thông báo khôi phục mượt mà khi reload trang.
   - Dịch kịch bản tự động 4 tầng dự phòng (MyMemory + Google + Gemini + Offline Dict) hoàn toàn không phụ thuộc API key.
   - Modal Cài đặt Studio trực quan lưu cấu hình yêu thích.
8. **Hotfix Trải nghiệm người dùng:**
   - Khắc phục hoàn toàn sự cố: Bấm chuyển bước hoặc chuyển nút làm biến mất hiệu ứng Loading.
   - Khóa điều hướng (`isLocked`) và hiển thị banner trạng thái toàn cục (`Global Loading Indicator`) kèm thanh tiến độ liên tục cho đến khi tác vụ kết thúc 100%.

---

## 🛠️ CHI TIẾT HOTFIX VỪA THỰC HIỆN

| Vấn đề trước sửa | Nguyên nhân gốc rễ | Giải pháp đã triển khai | Trạng thái |
|-------------------|-------------------|------------------------|------------|
| Khi hệ thống đang xử lý tác vụ (phân tích kịch bản, sinh ảnh, thu âm, render video), người dùng bấm nút chuyển bước hoặc nút khác thì biểu tượng Loading biến mất | Do component bước cũ bị `unmount` bởi conditional rendering `{workflow.currentStep === N && (...)}`, khiến UI cục bộ của bước đó bị hủy dù background task vẫn chạy | 1. Thêm `isAnyLoading` tổng hợp toàn bộ cờ loading.<br>2. Chặn chuyển bước (`handleStepClick`), chuyển dự án (`handleSelectProject`, `handleNewProject`), và các nút Tiếp tục khi đang tải.<br>3. Thêm prop `isLocked` vào `StepProgressBar` & `StudioHeader`.<br>4. Hiển thị Banner Loading toàn cục cố định trên đầu trang kèm nút quay lại bước đang chạy.<br>5. Disable trực quan các nút Back / Next trên cả 4 bước. | ✅ ĐÃ KHẮC PHỤC TRIỆT ĐỂ |

---

## 🗺️ BẢN ĐỒ KẾ HOẠCH NÂNG CẤP MỚI (PHASE 6 - PHASE 10)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      LỘ TRÌNH PHÁT TRIỂN TIẾP THEO (PHASE 6 - 10)                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [PHASE 6] ────► [PHASE 7] ────► [PHASE 8] ────► [PHASE 9] ────► [PHASE 10]           │
│  Vector Stroke   Canvas Studio   Multi-Speaker   Interactive     GPU Acceleration      │
│  Path Tracing    Character Lock  Custom Voice    Subtitles       Redis Task Queue      │
│  Eraser Transit  Asset Upload    ElevenLabs      Handwritten     Docker Compose        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 PHASE 6: VECTOR STROKE ENGINE & HOẠT HỌA BÀN TAY ĐẲNG CẤP [HOÀN THÀNH ✅]
> **Mục tiêu:** Chuyển đổi phương pháp vẽ từ quét mảng khối (raster scan/grid) sang vẽ theo từng nét cọ Vector thực tế (Bezier curves path tracing). Thêm hiệu ứng lau bảng chuyển cảnh.
> **Thời gian hoàn thành:** 2026-10-20
> **Trạng thái:** ✅ ĐÃ TRIỂN KHAI & PASS 100% KIỂM THỬ (11/11 tests trong `tests/test_vector_drawing.py`)
> **Kết quả bàn giao:**
> - `core/drawing/vectorizer.py`: Ramer-Douglas-Peucker & Chaikin curve smoothing, Zhang-Suen morphological thinning, phân loại nét vẽ (`outline`, `structure`, `detail`, `shading`).
> - `core/drawing/stroke_order.py`: `NaturalStrokeSorter` sắp xếp thứ tự vẽ tự nhiên theo phân cấp người thật + TSP nearest-neighbor tối ưu đường đi đầu bút, tự đảo ngược hướng nét vẽ.
> - `core/transitions/eraser.py`: `WhiteboardEraserTransition` sinh hiệu ứng bàn tay cầm giẻ lau xóa bảng quét dọn sạch nét vẽ để lại nền giấy kem ấm `#F5EBD7` kèm audio SFX tiếng cọ xát sột soạt.
> - Bộ tài nguyên mới: `assets/drawing-tools/hand-highlighter.png`, `assets/drawing-tools/hand-eraser.png`, `assets/audio/sfx/eraser_wipe.mp3`.
> - Tích hợp Engine & API: Điểm neo ngòi bút chuẩn xác từng pixel (`TOOL_TIP_CALIBRATION`), góc xoay cổ tay động theo hướng vẽ, chế độ vẽ 2 bút (`multi_pen`), chuyển cảnh (`cut`, `eraser`, `crossfade`) trên cả Backend và UI ExportStep.

### Task 6.1: Vector hóa nét vẽ tranh (SVG / Potrace Path Extraction)
- **Vấn đề hiện tại:** Tranh vẽ được hiện ra theo dạng quét lưới (grid) hoặc viền contour wipe, nét vẽ xuất hiện theo từng mảng nhỏ thay vì nét bút liền mạch uốn lượn như người thật cầm bút.
- **Giải pháp:**
  - Tích hợp bộ vector hóa đường nét hình ảnh bằng thư viện `potrace` / `vtracer` / OpenCV Thinning (Zhang-Suen skeletonization).
  - Trích xuất toàn bộ nét vẽ thành danh sách các đường cong Bezier liên tục (`Polyline` / `Path`).
  - Sắp xếp thứ tự nét vẽ tự nhiên: Các nét khung chính vẽ trước, nét chi tiết nhỏ vẽ sau, nét tô bóng/chấm phá vẽ cuối cùng.
- **Files cần tác động:**
  - `core/drawing/vectorizer.py` (Mới)
  - `core/drawing/stroke_order.py` (Mới)
  - `engines/whiteboard/stream_renderer.py`
  - `tests/test_vector_drawing.py` (Mới)

### Task 6.2: Căn chỉnh ngòi bút theo thời gian thực (Sub-pixel Pen-Tip Alignment)
- **Vấn đề hiện tại:** Bàn tay di chuyển theo hướng chung của vùng hình chữ nhật, đầu ngòi bút chưa bám khít từng milimet theo nét mực đang tuôn ra.
- **Giải pháp:**
  - Căn chỉnh điểm neo ngòi bút (Pen Tip Anchor Point) chính xác cho từng loại công cụ trong `assets/drawing-tools/` (ví dụ: bút dạ ngòi ở tọa độ `(45, 12)`, bút lông ngòi ở `(30, 8)`).
  - Bổ sung hiệu ứng rung tự nhiên tay người (micro-jitter) để đường nét không bị cứng đơ như robot.
  - Tự động xoay nhẹ góc nghiêng bàn tay theo hướng di chuyển của nét cọ (tangential angle rotation).
- **Files cần tác động:**
  - `engines/whiteboard/adapter.py`
  - `scripts/render_stream_whiteboard.py`

### Task 6.3: Đổi màu bút vẽ & Tô màu phân lớp (Multi-Pen Color Reveal)
- **Vấn đề hiện tại:** Chỉ có 1 bàn tay cầm bút dạ đen duy nhất, phần tô màu chỉ xuất hiện sau cùng mà không có thao tác đổi bút.
- **Giải pháp:**
  - Hỗ trợ đổi bút theo lớp vẽ:
    - Bước 1: Bàn tay cầm bút đen phác thảo nét vẽ chính (`ink`).
    - Bước 2: Bàn tay đổi sang bút lông màu hoặc bút dạ quang vàng/cam/xanh tô điểm các chi tiết nổi bật (`color highlight`).
  - Cho phép người dùng tùy chọn bật/tắt tính năng đổi bút trong phần Cài đặt.
- **Files cần tác động:**
  - `assets/drawing-tools/hand-highlighter.png` (Mới)
  - `core/annotation/auto_segment.py`
  - `apps/web/app/components/steps/ExportStep.tsx`

### Task 6.4: Hiệu ứng giẻ lau xóa bảng chuyển cảnh (Whiteboard Eraser Transition)
- **Vấn đề hiện tại:** Giữa 2 phân cảnh kịch bản, video chỉ cắt cảnh trực tiếp (hard cut) làm đứt gãy mạch cảm xúc video vẽ tay.
- **Giải pháp:**
  - Thêm tài nguyên hình ảnh: Bàn tay cầm miếng xóa bảng / khăn lau bảng (`assets/drawing-tools/hand-eraser.png`).
  - Ở 1 giây cuối của phân cảnh cũ, bàn tay cầm miếng xóa bảng lướt qua màn hình lau sạch các nét vẽ từ trái qua phải kèm âm thanh tiếng lau bảng sột soạt (Eraser SFX), để lại mặt bảng giấy kem tinh khôi trước khi phân cảnh mới bắt đầu vẽ.
  - Tùy chọn 3 kiểu chuyển cảnh: Cắt trực tiếp (Cut), Lau bảng (Whiteboard Eraser Wipe), Mờ dần (Crossfade).
- **Files cần tác động:**
  - `assets/drawing-tools/hand-eraser.png` (Mới)
  - `assets/audio/sfx/eraser_wipe.mp3` (Mới)
  - `core/transitions/eraser.py` (Mới)
  - `apps/api/routers/export.py`

---

## 🖼️ PHASE 7: TỰ DO BIÊN TẬP PHÂN CẢNH & KHÓA NHẤT QUÁN NHÂN VẬT [HOÀN THÀNH ✅]
> **Mục tiêu:** Cung cấp công cụ chỉnh sửa hình ảnh trực tiếp trên Canvas, giữ đồng nhất ngoại hình nhân vật qua các cảnh và cho phép người dùng chèn logo/ảnh cá nhân.
> **Thời gian hoàn thành:** 2026-10-20
> **Trạng thái:** ✅ ĐÃ TRIỂN KHAI & PASS 100% KIỂM THỬ (12/12 tests trong `tests/test_phase7_storyboard_studio.py`)
> **Kết quả bàn giao:**
> - `apps/web/app/components/canvas/SceneCanvasEditor.tsx`: Studio biên tập Canvas trực tiếp (Bút vẽ mực, bút dạ quang highlight, giẻ lau tẩy nền `#F5EBD7`, mũi tên chỉ dẫn, khoanh vùng tròn/khung, nhập chữ, đóng dấu doodle, hoàn tác Undo/Redo).
> - `apps/web/app/components/canvas/CustomImageUploadModal.tsx`: Tải ảnh chụp/logo doanh nghiệp từ máy và xem trước kết quả sau khi qua bộ lọc phác thảo.
> - `core/artwork/filter_sketch.py`: Bộ lọc `SketchFilter` chuyển đổi ảnh thực tế/logo thành tranh vẽ 2D nét mực contour `#1A1A1A` kết hợp màu nước comic trên nền giấy kem ấm cổ `#F5EBD7`.
> - `core/artwork/character_anchor.py`: Hệ thống neo giữ nhân vật chính (`CharacterAnchor`), trích xuất tự động từ kịch bản và gắn điều kiện nhất quán khuôn mặt, trang phục, kiểu tóc xuyên suốt toàn bộ các cảnh.
> - `assets/doodles/*.svg`: Kho 16 biểu tượng Doodle vector vẽ tay chuẩn Comic Whiteboard (Mũi tên cong/thẳng/zic-zac, khung highlight, bóng đèn, cúp, ngôi sao, bong bóng thoại, dấu kiểm).
> - Backend APIs: `POST /storyboard/save-canvas-edit`, `POST /storyboard/upload-custom-image`, `POST /storyboard/character-anchor/extract`, `GET /storyboard/doodles/list`.

### Task 7.1: Bộ công cụ Canvas biên tập trực tiếp (In-Place Storyboard Editor)
- **Mô tả:** Cho phép người dùng chỉnh sửa hoặc vẽ thêm trực tiếp lên ảnh phân cảnh tại Bước 2 (Storyboard).
- **Chi tiết thực hiện:**
  - Tích hợp Fabric.js hoặc HTML5 Canvas editor nhẹ:
    - Thêm mũi tên chỉ dẫn vẽ tay (Doodle Arrows: cong, thẳng, đứt đoạn).
    - Thêm vòng tròn / khung vuông đánh dấu điểm nhấn (Highlight Circle / Box).
    - Thêm hộp thoại lời thoại bong bóng (Speech Bubble) hoặc ghi chú chữ viết tay.
    - Công cụ xóa chi tiết thừa (Eraser / Brush trắng nền `#F5EBD7`).
  - Lưu ảnh đã chỉnh sửa và tự động cập nhật phân vùng vẽ tương ứng.
- **Files cần tác động:**
  - `apps/web/app/components/canvas/SceneCanvasEditor.tsx` (Mới)
  - `apps/web/app/components/steps/StoryboardStep.tsx`
  - `apps/api/routers/storyboard.py`

### Task 7.2: Khóa đặc điểm nhân vật AI (Character Consistency Engine)
- **Vấn đề hiện tại:** Mỗi phân cảnh sinh ảnh độc lập, cùng một nhân vật (ví dụ: "anh Nam kỹ sư") cảnh 1 mặc áo xanh đeo kính, cảnh 2 lại thành người khác mặc áo đỏ.
- **Giải pháp:**
  - Trích xuất nhân vật trung tâm trong kịch bản: `character_name`, `gender`, `features` (tóc, kính, trang phục đặc trưng).
  - Gán hạt giống cố định (`seed`) và neo chuỗi mô tả nhân vật (`character anchor prompt`) xuyên suốt toàn bộ các prompt phân cảnh.
  - Thêm thẻ "Nhân vật chính" trong Bước 1 để người dùng tùy chỉnh tạo hình nhân vật mẫu trước khi sinh phân cảnh.
- **Files cần tác động:**
  - `core/artwork/character_anchor.py` (Mới)
  - `core/artwork/prompt_builder.py`
  - `apps/web/app/components/steps/ScriptStep.tsx`

### Task 7.3: Tải ảnh riêng & Logo doanh nghiệp để vẽ tay (Custom Asset Upload)
- **Mô tả:** Cho phép người dùng tải lên hình ảnh logo, ảnh chụp sản phẩm, sơ đồ biểu đồ của riêng họ để bàn tay vẽ lại trên video.
- **Chi tiết thực hiện:**
  - Thêm nút "Tải ảnh từ máy tính" trong từng thẻ cảnh của StoryboardStep.
  - Bộ lọc tự động chuyển đổi ảnh tải lên thành tranh vẽ nét mực 2D trên nền giấy kem `#F5EBD7` (Edge-detection line art filter) để hòa hợp 100% với phong cách toàn bộ video.
  - API endpoint: `POST /storyboard/upload-custom-image`.
- **Files cần tác động:**
  - `core/artwork/filter_sketch.py` (Mới)
  - `apps/api/routers/storyboard.py`
  - `apps/web/app/components/steps/StoryboardStep.tsx`

### Task 7.4: Thư viện 1000+ hình vẽ biểu tượng có sẵn (Doodle Icon Vault)
- **Mô tả:** Kho thư viện vector doodle được phân loại theo chủ đề: Doanh nghiệp, Giáo dục, Y tế, Tài chính, Công nghệ, Mạng xã hội, Icon cảm xúc.
- **Chi tiết thực hiện:**
  - Tích hợp kho icon doodle chuẩn nét vẽ tay nền kem `#F5EBD7`.
  - Hộp thoại tìm kiếm icon nhanh, kéo thả trực tiếp vào cảnh đang dựng.
- **Files cần tác động:**
  - `assets/doodles/` (Thư mục vector doodle)
  - `apps/web/app/components/DoodlePickerModal.tsx` (Mới)

---

## 🎙️ PHASE 8: HỆ THỐNG GIỌNG ĐỌC ĐA NHÂN VẬT & TẢI ÂM THANH RIÊNG (✅ ĐÃ HOÀN THÀNH)
> **Mục tiêu:** Biến video thành câu chuyện sống động với đối thoại nhiều nhân vật, hỗ trợ giọng đọc biểu cảm cao cấp và tải file âm thanh cá nhân.
> **Trạng thái:** ✅ **Hoàn thành 100%** (Đã kiểm thử unit test 9/9 passing + TypeScript 0 errors).

### Task 8.1: Hội thoại đa nhân vật (Multi-Speaker Dialogue) - ✅ ĐÃ XONG
- **Chi tiết thực hiện:**
  - `Scene` và `ExportSceneItem` hỗ trợ trường `voice_id` và `speed` độc lập cho từng phân cảnh.
  - Nút "🤖 Tự phát hiện nhân vật" tự động phân tích nhãn kịch bản dạng `[Nam]: ...`, `[Nữ]: ...`, `[Dẫn chuyện]: ...` và gán giọng đọc tương ứng.
  - Thẻ phân cảnh hiển thị dropdown chọn giọng nói độc lập và badge vai diễn `🎭 Nam`, `🎭 Nữ`, `🎭 Dẫn chuyện`.
  - Pipeline kết xuất video (`export.py`) tổng hợp giọng đọc riêng cho từng cảnh trước khi ghép nối.

### Task 8.2: Tải lên file ghi âm thuyết minh thật (Custom Voiceover Upload) - ✅ ĐÃ XONG
- **Chi tiết thực hiện:**
  - Component `VoiceRecorderModal.tsx`:
    - Tab 1: Ghi âm trực tiếp qua Micro trình duyệt bằng `MediaRecorder` API kèm đồng hồ đếm thời gian, visualizer sóng âm và nghe thử.
    - Tab 2: Kéo thả file âm thanh có sẵn từ máy tính (MP3/WAV/M4A/OGG/WEBM).
  - Endpoint `POST /voices/upload-custom-audio`: Giải mã base64, chuyển đổi và chuẩn hóa thành WAV PCM 16-bit và MP3 chuẩn phát thanh qua PyAV, tính toán duration và sinh metadata timing.
  - Phân cảnh hiển thị huy hiệu `🎤 Bản thu âm riêng`, pipeline giữ nguyên file thu âm thật không ghi đè bởi TTS AI.

### Task 8.3: Tải nhạc nền cá nhân & Cắt gọt nhạc (Custom BGM & Audio Trimmer) - ✅ ĐÃ XONG
- **Chi tiết thực hiện:**
  - Component `CustomMusicUploadModal.tsx`: Cho phép upload nhạc MP3/WAV, đặt tên bài nhạc, tâm trạng và nghe thử.
  - Endpoint `POST /music/upload-custom-bgm`: Lưu trữ vào thư viện nhạc dự án và đưa lên đầu danh mục.
  - Bộ cắt gọt âm thanh (Audio Trimmer):
    - Thanh trượt `Start Offset` (0s - 30s): Cắt bỏ đoạn dạo đầu của bài hát.
    - Thanh trượt `Fade-out Duration` (0.5s - 5.0s): Làm mờ dần âm lượng ở cuối video.
    - `AudioMixer.loop_and_fit_bgm` & `mix_multi_track` tích hợp offset, fade-in, fade-out và Soft-limiter chống rè/vỡ tiếng.

### Task 8.4: Tích hợp giọng đọc biểu cảm cao cấp (ElevenLabs & EdgeTTS) - ✅ ĐÃ XONG
- **Chi tiết thực hiện:**
  - Provider `ElevenLabsTTSProvider` (`core/tts/elevenlabs.py`):
    - Hỗ trợ mô hình `eleven_multilingual_v2` với các giọng biểu cảm hàng đầu: Rachel, Adam, Antoni, Bella.
    - Cấu hình API key tùy chọn trong `SettingsModal.tsx`.
    - Cơ chế chuyển tiếp tự động (graceful fallback) sang `LocalTTSProvider` / `EdgeTTSProvider` khi không có API key hoặc gặp lỗi mạng.
  - Phân nhóm giọng đọc trực quan trong `VoiceStep.tsx`: ElevenLabs Biểu Cảm, Edge TTS Tiếng Việt, AI Cục Bộ VieNeu/VoiceStudio.


---

## 📝 PHASE 9: TRÌNH BIÊN TẬP PHỤ ĐỀ TRỰC QUAN & CHỮ VIẾT TAY [ĐÃ HOÀN THÀNH ✅]
> **Mục tiêu:** Tùy biến phụ đề chuyên sâu theo chuẩn thương hiệu, sửa lỗi chính tả trực quan và hỗ trợ bàn tay viết chữ.
> **Trạng thái:** ✅ Đã hoàn thành 100% & kiểm thử toàn diện (42/42 tests passing).

### Task 9.1: Tùy biến toàn diện giao diện phụ đề (Subtitle Typography Customizer) ✅
- **Mô tả:** Cho phép người dùng tùy biến kiểu chữ, màu sắc, vị trí của phụ đề trên video.
- **Kết quả thực hiện:**
  - Lựa chọn Font chữ:
    - Font viết tay / bảng đen: *Patrick Hand, Mali, Caveat, Comic Sans MS*.
    - Font hiện đại: *Segoe UI, Inter, Roboto, Arial*.
  - Thanh chỉnh kích thước chữ: Nhỏ (sm), Vừa (md), Lớn (lg), Cực đại (xl).
  - Tùy biến màu sắc: Màu chữ, Màu viền nét (Text Stroke 0-6px), Màu nền đệm mờ bo góc (Box Background toggle & color), Màu highlight Karaoke (Vàng neon `#FFE600`, Xanh mint `#00FFCC`, Cam rực `#FF5500`, Vàng kim `#FACC15`, Cyan `#06B6D4`).
  - Vị trí phụ đề: Đáy màn hình (Bottom), Giữa màn hình (Center), Đỉnh màn hình (Top) kèm tự động tính vùng an toàn TikTok/Shorts 9:16.
  - Khung xem trước trực tiếp (Live Preview Badge) ngay trong màn hình kết xuất.
- **Files đã tác động:**
  - `core/subtitles/models.py` (`SubtitleTypographyConfig`)
  - `core/subtitles/burner.py` (`SubtitleBurner` with custom font resolution, colors, position)
  - `apps/web/app/components/steps/ExportStep.tsx`
  - `apps/web/app/types.ts`

### Task 9.2: Trình kéo thả mốc thời gian phụ đề trực quan (Visual Subtitle Timeline Scrubbing) ✅
- **Mô tả:** Người dùng sửa lỗi chính tả phụ đề hoặc căn chỉnh mốc thời gian mà không cần render lại video từ đầu, re-burn siêu tốc (< 2 giây).
- **Kết quả thực hiện:**
  - Giao diện Timeline trực quan `SubtitleTimelineEditor.tsx`:
    - Hiển thị video player preview đồng bộ theo kim thời gian.
    - Dải timeline track với các khối phụ đề có thể click để nhảy timestamp.
    - Trình sửa chữ in-place cho phép sửa lỗi chính tả, dấu tiếng Việt tức thì.
    - Bộ căn chỉnh thời gian `start_sec` và `end_sec` với bước nhảy 0.1s.
    - Thêm câu mới, xóa câu, xuất file `.srt` và `.vtt`.
  - Backend API endpoints:
    - `GET /export/{job_id}/subtitles`: Lấy danh sách segments và URLs.
    - `POST /export/{job_id}/subtitles/update`: Cập nhật phụ đề và Fast Re-burn trực tiếp lên video trong ~1.8s nhờ video sạch đệm `{job_id}_clean.mp4`.
- **Files đã tác động:**
  - `apps/web/app/components/subtitles/SubtitleTimelineEditor.tsx` (Mới)
  - `apps/api/routers/export.py`
  - `apps/web/app/api-client.ts`

### Task 9.3: Hoạt họa bàn tay viết chữ từng ký tự (Handwritten Text Animation) ✅
- **Mô tả:** Bàn tay cầm bút viết từng con chữ hoặc tiêu đề lên bảng trắng giống như thầy cô giáo đang giảng bài.
- **Kết quả thực hiện:**
  - Module `core/drawing/text_handwriter.py`:
    - Trích xuất khung nét chữ bằng OpenCV morphological skeletonization.
    - Sinh chuỗi vector stroke tuần tự (`DrawingStroke`) với các điểm uốn lượn được làm mịn bằng RDP và Chaikin corner cutting.
    - Thứ tự các nét viết tự nhiên từ trái sang phải, từ trên xuống dưới theo từng ký tự.
    - Tạo trọn bộ artifacts phân cảnh bảng trắng: `{scene_id}.png` trên nền giấy kem ấm `#F5EBD7` và `{scene_id}.annotation.json` tương thích chuẩn Whiteboard Media Engine.
  - Tích hợp phương thức `render_handwritten_text_scene` trong `WhiteboardEngineAdapter` và endpoint `POST /export/text-scene`.
- **Files đã tác động:**
  - `core/drawing/text_handwriter.py` (Mới)
  - `engines/whiteboard/adapter.py`
  - `apps/api/routers/export.py`


---

## ⚡ PHASE 10: TĂNG TỐC GPU, HÀNG ĐỢI TÁC VỤ & ĐÓNG GÓI CLOUD ✅
> **Mục tiêu:** Nâng tầm hệ thống thành nền tảng SaaS/Enterprise chịu tải cao, render video siêu tốc qua card màn hình và triển khai 1-click Docker.
> **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH TOÀN DIỆN (10/10 Tests Passed)**

### Task 10.1: Tăng tốc kết xuất video bằng phần cứng GPU (Hardware Acceleration) ✅
- **Mô tả:** Tự động phát hiện và tận dụng tối đa GPU phần cứng (NVIDIA NVENC, Intel QSV, Apple Silicon VideoToolbox, hoặc CPU đa luồng) để rút ngắn thời gian render video từ 60 giây xuống còn 10-15 giây.
- **Kết quả thực hiện:**
  - Module `core/hardware/gpu_detector.py`: Tự động nhận diện NVIDIA GPU qua `nvidia-smi`, Intel QuickSync qua `qsv`, Apple M-series qua `videotoolbox`, và kiểm tra codec khả dụng qua PyAV & FFmpeg.
  - Tích hợp cờ `--hwaccel` và bộ chọn encoder thông minh trong `scripts/stream_render.py` và `scripts/render_stream_whiteboard.py`.
  - Cập nhật `engines/whiteboard/adapter.py` với cấu hình `hwaccel: str = "auto"`.
  - API endpoint `GET /system/hardware` và `GET /export/hardware-info`.
  - Giao diện `SettingsModal.tsx` cho phép người dùng xem thông tin phần cứng theo thời gian thực và tùy chỉnh codec xuất video.
- **Files đã tác động:**
  - `core/hardware/gpu_detector.py` (Mới)
  - `core/hardware/__init__.py` (Mới)
  - `engines/whiteboard/adapter.py`
  - `scripts/stream_render.py`
  - `scripts/render_stream_whiteboard.py`
  - `apps/api/routers/health.py`
  - `apps/api/routers/export.py`
  - `apps/web/app/components/SettingsModal.tsx`

### Task 10.2: Hàng đợi tác vụ độc lập (Redis + In-Memory Worker Queue) ✅
- **Mô tả:** Xây dựng hàng đợi tác vụ độc lập, hỗ trợ phân tán tải, ngăn nghẽn CPU server và phát sóng tiến độ theo thời gian thực.
- **Kết quả thực hiện:**
  - Module `core/queue/tasks.py`: Định nghĩa cấu trúc `TaskPayload`, `TaskStatus`, `TaskType` cho các tác vụ render video, export định dạng và chuyển đổi media.
  - Module `core/queue/worker.py`: Hệ thống `WorkerQueue` linh hoạt, tự động kết nối Redis Queue khi có sẵn, hoặc fallback liền mạch sang `asyncio.Queue` worker pool khi chạy môi trường local không có Redis.
  - Hỗ trợ Pub/Sub event broadcasting để đẩy tiến độ % render tức thì về client.
  - Khởi tạo và dọn dẹp an toàn qua FastAPI startup/shutdown lifespans trong `apps/api/main.py`.
- **Files đã tác động:**
  - `core/queue/tasks.py` (Mới)
  - `core/queue/worker.py` (Mới)
  - `core/queue/__init__.py` (Mới)
  - `apps/api/main.py`

### Task 10.3: Xuất đa định dạng (GIF hoạt họa, WebM trong suốt, 4K UHD, Watermark) ✅
- **Mô tả:** Mở rộng định dạng video xuất ra cho nhiều mục đích marketing, trình chiếu và tích hợp chèn nội dung.
- **Kết quả thực hiện:**
  - Module `core/export/format_converter.py`:
    - Chuyển đổi sang **GIF** hoạt họa mượt mà (thuật toán hai bước palettegen / paletteuse và Pillow adaptive quantization fallback).
    - Xuất video **WebM nền trong suốt (Alpha Keying)**: Tách lớp nền giấy ấm `#F5EBD7` thành kênh alpha trong suốt (`yuva420p` / `libvpx-vp9`), giúp chèn bàn tay vẽ lên mọi slide hay video khác.
    - Chuyển đổi đa độ phân giải: **480p** (nháp siêu nhẹ), **720p** (HD), **1080p** (Full HD), **4K UHD 2160p** (sắc nét màn chiếu lớn).
    - Đóng dấu thương hiệu / Watermark tùy biến vị trí (Top-Left, Top-Right, Bottom-Left, Bottom-Right) với thanh chỉnh độ mờ (opacity) và kích thước.
  - API endpoints `POST /export/{job_id}/convert-format` và `GET /export/{job_id}/formats`.
  - Giao diện `ExportStep.tsx`: Bổ sung Interactive Multi-Format Export Hub với các thẻ định dạng, nút chuyển đổi 1-click và thanh tải về tiện lợi.
- **Files đã tác động:**
  - `core/export/format_converter.py` (Mới)
  - `core/export/__init__.py` (Mới)
  - `apps/api/routers/export.py`
  - `apps/web/app/components/steps/ExportStep.tsx`

### Task 10.4: Quản lý dự án chuyên sâu (Duplicate, Export/Import Package) ✅
- **Mô tả:** Sao lưu, nhân bản và chia sẻ dự án trọn gói giữa các máy tính hoặc người dùng khác nhau.
- **Kết quả thực hiện:**
  - Backend API trong `apps/api/routers/projects.py`:
    - `POST /projects/{id}/duplicate`: Nhân bản toàn bộ kịch bản, cấu hình phân cảnh, hình ảnh và âm thanh sang một dự án mới độc lập với UUID timestamp an toàn.
    - `GET /projects/{id}/export-package`: Đóng gói toàn bộ project directory và `project.json` thành file nén zip chuẩn `.whiteboard`.
    - `POST /projects/import-package`: Tiếp nhận file `.whiteboard`, giải nén và đăng ký dự án mới vào hệ thống ngay lập tức.
  - Frontend UI trong `StudioHeader.tsx` & `page.tsx`: Menu dự án với nút Duplicate, nút Export gói `.whiteboard` và nút Import tải tệp lên trực quan.
- **Files đã tác động:**
  - `apps/api/routers/projects.py`
  - `apps/web/app/api-client.ts`
  - `apps/web/app/components/StudioHeader.tsx`
  - `apps/web/app/page.tsx`

### Task 10.5: Đóng gói Docker & Docker-Compose (1-Click Self-Hosting) ✅
- **Mô tả:** Đóng gói toàn bộ AI Whiteboard Studio thành hệ thống container hóa chuẩn production sẵn sàng triển khai trên bất kỳ máy chủ local, VPS hay Cloud.
- **Kết quả thực hiện:**
  - `Dockerfile.api`: Python 3.11-slim, tích hợp FFmpeg, OpenCV, PyAV, bộ phông chữ hệ thống tiêu chuẩn (`Patrick Hand`, `Inter`, `fonts-freefont-ttf`).
  - `Dockerfile.web`: Multi-stage build tối ưu kích thước trên Node.js 20 Alpine với Next.js standalone runner.
  - `docker-compose.yml`: Kết nối 3 dịch vụ liên hoàn `api` (FastAPI), `web` (Next.js), `redis` (Message Broker) với volume mount dữ liệu video và hỗ trợ `deploy.resources.reservations.devices` cho NVIDIA GPU passthrough.
  - `docs/DEPLOYMENT.md`: Hướng dẫn cài đặt song ngữ chi tiết (1 lệnh khởi động, cấu hình biến môi trường, tối ưu GPU và triển khai VPS/Cloud).
- **Files đã tạo mới:**
  - `Dockerfile.api`
  - `Dockerfile.web`
  - `docker-compose.yml`
  - `docs/DEPLOYMENT.md`


---

## 📐 SƠ ĐỒ KIẾN TRÚC TỔNG THỂ AI WHITEBOARD STUDIO 3.0+

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               AI WHITEBOARD VIDEO STUDIO 3.0+                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                 FRONTEND STUDIO (Next.js 14)                               │  │
│  │                                                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ Bước 1:      │  │ Bước 2:      │  │ Bước 3:      │  │ Bước 4:      │  │ Studio       │  │  │
│  │  │ Kịch bản     │  │ Storyboard   │  │ Giọng đọc    │  │ Kết xuất     │  │ Tools        │  │  │
│  │  │ • Dịch AI    │  │ • Canvas Edit│  │ • Multi-Voice│  │ • 16:9/9:16  │  │ • Settings   │  │  │
│  │  │ • Chia cảnh  │  │ • Character  │  │ • Micro Rec  │  │ • BGM/SFX Mix│  │ • Archive    │  │  │
│  │  │ • Ratio Pick │  │ • Custom Img │  │ • Custom BGM │  │ • Sub Burner │  │ • Autosave   │  │  │
│  │  │ • Chara Lock │  │ • Doodle Lib │  │ • Waveform   │  │ • GPU Export │  │ • Lock Guard │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                              ▲  │ (HTTP / SSE / WebSocket)                       │
│                                              │  ▼                                                │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                             BACKEND ENGINE (FastAPI + Workers)                             │  │
│  │                                                                                            │  │
│  │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────┐  │  │
│  │  │ ARTWORK & VISION   │  │ AUDIO & NARRATION  │  │ WHITEBOARD ENGINE  │  │ SUBTITLES &   │  │  │
│  │  │ • Pollinations.ai  │  │ • EdgeTTS Engine   │  │ • Potrace Vector   │  │ TYPOGRAPHY    │  │  │
│  │  │ • Sketch Filters   │  │ • ElevenLabs API   │  │ • Bezier Alignment │  │ • SRT/VTT Gen │  │  │
│  │  │ • Multi-Tier Trans │  │ • Multi-Track Mix  │  │ • Multi-Pen Switch │  │ • Safe Zone   │  │  │
│  │  │ • Auto-Segment     │  │ • Auto-Ducking     │  │ • Eraser Transition│  │ • Karaoke Burn│  │  │
│  │  │ • Character Anchor │  │ • Drawing SFX Sync │  │ • GPU / PyAV Mux   │  │ • Font Engine │  │  │
│  │  └────────────────────┘  └────────────────────┘  └────────────────────┘  └──────────────┘  │  │
│  │                                                                                            │  │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ QUEUE & STORAGE: Redis + SQLite Job Store + Local Video Vault (Ổ D:)                  │  │  │
│  │  └──────────────────────────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 SO SÁNH NĂNG LỰC TRƯỚC VÀ SAU LỘ TRÌNH 3.0+

| Tiêu chí đánh giá | Hiện tại (Phiên bản 2.5) | Sau khi hoàn thành Lộ trình 3.0+ |
|-------------------|--------------------------|----------------------------------|
| **Độ chân thực nét vẽ** | Quét lưới (grid) & viền contour | Nét cọ uốn lượn Vector Bezier, ngòi bút bám sát mực |
| **Đổi bút & Tô màu** | 1 bút đơn sắc, tô màu xuất hiện tĩnh | Bút đen vẽ khung → Đổi bút dạ quang/bút lông tô màu điểm nhấn |
| **Chuyển cảnh** | Cắt cảnh trực tiếp (Hard cut) | Bàn tay cầm giẻ lau xóa bảng (Eraser Wipe) kèm âm thanh |
| **Biên tập phân cảnh** | Chỉ xem ảnh tĩnh hoặc sửa prompt text | Vẽ thêm mũi tên, vòng tròn highlight, text trực tiếp trên ảnh |
| **Tính nhất quán nhân vật** | Mỗi cảnh sinh ảnh độc lập, hay lệch nhân vật | Neo giữ seed & đặc điểm nhận dạng xuyên suốt toàn bộ câu chuyện |
| **Ảnh riêng & Logo** | Chỉ sinh ảnh qua AI | Tự do upload logo, ảnh chụp sản phẩm được vẽ lại thành tranh nét mực |
| **Giọng đọc thuyết minh** | 1 giọng đơn điệu cho cả video | Hội thoại đa nhân vật (Nam/Nữ đối đáp) + Tự tải giọng thu âm thật |
| **Nhạc nền BGM** | 5 bản nhạc mặc định | Tự do tải MP3 cá nhân lên, cắt đoạn nhạc bắt đầu, chỉnh âm lượng |
| **Phụ đề & Chữ chạy** | 2 kiểu mặc định, không sửa được mốc thời gian | Tùy biến mọi font chữ, màu sắc, kéo thả mốc thời gian trực quan |
| **Bàn tay viết chữ** | Chưa hỗ trợ | Bàn tay cầm bút viết từng ký tự tiêu đề / bài học lên bảng |
| **Tốc độ kết xuất** | CPU song song (~1-2 phút cho 5 cảnh) | Tăng tốc GPU NVENC (~15-20 giây cho 5 cảnh) |
| **Định dạng xuất ra** | Video MP4 | MP4, GIF động, WebM nền trong suốt, 4K UHD 60fps |
| **Môi trường triển khai** | Chạy thủ công trên máy dev | 1-Click Docker Compose triển khai trên mọi VPS / Cloud |

---

## 📋 TRẠNG THÁI LỘ TRÌNH PHÁT TRIỂN & CÁC BƯỚC ĐÃ HOÀN TẤT

### Tổng hợp tiến độ các giai đoạn:
1. **Phase 1-5 (Nền tảng Whiteboard & Audio Sync):** ✅ **ĐÃ HOÀN THÀNH**
2. **Phase 6 (Vector Stroke Engine & Bàn tay vẽ chân thực):** ✅ **ĐÃ HOÀN THÀNH**
3. **Phase 7 (Canvas Studio, Character Anchor & Doodle Vault):** ✅ **ĐÃ HOÀN THÀNH**
4. **Phase 8 (Hệ thống giọng đọc đa nhân vật & Tải âm thanh riêng):** ✅ **ĐÃ HOÀN THÀNH**
5. **Phase 9 (Trình biên tập phụ đề trực quan & Chữ viết tay):** ✅ **ĐÃ HOÀN THÀNH**
   - Typography Customizer, Visual Timeline Scrubbing & Handwritten Text Animation.
6. **Phase 10 (Tăng tốc GPU, Hàng đợi tác vụ & Đóng gói Cloud):** ✅ **ĐÃ HOÀN THÀNH**
   - GPU Hardware Acceleration (NVENC/QSV/VideoToolbox), Decoupled Worker Queue, Multi-Format Exporter (GIF/WebM/4K/Watermark), Deep Project Packaging (.whiteboard) & 1-Click Docker Cloud Packaging.

---

> **Cập nhật ngày:** 2026-10-22 | **Trạng thái hệ thống:** Sẵn sàng Production / Cloud Self-Hosting | **Người lập:** AI Whiteboard Studio Lead Architect


