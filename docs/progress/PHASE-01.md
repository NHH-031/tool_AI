# Phase 01 — Repository Analysis & Baseline

## Objective
Phân tích toàn diện repository nền tảng `srt-whiteboard-animation`, thiết lập môi trường thực thi, chạy kiểm thử pipeline đầy đủ từ SRT đến MP4, xác thực media và hình ảnh trực quan, ghi nhận lỗi phát hiện và lập tài liệu kiến trúc baseline cho dự án **AI Whiteboard Video Production Studio**.

---

## Repository inspected
- **URL**: `https://github.com/geeklee/srt-whiteboard-animation`
- **Commit SHA**: `33a25b508f7db010313f8902d29aaeeaa92a149a` (HEAD tại nhánh main)
- **Cấu trúc repo**:
  - `README.md`, `SKILL.md`, `LICENSE`
  - `agents/openai.yaml`
  - `assets/`: `drawing-hand.png`, `preview.html`
  - `scripts/`: `prepare_env.py`, `parse_srt.py`, `render_annotation_preview.py`, `render_stream_whiteboard.py`, `stream_render.py`, `merge_scenes.py`
  - `examples/`: hình ảnh mẫu, file annotation mẫu và video MP4/GIF tham chiếu.

---

## Environment
- **Hệ điều hành**: Windows 11 Pro (win32, x64)
- **Shell**: PowerShell 7 / Windows PowerShell
- **Python**: Python 3.13.2 (`C:\Users\ACER\AppData\Local\Programs\Python\Python313\python.exe`)
- **Virtual Environment**: `d:\Tool\.venv` (được tạo tự động qua `scripts/prepare_env.py`)
- **Python Interpreter**: `d:\Tool\.venv\Scripts\python.exe`
- **Installed Packages**:
  - `opencv-python`: 4.13.0.92
  - `numpy`: 2.2.6
  - `av` (PyAV): 16.1.1
  - `Pillow`: 12.1.1
- **Công cụ Media ngoài**:
  - `ffmpeg`: Không có trong system PATH.
  - `ffprobe`: Không có trong system PATH.
  - Hệ thống sử dụng engine giải mã/mã hóa video nội bộ thông qua thư viện `av` (PyAV với libavcodec/libavformat tích hợp sẵn).

---

## Commands executed
1. **Kiểm tra và chuẩn bị môi trường**:
   ```powershell
   # Kiểm tra môi trường ban đầu
   $env:PYTHONUTF8="1"; python scripts/prepare_env.py --check

   # Thiết lập virtualenv và cài đặt dependencies
   $env:PYTHONUTF8="1"; python scripts/prepare_env.py

   # Xác minh môi trường đã hoàn tất
   $env:PYTHONUTF8="1"; python scripts/prepare_env.py --check
   ```
2. **Kiểm thử bộ phân tích phụ đề SRT**:
   ```powershell
   $env:PYTHONUTF8="1"; & "d:\Tool\.venv\Scripts\python.exe" scripts/parse_srt.py examples/sample_story.srt --target-sec 8 --min-sec 5 --max-sec 15
   ```
3. **Kiểm thử kết xuất ảnh phân vùng Bounding Box**:
   ```powershell
   $env:PYTHONUTF8="1"; & "d:\Tool\.venv\Scripts\python.exe" scripts/render_annotation_preview.py examples/scene-01-monkey-mountain-banana.png examples/scene-01-monkey-mountain-banana.annotation.json out/preview/scene-01-preview.png
   ```
4. **Kiểm thử kết xuất video Whiteboard Animation**:
   ```powershell
   $env:PYTHONUTF8="1"; & "d:\Tool\.venv\Scripts\python.exe" scripts/render_stream_whiteboard.py examples/scene-01-monkey-mountain-banana.png examples/scene-01-monkey-mountain-banana.annotation.json out/baseline/scene-01-whiteboard.mp4 assets/drawing-hand.png --ink-path grid --color-fill contour-wipe
   ```
