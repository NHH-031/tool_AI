from __future__ import annotations

import re
from typing import List, Optional
from pydantic import BaseModel, Field


class CharacterAnchor(BaseModel):
    """
    Điểm neo đặc điểm nhân vật AI (Character Consistency Anchor):
    Giữ nhận diện ngoại hình (gương mặt, tóc, trang phục, kính, phong thái)
    và hạt giống ngẫu nhiên (seed) đồng nhất qua tất cả các phân cảnh kịch bản.
    """
    name: str = Field(default="Nhân vật chính", description="Tên hoặc danh xưng nhân vật")
    gender: str = Field(default="male", description="Giới tính: male, female, neutral, child")
    age_group: str = Field(default="adult", description="Độ tuổi: adult, young_adult, elderly, child")
    hair_style: str = Field(
        default="neat short black hair",
        description="Kiểu tóc và màu tóc đặc trưng"
    )
    facial_features: str = Field(
        default="friendly expressive face, neat appearance",
        description="Đặc điểm khuôn mặt (kính mắt, râu, lúm đồng tiền...)"
    )
    clothing: str = Field(
        default="smart casual navy blue jacket and white shirt",
        description="Trang phục đặc trưng cố định xuyên suốt câu chuyện"
    )
    accessories: str = Field(
        default="",
        description="Phụ kiện nhận diện (đồng hồ, cặp sách, mũ...)"
    )
    seed: Optional[int] = Field(
        default=42,
        description="Hạt giống sinh ảnh ngẫu nhiên cố định (lock seed)"
    )
    custom_notes: Optional[str] = Field(
        default="",
        description="Ghi chú nhận diện tùy chỉnh thêm của người dùng"
    )

    def build_anchor_prompt(self) -> str:
        """
        Tạo chuỗi prompt neo đặc điểm nhân vật chuẩn mực để gắn vào prompt phân cảnh.
        """
        parts = [f"Recurring main character named {self.name}"]

        # Giới tính & độ tuổi
        gender_word = "man" if self.gender == "male" else ("woman" if self.gender == "female" else "person")
        if self.age_group == "child":
            gender_word = "boy" if self.gender == "male" else ("girl" if self.gender == "female" else "child")
        elif self.age_group == "elderly":
            gender_word = f"elderly {gender_word}"
        elif self.age_group == "young_adult":
            gender_word = f"young adult {gender_word}"
        parts.append(f"a recognizable {gender_word}")

        # Tóc
        if self.hair_style:
            parts.append(f"with {self.hair_style.strip()}")

        # Mặt & phụ kiện
        if self.facial_features:
            parts.append(f"distinctive {self.facial_features.strip()}")

        # Trang phục
        if self.clothing:
            parts.append(f"wearing {self.clothing.strip()}")

        # Phụ kiện
        if self.accessories:
            parts.append(f"accompanied by {self.accessories.strip()}")

        if self.custom_notes:
            parts.append(self.custom_notes.strip())

        clause = ", ".join(parts)
        return (
            f"[Character Identity Consistency]: {clause}. "
            f"Strictly maintain this exact same character appearance, facial structure, haircut, and attire in 2D comic art style."
        )


def extract_character_from_script(script_text: str) -> Optional[CharacterAnchor]:
    """
    Tự động phát hiện nhân vật trung tâm từ nội dung kịch bản văn bản (tiếng Việt hoặc tiếng Anh).
    """
    if not script_text or len(script_text.strip()) < 10:
        return None

    text_lower = script_text.lower()

    # Nhận diện tên nhân vật tiêu biểu tiếng Việt
    name_match = re.search(r"\b(?:tôi là|nhân vật|anh|chị|cô|bác|ông|bạn)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+)", script_text)
    char_name = name_match.group(1) if name_match else "Nhân vật chính"

    # Nhận diện giới tính & nghề nghiệp
    gender = "male"
    age_group = "adult"
    clothing = "smart casual navy blue jacket and white shirt"
    facial_features = "friendly expressive face"

    if any(k in text_lower for k in ["chị", "cô", "bà", "nữ", "woman", "girl", "bà mẹ", "phụ nữ"]):
        gender = "female"
        clothing = "elegant teal blouse and tailored trousers"
        hair_style = "shoulder-length dark wavy hair"
    elif any(k in text_lower for k in ["bé", "em nhỏ", "cậu bé", "cô bé", "kid", "child"]):
        age_group = "child"
        clothing = "bright yellow t-shirt and denim overalls"
        hair_style = "short neat black hair"
    elif any(k in text_lower for k in ["cụ", "ông lão", "bà lão", "elderly"]):
        age_group = "elderly"
        clothing = "traditional cozy wool cardigan"
        hair_style = "neat gray hair"
        facial_features = "kind smiling eyes with spectacles"
    else:
        gender = "male"
        hair_style = "neat short black hair"

    # Kiểm tra kính mắt
    if any(k in text_lower for k in ["kính", "glasses", "spectacles"]):
        facial_features += ", round tortoiseshell spectacles"

    # Kiểm tra nghề nghiệp
    if any(k in text_lower for k in ["bác sĩ", "doctor", "y tá"]):
        clothing = "clean white medical doctor coat over blue scrubs"
    elif any(k in text_lower for k in ["kỹ sư", "engineer", "lập trình", "developer"]):
        clothing = "modern tech casual dark hoodie and denim jeans"
    elif any(k in text_lower for k in ["thầy", "giáo viên", "teacher"]):
        clothing = "formal collared shirt and knitted sweater vest"

    return CharacterAnchor(
        name=char_name,
        gender=gender,
        age_group=age_group,
        hair_style=hair_style,
        facial_features=facial_features,
        clothing=clothing,
        seed=42,
    )
