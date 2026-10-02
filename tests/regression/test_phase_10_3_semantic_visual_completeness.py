import json
from pathlib import Path
import cv2
import numpy as np
import pytest

from core.assets.resolver import GenericAssetResolver
from core.pipeline.semantic_planner import SemanticVisualPlanner
from core.qa.media_probe import MediaProbe
from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import Position, SceneGraph, VisualAction, VisualEntity, VisualRelationship
from core.schemas.timeline import DrawingTimeline, DrawingTimelineEvent
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from core.validation.illustration import SourceIllustrationValidator
from core.validation.semantic import SemanticValidator
from engines.whiteboard.adapter import WhiteboardEngineAdapter


# ==============================================================================
# SECTION 12: REGRESSION TESTS
# ==============================================================================

def test_regression_case_a_cat_climbing_areca_palm(tmp_path):
    """
    TEST A — MÈO LEO CÂY CAU
    Input: 'Con mèo leo cây cau.'
    Required:
      - cat
      - areca palm
      - climbing action
      - cat-to-palm relationship
    FAIL nếu thiếu mèo hoặc chỉ có cây.
    """
    script = "Con mèo leo cây cau."

    # 1. Pipeline Script Understanding & Planning
    plan = SemanticVisualPlanner.plan_from_script(script)
    assert len(plan.scenes) >= 1
    sg: SceneGraph = plan.scenes[0].scene_graph

    # Kiểm tra thực thể
    entity_species = {e.species for e in sg.entities}
    entity_labels = {e.label for e in sg.entities}
    assert "cat" in entity_species or "cat" in entity_labels, "FAIL: Thiếu thực thể cat!"
    assert "areca_palm" in entity_species or "areca_palm" in entity_labels, "FAIL: Thiếu thực thể areca_palm!"
    assert "tree" not in entity_labels, "FAIL: Không được suy thoái cây cau thành cây chung chung!"

    cat_ent = next((e for e in sg.entities if e.species == "cat" or e.label == "cat"), None)
    palm_ent = next((e for e in sg.entities if e.species == "areca_palm" or e.label == "areca_palm"), None)
    assert cat_ent is not None
    assert palm_ent is not None

    # Kiểm tra metadata ngữ nghĩa
    assert cat_ent.semantic_type == "animal"
    assert cat_ent.visual_role == "main_character"
    assert cat_ent.required is True
    assert cat_ent.pose == "climbing"
    assert "climbing" in cat_ent.actions

    assert palm_ent.semantic_type == "plant"
    assert palm_ent.visual_role == "climbing_structure"
    assert palm_ent.required is True

    # Kiểm tra Action
    assert any(a.entity_id == cat_ent.id and a.action_type == "climbing" for a in sg.actions), "FAIL: Thiếu visual action climbing!"

    # Kiểm tra Relationship
    climb_rels = [
        r for r in sg.relationships
        if r.source_id == cat_ent.id and r.target_id == palm_ent.id
    ]
    assert len(climb_rels) >= 1, "FAIL: Thiếu quan hệ cat -> climbing_on -> areca_palm!"
    assert climb_rels[0].relation_type in ["climbing_on", "climbing"]

    # Kiểm tra tiếp xúc vật lý giữa chân mèo và thân cây
    # Thân cây cau x ~ 920, width 540 (trunk ở giữa x ~ 1160..1220).
    # Chân mèo vươn sang phải (x + width ~ 820 + 360 = 1180), tiếp xúc trực tiếp thân cây!
    assert cat_ent.position.x + cat_ent.position.width >= palm_ent.position.x + 200, "FAIL: Chân mèo không chạm vào thân cây!"

    # 2. Asset Resolution
    resolver = GenericAssetResolver()
    res_cat = resolver.resolve_entity(cat_ent)
    assert res_cat.stroke_count > 0, "Cat asset phải có stroke_count > 0"
    assert res_cat.is_valid_vector is True

    res_palm = resolver.resolve_entity(palm_ent)
    assert res_palm.stroke_count > 0, "Areca palm asset phải có stroke_count > 0"
    assert res_palm.is_valid_vector is True

    # 3. Timeline Synchronization
    sync = DrawingTimelineSynchronizer()
    timing = NarrationTiming(text=script, duration=5.0, words=[WordTiming(word=w, start_time=0.5*i, end_time=0.5*(i+1)) for i, w in enumerate(script.split())])
    timeline = sync.build_timeline(timing, sg)
    assert len(timeline.events) > 0

    # 4. Adapter Export & Pre-render Validation
    adapter = WhiteboardEngineAdapter()
    img_p, ann_p = adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    val_res = SourceIllustrationValidator.validate_pre_render(
        script_text=script,
        scene_graph=sg,
        timeline=timeline,
        image_path=img_p,
        annotation_path=ann_p,
    )
    assert val_res.is_valid is True, f"Pre-render validation failed: {val_res.errors}"


