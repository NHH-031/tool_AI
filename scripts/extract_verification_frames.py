import cv2
from pathlib import Path

video_path = Path("output/monkey_banana_e2e/scene_default_final.mp4")
artifact_dir = Path(r"C:\Users\ACER\.gemini\antigravity-ide\brain\ae80ef99-83b9-425a-8f28-d25759118500")
out_dir = Path("output/verification_frames")
out_dir.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(video_path))
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

print(f"Video {video_path}: FPS={fps}, Total Frames={total_frames}, Duration={duration:.2f}s")

# Extract key timestamps
sample_times = [
    ("first_frame", 0.0),
    ("mid_frame_1s", 1.0),
    ("mid_frame_2_5s", 2.5),
    ("mid_frame_4s", 4.0),
    ("final_frame", max(0.0, duration - 0.1)),
]

for name, t in sample_times:
    frame_idx = min(total_frames - 1, int(t * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        local_out = out_dir / f"{name}.png"
        cv2.imwrite(str(local_out), frame)
        artifact_out = artifact_dir / f"phase10_1_{name}.png"
        cv2.imwrite(str(artifact_out), frame)
        print(f"Extracted {name} at frame {frame_idx} (t={t:.2f}s) -> {local_out}")

cap.release()
print("All verification frames extracted successfully.")
