# Tiến Độ Thực Hiện Dự Án: Phase 04

## Thông Tin Giai Đoạn
* **Tên Phase**: Phase 04 — Script Agent & Visual Planner Agent
* **Mục Tiêu**: Kết nối AI để biến Video Idea thành Script -> Narration Segments -> Visual Scene Graph với nguyên tắc "Show Don't Write" và cơ chế sửa lỗi tự động có giới hạn.
* **Thời Gian Hoàn Thành**: 2026-10-02
* **Trạng Thái**: **PASS**

---

## Các Hạng Mục Đã Thực Hiện

### 1. Phân Tách LLM Provider & Tích Hợp Gemini
- Hiện thực hóa `GeminiProvider` kế thừa từ `LLMProvider`, kết nối trực tiếp qua Google Generative Language REST API mà không bị khóa cứng (vendor lock-in) vào SDK độc quyền.
- Hỗ trợ Native Structured Output bằng cách gửi JSON Schema của Pydantic v2 sang `generationConfig.responseSchema`.
- Mở rộng `MockLLMProvider` với hàng đợi structured responses, callback handler và cơ chế mô phỏng lỗi malformed JSON để phục vụ kiểm thử tự động offline.

### 2. Hiện Thực Hóa ScriptAgent
- Nhận diện `idea`, `language`, `target_duration_sec`, `style`.
- Sinh kịch bản hoàn chỉnh tuân thủ schema `ScriptOutput` với các `ScriptSegment` có thời lượng ước tính và ngữ nghĩa thông điệp cốt lõi.
- Cơ chế thử lại có giới hạn (`max_retries = 2`) khi gặp phản hồi rỗng hoặc malformed JSON.
- Từ chối ngay lập tức khi đầu vào rỗng mà không lãng phí token LLM.

### 3. Hiện Thực Hóa VisualPlannerAgent & Nguyên Tắc "Show Don't Write"
- Chuyển hóa kịch bản và phân đoạn thoại thành đồ thị cảnh trực quan (`Visual Scene Graph`) trên canvas chuẩn 1920x1080.
- Thực thi nghiêm ngặt nguyên tắc **"Show Don't Write"**:
  - Tuyệt đối ngăn chặn AI xuất các thực thể chính dưới dạng text chữ cái (ví dụ: cấm dùng `text: "CON KHỈ"` hay `text: "CÂY"` thay vì vẽ hình).
  - Yêu cầu các khái niệm trừu tượng (như lạm phát, nhiệt độ, vận tốc) phải sử dụng **Visual Metaphor / Diagram** (khinh khí cầu giá cả, đồng tiền teo nhỏ, ngọn lửa burner, mũi tên gia tốc).
- Cơ chế tự sửa chữa lỗi ngữ nghĩa (Semantic Repair Loop): Tự động phát hiện thiếu thực thể, thiếu quan hệ tương tác hoặc vi phạm Show Don't Write, gửi phản hồi lỗi chi tiết để mô hình sửa lại trong tối đa 2 lần thử.
- Bounded Retries: Nếu lỗi kéo dài vượt quá số lần thử, trả về `AgentResult(success=False)` có cấu trúc, không gây crash pipeline.

