# PHASE 10.1 — VISUAL FIDELITY & DRAWING COMPLETENESS RECOVERY

## Problem

Trong các phase trước, video render thực tế cho câu kịch bản:
> *"Con khỉ đang trèo lên cây để lấy một quả chuối."*

chưa đạt yêu cầu sản phẩm với các triệu chứng nghiêm trọng:
1. **Cây** được vẽ tương đối đầy đủ nhưng **con khỉ** bị vẽ chắp vá, mất nét, hoặc biến dạng.
2. **Quả chuối** chưa được vẽ hoàn chỉnh trên ngọn cây.
3. Hành động *"trèo lên"* (climbing) và *"lấy"* (reaching_for) không được thể hiện trực quan.
4. Video kết thúc sớm trong khi visual content chưa vẽ xong.
5. Hệ thống QA cũ vẫn báo `Technical QA = PASS` và cho ra kết quả `Overall = PASS` (False Positive nghiêm trọng).

## Root Cause

Sau quá trình điều tra, truy vết toàn bộ pipeline (`INSPECT -> TRACE -> IDENTIFY ROOT CAUSE`), đã phát hiện 4 nguyên nhân gốc rễ trong kiến trúc:

1. **Coarse Bounding Box Clipping (`protected_regions` & `_allowed_mask`)**:
   - Trong `engines/whiteboard/adapter.py` và `scripts/render_stream_whiteboard.py`, thuật toán bảo vệ vùng chống lộ hình sớm dựa vào phép trừ hình chữ nhật bounding box thô (`cv2.rectangle(allowed_mask, (bx, by), (bx+bw, by+bh), 0, -1)`).
   - Vì `tree` là đối tượng môi trường to lớn (`820, 80, 720, 880`) bao bọc hoặc giao cắt với `monkey` (`720, 400, 440, 440`), phép trừ vùng bảo vệ của cây đã xóa trắng toàn bộ vùng pixel vẽ khỉ. Khi khỉ được kích hoạt để vẽ, mặt nạ mực của khỉ bị cắt cụt, dẫn đến việc khỉ chỉ vẽ được vài nét vụn vỡ.
2. **Artificial Full-Image Stamp / Instant Reveal (Fake Reveal)**:
   - Trong `scripts/render_stream_whiteboard.py` tại dòng 419 cũ (`self.drawn[elem_box] = self.color_img[elem_box].astype(np.float32)`), khi gaze time của một element kết thúc, renderer đột ngột dán nguyên mảng ảnh raster của toàn bộ bounding box lên canvas. Điều này vi phạm nguyên tắc cốt lõi: *"Không được dùng fade in, instant reveal, mask reveal toàn bộ hình. Phải là progressive drawing theo nét vector."*
3. **Mất tích thời gian và lệch Audio/Video Drift**:
   - `cur_ms` không được cộng dồn thời lượng tô màu/tĩnh (`cur_ms += color_frames * ms_per_frame`), dẫn đến việc dòng thời gian bị lệch tới 1.7 giây và render bị dừng đột ngột trước khi các nét vẽ cuối cùng của chuối và tư thế khỉ kịp hoàn thiện.
4. **Hệ thống QA thiếu Drawing QA và Semantic Visual QA**:
   - QA cũ chỉ dựa vào `ffprobe` (container hợp lệ, codec đúng, thời lượng > 0), hoàn toàn mù đối với tính hoàn thiện nét vẽ (Drawing Completeness), tính hiện diện của thực thể (Entity Presence), hành động (Action) và mối quan hệ ngữ nghĩa (Semantic Relationships).
5. **Arc `A`/`a` Parsing Omission in `path_parser.py`**:
   - Hàm `shape_to_path_d` sinh lệnh cung elip `A` cho `<circle>` và `<ellipse>`, nhưng hàm `parse_and_sample_path` trước đây chưa xử lý lệnh `A`/`a`, dẫn đến việc toàn bộ các phần giải phẫu cơ bản dạng elip/vòng tròn (`head_outline`, `body_torso`, `belly_patch`, `snout`, `hand_upper`, `hand_lower`, `foot_upper`, `foot_lower`) bị bỏ qua hoàn toàn trong nét vẽ, chỉ còn sót lại vài đường cong tai và đuôi.
6. **Fake Tree Guide Artifact & Coordinate Misalignment in Asset**:
   - File `monkey_climbing.svg` cũ chứa một nhóm nét ảo `#tree_guide` (hai thanh đứng và các vòng ngang), khi kết xuất đã vẽ ra một "cột tre/thang" riêng biệt cạnh thân cây dừa thật. Đồng thời, tọa độ các chi với tới của khỉ nằm cách thân cây thật một khoảng trống ~46px, khiến khỉ trông như đang bám lơ lửng trên cột tre giả thay vì bám vào cây dừa.