5. **Kiểm thử ghép nối nhiều phân cảnh MP4**:
   ```powershell
   $env:PYTHONUTF8="1"; & "d:\Tool\.venv\Scripts\python.exe" scripts/merge_scenes.py --inputs out/baseline/scene-01-whiteboard.mp4 out/baseline/scene-01-whiteboard.mp4 --output out/baseline/merged-test.mp4
   ```
6. **Kiểm tra thông số kỹ thuật media và giải mã khung hình**:
   ```powershell
   & "d:\Tool\.venv\Scripts\python.exe" -c "<PyAV verification probe script>"
   ```
7. **Trích xuất các khung hình trọng yếu phục vụ visual audit**:
   ```powershell
   & "d:\Tool\.venv\Scripts\python.exe" -c "<Frame extraction script>"
   ```

---

## Existing pipeline
Quy trình hiện tại bao gồm:
1. `parse_srt.py`: Parse timecode, gom nhóm câu thoại thành scene 25-35s.
2. `preview.html`: Ứng dụng client-side trực quan cho phép load cặp `.png` + `.annotation.json`, chỉnh sửa tọa độ `region`, `durationMs`, sắp xếp thứ tự và lưu file.
3. `render_annotation_preview.py`: Vẽ overlay các bounding box, nhãn và hướng vẽ lên ảnh tĩnh.
4. `render_stream_whiteboard.py`:
   - Phân tích ảnh nhị phân bằng Gaussian Adaptive Threshold.
   - Quét nét mực theo Grid hoặc Skeleton.
   - Áp dụng `_allowed_mask` để bảo vệ các vùng chưa vẽ và `protectedRegions`.
   - Pha nét mực `ink` (tỷ lệ 2/3 thời gian vùng) và pha lên màu `color` (tỷ lệ 1/3 thời gian).
   - Ghép bàn tay vẽ `TipOverlay` theo mốc neo đầu bút (0, 0).
   - Giữ lại hình ảnh hoàn thiện tối thiểu 0.5s ở pha `gaze`.
   - Kết xuất file raw `mp4v` rồi transcode sang H.264 qua `PyAV` hoặc `ffmpeg`.
5. `merge_scenes.py`: Ghép nối các scene theo danh sách thứ tự.

---

## Tests executed
- [x] **Environment Detection Test**: Phát hiện và xử lý lỗi thiếu biến môi trường UTF-8 trên Windows console.
- [x] **Venv Bootstrap Test**: Tạo lập `.venv` và cài đặt đầy đủ các package `opencv-python`, `numpy`, `av`, `Pillow`.
- [x] **SRT Parsing & Scene Grouping Test**: Đọc chính xác file SRT mẫu 3 cues, tính toán milliseconds chuẩn mực và gom nhóm thành scene 7.8s.
- [x] **Annotation Preview Image Test**: Tạo ảnh `out/preview/scene-01-preview.png` (2,345,832 bytes) hiển thị đầy đủ 3 vùng phân đoạn với màu sắc, số thứ tự và mũi tên điều hướng.
- [x] **Whiteboard MP4 Render Test**: Kết xuất thành công file `out/baseline/scene-01-whiteboard.mp4` (1,968,986 bytes) với đầy đủ 516 khung hình.
- [x] **Multi-Scene Merge Test**: Nối thành công 2 video thành `out/baseline/merged-test.mp4` (4,627,128 bytes) với 1032 khung hình sau khi áp dụng bản vá timebase/PTS.

---

## Media validation
Dữ liệu kiểm tra thực tế bằng thư viện `av` (PyAV):

