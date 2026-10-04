import json
import subprocess
from pathlib import Path
import cv2

def render_option4_trial():
    repo_root = Path("d:/Tool")
    output_dir = repo_root / "output" / "option4_trial"
    img_path = output_dir / "option4_astronaut_cleaned_1080p.png"
    ann_path = output_dir / "option4_astronaut.annotation.json"
    mp4_path = output_dir / "option4_astronaut_trial.mp4"
    hand_path = repo_root / "assets" / "drawing-hand.png"
    render_script = repo_root / "scripts" / "render_stream_whiteboard.py"
    py_exe = repo_root / ".venv" / "Scripts" / "python.exe"

    ann_data = {
        "sceneId": "option4_astronaut",
        "canvas": {"width": 1920, "height": 1080},
        "storyBasis": "Trial render of Option 4 (Local SD 1.5)",
        "sceneDurationMs": 7000,
        "elements": [
            {
                "id": "equipment_left",
                "label": "Trạm điều khiển bên trái",
                "sequence": 1,
                "narrativeRole": "Thiết bị không gian cánh trái",
                "subtitle": "Hệ thống trạm đổ bộ và pin năng lượng mặt trời.",
                "type": "structure",
                "region": {"x": 0, "y": 0, "width": 750, "height": 750},
                "reveal": {
                    "direction": "top_to_bottom",
                    "startMs": 200,
                    "durationMs": 2200,
                    "maskPaddingPx": 22,
                    "protectedRegions": []
                },
                "handPath": {"start": [350, 150], "end": [350, 700], "easing": "easeInOut"}
            },
            {
                "id": "astronaut_center",
                "label": "Phi hành gia trung tâm",
                "sequence": 2,
                "narrativeRole": "Phi hành gia",
                "subtitle": "Phi hành gia đứng tại buồng trung tâm.",
                "type": "character",
                "region": {"x": 750, "y": 100, "width": 420, "height": 700},
                "reveal": {
                    "direction": "top_to_bottom",
                    "startMs": 2500,
                    "durationMs": 2200,
                    "maskPaddingPx": 22,
                    "protectedRegions": []
                },
                "handPath": {"start": [960, 200], "end": [960, 750], "easing": "easeInOut"}
            },
            {
                "id": "equipment_right_ground",
                "label": "Trạm bên phải và mặt đất",
                "sequence": 3,
                "narrativeRole": "Cánh phải và nền đất",
                "subtitle": "Hoàn tất thiết bị trạm và nền Sao Hỏa.",
                "type": "structure",
                "region": {"x": 1150, "y": 0, "width": 770, "height": 1080},
                "reveal": {
                    "direction": "top_to_bottom",
                    "startMs": 4800,
                    "durationMs": 2000,
                    "maskPaddingPx": 22,
                    "protectedRegions": []
                },
                "handPath": {"start": [1500, 200], "end": [1500, 900], "easing": "easeInOut"}
            }
        ]
    }
    ann_path.write_text(json.dumps(ann_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    cmd = [
        str(py_exe),
        str(render_script),
        str(img_path),
        str(ann_path),
        str(mp4_path),
        str(hand_path),
        "--ink-path", "skeleton",
        "--color-fill", "contour-wipe",
        "--fps", "30",
        "--cap-long-edge", "1920",
        "--total-ms", "7000"
    ]
    
    print("Running render_stream_whiteboard for Option 4...")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"Render failed: {res.stderr}")
        return False
        
    print(f"SUCCESS: Rendered {mp4_path}")
    
    # Extract progress frames (0%, 25%, 50%, 75%, 100%)
    cap = cv2.VideoCapture(str(mp4_path))
    total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for pct in [0, 25, 50, 75, 100]:
        fi = int(round(pct / 100.0 * (total_f - 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if ret:
            f_p = output_dir / f"option4_frame_{pct}pct.png"
            cv2.imwrite(str(f_p), frame)
            print(f"Saved {pct}% frame: {f_p}")
    cap.release()
    return True

if __name__ == "__main__":
    render_option4_trial()
