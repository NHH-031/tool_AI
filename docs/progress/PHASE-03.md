# Phase 03 — Core Schemas & Validation

## Objective
Xây dựng mô hình dữ liệu (Data Model) chuẩn cho toàn bộ pipeline sản xuất video Whiteboard Animation. Triển khai cấu trúc **Visual Scene Graph** thể hiện mối quan hệ động giữa các thực thể, xây dựng hệ thống kiểm tra tính toàn vẹn cấu trúc kỹ thuật (Structural Validation) và thẩm định sự tương thích ngữ nghĩa logic giữa kịch bản lời thoại và hình ảnh (Semantic Validation); tạo regression fixture `monkey-banana-demo` và bộ unit test tự động.

---

## Models implemented
Tất cả các model đều được triển khai bằng **Pydantic v2** với kiểu dữ liệu chặt chẽ (strongly typed):
1. **`Project`**: Mô hình gốc của dự án chứa danh sách các phân cảnh, tài nguyên và cấu hình template.
2. **`VideoTemplate`**: Định nghĩa chuẩn mỹ thuật, canvas, FPS và cờ `text_required`.
3. **`ProductionJob`**: Mô hình quản trị tiến trình và trạng thái các bước trong pipeline.
4. **`Scene`**: Đại diện cho một phân cảnh video hoàn chỉnh (chứa SceneGraph, Narration, DrawingActions, TimelineEvents, AudioTracks).
5. **`NarrationSegment`**: Đoạn lời thoại thuyết minh gắn kèm mốc thời gian và ID file âm thanh.
6. **`VisualEntity`**: Đối tượng thị giác trên canvas kèm phân loại category, tọa độ `Position`, lớp `layer` và thời gian xuất hiện.
7. **`VisualRelationship`**: Quan hệ ngữ nghĩa hoặc hành động kết nối giữa 2 thực thể (`source_id -> relation_type -> target_id`).
8. **`Asset`**: Quản lý tài nguyên số đính kèm (hình ảnh, âm thanh, phông chữ, config JSON).
9. **`DrawingStroke`**: Chi tiết quỹ đạo nét vẽ (grid hoặc skeleton Zhang-Suen, tọa độ điểm, màu sắc, bề dày nét).
10. **`DrawingAction`**: Hành động vẽ của bàn tay lên một thực thể (hạ nét ink, lên màu color, ngắm gaze) kèm vùng bảo vệ `protected_regions`.
11. **`TimelineEvent`**: Sự kiện tổng hợp được sắp xếp trên trục thời gian đồng bộ.
12. **`AudioTrack`**: Rãnh âm thanh đa kênh (voiceover, BGM, SFX).
13. **`RenderArtifact`**: Sản phẩm đầu ra sau render (preview image, scene MP4, final MP4).
14. **`QAResult`**: Báo cáo kiểm định chất lượng tự động sau kết xuất.

---

## Visual Scene Graph
Đã triển khai lớp `SceneGraph` hỗ trợ đầy đủ 6 khía cạnh yêu cầu:
- **Entity**: `VisualEntity` (đối tượng, nhân vật, bối cảnh, đạo cụ).
- **Relationship**: `VisualRelationship` (vị từ quan hệ giữa các thực thể).
- **Action**: Hành động cụ thể gắn với quan hệ (ví dụ: `climbing`, `reaching`, `located_on`).
- **Position**: Tọa độ pixel hình học trên canvas (`x, y, width, height`).
- **Layer**: Thứ tự vẽ từ dưới lên trên (0 = background, 1 = item, 2 = character).
- **Timing**: Mốc thời gian bắt đầu `start_ms` và thời lượng `duration_ms`.

---

## Validation rules
Triển khai trong `StructuralValidator`:
- **ID Uniqueness**: Không trùng lặp ID giữa các entities, relationships, scenes, events, assets.
- **Coordinate Bounds**: Tọa độ không được âm ($x \ge 0, y \ge 0$) và kích thước không được vượt biên canvas ($x + \text{width} \le \text{canvas.width}$, $y + \text{height} \le \text{canvas.height}$).
- **Timestamp Consistency**: Mốc bắt đầu $\ge 0$, mốc kết thúc $\ge$ mốc bắt đầu, không vượt quá tổng thời lượng cảnh.
- **Duration**: Thời lượng bắt buộc phải $> 0$.
- **Asset References**: Mọi `asset_id` được tham chiếu phải tồn tại trong danh mục assets của dự án.
- **Relationship References**: `source_id` và `target_id` phải tồn tại trong danh sách thực thể và không được tự trỏ vào chính nó.

