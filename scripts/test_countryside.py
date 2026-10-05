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
    print("STARTING COUNTRYSIDE SCENARIO TEST: Làng quê Việt Nam mùa lúa chín")
    print("=" * 80)

    out_dir = Path("output/countryside_demo")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=640,
        ink_path="skeleton",
        color_fill="contour-wipe",
    )

    result = await pipeline.run(
        idea="Một ngày mùa màng rộn rã ở làng quê Việt Nam, người nông dân đội nón lá cấy lúa bên căn nhà tranh",
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
    print(f"Script: {result.script_text}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
