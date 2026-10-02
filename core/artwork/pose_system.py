from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PoseGuidance(BaseModel):
    """Đặc tả tư thế hình học và giải phẫu cho nhân vật trong phong cách Whiteboard."""
    pose_name: str = Field(description="Tên tư thế (running, climbing, planting, etc.)")
    silhouette_notes: str = Field(description="Đặc điểm nhận diện hình bóng (silhouette)")
    limbs_guidance: str = Field(description="Hướng dẫn cách đặt các chi (tay/chân/paws)")
    head_expression_guidance: str = Field(description="Hướng dẫn hướng nhìn và nét biểu cảm")
    contact_notes: str = Field(description="Điểm tiếp xúc vật lý với đối tượng tương tác hoặc mặt đất")


class CharacterPoseSystem:
    """
    Hệ thống tư thế nhân vật tổng quát (Generic Pose System).
    Không giới hạn cho bất kỳ loài nào (người, mèo, chó, khỉ, chim, phi hành gia,...).
    Cung cấp đặc tả tư thế động lực học cho từng hành động.
    """

    GENERIC_POSES: Dict[str, PoseGuidance] = {
        "climbing": PoseGuidance(
            pose_name="climbing",
            silhouette_notes="Thân thể uốn cong hướng lên, lưng gồng tạo lực kéo, đuôi giữ thăng bằng",
            limbs_guidance="Các chi phía trước vươn cao bám chặt, các chi phía sau co đạp đẩy thân lên",
            head_expression_guidance="Đầu hướng ngước lên trên theo hướng leo, mắt tập trung",
            contact_notes="Các bàn chân/móng vuốt tiếp xúc vật lý trực tiếp với thân cây/vách đá",
        ),
        "running": PoseGuidance(
            pose_name="running",
            silhouette_notes="Thân nghiêng về phía trước, dáng sải dài tạo cảm giác tốc độ chuyển động",
            limbs_guidance="Chân trước vươn tối đa về phía trước, chân sau đạp mạnh về sau",
            head_expression_guidance="Đầu hướng thẳng về phía mục tiêu rượt đuổi, tai/tóc bay về sau",
            contact_notes="Chỉ một hoặc hai chi chạm đất, tạo cảm giác lơ lửng sải bước",
        ),
        "planting": PoseGuidance(
            pose_name="planting",
            silhouette_notes="Thân gập cong hoặc quỳ gối tự nhiên hướng sát mặt đất",
            limbs_guidance="Hai tay khum nhẹ nâng đỡ rễ cây non cắm vào luống đất tơi xốp",
            head_expression_guidance="Đầu cúi xuống chăm chú nhìn vào gốc cây non đang trồng",
            contact_notes="Bàn chân hoặc đầu gối tựa chắc trên mặt đất, tay chạm vào đất/cây non",
        ),
        "orbiting": PoseGuidance(
            pose_name="orbiting",
            silhouette_notes="Đối tượng nghiêng theo trục elip quỹ đạo, có đường hướng tâm",
            limbs_guidance="Không áp dụng (với thiên thể: trục nghiêng và các đường vĩ tuyến/kinh tuyến)",
            head_expression_guidance="Hướng di chuyển tuần hoàn theo chiều mũi tên quỹ đạo",
            contact_notes="Tâm đối tượng nằm chính xác trên cung elip bao quanh vật thể trung tâm",
        ),
        "stepping": PoseGuidance(
            pose_name="stepping",
            silhouette_notes="Dáng bước đi thận trọng, chân sau trụ vững, chân trước nâng đặt xuống mặt đất",
            limbs_guidance="Hai tay giữ thăng bằng hoặc bám vào tay vịn/thang tàu, một chân đặt chạm đất",
            head_expression_guidance="Mũ bảo hộ/khuôn mặt hướng khám phá không gian xung quanh",
            contact_notes="Bàn chân đặt lên bề mặt địa hình gồ ghề (sao Hỏa, mặt trăng)",
        ),
        "standing": PoseGuidance(
            pose_name="standing",
            silhouette_notes="Dáng đứng thẳng tự nhiên, cân đối hai bên trọng tâm",
            limbs_guidance="Chân đứng vững trên mặt đất, tay buông thõng tự nhiên hoặc vẫy chào",
            head_expression_guidance="Mặt hướng về người xem hoặc góc 3/4 thân thiện",
            contact_notes="Hai chân chạm đều mặt đất",
        ),
        "sitting": PoseGuidance(
            pose_name="sitting",
            silhouette_notes="Thân hạ thấp, mông tựa lên mặt phẳng hoặc mô đất, lưng thẳng thư thái",
            limbs_guidance="Chân xếp gọn hoặc co gối, tay đặt lên đùi hoặc chống xuống đất",
            head_expression_guidance="Khuôn mặt thư giãn, hướng nhìn quan sát",
            contact_notes="Phần thân dưới tiếp xúc hoàn toàn với bề mặt nâng đỡ",
        ),
        "walking": PoseGuidance(
            pose_name="walking",
            silhouette_notes="Dáng di chuyển nhẹ nhàng, thân hơi nghiêng",
            limbs_guidance="Một chân trước một chân sau sải vừa phải, hai tay vung so le",
            head_expression_guidance="Nhìn về phía trước theo hướng đi",
            contact_notes="Gót chân trước chạm đất, mũi chân sau chuẩn bị nhấc lên",
        ),
        "jumping": PoseGuidance(
            pose_name="jumping",
            silhouette_notes="Thân bung mở trên không trung, trọng tâm nhấc bổng khỏi mặt đất",
            limbs_guidance="Chân co gập bật nhảy, tay vung cao",
            head_expression_guidance="Khuôn mặt phấn khích hoặc tập trung cao độ",
            contact_notes="Hoàn toàn không chạm đất, có vệt nét gạch biểu thị lực đẩy",
        ),
        "holding": PoseGuidance(
            pose_name="holding",
            silhouette_notes="Thân người hoặc động vật ôm giữ hoặc cầm vật phẩm",
            limbs_guidance="Ngón tay/móng vuốt quặp chặt quanh vật phẩm",
            head_expression_guidance="Mắt nhìn vào vật đang cầm",
            contact_notes="Bàn tay bao quanh bề mặt của vật thể",
        ),
        "flying": PoseGuidance(
            pose_name="flying",
            silhouette_notes="Thân ngang song song luồng gió, cánh hoặc thân trải rộng lướt đi",
            limbs_guidance="Cánh đập hoặc xòe rộng, chân co sát bụng",
            head_expression_guidance="Đầu vươn thẳng theo luồng bay",
            contact_notes="Không chạm đất, có nét lượn sóng biểu thị khí động học",
        ),
    }

    @classmethod
    def get_pose(cls, action_or_pose: str) -> PoseGuidance:
        """Lấy đặc tả tư thế cho một hành động hoặc tên tư thế."""
        key = (action_or_pose or "").strip().lower()
        # Tra cứu trực tiếp
        if key in cls.GENERIC_POSES:
            return cls.GENERIC_POSES[key]

        # Tra cứu theo ánh xạ hành động
        action_map = {
            "leo": "climbing",
            "trèo": "climbing",
            "climb": "climbing",
            "chạy": "running",
            "đuổi": "running",
            "run": "running",
            "chase": "running",
            "trồng": "planting",
            "plant": "planting",
            "quay": "orbiting",
            "xoay": "orbiting",
            "orbit": "orbiting",
            "bước": "stepping",
            "step": "stepping",
            "đi": "walking",
            "walk": "walking",
            "nhảy": "jumping",
            "jump": "jumping",
            "bay": "flying",
            "fly": "flying",
            "cầm": "holding",
            "nắm": "holding",
            "hold": "holding",
            "ngồi": "sitting",
            "sit": "sitting",
            "đứng": "standing",
            "stand": "standing",
        }
        for act_word, mapped_pose in action_map.items():
            if act_word in key:
                return cls.GENERIC_POSES[mapped_pose]

        return cls.GENERIC_POSES["standing"]