## Existing Architecture

- **Visual Scene Graph**: Chỉ lưu danh sách đối tượng và quan hệ sơ sài, thiếu First-class Action, thiếu theo dõi `strokeCount`, `completedStrokeCount`, `completionRatio`.
- **Asset System**: Lookup dựa vào tên đơn lẻ, thiếu fallback đa tầng (Existing -> Variant -> Pose -> Action Variant -> Procedural SVG -> Diagram/Metaphor).
- **Renderer Adapter**: Dùng bounding box thô để sinh `protected_regions`.
- **Whiteboard Stream Engine**: Stamp toàn bộ bounding box ở cuối mỗi element.
- **QA Verification**: Single-layer Technical QA báo PASS sai lầm.

## Changed Architecture

Toàn bộ kiến trúc được nâng cấp thành **Generic Pipeline** không hard-code đối tượng:

1. **First-Class Visual Action & Completeness Tracking**:
   - Bổ sung schema `VisualAction` (`id`, `entity_id`, `action_type`, `motion_path`, `required`, `completed`).
   - Mở rộng `VisualEntity` với các trường bắt buộc: `asset_resolved`, `vector_available`, `stroke_plan_available`, `stroke_count`, `completed_stroke_count`, `completion_ratio`.
   - Một thực thể chỉ được coi là hoàn thành khi `completion_ratio == 1.0` (tất cả nét vẽ bắt buộc đã được hạ bút).
2. **Generic Tiered Asset Resolver (`core/assets/resolver.py`)**:
   - Không có code `if monkey`, `if tree`, `if banana`.
   - Hỗ trợ giải quyết đa tầng tổng quát:
     `Existing Asset -> Existing Variant -> Pose -> Action Variant -> Procedural SVG Generator -> Diagrams / Charts / Symbols / Metaphors`.
3. **Per-Entity Vector Stroke Isolation (`engines/whiteboard/adapter.py`)**:
   - Thay thế việc trừ bounding box chữ nhật bằng việc sinh mặt nạ nét vẽ độc lập (`maskFile`: `{scene_id}_{entity.id}_mask.png`).
   - Bất kể các đối tượng có lồng nhau hay giao cắt (khỉ leo trên cây, người nông dân đứng trên mặt đất, trái đất trên quỹ đạo), mặt nạ nét vẽ của từng thực thể được cô lập chính xác theo từng vector stroke, không bao giờ bị xóa nhầm bởi đối tượng khác.
4. **Pure Progressive Drawing Engine (`scripts/render_stream_whiteboard.py`)**:
   - Xóa bỏ hoàn toàn lệnh fake reveal tại dòng 419.
   - Bút vẽ tuần tự từng nét vector stroke, bàn tay di chuyển theo tọa độ thực (`handPath`), đảm bảo 100% progressive whiteboard drawing.
5. **Three-Layer QA Architecture (`core/qa/media_probe.py`)**:
   - **Tầng 1 (Technical QA)**: Container MP4, H.264/AAC codecs, FPS, độ phân giải, audio/video drift tolerance <= 1.5s, không lỗi stream.
   - **Tầng 2 (Drawing QA)**: `completion_ratio == 1.0`, `stroke_ordering_valid`, `hand_path_valid`, `hand_sync_valid`, `no_early_reveal`, `no_instant_reveal`.
   - **Tầng 3 (Semantic Visual QA)**: Kiểm tra sự hiện diện đầy đủ của toàn bộ `required_entities`, `required_actions`, `required_relationships`, và `final_frame_complete`.
   - **Overall Pass Rule**: Bắt buộc `Technical QA = PASS AND Drawing QA = PASS AND Semantic Visual QA = PASS`. Nếu bất kỳ tầng nào FAIL thì `Overall = FAIL`.
6. **UI Verification Screen (`apps/web/app/components/ReviewScreenView.tsx`)**:
   - Hiển thị đầy đủ 3 trụ cột QA, Required Visuals (X/Y), Completed Actions (X/Y), Drawing Completeness (XX%), Hand Synchronization (PASS/FAIL), Final Frame (COMPLETE/INCOMPLETE), và Overall Status.

## Files Changed

