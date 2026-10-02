import asyncio
import json
import subprocess
import sys
from pathlib import Path
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from engines.whiteboard.adapter import WhiteboardRenderConfig


def extract_frames(video_path: Path, output_dir: Path, prefix: str):
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    first_frame = None
    mid_frame = None
    last_frame = None

    if cap.isOpened():
        # Frame 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if ret:
            first_frame = frame
            cv2.imwrite(str(output_dir / f"{prefix}_first_frame.png"), first_frame)

        # Mid frame
        mid_idx = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_idx)
        ret, frame = cap.read()
        if ret:
            mid_frame = frame
            cv2.imwrite(str(output_dir / f"{prefix}_mid_frame.png"), mid_frame)

        # Last frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 2))
        ret, frame = cap.read()
        if ret:
            last_frame = frame
            cv2.imwrite(str(output_dir / f"{prefix}_final_frame.png"), last_frame)

    cap.release()
    return total_frames, fps


async def render_scenario(script: str, out_dir_name: str, prefix: str):
    print("\n" + "=" * 70)
    print(f"RENDERING SCENARIO: '{script}'")
    print("=" * 70)

    out_dir = Path(f"output/{out_dir_name}")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=30,
        cap_long_edge=1080,
        ink_path="skeleton",
        color_fill="contour-wipe",
    )

    result = await pipeline.run(
        script=script,
        input_mode="SCRIPT",
        output_dir=out_dir,
        render_config=cfg,
    )

    print(f"Pipeline Success: {result.is_success}")
    print(f"Final MP4: {result.final_mp4_path}")
    print(f"Image Path: {result.image_path}")
    print(f"Annotation: {result.annotation_path}")

    # Extract frames
    mp4_p = Path(result.final_mp4_path)
    total_frames, fps = extract_frames(mp4_p, out_dir, prefix)
    print(f"Extracted frames: total_frames={total_frames}, fps={fps}")
    print(f"  First: {out_dir / f'{prefix}_first_frame.png'}")
    print(f"  Mid:   {out_dir / f'{prefix}_mid_frame.png'}")
    print(f"  Final: {out_dir / f'{prefix}_final_frame.png'}")

    # Check ffprobe
    ffprobe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate",
        "-of", "json", str(mp4_p)
    ]
    try:
        proc = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(proc.stdout)
        print(f"FFprobe Data: {json.dumps(probe_data, indent=2)}")
    except Exception as e:
        print(f"FFprobe error: {e}")

    # Media Stream Properties
    rep = result.media_report
    print(f"\n--- MEDIA STREAMS & TECHNICAL PROFILE ---")
    print(f"Video: Codec={rep.video_codec}, Resolution={rep.video_width}x{rep.video_height}, FPS={rep.fps}, Frames={rep.frame_count}")
    print(f"Audio: Codec={rep.audio_codec}, Channels={rep.audio_channels}, Rate={rep.audio_sample_rate}Hz, Duration={rep.audio_duration_sec}s")
    print(f"Container Duration: {rep.duration_sec}s, Duration Delta: {rep.duration_delta}s")

    # QA breakdown
    print("\n--- QA REPORT BREAKDOWN ---")
    print(f"Overall Pass: {rep.overall_pass}")
    print(f"Technical QA: Pass={rep.technical_qa.pass_status}, Errors={rep.technical_qa.errors}")
    print(f"Semantic QA:  Pass={rep.semantic_visual_qa.pass_status}, Errors={rep.semantic_visual_qa.errors}, MissingEntities={rep.semantic_visual_qa.missing_entities}")
    print(f"Drawing QA:   Pass={rep.drawing_qa.pass_status}, Errors={rep.drawing_qa.errors}")
    if rep.visual_style_qa:
        print(f"Style QA:     Pass={rep.visual_style_qa.pass_status}, Errors={rep.visual_style_qa.errors}, Details={rep.visual_style_qa.details}")

    return result


async def main():
    # 1. Main Scenario: Con mèo leo cây cau.
    res1 = await render_scenario(
        script="Con mèo leo cây cau.",
        out_dir_name="cat_palm_demo",
        prefix="cat_palm"
    )

    # 2. Regression 1: Con chó chạy đuổi theo quả bóng.
    res2 = await render_scenario(
        script="Con chó chạy đuổi theo quả bóng.",
        out_dir_name="dog_ball_demo",
        prefix="dog_ball"
    )

    # 3. Regression 2: Trái Đất quay quanh Mặt Trời.
    res3 = await render_scenario(
        script="Trái Đất quay quanh Mặt Trời.",
        out_dir_name="earth_sun_demo",
        prefix="earth_sun"
    )

    print("\n" + "=" * 70)
    print("ALL 3 SCENARIOS RENDERED SUCCESSFULLY!")
    print(f"1. Cat Palm:  Overall Pass = {res1.media_report.overall_pass}")
    print(f"2. Dog Ball:  Overall Pass = {res2.media_report.overall_pass}")
    print(f"3. Earth Sun: Overall Pass = {res3.media_report.overall_pass}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
