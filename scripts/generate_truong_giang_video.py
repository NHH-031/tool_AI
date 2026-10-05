import asyncio
import os
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.qa.media_probe import MediaProbe
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.script import ScriptOutput, ScriptSegment
from core.tts.edge import EdgeTTSProvider
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig
from scripts.merge_scenes import _ffmpeg_concat_copy, _pyav_concat


async def main():
    print("=" * 80)
    print("BẮT ĐẦU TẠO VIDEO TÓM TẮT CUỘC ĐỜI NGHỆ SĨ TRƯỜNG GIANG (MƯỜI KHÓ)")
    print("Phong cách: Studio Ghibli Anime Watercolor Storybook (Vẽ nhanh 2s đầu, giữ màu nguyên bản)")
    print("=" * 80)

    out_dir = Path("output/truong_giang_story").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Chuẩn bị 3 tác phẩm mỹ thuật Anime Ghibli đặc sắc
    art_sources = [
        Path(r"C:\Users\ACER\.gemini\antigravity-ide\brain\8039abad-dc3c-41ce-8103-245527dce96c\truong_giang_scene_1_1791206155661.jpg"),
        Path(r"C:\Users\ACER\.gemini\antigravity-ide\brain\8039abad-dc3c-41ce-8103-245527dce96c\truong_giang_scene_2_1791206190083.jpg"),
        Path(r"C:\Users\ACER\.gemini\antigravity-ide\brain\8039abad-dc3c-41ce-8103-245527dce96c\truong_giang_scene_3_1791206220356.jpg"),
    ]

    scenes_data = [
        {
            "id": "scene_1",
            "title": "Tuổi thơ nghèo khó tại Quảng Nam",
            "narration": "Sinh ra trong nghèo khó tại vùng đất Quảng Nam và sớm mồ côi mẹ, cậu bé Trường Giang đã trải qua tuổi thơ đầy gian khó với gánh củi trên vai.",
            "visual_prompt": "A young Vietnamese boy wearing faded brown clothes carrying a bundle of firewood on a quiet dusty rural village path in Quảng Nam",
            "art_file": art_sources[0],
            "entities": [
                VisualEntity(id="cau_be", name="Cậu bé Trường Giang", label="Cậu bé Trường Giang", importance="primary", layer=1, position=Position(x=700, y=350, width=500, height=650)),
                VisualEntity(id="ganh_cui", name="Gánh củi", label="Gánh củi", importance="secondary", layer=2, position=Position(x=720, y=450, width=400, height=300)),
            ],
        },
        {
            "id": "scene_2",
            "title": "Gian nan bươn chải tại Sài Gòn",
            "narration": "Bước chân vào Sài Gòn bươn chải, anh không ngần ngại làm đủ mọi công việc từ phục vụ quán ăn đến rửa chén để kiên trì nuôi dưỡng ước mơ nghệ thuật.",
            "visual_prompt": "A young Vietnamese man working diligently serving dishes in a bustling retro Saigon street diner",
            "art_file": art_sources[1],
            "entities": [
                VisualEntity(id="phuc_vu", name="Trường Giang phục vụ bàn", label="Trường Giang phục vụ bàn", importance="primary", layer=1, position=Position(x=700, y=250, width=550, height=750)),
                VisualEntity(id="mam_com", name="Mâm cơm phục vụ", label="Mâm cơm phục vụ", importance="secondary", layer=2, position=Position(x=750, y=450, width=350, height=200)),
            ],
        },
        {
            "id": "scene_3",
            "title": "Tỏa sáng vinh quang với Mười Khó",
            "narration": "Bằng tài năng và sự mộc mạc, vai diễn Mười Khó với chiếc áo bà ba đã đưa Trường Giang tỏa sáng rực rỡ, trở thành danh hài được triệu khán giả yêu mến.",
            "visual_prompt": "Charismatic Vietnamese comedian in brown peasant shirt áo bà ba and checkered scarf khăn rằn performing triumphantly on stage under warm spotlights",
            "art_file": art_sources[2],
            "entities": [
                VisualEntity(id="muoi_kho", name="Nghệ sĩ Mười Khó", label="Nghệ sĩ Mười Khó", importance="primary", layer=1, position=Position(x=550, y=150, width=800, height=850)),
                VisualEntity(id="san_khau", name="Sân khấu nhà hát", label="Sân khấu rực rỡ", importance="secondary", layer=2, position=Position(x=100, y=100, width=1720, height=880)),
            ],
        },
    ]

    from core.schemas.tts import VoiceConfig
    from core.pipeline.semantic_planner import SemanticVisualPlanner

    v_cfg = VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi", speed=1.0)
    tts = EdgeTTSProvider(default_voice="vi-VN-HoaiMyNeural")
    adapter = WhiteboardEngineAdapter()

    render_cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=640,
        ink_path="skeleton",
        color_fill="contour-wipe",
        draw_ratio=0.35,  # Vẽ nhanh trong ~35% thời lượng (2.0 - 2.4s)
        max_draw_ms=2200, # Giới hạn tối đa 2.2s vẽ xong
    )

    scene_clips = []
    start_total_time = time.perf_counter()

    for idx, sc in enumerate(scenes_data, 1):
        scene_id = sc["id"]
        print(f"\n--- [XỬ LÝ PHÂN CẢNH {idx}/3: {sc['title']}] ---")

        # A. Chuẩn bị ảnh AI 1080p
        target_art = out_dir / f"{scene_id}_ai_artwork.png"
        src_art = sc["art_file"]
        if src_art.exists():
            img = cv2.imread(str(src_art))
            if img is not None:
                resized = cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)
                cv2.imwrite(str(target_art), resized)
                print(f"-> Đã tối ưu hóa tác phẩm mỹ thuật 1920x1080: {target_art.name}")

        # B. Tạo giọng đọc thuyết minh TTS
        narration_audio = out_dir / f"{scene_id}_narration.wav"
        print(f"-> Sinh giọng đọc thuyết minh: '{sc['narration']}'")
        seg_audio = await tts.generate(sc["narration"], v_cfg)
        timing = seg_audio.timing or await tts.get_timing(sc["narration"], v_cfg)
        seg_audio.save_to_file(narration_audio)
        dur = timing.duration
        print(f"-> Thời lượng audio: {dur:.2f}s | Dự kiến hoàn thành vẽ: {min(2.2, dur * 0.35):.2f}s")

        # C. Xây dựng SceneGraph & Timeline
        seg = ScriptSegment(
            cue_index=idx,
            text=sc["narration"],
            estimated_duration_sec=dur,
            semantic_meaning=sc["title"],
            visual_prompt=sc["visual_prompt"],
        )
        seg_plan = SemanticVisualPlanner.plan_from_script(
            script=sc["narration"],
            segments=[seg],
            title=sc["title"],
        )
        sg = seg_plan.scenes[0].scene_graph
        sg.scene_id = scene_id
        sg.narration = sc["narration"]
        sg.visual_prompt = sc["visual_prompt"]

        from core.timeline.synchronizer import DrawingTimelineSynchronizer
        syncer = DrawingTimelineSynchronizer()
        timeline = syncer.build_timeline(timing, sg)

        # D. Chuẩn bị Artifacts (Ảnh canvas & Annotation JSON)
        img_path, annot_path = adapter.prepare_scene_artifacts(
            scene_graph=sg,
            timeline=timeline,
            output_dir=out_dir,
        )

        # E. Render Video Whiteboard Animation
        raw_video = out_dir / f"{scene_id}_raw.mp4"
        seg_cfg = WhiteboardRenderConfig(
            fps=render_cfg.fps,
            cap_long_edge=render_cfg.cap_long_edge,
            ink_path=render_cfg.ink_path,
            color_fill=render_cfg.color_fill,
            draw_ratio=render_cfg.draw_ratio,
            max_draw_ms=render_cfg.max_draw_ms,
            total_ms=int(round(dur * 1000)),
        )
        print(f"-> Bắt đầu render video phân cảnh {idx}...")
        t_render_start = time.perf_counter()
        adapter.render_scene(
            image_path=img_path,
            annotation_path=annot_path,
            output_path=raw_video,
            config=seg_cfg,
        )
        print(f"-> Render video hoàn tất trong {time.perf_counter() - t_render_start:.1f}s")

        # F. Mux Audio & Video
        final_scene_mp4 = out_dir / f"{scene_id}_final.mp4"
        adapter.mux_audio_video(
            video_path=raw_video,
            audio_path=narration_audio,
            output_path=final_scene_mp4,
        )
        print(f"-> Đã ghép audio vào video cảnh {idx}: {final_scene_mp4.name}")
        scene_clips.append(final_scene_mp4)

    # 2. Ghép nối 3 phân cảnh thành video trọn vẹn
    print("\n" + "=" * 80)
    print("GHÉP NỐI CÁC PHÂN CẢNH THÀNH VIDEO HOÀN CHỈNH...")
    final_merged_mp4 = out_dir / "truong_giang_cuoc_doi_final.mp4"
    concat_ok = _ffmpeg_concat_copy(scene_clips, final_merged_mp4) or _pyav_concat(scene_clips, final_merged_mp4)
    if not (concat_ok and final_merged_mp4.exists()):
        final_merged_mp4 = scene_clips[0]

    total_time = time.perf_counter() - start_total_time
    print(f"TỔNG THỜI GIAN THỰC HIỆN: {total_time:.1f}s")
    print(f"VIDEO CUỐI CÙNG: {final_merged_mp4}")

    # 3. Media Quality Assurance
    probe = MediaProbe.inspect_media(final_merged_mp4)
    print("\n" + "=" * 80)
    print("BÁO CÁO KIỂM TRA CHẤT LƯỢNG (MEDIA QA):")
    print(f"- Tệp hợp lệ: {probe.is_valid_mp4}")
    print(f"- Thời lượng: {probe.duration_sec:.2f}s")
    print(f"- Độ phân giải: {probe.video_width}x{probe.video_height} @ {probe.fps}fps")
    print(f"- Codec Video: {probe.video_codec} | Audio: {probe.audio_codec}")
    print(f"- Độ lệch Audio-Video: {probe.duration_delta:.2f}s")
    print(f"- Dung lượng: {probe.file_size_bytes / (1024 * 1024):.2f} MB")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