---

## Semantic validation
Triển khai trong `SemanticValidator`:
- Phân tích ngữ nghĩa tự động từ lời thoại thuyết minh (hỗ trợ cả tiếng Việt và tiếng Anh).
- **Phát hiện thiếu đối tượng (Missing Entity)**:
  * Narration: "Con khỉ trèo lên cây."
  * Visual Plan: `monkey`, `car`, `banana`.
  * Kết quả: Báo lỗi `Missing entity: 'tree'`.
- **Phát hiện thiếu hành động/quan hệ (Missing Relationship)**:
  * Narration: "Con khỉ trèo lên cây."
  * Visual Plan: có `monkey` và `tree` nhưng không có quan hệ `climbing`.
  * Kết quả: Báo lỗi `Missing relationship: monkey -> climbing -> tree`.

---

## Regression fixture: `monkey-banana-demo`
Được thiết lập tại `tests/fixtures/monkey-banana-demo/scene.json` và loader tại `tests/fixtures/monkey_banana_loader.py`:
- **Thực thể**: `monkey`, `tree`, `banana`.
- **Quan hệ**:
  * `monkey -> climbing -> tree`
  * `monkey -> reaching -> banana`
  * `banana -> located_on -> tree`
- **Quy chuẩn**: `text_required = false`.
- **Kết quả kiểm thử**: Đạt 100% Structural và Semantic Validation.

---

## Tests executed
Toàn bộ 23 test cases (11 test mới cho Phase 03 và 12 test kế thừa từ Phase 02) đều đạt kết quả **PASSED** trong 0.83s:
- `tests/core/test_scene_graph.py::test_scene_graph_creation_and_traversal` — PASSED
- `tests/core/test_structural_validation.py::test_invalid_coordinates_exceeding_canvas` — PASSED
- `tests/core/test_structural_validation.py::test_negative_coordinates` — PASSED
- `tests/core/test_structural_validation.py::test_duplicate_entity_id` — PASSED
- `tests/core/test_structural_validation.py::test_broken_relationship_reference` — PASSED
- `tests/core/test_structural_validation.py::test_broken_asset_reference` — PASSED
- `tests/core/test_structural_validation.py::test_inverted_timeline_events` — PASSED
- `tests/core/test_semantic_validation.py::test_semantic_detects_missing_tree` — PASSED
- `tests/core/test_semantic_validation.py::test_semantic_detects_missing_climbing_relationship` — PASSED
- `tests/core/test_semantic_validation.py::test_semantic_passes_when_all_entities_and_actions_match` — PASSED
- `tests/core/test_monkey_fixture.py::test_monkey_banana_regression_fixture` — PASSED
- Toàn bộ 12 test cases của Phase 02 tiếp tục PASSED không bị regression.

---

## Verification results
- Cấu trúc dữ liệu đáp ứng đầy đủ yêu cầu của bài toán Whiteboard Animation Studio.
- Validator phân biệt rõ ràng giữa lỗi cú pháp (Syntax), lỗi biên kỹ thuật (Bounds/References) và lỗi logic kịch bản (Semantics).

---

## Known issues
- Từ điển ánh xạ từ vựng của `SemanticValidator` hiện tại dựa trên bộ quy tắc rule-based từ khóa cốt lõi (sẽ được mở rộng bằng embedding hoặc LLM ở Phase AI Agents sau này).

---

## Evidence
- Báo cáo Pytest: `23 passed, 1 warning in 0.83s`.
- Fixture data: `tests/fixtures/monkey-banana-demo/scene.json`.
- Tài liệu Data Model: [`docs/DATA_MODEL.md`](file:///d:/Tool/docs/DATA_MODEL.md).

---

## Phase status
**PASS**
Mọi yêu cầu kỹ thuật của Phase 03 đã được hoàn thành trọn vẹn và xác thực bằng kiểm thử tự động.