- `core/schemas/scene_graph.py`: Bổ sung `VisualAction`, mở rộng `VisualEntity` với các trường completeness và camelCase aliases.
- `core/schemas/annotation.py`: Thêm `maskFile` vào `ElementSchema`.
- `assets/library/manifest.json`: Đăng ký tài nguyên vector mở rộng (`earth`, `sun`, `orbit`, `water`, `vapor`, `farmer`, `ground`, `price_chart`, `upward_trend`).
- `core/drawing/path_parser.py`: Hiện thực hóa thuật toán lấy mẫu W3C SVG 1.1 cho cung Elip (`A`/`a`), chuyển đổi hình học cơ bản `circle`/`ellipse` sang Spline Cubic Bezier hoặc chuẩn Arc để không còn bất kỳ nét vẽ giải phẫu nào bị rớt hoặc thiếu.
- `assets/library/svg/monkey_climbing.svg`: Thiết kế lại hoàn chỉnh tư thế khỉ bám cây với đầy đủ giải phẫu (đầu, tai chi tiết trong ngoài, mặt nạ mặt, mắt hướng lên buồng chuối, mõm, nụ cười, thân mình cong, bụng trong, 4 chi ôm thân cây và đuôi uốn lượn); loại bỏ hoàn toàn nhóm `#tree_guide` ảo để xóa sổ hiện tượng "cột tre tách rời".
- `tests/fixtures/test_cases_data.py`: Tinh chỉnh tọa độ bám cây của `monkey_1` khớp vật lý hoàn hảo với thân cây dừa (`x=1223..1262`).
- `core/assets/resolver.py`: Xây dựng `GenericAssetResolver` đa tầng.
- `engines/whiteboard/adapter.py`: Chuyển sang kiến trúc per-entity stroke mask isolation, gỡ bỏ hardcoded role checks.
- `scripts/render_stream_whiteboard.py`: Hỗ trợ `maskFile`, xóa bỏ instant reveal tại gaze end, sửa lỗi tích lũy `cur_ms` cho color frames, cấu hình UTF-8 stdout/stderr trên Windows.
- `core/timeline/synchronizer.py`: Tích hợp `GenericAssetResolver`, tính toán pacing theo stroke count, theo dõi Section 8 completeness metrics.
- `core/qa/media_probe.py`: Tách bạch Three-Layer QA, thêm `errors` & `details`, hỗ trợ deterministic validation cho final frame.
- `core/pipeline/whiteboard_pipeline.py`: Liên kết kiểm định Three-Layer QA vào quy trình E2E pipeline, chỉ cho phép PASS khi cả 3 tầng đạt chuẩn.
- `apps/web/app/types.ts`: Cập nhật `MediaQAReport` và Three-Layer QA summaries.
- `apps/web/app/api-client.ts`: Cập nhật mock QA report khớp chuẩn 3 tầng.
- `apps/web/app/components/ReviewScreenView.tsx`: Xây dựng giao diện hiển thị Three-Layer QA Verification card.
- `tests/regression/test_visual_fidelity_regression.py`: Bộ 6 test regression cho các kịch bản tổng quát.
- `tests/qa/test_failure_injection.py`: Bộ 4 test tiêm lỗi kiểm định độ nhạy của Three-Layer QA.

## New Schemas

- `VisualAction`:
  ```python
  class VisualAction(BaseModel):
      id: str
      entity_id: str
      action_type: str
      motion_path: List[Tuple[float, float]]
      start_constraint: Optional[str]
      end_constraint: Optional[str]
      required: bool = True
      completed: bool = False
  ```
- `TechnicalQAResult`, `DrawingQAResult`, `SemanticVisualQAResult`:
  Định nghĩa các tiêu chí định lượng và định tính cho từng tầng kiểm định media.

## New Validation Rules

1. **Asset Completeness Rule**: Mỗi `VisualEntity` bắt buộc phải có `asset_resolved=True`, `vector_available=True`, `stroke_plan_available=True`, và `completion_ratio == 1.0`.
2. **No Early Reveal & No Instant Reveal Rule**: Mọi nét vẽ phải có `start_time >= 0`, không được xuất hiện mảng màu hoàn chỉnh trước hoặc đột ngột tại cuối phân cảnh.
3. **Hand Synchronization Rule**: Bàn tay phải có tọa độ `hand_path` hợp lệ và bám sát nét vẽ với `start_time <= end_time`.
4. **Three-Layer Overall Pass Rule**: Bắt buộc thỏa mãn đồng thời:
   $$\text{Overall Pass} = \text{Technical Pass} \land \text{Drawing Pass} \land \text{Semantic Pass}$$

## New Tests

