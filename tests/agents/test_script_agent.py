import pytest
from core.providers.mock import MockLLMProvider
from core.schemas.script import ScriptOutput, ScriptSegment
from agents.script.agent import ScriptAgent
from agents.base import AgentContext


@pytest.mark.asyncio
async def test_script_agent_generates_valid_script():
    """Kiểm tra ScriptAgent sinh kịch bản thành công với các phân đoạn chuẩn."""
    mock_output = ScriptOutput(
        title="Hành trình quả chuối",
        script="Một chú khỉ con sống trên tán rừng xanh mát. Hôm nay chú quyết định trèo lên cây cao để hái quả chuối chín vàng.",
        segments=[
            ScriptSegment(
                cue_index=1,
                text="Một chú khỉ con sống trên tán rừng xanh mát.",
                estimated_duration_sec=3.5,
                semantic_meaning="Giới thiệu chú khỉ trong môi trường rừng",
                key_entities=["monkey", "forest"],
                suggested_actions=["standing"],
            ),
            ScriptSegment(
                cue_index=2,
                text="Hôm nay chú quyết định trèo lên cây cao để hái quả chuối chín vàng.",
                estimated_duration_sec=4.5,
                semantic_meaning="Chú khỉ leo lên cây tìm chuối",
                key_entities=["monkey", "tree", "banana"],
                suggested_actions=["climbing", "reaching"],
            ),
        ],
        language="vi",
        target_duration_sec=15,
        style="educational",
    )
    llm = MockLLMProvider(structured_responses=[mock_output])
    agent = ScriptAgent(llm=llm, max_retries=2)

    result = await agent.generate_script(
        idea="Một chú khỉ tìm chuối trên cây",
        language="vi",
        target_duration_sec=15,
        style="educational",
    )

    assert result.success is True
    assert result.data["title"] == "Hành trình quả chuối"
    assert result.data["segments_count"] == 2
    assert result.data["retries"] == 0


@pytest.mark.asyncio
async def test_script_agent_retries_on_malformed_output():
    """Kiểm tra ScriptAgent tự động retry và khôi phục khi gặp lỗi malformed JSON lần đầu."""
    mock_output = ScriptOutput(
        title="Dog and Ball Story",
        script="A playful dog runs after a tennis ball across the green field.",
        segments=[
            ScriptSegment(
                cue_index=1,
                text="A playful dog runs after a tennis ball across the green field.",
                estimated_duration_sec=4.0,
                semantic_meaning="Dog chasing ball",
                key_entities=["dog", "ball"],
                suggested_actions=["chasing"],
            )
        ],
        language="en",
    )
    # Lần 1 fail_first_n_structured = 1 mô phỏng lỗi malformed JSON, lần 2 trả về mock_output
    llm = MockLLMProvider(
        fail_first_n_structured=1,
        structured_responses=[mock_output],
    )
    agent = ScriptAgent(llm=llm, max_retries=2)

    result = await agent.generate_script(idea="Dog chasing ball", language="en")
    assert result.success is True
    assert result.data["retries"] == 1
    assert result.data["title"] == "Dog and Ball Story"


@pytest.mark.asyncio
async def test_script_agent_bounded_retry_exhaustion():
    """Kiểm tra ScriptAgent dừng lại và trả về lỗi có cấu trúc khi vượt quá số lần retry, không crash."""
    # Luôn mô phỏng lỗi vượt quá max_retries
    llm = MockLLMProvider(fail_first_n_structured=10)
    agent = ScriptAgent(llm=llm, max_retries=2)

    result = await agent.generate_script(idea="Chuyện vũ trụ")
    assert result.success is False
    assert "Thất bại khi sinh kịch bản sau 3 lần thử" in result.error_message
    assert result.data["error_type"] == "script_generation_exhausted"
    assert result.data["retries"] == 2


@pytest.mark.asyncio
async def test_script_agent_rejects_empty_idea():
    """Kiểm tra ScriptAgent từ chối khi idea rỗng mà không gọi LLM."""
    llm = MockLLMProvider()
    agent = ScriptAgent(llm=llm)

    result = await agent.generate_script(idea="   ")
    assert result.success is False
    assert result.data["error_type"] == "empty_idea"
    assert len(llm.call_history) == 0


@pytest.mark.asyncio
async def test_script_agent_context_integration():
    """Kiểm tra phương thức run qua AgentContext."""
    mock_output = ScriptOutput(
        title="Lạm phát là gì",
        script="Lạm phát làm tăng giá cả hàng hóa.",
        segments=[
            ScriptSegment(
                cue_index=1,
                text="Lạm phát làm tăng giá cả hàng hóa.",
                estimated_duration_sec=3.0,
                semantic_meaning="Giải thích lạm phát",
                key_entities=["inflation", "price"],
                suggested_actions=["rising"],
            )
        ],
    )
    llm = MockLLMProvider(structured_responses=[mock_output])
    agent = ScriptAgent(llm=llm)

    context = AgentContext(
        project_id="proj_01",
        project_title="Inflation Explainer",
        prompt="Giải thích hiện tượng lạm phát",
    )
    res = await agent.run(context)
    assert res.success is True
    assert "script_output" in context.shared_state
    assert context.shared_state["title"] == "Lạm phát là gì"