def test_regression_case_b_dog_chasing_ball(tmp_path):
    """
    TEST B — CHÓ ĐUỔI BÓNG
    Input: 'Con chó chạy đuổi theo quả bóng.'
    Required:
      - dog
      - ball
      - running / chasing
      - chasing relationship
    """
    script = "Con chó chạy đuổi theo quả bóng."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    labels = {e.label for e in sg.entities}
    assert "dog" in labels
    assert "ball" in labels

    # Kiểm tra hành động & quan hệ
    assert any("chasing" in a.action_type or "running" in a.action_type for a in sg.actions) or any("chasing" in r.relation_type for r in sg.relationships)
    dog_ent = next(e for e in sg.entities if e.label == "dog")
    ball_ent = next(e for e in sg.entities if e.label == "ball")
    assert dog_ent.position.x < ball_ent.position.x, "Chó phải ở phía sau đuổi theo bóng!"


def test_regression_case_c_earth_orbiting_sun(tmp_path):
    """
    TEST C — TRÁI ĐẤT QUAY QUANH MẶT TRỜI
    Required:
      - Earth
      - Sun
      - orbital relationship or clear orbit diagram
    """
    script = "Trái Đất quay quanh Mặt Trời."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    labels = {e.label for e in sg.entities}
    assert "earth" in labels
    assert "sun" in labels
    assert any(r.relation_type == "orbiting" for r in sg.relationships)


def test_regression_case_d_farmer_planting_tree(tmp_path):
    """
    TEST D — NGƯỜI NÔNG DÂN TRỒNG CÂY
    Required:
      - farmer
      - ground
      - seedling or tree
      - planting action
    """
    script = "Người nông dân trồng cây."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    labels = {e.label for e in sg.entities}
    assert "farmer" in labels
    assert "ground" in labels
    assert ("tree" in labels or "areca_palm" in labels)
    assert any(a.action_type == "planting" for a in sg.actions) or any(r.relation_type == "planting" for r in sg.relationships)


# ==============================================================================
# SECTION 13: FAILURE INJECTION TESTS
# ==============================================================================

def test_failure_injection_missing_entity_in_scene_graph():
    """
    Failure Injection 1: Thiếu entity trong scene graph.
    Script có 'Con mèo leo cây cau.', nhưng SceneGraph chỉ có cây, thiếu mèo.
    Phải bị phát hiện ở SemanticValidator và SourceIllustrationValidator.
    """
    script = "Con mèo leo cây cau."
    sg = SceneGraph(
        scene_id="only_palm",
        entities=[
            VisualEntity(id="palm_1", label="areca_palm", species="areca_palm", required=True)
        ],
    )
    val = SemanticValidator.validate_narration_against_graph(script, sg)
    assert val.is_valid is False
    assert "cat" in val.missing_entities

    pre_val = SourceIllustrationValidator.validate_pre_render(script, sg)
    assert pre_val.is_valid is False
    assert "cat" in pre_val.missing_entities


def test_failure_injection_missing_entity_in_illustration(tmp_path):
    """
    Failure Injection 2: Scene graph có entity nhưng illustration thiếu entity.
    Ảnh composite rỗng ở vùng của mèo (không có ink pixels).
    SourceIllustrationValidator phải phát hiện và ngăn cản render.
    """
    script = "Con mèo leo cây cau."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    # Tạo ảnh giả lập chỉ vẽ cây, vùng của mèo để trống (nền kem 215, 235, 245)
    img = np.full((1080, 1920, 3), (215, 235, 245), dtype=np.uint8)
    palm = next(e for e in sg.entities if e.label == "areca_palm")
    # Vẽ vài nét ở vùng cây
    cv2.line(img, (int(palm.position.x), int(palm.position.y)), (int(palm.position.x+100), int(palm.position.y+100)), (26, 26, 26), 4)
    img_path = tmp_path / "scene_missing_cat_ink.png"
    cv2.imwrite(str(img_path), img)

    pre_val = SourceIllustrationValidator.validate_pre_render(
        script_text=script,
        scene_graph=sg,
        image_path=img_path,
    )
    assert pre_val.is_valid is False
    assert any("cat" in err.lower() and "mực" in err.lower() for err in pre_val.errors)


def test_failure_injection_missing_annotation_region(tmp_path):
    """
    Failure Injection 3: Illustration đủ nhưng annotation thiếu region của một đối tượng bắt buộc.
    """
    script = "Con mèo leo cây cau."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    # Annotation chỉ chứa areca_palm, không chứa cat
    ann_data = {
        "sceneId": "scene_test",
        "elements": [
            {"id": "areca_palm_1", "region": {"x": 920, "y": 100, "width": 540, "height": 880}}
        ]
    }
    ann_path = tmp_path / "missing_cat.annotation.json"
    ann_path.write_text(json.dumps(ann_data), encoding="utf-8")

    pre_val = SourceIllustrationValidator.validate_pre_render(
        script_text=script,
        scene_graph=sg,
        annotation_path=ann_path,
    )
    assert pre_val.is_valid is False
    assert any("cat" in r for r in pre_val.missing_regions)


