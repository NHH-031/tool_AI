import asyncio
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
    print("=" * 80)
    print("STARTING TIKTOK REFERENCE SCENARIO TEST: Cô bé áo vàng nón lá & chú cún con")
    print("TikTok Reference: https://www.tiktok.com/@hungnpv/video/7689464882944625940")
    print("=" * 80)

    out_dir = Path("output/tiktok_reference_demo")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=640,
        ink_path="skeleton",
        color_fill="contour-wipe",
        draw_ratio=0.40,
        max_draw_ms=2500,
    )

    result = await pipeline.run(
        idea="Một cô bé nhỏ mặc váy vàng đội nón lá cùng chú cún con dạo bước dưới bóng cây cổ thụ trên cánh đồng hoa rực rỡ nắng vàng",
        input_mode="IDEA",
        output_dir=out_dir,
        render_config=cfg,
    )

    print("\n" + "=" * 80)
    print("PIPELINE RESULT:")
    print(f"Success: {result.is_success}")
    print(f"Final MP4: {result.final_mp4_path}")
    print(f"Execution time: {result.execution_time_sec}s")
    print(f"Scenes count: {result.metadata.get('scenes_count')}")
    print(f"Script:\n{result.script_text}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