### 1. File `out/baseline/scene-01-whiteboard.mp4`
- **File tồn tại**: Có (`True`)
- **Kích thước file**: 1,968,986 bytes (~1.88 MB)
- **Khả năng đọc/giải mã**: Đọc và decode toàn bộ 516 khung hình thành công
- **Thời lượng**: 8.60 giây (khớp tuyệt đối với `sceneDurationMs: 8600`)
- **Độ phân giải**: 1080 x 600
- **Tốc độ khung hình**: 60.0 FPS
- **Video Codec**: H.264 / AVC (High Profile, YUV420p)
- **Container Format**: `mov,mp4,m4a,3gp,3g2,mj2`
- **Audio Stream**: Không có (Engine thuần tạo hoạt họa visual)
- **Số khung hình lý thuyết**: 516
- **Số khung hình giải mã thực tế**: 516

### 2. File `out/baseline/merged-test.mp4`
- **File tồn tại**: Có (`True`)
- **Kích thước file**: 4,627,128 bytes (~4.41 MB)
- **Khả năng đọc/giải mã**: Đọc và decode toàn bộ 1032 khung hình thành công
- **Thời lượng**: 17.20 giây (gấp đôi 8.6s)
- **Độ phân giải**: 1080 x 600
- **Tốc độ khung hình**: 60.0 FPS
- **Video Codec**: H.264 / AVC (High Profile, YUV420p)
- **Số khung hình giải mã thực tế**: 1032

---

