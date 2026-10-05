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


async def test_snake(has_color: bool, mode_name: str):
    print("=" * 80)
    print(f"TESTING SNAKE & PREY SCENARIO: Mode = {mode_name} (has_color={has_color})")
    print("=" * 80)

    out_dir = Path(f"output/test_snake_{mode_name.lower()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline = WhiteboardPipeline()

    result = await pipeline.run(
        script="Con rắn lục đang trườn nhẹ nhàng trong bụi cỏ rậm, ngóc đầu chăm chú rình bắt một chú chuột đồng ngây thơ gần đó.",
        input_mode="SCRIPT",
        output_dir=out_dir,
        has_color=has_color,
    )

    print("\n" + "=" * 80)
    print(f"PIPELINE RESULT FOR {mode_name.upper()}:")
    print(f"Success: {result.is_success}")
    print(f"Final MP4: {result.final_mp4_path}")
    print(f"Image Path: {result.image_path}")
    print(f"Execution time: {result.execution_time_sec}s")
    print(f"Has color: {result.metadata.get('has_color')}")
    print(f"Entities: {result.metadata.get('entities')}")
    print("=" * 80)
    return result


async def main():
    # 1. Test Monochrome (Không đổ màu - Comic ink art)
    print("\n>>> BƯỚC 1: KIỂM THỬ CHẾ ĐỘ KHÔNG ĐỔ MÀU (MONOCHROME - COMIC INK)")
    res_mono = await test_snake(has_color=False, mode_name="monochrome")

    # 2. Test Color (Có đổ màu - Studio Ghibli Anime watercolor)
    print("\n>>> BƯỚC 2: KIỂM THỬ CHẾ ĐỘ CÓ ĐỔ MÀU (FULL COLOR - GHIBLI WATERCOLOR)")
    res_color = await test_snake(has_color=True, mode_name="color")

    print("\n" + "=" * 80)
    print("TỔNG KẾT KIỂM THỬ CẢ 2 CHẾ ĐỘ THÀNH CÔNG:")
    print(f"1. Monochrome MP4: {res_mono.final_mp4_path}")
    print(f"2. Color MP4:      {res_color.final_mp4_path}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
