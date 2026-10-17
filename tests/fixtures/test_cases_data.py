"""Dữ liệu chuẩn hóa cho 5 Test Cases của Phase 04.

Được chuyển vào core/pipeline/reference_cases.py để production code không phụ thuộc tests.
File này re-export toàn bộ để đảm bảo 100% backward compatibility cho existing tests.
"""
from __future__ import annotations

from core.pipeline.reference_cases import (
    CANVAS_1080P,
    get_case_1_dog_ball,
    get_case_2_teacher_math,
    get_case_3_temperature_molecules,
    get_case_4_inflation,
    get_case_5_monkey_tree_banana,
)

__all__ = [
    "CANVAS_1080P",
    "get_case_1_dog_ball",
    "get_case_2_teacher_math",
    "get_case_3_temperature_molecules",
    "get_case_4_inflation",
    "get_case_5_monkey_tree_banana",
]
