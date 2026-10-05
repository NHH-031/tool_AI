import asyncio
import json
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


async def main():
    print("=" * 80)
    print("STARTING MULTI-SCENE STORYBOARD GENERATION FOR: 'kể về chiến dịch Điện Biên Phủ'")
    print("=" * 80)

    out_dir = Path("output/dien_bien_phu_demo")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=640,  # Fast high-res preview
        ink_path="skeleton",
        color_fill="contour-wipe",
    )

    result = await pipeline.run(
        idea="kể về chiến dịch Điện Biên Phủ",
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

    # Validate output video
    mp4_p = Path(result.final_mp4_path)
    if mp4_p.exists():
        import av
        cont = av.open(str(mp4_p))
        v_dur = float(cont.streams.video[0].duration * cont.streams.video[0].time_base)
        a_dur = float(cont.streams.audio[0].duration * cont.streams.audio[0].time_base) if cont.streams.audio else 0.0
        print(f"Video duration: {v_dur:.2f}s, Audio duration: {a_dur:.2f}s")
        print(f"Video stream: {cont.streams.video[0].codec_context.name}, {cont.streams.video[0].width}x{cont.streams.video[0].height}")
        print(f"Audio stream: {cont.streams.audio[0].codec_context.name if cont.streams.audio else 'None'}")
        cont.close()


if __name__ == "__main__":
    asyncio.run(main())