def test_failure_injection_missing_strokes():
    """
    Failure Injection 4: Region tồn tại nhưng stroke bị thiếu (0 nét vẽ).
    """
    script = "Con mèo leo cây cau."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    # Timeline rỗng (0 events cho cat)
    tl = DrawingTimeline(events=[], total_duration=5.0)
    pre_val = SourceIllustrationValidator.validate_pre_render(
        script_text=script,
        scene_graph=sg,
        timeline=tl,
    )
    assert pre_val.is_valid is False
    assert any("cat" in e for e in pre_val.zero_stroke_entities)


def test_failure_injection_stroke_not_played_in_timeline():
    """
    Failure Injection 5: Stroke tồn tại nhưng timeline không phát (không được schedule).
    """
    script = "Con mèo leo cây cau."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    # Timeline chỉ phát event cho areca_palm_1
    tl = DrawingTimeline(
        total_duration=5.0,
        events=[
            DrawingTimelineEvent(
                asset_id="asset_palm",
                stroke_id="stroke_palm_1",
                entity_id="areca_palm_1",
                action="draw",
                start_time=0.0,
                end_time=2.0,
                hand_path=[(900.0, 100.0)],
                points=[(900.0, 100.0), (950.0, 150.0)],
            )
        ]
    )
    rep = MediaProbe.inspect_media(
        file_path="mock.mp4",
        scene_graph=sg,
        timeline=tl,
        run_ffprobe=False,
    )
    assert rep.overall_pass is False
    assert rep.semantic_visual_qa.pass_status is False
    assert any("cat" in err.lower() for err in rep.semantic_visual_qa.errors)


def test_failure_injection_mp4_valid_but_missing_character():
    """
    Failure Injection 6: MP4 hợp lệ về mặt kỹ thuật nhưng thiếu nhân vật bắt buộc từ kịch bản.
    """
    script = "Con mèo leo cây cau."
    # Scene graph chỉ có cây
    sg = SceneGraph(
        scene_id="only_palm",
        entities=[
            VisualEntity(id="areca_palm_1", label="areca_palm", species="areca_palm", completion_ratio=1.0, required=True)
        ],
    )
    tl = DrawingTimeline(
        total_duration=5.0,
        events=[
            DrawingTimelineEvent(
                asset_id="asset_palm",
                stroke_id="stroke_palm_1",
                entity_id="areca_palm_1",
                action="draw",
                start_time=0.0,
                end_time=3.0,
                hand_path=[(920.0, 100.0)],
                points=[(920.0, 100.0), (950.0, 200.0)],
            )
        ]
    )
    # Media probe kiểm tra đối chiếu script_text
    rep = MediaProbe.inspect_media(
        file_path="mock.mp4",
        scene_graph=sg,
        timeline=tl,
        run_ffprobe=False,
        script_text=script,
    )
    assert rep.technical_qa.pass_status is True, "Technical QA đạt"
    assert rep.semantic_visual_qa.pass_status is False, "Semantic QA phải FAIL do thiếu mèo từ script"
    assert "cat" in rep.semantic_visual_qa.missing_entities
    assert rep.overall_pass is False, "Overall QA KHÔNG được PASS!"


def test_failure_injection_video_ends_before_drawing_complete():
    """
    Failure Injection 7: Video kết thúc khi nét vẽ chưa hoàn tất (completion_ratio < 1.0).
    """
    script = "Con mèo leo cây cau."
    plan = SemanticVisualPlanner.plan_from_script(script)
    sg = plan.scenes[0].scene_graph

    # Cố ý đặt completion_ratio của mèo = 0.6
    cat = next(e for e in sg.entities if e.label == "cat" or e.species == "cat")
    cat.completion_ratio = 0.6

    tl = DrawingTimeline(
        total_duration=5.0,
        events=[
            DrawingTimelineEvent(asset_id="asset_palm", stroke_id="p1", entity_id="areca_palm_1", action="draw", start_time=0.0, end_time=2.0, hand_path=[(0.0, 0.0)], points=[(0.0, 0.0), (1.0, 1.0)]),
            DrawingTimelineEvent(asset_id="asset_cat", stroke_id="c1", entity_id=cat.id, action="draw", start_time=2.0, end_time=3.0, hand_path=[(0.0, 0.0)], points=[(0.0, 0.0), (1.0, 1.0)]),
        ]
    )
    rep = MediaProbe.inspect_media(
        file_path="mock.mp4",
        scene_graph=sg,
        timeline=tl,
        run_ffprobe=False,
    )
    assert rep.drawing_qa.pass_status is False
    assert rep.overall_pass is False