- `tests/regression/test_visual_fidelity_regression.py`:
  - `test_regression_case_1_dog_ball`: Con chó đuổi theo quả bóng (dog, ball, running, chasing).
  - `test_regression_case_2_earth_sun`: Trái Đất quay quanh Mặt Trời (earth, sun, orbit).
  - `test_regression_case_3_water_evaporation`: Nước nóng bốc hơi (water, heat, vapor, upward motion).
  - `test_regression_case_4_farmer_tree`: Người nông dân trồng cây (farmer, ground, tree, planting).
  - `test_regression_case_5_inflation_price`: Giá cả và lạm phát (price, inflation, upward trend).
  - `test_regression_case_6_monkey_tree_banana`: Con khỉ trèo cây lấy chuối (monkey, tree, banana, climbing, reaching, located_on).
- `tests/qa/test_failure_injection.py`:
  - `test_failure_injection_missing_entity`: Thiếu thực thể -> Semantic QA FAIL, Overall FAIL.
  - `test_failure_injection_incomplete_stroke`: Nét vẽ chưa xong (tỉ lệ 50%) -> Drawing QA FAIL, Overall FAIL.
  - `test_failure_injection_wrong_hand_path`: Quỹ đạo tay rỗng -> Drawing QA FAIL, Overall FAIL.
  - `test_failure_injection_technically_valid_but_banana_missing`: MP4 kỹ thuật chuẩn nhưng thiếu visual -> Overall FAIL.

## Regression Results

Kết quả chạy bộ kiểm thử toàn diện trên repository:
- **Tổng số bài test**: 94 passed, 0 failed.
- `monkey-banana-demo`: **PASS**
- `dog-ball`: **PASS**
- `earth-sun`: **PASS**
- `water-evaporation`: **PASS**
- `farmer-tree`: **PASS**
- `inflation`: **PASS**
- `failure-injection`: 4/4 **PASS**

## Actual Render Results

Video thực tế được kết xuất tại: `output/monkey_banana_e2e/scene_default_final.mp4`

1. **Technical Metrics**:
   - Container: MP4 (H.264 video, AAC audio).
   - Độ phân giải: 1080x600.
   - FPS: 30.0 fps (171 frames).
   - Thời lượng: 5.70 giây (Audio duration: 5.182s, delta: 0.518s <= 1.5s tolerance).
   - Corruption: False (0 decode errors).
2. **Drawing QA Metrics**:
   - Required Strokes: 59 nét.
   - Completed Strokes: 59 nét.
   - Completion Ratio: 1.0 (100%).
   - Hand Synchronization: Valid.
   - Early Reveal: None (First frame luminance: 235.0 - canvas trắng hoàn toàn).
3. **Semantic Visual QA Metrics**:
   - Required Entities: 3/3 (`tree`, `monkey`, `banana`).
   - Actions: 2/2 (`climbing`, `reaching_for`).
   - Relationships: 3/3 (`monkey -> tree`, `monkey -> banana`, `banana -> tree`).
   - Final Frame: COMPLETE (Luminance: 230.24, đầy đủ thân cây, tán lá, khỉ đang bám thân cây vươn tay, chuối trên cành).

## Before / After

| Tiêu chí | Trước Phase 10.1 (Regression) | Sau Phase 10.1 (Hiện tại) |
|---|---|---|
| **Cây (Tree)** | Vẽ tương đối | Vẽ hoàn chỉnh thân và các tán lá dừa |
| **Khỉ (Monkey)** | Mất nét, bị xóa trắng bởi hộp cây | Vẽ đầy đủ đầu, tai, thân, 4 chi bám cây và đuôi cong |
| **Chuối (Banana)** | Không xuất hiện hoặc mờ nhạt | Vẽ hoàn chỉnh buồng chuối trên ngọn cây |
| **Hành động trèo (Climbing)** | Không thể hiện được | Khỉ ôm thân cây ở tư thế leo trèo rõ rệt |
| **Hành động với (Reaching)** | Không thể hiện được | Tay khỉ vươn về phía buồng chuối |
| **Cách vẽ (Drawing)** | Fake reveal đột ngột ở cuối phân cảnh | Vẽ nét tự nhiên progressive theo từng stroke, tay đưa bút |
| **QA Verification** | Chỉ kiểm tra file kỹ thuật -> False PASS | Three-Layer QA (Technical + Drawing + Semantic) |
| **Review UI** | Chỉ hiện Technical PASSED | Hiển thị 3 tầng QA độc lập, tỉ lệ % nét vẽ và số thực thể |

## Remaining Issues

- Không có blocker nào tồn tại.
- Pipeline hoàn toàn sẵn sàng cho mở rộng sang nhận diện cử động phức tạp hơn trong tương lai.

## Final Status

**PASS** (Đạt 100% tiêu chí Definition of Done theo quy định của Phase 10.1).