### 4. Kiểm Thử 5 Test Cases Toàn Diện
Đã kiểm tra và vượt qua toàn bộ 5 test cases theo yêu cầu:
1. **Case 1: Dog running after ball** (`dog`, `ball`, quan hệ `chasing`, visual_type `character` & `object`).
2. **Case 2: Teacher explaining mathematics** (`teacher`, `mathematics`, quan hệ `explaining`, visual_type `character` & `diagram`).
3. **Case 3: Temperature makes molecules move faster** (`temperature`, `molecules`, quan hệ `accelerating`, visual_type `diagram`).
4. **Case 4: Inflation** (`inflation`, `money`, quan hệ `eroding`, visual metaphor `metaphor`).
5. **Case 5: Monkey climbing tree for banana** (`monkey`, `tree`, `banana`, quan hệ `climbing`, `reaching`, `located_on`, Show Don't Write pass).

---

## Bằng Chứng Kiểm Thử (Test Verification Evidence)

Chạy thực tế với `pytest -v tests`:
```text
tests/agents/test_script_agent.py::test_script_agent_generates_valid_script PASSED [  2%]
tests/agents/test_script_agent.py::test_script_agent_retries_on_malformed_output PASSED [  5%]
tests/agents/test_script_agent.py::test_script_agent_bounded_retry_exhaustion PASSED [  7%]
tests/agents/test_script_agent.py::test_script_agent_rejects_empty_idea PASSED [ 10%]
tests/agents/test_script_agent.py::test_script_agent_context_integration PASSED [ 13%]
tests/agents/test_visual_planner.py::test_case_1_dog_running_after_ball PASSED [ 15%]
tests/agents/test_visual_planner.py::test_case_2_teacher_explaining_mathematics PASSED [ 18%]
tests/agents/test_visual_planner.py::test_case_3_temperature_molecules PASSED [ 21%]
tests/agents/test_visual_planner.py::test_case_4_inflation_metaphor PASSED [ 23%]
tests/agents/test_visual_planner.py::test_case_5_monkey_climbing_tree_for_banana PASSED [ 26%]
tests/agents/test_visual_planner.py::test_show_dont_write_rejection_and_repair PASSED [ 28%]
tests/agents/test_visual_planner.py::test_semantic_missing_entity_triggers_repair PASSED [ 31%]
tests/agents/test_visual_planner.py::test_visual_planner_bounded_retries_failure PASSED [ 34%]
tests/backend/test_config.py::test_default_config PASSED                 [ 36%]
tests/backend/test_health.py::test_get_health_endpoint PASSED            [ 39%]
tests/backend/test_jobs_api.py::test_create_and_get_job PASSED           [ 42%]
tests/backend/test_jobs_api.py::test_get_nonexistent_job PASSED          [ 44%]
tests/core/test_imports.py::test_core_imports PASSED                     [ 47%]
tests/core/test_jobs.py::test_production_job_lifecycle PASSED            [ 50%]
tests/core/test_monkey_fixture.py::test_monkey_banana_regression_fixture PASSED [ 52%]
tests/core/test_providers.py::test_mock_llm_provider PASSED              [ 55%]
tests/core/test_providers.py::test_mock_tts_provider PASSED              [ 57%]
tests/core/test_providers.py::test_mock_image_provider PASSED            [ 60%]
tests/core/test_providers.py::test_mock_storage_provider PASSED          [ 63%]
tests/core/test_scene_graph.py::test_scene_graph_creation_and_traversal PASSED [ 65%]
tests/core/test_schemas.py::test_validate_example_annotation PASSED      [ 68%]
tests/core/test_semantic_validation.py::test_semantic_detects_missing_tree PASSED [ 71%]
tests/core/test_semantic_validation.py::test_semantic_detects_missing_climbing_relationship PASSED [ 73%]
tests/core/test_semantic_validation.py::test_semantic_passes_when_all_entities_and_actions_match PASSED [ 76%]
tests/core/test_structural_validation.py::test_invalid_coordinates_exceeding_canvas PASSED [ 78%]
tests/core/test_structural_validation.py::test_negative_coordinates PASSED [ 81%]
tests/core/test_structural_validation.py::test_duplicate_entity_id PASSED [ 84%]
tests/core/test_structural_validation.py::test_broken_relationship_reference PASSED [ 86%]
tests/core/test_structural_validation.py::test_broken_asset_reference PASSED [ 89%]
tests/core/test_structural_validation.py::test_inverted_timeline_events PASSED [ 92%]
tests/engines/test_whiteboard_adapter.py::test_whiteboard_adapter_instantiation PASSED [ 94%]
tests/providers/test_gemini_provider.py::test_gemini_provider_prepare_contents PASSED [ 97%]
tests/providers/test_gemini_provider.py::test_gemini_provider_requires_api_key PASSED [100%]

======================== 38 passed, 1 warning in 1.06s ========================
```

---

## Tài Liệu Được Tạo
- [docs/AI_AGENTS.md](file:///d:/Tool/docs/AI_AGENTS.md)
- [docs/progress/PHASE-04.md](file:///d:/Tool/docs/progress/PHASE-04.md)