## Visual validation
Đã trích xuất và kiểm tra trực tiếp các khung hình tại các mốc thời gian đại diện:
- **Khung hình 0 (0.00s)**: Toàn bộ nền canvas là màu giấy ngà ấm sạch tinh (`#F6F1E3`), hoàn toàn không có bất kỳ nét vẽ nào bị lộ sớm. Tính bất biến che chắn đạt 100%.
- **Khung hình 60 (1.00s)**: Bàn tay cầm bút đang vẽ đối tượng 1 (núi giả và khỉ nhỏ). Hai vùng bên phải hoàn toàn trống. Nét vẽ mượt mà, đầu ngòi bút chạm sát đường nét đang hình thành.
- **Khung hình 210 (3.50s)**: Vùng 1 đã hoàn thiện nét và lên màu; bàn tay chuyển sang vẽ vùng 2 (chú khỉ lớn lao vào cướp chuối). Vùng 3 (trẻ em đứng xem) vẫn giữ nguyên trạng thái ẩn hoàn toàn.
- **Khung hình 360 (6.00s)**: Vùng 1 và vùng 2 đã hoàn tất; bàn tay đang vẽ các em thiếu nhi ở góc phải. Nét vẽ đi tuần tự, không bị nhảy giật.
- **Khung hình 515 (8.58s - Frame cuối)**: Bàn tay vẽ đã rời khỏi khung hình. Toàn bộ tác phẩm được hiển thị đầy đủ, sắc nét, màu sắc hài hòa. Thời gian chiêm ngưỡng (`gaze`) diễn ra tĩnh trong đúng 500ms cuối.
- **Ảnh preview (`out/preview/scene-01-preview.png`)**: 3 hộp bounding box phân bố chính xác theo đúng tọa độ trong JSON: Xanh dương (#1), Cam (#2), Xanh lá (#3), chữ số và nhãn tiếng Trung hiển thị rõ nét.

---

## Files created/changed

### Files tạo mới:
1. `examples/sample_story.srt`: File phụ đề 3 câu thoại chuẩn để kiểm thử parser và liên kết kịch bản.
2. `docs/ARCHITECTURE_BASELINE.md`: Tài liệu phân tích kiến trúc baseline chi tiết gồm 8 phần theo quy chuẩn.
3. `docs/progress/PHASE-01.md`: (File này) Tài liệu theo dõi tiến độ Phase 01.
4. `out/preview/scene-01-preview.png`: Ảnh kiểm tra bounding box được sinh ra trong kiểm thử.
5. `out/baseline/scene-01-whiteboard.mp4`: Video whiteboard kết xuất baseline hoàn chỉnh.
6. `out/baseline/merged-test.mp4`: Video ghép nối từ baseline render.
7. `out/baseline/frames/frame_*.png`: Các khung hình trích xuất phục vụ kiểm định thị giác.

### Files chỉnh sửa:
1. `scripts/merge_scenes.py`:
   - **Lý do sửa**: Hàm fallback `_pyav_concat()` gặp lỗi `av.error.ArgumentError: Invalid argument (errno 22)` khi hệ thống không cài sẵn `ffmpeg` toàn cục. Nguyên nhân do PyAV nhận các frame từ clip thứ 2 có PTS bị reset về 0 dẫn đến các packet sinh ra không đơn điệu tăng dần.
   - **Nội dung sửa**: Bổ sung `from fractions import Fraction`, thiết lập `ostream.time_base = Fraction(rate.denominator, rate.numerator)` và gán `frame.pts` tăng dần liên tục qua các clip đầu vào.

---

## Problems discovered
1. **Lỗi `UnicodeEncodeError` trên Windows PowerShell**:
   - `scripts/prepare_env.py` in các chuỗi ký tự tiếng Trung (`[err] 虚拟环境尚未建立`). Khi chạy trên Windows với codepage 1252 mặc định, Python 3.13 văng exception `UnicodeEncodeError`.
   - *Cách khắc phục*: Thiết lập biến môi trường `$env:PYTHONUTF8="1"` hoặc thêm đối số `-X utf8` khi gọi Python.
2. **Lỗi PTS trong `_pyav_concat` (`scripts/merge_scenes.py`)**:
   - Như đã phân tích, PyAV không thể mux khi nối nhiều file nếu không reset và cộng dồn timestamp `pts` liên tục.
   - *Cách khắc phục*: Đã sửa contiguos PTS assignment trong `merge_scenes.py`.
3. **Hardcode font chữ Windows trong `render_annotation_preview.py`**:
   - Dòng 12: `font_file = "C:/Windows/Fonts/msyh.ttc"` khiến script không thể chạy độc lập trên môi trường Linux/macOS. Cần đóng gói font cục bộ trong assets ở các phase sau.
4. **Không có kênh Audio**:
   - Video hoàn toàn không có âm thanh. Toàn bộ pipeline hiện tại chưa có khả năng nhập/mux audio.

---

## Known limitations
1. **Chưa có Voiceover / Background Music**: Chỉ tạo video visual.
2. **Tốc độ render CPU**: Chưa có hỗ trợ tăng tốc GPU phần cứng cho các thuật toán hình thái học (morphological operations) của OpenCV và Zhang-Suen thinning.
3. **Bản quyền hình ảnh bàn tay**: Bàn tay mẫu `drawing-hand.png` có in chữ "江哥是老登啊", cần hỗ trợ tùy biến hoặc thay thế bàn tay trung tính cho sản phẩm thương mại.
4. **Giao diện hiện tại là công cụ cục bộ**: Cần người dùng tương tác thủ công trên `preview.html` để nắn chỉnh vùng.

---

## Evidence
- Video đơn cảnh: `out/baseline/scene-01-whiteboard.mp4` (1,968,986 bytes, 516 frames, duration 8.60s, H.264 High 1080x600, 60.0 fps).
- Video ghép nối: `out/baseline/merged-test.mp4` (4,627,128 bytes, 1032 frames, duration 17.20s, H.264 High 1080x600, 60.0 fps).
- Ảnh bounding box: `out/preview/scene-01-preview.png` (2,345,832 bytes, 1672x941).
- Các khung hình trích xuất đối soát: `out/baseline/frames/frame_0000_0.00s.png`, `frame_0060_1.00s.png`, `frame_0210_3.50s.png`, `frame_0360_6.00s.png`, `frame_0515_8.58s.png`.

---

## Phase status
**PASS**
Mọi mục tiêu của Phase 01 đã được hoàn thành 100%, có bằng chứng kỹ thuật và media cụ thể.
