from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np


def hex_to_bgr(hex_color: str) -> np.ndarray:
    digits = hex_color.lstrip("#")
    if len(digits) != 6:
        return np.array([215, 235, 245], dtype=np.uint8)  # Fallback #F5EBD7
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


class WhiteboardEraserTransition:
    """
    Hiệu ứng chuyển cảnh bằng giẻ lau / miếng xóa bảng trắng (Whiteboard Eraser Transition):
    Mô phỏng bàn tay cầm miếng xóa bảng quét ngang màn hình, lau sạch các nét vẽ cũ
    để lại nền giấy màu kem ấm #F5EBD7 tinh khôi trước khi phân cảnh mới bắt đầu.
    """

    def __init__(
        self,
        eraser_hand_path: Optional[Path] = None,
        canvas_hex: str = "#F5EBD7",
        fps: int = 30,
        duration_sec: float = 1.0,
    ):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.eraser_hand_path = (
            eraser_hand_path
            or (self.root_dir / "assets" / "drawing-tools" / "hand-eraser.png")
        )
        self.canvas_bgr = hex_to_bgr(canvas_hex)
        self.fps = fps
        self.duration_sec = duration_sec

        # Nạp và chuẩn bị ảnh bàn tay cầm miếng lau bảng
        self.hand_img, self.hand_mask = self._load_eraser_hand()

    def _load_eraser_hand(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if not self.eraser_hand_path.exists():
            return None, None

        raw = cv2.imread(str(self.eraser_hand_path), cv2.IMREAD_UNCHANGED)
        if raw is None:
            return None, None

        if raw.shape[2] == 4:
            hand = raw[:, :, :3]
            mask = raw[:, :, 3].astype(np.float32) / 255.0
        else:
            hand = raw
            mask = np.ones((raw.shape[0], raw.shape[1]), dtype=np.float32)

        return hand, mask

    def generate_transition_frames(
        self,
        frame_from: np.ndarray,
        frame_to: Optional[np.ndarray] = None,
        target_fps: Optional[int] = None,
        target_duration_sec: Optional[float] = None,
    ) -> List[np.ndarray]:
        """
        Sinh chuỗi khung hình BGR của hiệu ứng lau bảng chuyển cảnh.
        """
        h, w = frame_from.shape[:2]
        fps = target_fps or self.fps
        dur = target_duration_sec or self.duration_sec
        num_frames = max(2, int(round(fps * dur)))

        # Nếu không có frame_to, dùng nền giấy kem #F5EBD7
        if frame_to is None:
            bg_target = np.full((h, w, 3), self.canvas_bgr, dtype=np.uint8)
        else:
            if frame_to.shape[:2] != (h, w):
                bg_target = cv2.resize(frame_to, (w, h), interpolation=cv2.INTER_LANCZOS4)
            else:
                bg_target = frame_to.copy()

        # Chuẩn bị mặt nạ xóa (erased mask: False = chưa xóa, True = đã lau sạch)
        erased_mask = np.zeros((h, w), dtype=bool)

        # Chuẩn bị kích thước bàn tay phù hợp độ phân giải màn hình
        target_hand_h = int(h * 0.48)
        if self.hand_img is not None and self.hand_mask is not None:
            scale = target_hand_h / float(self.hand_img.shape[0])
            new_w = max(1, int(round(self.hand_img.shape[1] * scale)))
            eraser_scaled = cv2.resize(self.hand_img, (new_w, target_hand_h), interpolation=cv2.INTER_AREA)
            mask_scaled = cv2.resize(self.hand_mask, (new_w, target_hand_h), interpolation=cv2.INTER_AREA)
            pad_contact_x = int(new_w * 0.22)
            pad_contact_y = int(target_hand_h * 0.16)
        else:
            eraser_scaled, mask_scaled = None, None
            pad_contact_x, pad_contact_y = 50, 50

        # Quỹ đạo lau bảng: Quét uốn lượn 2-3 đường zic-zắc tự nhiên từ trái qua phải
        frames: List[np.ndarray] = []
        wipe_radius = int(h * 0.22)  # Bán kính vùng làm sạch mỗi lần lướt qua

        for fi in range(num_frames):
            prog = fi / float(num_frames - 1) if num_frames > 1 else 1.0

            # Quỹ đạo bàn tay: Di chuyển ngang từ x=-100 đến x=w+150
            # kèm dao động sóng sine lên xuống mô phỏng động tác tay người
            hand_x = int(-120 + prog * (w + 260))
            wave_freq = 2.5 * math.pi
            hand_y = int(h * 0.45 + math.sin(prog * wave_freq) * (h * 0.32))

            # Tâm của mặt tiếp xúc giẻ lau
            cx = hand_x
            cy = hand_y

            # Cập nhật mặt nạ đã xóa
            y_indices, x_indices = np.ogrid[:h, :w]
            dist_sq = (x_indices - cx) ** 2 + (y_indices - cy) ** 2
            # Vùng lau sạch có dạng elip ngang mô phỏng hình dạng miếng xóa bảng
            ellipse_dist = ((x_indices - cx) / 1.3) ** 2 + ((y_indices - cy) / 0.85) ** 2
            current_wipe = ellipse_dist <= (wipe_radius ** 2)
            # Lau sạch dần về phía bên trái đã đi qua
            left_swept = (x_indices < cx - int(wipe_radius * 0.5))
            erased_mask |= current_wipe | left_swept

            # Hợp nhất lớp ảnh gốc và ảnh đích
            comp = frame_from.copy()
            comp[erased_mask] = bg_target[erased_mask]

            # Thêm hiệu ứng vệt bụi phấn / mực khô mờ thoáng qua tại mép giẻ lau
            edge_band = (ellipse_dist > (wipe_radius * 0.8) ** 2) & (ellipse_dist <= (wipe_radius * 1.08) ** 2)
            if np.any(edge_band):
                noise = np.random.normal(0, 8, comp.shape).astype(np.int16)
                blend_edge = np.clip(comp.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                comp[edge_band] = cv2.addWeighted(comp[edge_band], 0.65, blend_edge[edge_band], 0.35, 0)

            # Đè bàn tay cầm miếng xóa bảng lên khung hình
            if eraser_scaled is not None and mask_scaled is not None:
                bx = cx - pad_contact_x
                by = cy - pad_contact_y
                ew, eh = eraser_scaled.shape[1], eraser_scaled.shape[0]

                x0 = max(0, bx)
                y0 = max(0, by)
                x1 = min(w, bx + ew)
                y1 = min(h, by + eh)

                if x1 > x0 and y1 > y0:
                    sx0 = x0 - bx
                    sy0 = y0 - by
                    sx1 = sx0 + (x1 - x0)
                    sy1 = sy0 + (y1 - y0)

                    m = mask_scaled[sy0:sy1, sx0:sx1, None]
                    hand_patch = eraser_scaled[sy0:sy1, sx0:sx1]
                    comp[y0:y1, x0:x1] = (
                        comp[y0:y1, x0:x1].astype(np.float32) * (1.0 - m)
                        + hand_patch.astype(np.float32) * m
                    ).astype(np.uint8)

            frames.append(comp)

        return frames

    def render_transition_video(
        self,
        frame_from: np.ndarray,
        frame_to: Optional[np.ndarray],
        output_path: Path,
    ) -> Path:
        """
        Kết xuất trực tiếp hiệu ứng chuyển cảnh ra file MP4.
        """
        frames = self.generate_transition_frames(frame_from, frame_to)
        if not frames:
            raise RuntimeError("Không thể tạo các khung hình chuyển cảnh.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, self.fps, (w, h))

        for f in frames:
            writer.write(f)
        writer.release()

        return output_path
