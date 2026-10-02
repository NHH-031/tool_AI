# Tiến Độ Thực Hiện Dự Án: Phase 05

## Thông Tin Giai Đoạn
* **Tên Phase**: Phase 05 — Asset System & SVG Library
* **Mục Tiêu**: Biến Visual Scene Graph thành các visual asset có thể render và animate; xây dựng thư viện SVG tất định với nhiều tư thế hành động (poses/actions); thiết lập cơ chế tra cứu và kiểm định toàn vẹn không gây crash.
* **Thời Gian Hoàn Thành**: 2026-10-02
* **Trạng Thái**: **PASS**

---

## Các Hạng Mục Đã Thực Hiện

### 1. Kiến Trúc Nhà Cung Cấp Asset Mở Rộng (Asset Providers)
- [AssetProvider](file:///d:/Tool/core/assets/providers.py#L20-L34): Interface trừu tượng định nghĩa các phương thức `lookup`, `get_asset`, `load_svg`.
- [LocalAssetProvider](file:///d:/Tool/core/assets/providers.py#L37-L188): Quản lý thư viện SVG cục bộ dựa trên [manifest.json](file:///d:/Tool/assets/library/manifest.json), hỗ trợ tra cứu song ngữ (Việt - Anh) qua `tags`, tự động suy diễn pose từ action và xác thực cú pháp XML của file SVG trước khi sử dụng.
- [GeneratedAssetProvider](file:///d:/Tool/core/assets/providers.py#L191-L245): Nhà cung cấp dự phòng động tạo vector SVG procedural khi asset chưa có sẵn trong kho lưu trữ tĩnh.
- [CompositeAssetProvider](file:///d:/Tool/core/assets/providers.py#L248-L278): Ghép chuỗi tra cứu tự động: ưu tiên Local trước, fallback sang Generated khi gặp `ASSET_NOT_FOUND`.

### 2. Mô Hình Dữ Liệu Asset Chuẩn (Pydantic v2)
- [VisualAsset](file:///d:/Tool/core/schemas/asset.py#L16-L53): Đáp ứng đầy đủ các trường `id`, `name`, `category`, `tags`, `format`, `path`, `poses`, `actions`, `metadata`.
- [AssetPose](file:///d:/Tool/core/schemas/asset.py#L7-L14): Đặc tả từng tư thế cụ thể (`standing`, `climbing`, `eating`, `walking`, `sitting`, `jumping`) kèm `file_path` và `view_box`.
- [AssetLookupQuery](file:///d:/Tool/core/schemas/asset.py#L56-L64) & [AssetLookupResult](file:///d:/Tool/core/schemas/asset.py#L67-L79): Cơ chế đóng gói yêu cầu và kết quả tra cứu với mã lỗi có cấu trúc (`ASSET_NOT_FOUND`, `INVALID_ASSET`), tuyệt đối không gây crash.

### 3. Thư Viện SVG Tất Định (Deterministic SVG Vector Library)
Đã tạo 18 file SVG vector chất lượng cao theo phong cách Whiteboard line art (nét vẽ màu `#1A1A1A`, stroke-width chuẩn, viewBox rõ ràng):
- **Monkey (6 tư thế/hành động)**:
  - `svg/monkey_standing.svg`: Đứng thẳng vẫy tay tươi vui.
  - `svg/monkey_climbing.svg`: Bám thân cây leo lên cao.
  - `svg/monkey_eating.svg`: Ngồi ăn chuối ngon lành.
  - `svg/monkey_walking.svg`: Bước đi 4 chân sải bước.
  - `svg/monkey_sitting.svg`: Ngồi gãi đầu tò mò.
  - `svg/monkey_jumping.svg`: Bật nhảy trên không vươn tay.
- **Tree**:
  - `svg/tree_palm.svg`: Cây dừa nhiệt đới thân có vân, tán lá tỏa rộng.
  - `svg/tree_with_bananas.svg`: Cây có chùm chuối chín treo lủng lẳng.
- **Banana**:
  - `svg/banana_single.svg`: Quả chuối cong chín vàng có cuống rõ nét.
  - `svg/banana_bunch.svg`: Nải 3 quả chuối kết chùm.
- **Các Asset Bổ Trợ (cho các Test Cases khác)**:
  - `svg/dog_running.svg`, `svg/ball.svg`
  - `svg/teacher.svg`, `svg/blackboard_math.svg`
  - `svg/temperature_heat.svg`, `svg/molecules_diagram.svg`
  - `svg/inflation_balloon.svg`, `svg/money_wallet.svg`

### 4. Kiểm Thử Trực Quan (Visual Inspection)
- Đã tạo trang web trực quan [assets/library_preview.html](file:///d:/Tool/assets/library_preview.html) hiển thị:
  - Từng tư thế riêng biệt của Monkey, Tree và Banana.
  - Phối cảnh kết hợp (Composite Scene) kiểm tra sự phối hợp không gian giữa `Tree` (layer 0) + `Monkey Climbing` (layer 1) + `Banana` (layer 2) trên nền giấy bảng trắng `#FAF6ED`.

---

## Bằng Chứng Kiểm Thử (Test Verification Evidence)

Chạy thực tế với `pytest -v tests`:
```text
tests/agents/test_script_agent.py::test_script_agent_generates_valid_script PASSED [  1%]
tests/agents/test_script_agent.py::test_script_agent_retries_on_malformed_output PASSED [  3%]
tests/agents/test_script_agent.py::test_script_agent_bounded_retry_exhaustion PASSED [  5%]
tests/agents/test_script_agent.py::test_script_agent_rejects_empty_idea PASSED [  7%]
tests/agents/test_script_agent.py::test_script_agent_context_integration PASSED [  9%]
tests/agents/test_visual_planner.py::test_case_1_dog_running_after_ball PASSED [ 11%]
tests/agents/test_visual_planner.py::test_case_2_teacher_explaining_mathematics PASSED [ 13%]
tests/agents/test_visual_planner.py::test_case_3_temperature_molecules PASSED [ 15%]
tests/agents/test_visual_planner.py::test_case_4_inflation_metaphor PASSED [ 17%]
tests/agents/test_visual_planner.py::test_case_5_monkey_climbing_tree_for_banana PASSED [ 19%]
tests/agents/test_visual_planner.py::test_show_dont_write_rejection_and_repair PASSED [ 21%]
tests/agents/test_visual_planner.py::test_semantic_missing_entity_triggers_repair PASSED [ 23%]
tests/agents/test_visual_planner.py::test_visual_planner_bounded_retries_failure PASSED [ 25%]
tests/assets/test_asset_system.py::test_asset_lookup_by_name_and_tags PASSED [ 27%]
tests/assets/test_asset_system.py::test_missing_asset_returns_not_found PASSED [ 29%]
tests/assets/test_asset_system.py::test_invalid_asset_handling PASSED    [ 31%]
tests/assets/test_asset_system.py::test_pose_selection PASSED            [ 33%]
tests/assets/test_asset_system.py::test_action_selection PASSED          [ 35%]
tests/assets/test_asset_system.py::test_svg_loading_validity PASSED      [ 37%]
tests/assets/test_asset_system.py::test_asset_metadata PASSED            [ 39%]
tests/assets/test_composite_asset_provider_fallback PASSED [ 41%]
tests/assets/test_visual_svg_rendering.py::test_visual_svg_monkey_standing PASSED [ 43%]
tests/assets/test_visual_svg_rendering.py::test_visual_svg_monkey_climbing PASSED [ 45%]
tests/assets/test_visual_svg_rendering.py::test_visual_svg_tree PASSED   [ 47%]
tests/assets/test_visual_svg_rendering.py::test_visual_svg_banana PASSED [ 49%]
tests/assets/test_visual_svg_rendering.py::test_composite_scene_structure PASSED [ 50%]
tests/backend/test_config.py::test_default_config PASSED                 [ 52%]
tests/backend/test_health.py::test_get_health_endpoint PASSED            [ 54%]
tests/backend/test_jobs_api.py::test_create_and_get_job PASSED           [ 56%]
tests/backend/test_jobs_api.py::test_get_nonexistent_job PASSED          [ 58%]
tests/core/test_imports.py::test_core_imports PASSED                     [ 60%]
tests/core/test_jobs.py::test_production_job_lifecycle PASSED            [ 62%]
tests/core/test_monkey_fixture.py::test_monkey_banana_regression_fixture PASSED [ 64%]
tests/core/test_providers.py::test_mock_llm_provider PASSED              [ 66%]
tests/core/test_providers.py::test_mock_tts_provider PASSED              [ 68%]
tests/core/test_providers.py::test_mock_image_provider PASSED            [ 70%]
tests/core/test_providers.py::test_mock_storage_provider PASSED          [ 72%]
tests/core/test_scene_graph.py::test_scene_graph_creation_and_traversal PASSED [ 74%]
tests/core/test_schemas.py::test_validate_example_annotation PASSED      [ 76%]
tests/core/test_semantic_validation.py::test_semantic_detects_missing_tree PASSED [ 78%]
tests/core/test_semantic_validation.py::test_semantic_detects_missing_climbing_relationship PASSED [ 80%]
tests/core/test_semantic_validation.py::test_semantic_passes_when_all_entities_and_actions_match PASSED [ 82%]
tests/core/test_structural_validation.py::test_invalid_coordinates_exceeding_canvas PASSED [ 84%]
tests/core/test_structural_validation.py::test_negative_coordinates PASSED [ 86%]
tests/core/test_structural_validation.py::test_duplicate_entity_id PASSED [ 88%]
tests/core/test_structural_validation.py::test_broken_relationship_reference PASSED [ 90%]
tests/core/test_structural_validation.py::test_broken_asset_reference PASSED [ 92%]
tests/core/test_structural_validation.py::test_inverted_timeline_events PASSED [ 94%]
tests/engines/test_whiteboard_adapter.py::test_whiteboard_adapter_instantiation PASSED [ 96%]
tests/providers/test_gemini_provider.py::test_gemini_provider_prepare_contents PASSED [ 98%]
tests/providers/test_gemini_provider.py::test_gemini_provider_requires_api_key PASSED [100%]

======================== 51 passed, 1 warning in 1.12s ========================
```

---

## Tài Liệu Được Tạo / Cập Nhật
- [docs/ASSET_SYSTEM.md](file:///d:/Tool/docs/ASSET_SYSTEM.md)
- [docs/progress/PHASE-05.md](file:///d:/Tool/docs/progress/PHASE-05.md)
