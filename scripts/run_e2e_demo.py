import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from engines.whiteboard.adapter import WhiteboardRenderConfig


async def main():
    print("=" * 60)
    print("PHASE 09 — END-TO-END WHITEBOARD GENERATION")
    print("=" * 60)
    idea = "Con khỉ đang trèo lên cây để lấy một quả chuối."
    print(f"Input Idea: {idea}")

    out_dir = Path("output/monkey_banana_e2e")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=30,
        cap_long_edge=1080,  # 1080p Full HD
        ink_path="grid",
        color_fill="contour-wipe",
    )

    print("\nExecuting End-to-End Pipeline...")
    res = await pipeline.run(
        idea=idea,
        output_dir=out_dir,
        render_config=cfg,
    )

    print(f"\nPipeline Status: {'SUCCESS' if res.is_success else 'FAILED'}")
    print(f"Total Execution Time: {res.execution_time_sec}s")
    print(f"Audio Path: {res.audio_path}")
    print(f"Composition Image: {res.image_path}")
    print(f"Annotation JSON: {res.annotation_path}")
    print(f"Raw Video: {res.raw_video_path}")
    print(f"Final MP4 Video: {res.final_mp4_path}")

    print("\n--- MEDIA QA & TECHNICAL REPORT ---")
    report = res.media_report
    print(f"File Exists: {report.file_exists}")
    print(f"File Size: {report.file_size_bytes:,} bytes ({report.file_size_bytes / (1024*1024):.2f} MB)")
    print(f"Valid MP4: {report.is_valid_mp4}")
    print(f"Duration: {report.duration_sec}s")
    print(f"Video Stream: {report.video_codec} ({report.video_width}x{report.video_height} @ {report.fps}fps, {report.frame_count} frames)")
    print(f"Audio Stream: {report.audio_codec} ({report.audio_channels}ch @ {report.audio_sample_rate}Hz, {report.audio_duration_sec}s)")
    print(f"Audio-Video Duration Delta: {report.duration_delta}s (Compatible: {report.is_duration_compatible})")
    print(f"Corruption Detected: {report.is_corrupted}")
    print(f"Visual Invariants QA Pass: {report.visual_qa_pass}")
    print(f"  First Frame Mean Luminance: {report.first_frame_mean_luminance}")
    print(f"  Final Frame Mean Luminance: {report.final_frame_mean_luminance}")

    # Ghi báo cáo JSON
    qa_report_path = out_dir / "media_qa_report.json"
    qa_report_path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    print(f"\nQA Report saved to: {qa_report_path}")


if __name__ == "__main__":
    asyncio.run(main())
