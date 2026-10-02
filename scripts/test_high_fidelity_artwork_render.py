import json
import subprocess
from pathlib import Path
import cv2
import numpy as np

def test_render_high_fidelity_scenes():
    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / "output" / "high_fidelity_demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    hand_path = repo_root / "assets" / "drawing-hand.png"
    render_script = repo_root / "scripts" / "render_stream_whiteboard.py"
    py_exe = repo_root / ".venv" / "Scripts" / "python.exe"

    scenes = [
        {
            "name": "astronaut_mars",
            "img": repo_root / "assets" / "artwork" / "generated" / "astronaut_mars.png",
            "duration_ms": 7000,
            "elements": [
                {
                    "id": "spacecraft",
                    "label": "Tàu đổ bộ không gian",
                    "sequence": 1,
                    "narrativeRole": "Tàu vũ trụ đáp xuống",
                    "subtitle": "Tàu vũ trụ đáp xuống bề mặt Sao Hỏa.",
                    "type": "structure",
                    "region": {"x": 0, "y": 0, "width": 650, "height": 900},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 200,
                        "durationMs": 2500,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [300, 150], "end": [300, 750], "easing": "easeInOut"}
                },
                {
                    "id": "astronaut",
                    "label": "Phi hành gia",
                    "sequence": 2,
                    "narrativeRole": "Phi hành gia bước ra",
                    "subtitle": "Một phi hành gia bước ra khỏi tàu vũ trụ.",
                    "type": "character",
                    "region": {"x": 580, "y": 200, "width": 450, "height": 700},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 2800,
                        "durationMs": 2400,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [800, 250], "end": [800, 750], "easing": "easeInOut"}
                },
                {
                    "id": "mars_surface",
                    "label": "Bề mặt Sao Hỏa",
                    "sequence": 3,
                    "narrativeRole": "Địa hình đất đá và miệng hố",
                    "subtitle": "Đặt chân lên bề mặt đất đá gồ ghề của Sao Hỏa.",
                    "type": "environment",
                    "region": {"x": 0, "y": 600, "width": 1920, "height": 480},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 5300,
                        "durationMs": 1400,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [960, 650], "end": [960, 950], "easing": "easeInOut"}
                }
            ]
        },
        {
            "name": "cat_palm",
            "img": repo_root / "assets" / "artwork" / "generated" / "cat_palm.png",
            "duration_ms": 6500,
            "elements": [
                {
                    "id": "palm_tree",
                    "label": "Cây cau",
                    "sequence": 1,
                    "narrativeRole": "Bối cảnh cây cau thẳng đứng",
                    "subtitle": "Cây cau vươn cao với tán lá xanh mướt.",
                    "type": "structure",
                    "region": {"x": 650, "y": 20, "width": 650, "height": 1040},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 200,
                        "durationMs": 3200,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [960, 100], "end": [960, 950], "easing": "easeInOut"}
                },
                {
                    "id": "cat_climbing",
                    "label": "Mèo leo trèo",
                    "sequence": 2,
                    "narrativeRole": "Hành động chú mèo bám thân cây",
                    "subtitle": "Con mèo tinh nghịch đang leo thoăn thoắt lên cây cau.",
                    "type": "character",
                    "region": {"x": 680, "y": 400, "width": 350, "height": 420},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 3500,
                        "durationMs": 2500,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [850, 450], "end": [850, 750], "easing": "easeInOut"}
                }
            ]
        },
        {
            "name": "dog_ball",
            "img": repo_root / "assets" / "artwork" / "generated" / "dog_ball.png",
            "duration_ms": 6000,
            "elements": [
                {
                    "id": "dog_running",
                    "label": "Chó chạy sải bước",
                    "sequence": 1,
                    "narrativeRole": "Chú chó phấn khích rượt đuổi",
                    "subtitle": "Con chó chạy thật nhanh trên sân cỏ.",
                    "type": "character",
                    "region": {"x": 100, "y": 180, "width": 1100, "height": 750},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 200,
                        "durationMs": 3200,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [600, 250], "end": [600, 750], "easing": "easeInOut"}
                },
                {
                    "id": "soccer_ball",
                    "label": "Quả bóng nảy",
                    "sequence": 2,
                    "narrativeRole": "Mục tiêu quả bóng lăn phía trước",
                    "subtitle": "Chạy theo quả bóng đang lăn tròn.",
                    "type": "object",
                    "region": {"x": 1050, "y": 500, "width": 800, "height": 450},
                    "reveal": {
                        "direction": "top_to_bottom",
                        "startMs": 3500,
                        "durationMs": 2000,
                        "maskPaddingPx": 22,
                        "protectedRegions": []
                    },
                    "handPath": {"start": [1400, 600], "end": [1600, 750], "easing": "easeInOut"}
                }
            ]
        }
    ]

    for sc in scenes:
        name = sc["name"]
        img_p = sc["img"]
        ann_p = output_dir / f"{name}.annotation.json"
        mp4_p = output_dir / f"{name}_high_fidelity.mp4"

        ann_data = {
            "sceneId": name,
            "canvas": {"width": 1920, "height": 1080},
            "storyBasis": f"High fidelity comic whiteboard render for {name}",
            "sceneDurationMs": sc["duration_ms"],
            "elements": sc["elements"]
        }
        ann_p.write_text(json.dumps(ann_data, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"\n=======================================================")
        print(f"RENDERING HIGH-FIDELITY SCENE: {name}")
        print(f"Image: {img_p}")
        print(f"Annotation: {ann_p}")
        print(f"Output MP4: {mp4_p}")

        cmd = [
            str(py_exe),
            str(render_script),
            str(img_p),
            str(ann_p),
            str(mp4_p),
            str(hand_path),
            "--ink-path", "skeleton",
            "--color-fill", "contour-wipe",
            "--fps", "30",
            "--cap-long-edge", "1920",
            "--total-ms", str(sc["duration_ms"])
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            print(f"FAILED {name}: {res.stderr}")
        else:
            print(f"SUCCESS: Rendered {mp4_p} (size={mp4_p.stat().st_size} bytes)")

            # Extract 5 progression frames
            cap = cv2.VideoCapture(str(mp4_p))
            total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for pct in [0, 25, 50, 75, 100]:
                fi = int(round(pct / 100.0 * (total_f - 1)))
                cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
                ret, frame = cap.read()
                if ret:
                    frame_path = output_dir / f"{name}_frame_{pct}pct.png"
                    cv2.imwrite(str(frame_path), frame)
                    print(f"  Saved {pct}% frame: {frame_path}")
            cap.release()

if __name__ == "__main__":
    test_render_high_fidelity_scenes()
