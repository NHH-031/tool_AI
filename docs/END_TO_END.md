# End-to-End Whiteboard Video Production Pipeline

Tài liệu thiết kế và vận hành pipeline sản xuất video bảng trắng tự động từ ý tưởng đến video MP4 hoàn chỉnh.

---

## 1. Tổng Quan Kiến Trúc Pipeline

Pipeline kết nối toàn bộ hệ thống từ xử lý ngôn ngữ tự nhiên (AI Agents) đến động cơ kết xuất video streaming (Media Engine) và module kiểm định chất lượng phát sóng (Media & Visual QA):

```text
[ Idea / User Prompt ]
          │
          ▼
   ScriptAgent
          │ (title, full_script, segments)
          ├───► MockTTSProvider / TTS Engine ───► Narration Audio (.wav) + Word Timings
          │
          ▼
 VisualPlannerAgent
          │ (Visual Scene Graph: Entities, Relations, Layout)
          ▼
    AssetSystem (Local / Generated SVG Assets)
          │
          ▼
DrawingStrokeEngine (Hierarchical Strokes & Hand Paths)
          │
          ▼
DrawingTimelineSynchronizer (Semantic Word-Aligned Events)
          │
          ▼
WhiteboardEngineAdapter
  ├── 1. Canvas Composition (.png)
  └── 2. Engine Annotation Schema (.annotation.json)
          │
          ▼
Whiteboard Media Engine (render_stream_whiteboard.py)
          │ (Stream Render Video: scene_raw.mp4)
          ▼
Audio-Video Muxer (PyAV H.264 + AAC Mono)
          │ (Final Broadcast MP4)
          ▼
Media & Visual QA (MediaProbe)
          │
          ▼
   [ Certified MP4 ]
```

---

## 2. Whiteboard Media Engine Nền Tảng

Dự án sử dụng repository nền tảng `geeklee/srt-whiteboard-animation` làm media engine kết xuất đồ họa bảng trắng:
- **Nguyên tắc**: Sử dụng kiến trúc Adapter (`WhiteboardEngineAdapter`) để giao tiếp với engine thông qua subprocess và file trao đổi chuẩn (`.annotation.json` và `.png`), **tuyệt đối không rewrite engine**.
- **Sửa lỗi phát hiện (Engine Bugfix)**:
  - Trong `scripts/render_stream_whiteboard.py` tại dòng 405: hàm `_lay_ink` chỉ nhận 5 đối số nhưng engine upstream truyền 6 đối số (`(writer, ink_frames, [], set(), None, allowed)`). Lỗi này khiến render bị crash `TypeError` khi xử lý các region không chứa ink. Đã được khắc phục triệt để.
  - Hỗ trợ biến môi trường UTF-8 (`PYTHONUTF8=1`, `encoding="utf-8"`) để tương thích hoàn toàn trên nền tảng Windows.

---

## 3. Data Model Adapter

Lớp Adapter chuyển đổi cấu trúc dữ liệu AI Studio sang định dạng của whiteboard engine:

| AI Studio Data Model | Engine Format (`.annotation.json`) | Mục đích |
| :--- | :--- | :--- |
| `CanvasConfig` (width, height, bg) | `CanvasSchema` (`width`, `height`, `background_color`) | Thiết lập kích thước khung hình và nền trắng sạch |
| `VisualEntity` + `Asset` | `ElementSchema` (`id`, `bbox`, `order`, `color`) | Vị trí bounding box và thứ tự xuất hiện của thực thể |
| `DrawingStroke` + `handPath` | `RegionSchema` + `HandPathSchema` | Vùng vẽ chi tiết và lộ trình tọa độ di chuyển đầu bút |
| `DrawingTimelineEvent` | `RevealSchema` (`start_ms`, `end_ms`, `mode`) | Lập lịch thời gian vẽ cho từng vùng theo mốc âm thanh |
| Trạng thái chưa vẽ | `protectedRegions` | Che chắn các thực thể chưa đến lượt vẽ (chống early reveal) |

---

## 4. Ghép Kênh Audio - Video (Muxing)

- **Mã hóa âm thanh**: Sử dụng PyAV (FFmpeg C bindings) để chuyển mã narration audio (`PCM WAV 24kHz`) sang chuẩn `AAC Mono 24kHz`.
- **Mã hóa hình ảnh**: Chuyển tiếp stream `H.264` (YUV420p) từ engine kết xuất với tốc độ khung hình chuẩn (30 fps).
- **Đồng bộ thời lượng**: Tính toán và căn chỉnh thời lượng video theo âm thanh (độ lệch $\Delta t < 0.2\text{s}$), đảm bảo không lệch tiếng hay cụt hình.

---

## 5. Hệ Thống Kiểm Định Chất Lượng (Media & Visual QA)

Lớp `MediaProbe` ([`core/qa/media_probe.py`](file:///d:/Tool/core/qa/media_probe.py)) tự động phân tích và xác thực toàn diện:

1. **Media QA (Kỹ thuật container & stream)**:
   - File tồn tại và dung lượng $> 0$.
   - Container MP4 hợp lệ, phát lại bình thường.
   - Luồng video: Chuẩn H.264, đúng kích thước (ví dụ 1080p), tốc độ khung hình và số lượng frames chính xác.
   - Luồng audio: Chuẩn AAC, sample rate hợp lệ.
   - Độ lệch thời lượng Audio/Video trong ngưỡng cho phép ($< 0.5\text{s}$).
   - Không xuất hiện frame lỗi hoặc stream hỏng (`is_corrupted == False`).

2. **Visual Invariants QA (Hình ảnh bảng trắng)**:
   - **Background White**: Khung hình nền trắng sạch.
   - **No Early Reveal**: Khung hình đầu tiên ($t = 0$) không bị lộ nét vẽ trước khi bút chạm bảng.
   - **Stroke Completion**: Khung hình cuối cùng ($t = T_{end}$) thể hiện đầy đủ toàn bộ nét vẽ của phân cảnh.

---

## 6. Hướng Dẫn Vận Hành

### Chạy pipeline tự động qua mã Python
```python
from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from engines.whiteboard.adapter import WhiteboardRenderConfig

pipeline = WhiteboardPipeline()
cfg = WhiteboardRenderConfig(
    fps=30,
    cap_long_edge=1080, # Full HD
    ink_path="grid",
    color_fill="contour-wipe"
)

result = await pipeline.run(
    idea="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    output_dir=Path("output/my_render"),
    config=cfg
)

print(f"Status: {result.status}")
print(f"MP4 Path: {result.final_video_path}")
print(f"QA Passed: {result.media_report.visual_qa_pass}")
```

### Chạy CLI Demo Runner
```bash
.venv\Scripts\python scripts/run_e2e_demo.py
```
Video và báo cáo kiểm định sẽ được lưu tại:
- Video kết quả: `output/monkey_banana_e2e/scene_default_final.mp4`
- Báo cáo QA: `output/monkey_banana_e2e/media_qa_report.json`
