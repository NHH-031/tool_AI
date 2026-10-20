"""
Tạo kho thư viện Doodle SVG nét vẽ tay chuẩn Comic Whiteboard (#1A1A1A trên nền trong suốt/kem).
"""
from pathlib import Path

DOODLE_DIR = Path(__file__).resolve().parent.parent / "assets" / "doodles"
DOODLE_DIR.mkdir(parents=True, exist_ok=True)

DOODLES = {
    # 1. ARROWS
    "arrow-curved": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 30 150 Q 80 40 160 70" />
  <path d="M 125 50 L 165 72 L 140 105" />
</svg>""",

    "arrow-straight": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 30 100 L 165 100" />
  <path d="M 130 65 L 170 100 L 130 135" />
</svg>""",

    "arrow-zigzag": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 30 160 L 70 80 L 120 140 L 160 50" />
  <path d="M 135 45 L 165 48 L 160 80" />
</svg>""",

    # 2. HIGHLIGHTS & FRAMES
    "circle-highlight": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#FFE600" stroke-width="12" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 100 25 C 150 20 185 60 180 110 C 175 160 135 185 85 180 C 40 175 15 135 25 85 C 35 40 75 22 115 28" />
</svg>""",

    "box-highlight": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#E05A47" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 30 45 Q 100 35 170 42 Q 175 105 168 165 Q 95 172 32 163 Q 25 100 30 45" />
</svg>""",

    "speech-bubble": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 35 45 Q 100 35 165 45 Q 175 95 165 135 Q 105 145 65 140 L 35 175 L 45 135 Q 25 95 35 45 Z" fill="#F5EBD7" />
</svg>""",

    "underline-scribble": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#E67E22" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 25 110 Q 55 95 85 115 T 145 105 T 180 115" />
  <path d="M 35 135 Q 70 120 105 135 T 165 125" />
</svg>""",

    # 3. SYMBOLS
    "lightbulb": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 70 130 C 50 115 40 90 45 65 C 55 35 85 20 115 25 C 145 30 165 60 155 90 C 150 110 135 125 125 130 Z" fill="#FFE600" fill-opacity="0.3" />
  <path d="M 75 145 L 125 145" />
  <path d="M 80 160 L 120 160" />
  <path d="M 90 175 L 110 175" />
  <path d="M 100 10 L 100 2" />
  <path d="M 160 30 L 170 20" />
  <path d="M 35 30 L 25 20" />
</svg>""",

    "star-sparkle": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="#FFE600" stroke="#1A1A1A" stroke-width="7" stroke-linejoin="round">
  <polygon points="100,20 125,75 185,80 140,120 155,180 100,150 45,180 60,120 15,80 75,75" />
</svg>""",

    "checkmark-hand": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#10B981" stroke-width="12" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 35 110 L 80 155 L 170 50" />
</svg>""",

    "cross-hand": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#E53935" stroke-width="12" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 45 45 L 155 155" />
  <path d="M 155 45 L 45 155" />
</svg>""",

    "question-mark": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#3498DB" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 65 65 C 65 35 135 35 135 75 C 135 105 100 110 100 135" />
  <circle cx="100" cy="165" r="4" fill="#3498DB" stroke="#3498DB" stroke-width="6" />
</svg>""",

    "exclamation-mark": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#FF5500" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 100 40 L 100 125" />
  <circle cx="100" cy="165" r="4" fill="#FF5500" stroke="#FF5500" stroke-width="6" />
</svg>""",

    # 4. BUSINESS & GROWTH
    "chart-up": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 30 170 L 175 170" />
  <path d="M 30 170 L 30 25" />
  <path d="M 45 140 L 80 100 L 120 120 L 165 45" stroke="#10B981" stroke-width="10" />
  <path d="M 140 45 L 168 45 L 165 72" stroke="#10B981" stroke-width="10" />
</svg>""",

    "target-bullseye": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="100" cy="100" r="70" />
  <circle cx="100" cy="100" r="45" stroke="#E53935" stroke-width="8" />
  <circle cx="100" cy="100" r="20" fill="#E53935" />
  <path d="M 100 15 L 100 40" />
  <path d="M 100 160 L 100 185" />
  <path d="M 15 100 L 40 100" />
  <path d="M 160 100 L 185 100" />
</svg>""",

    "trophy-cup": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" stroke="#1A1A1A" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 55 45 L 145 45 L 135 110 C 130 130 115 140 100 140 C 85 140 70 130 65 110 Z" fill="#FFE600" fill-opacity="0.3" />
  <path d="M 55 60 C 35 60 30 85 45 95 C 55 100 62 100 65 95" />
  <path d="M 145 60 C 165 60 170 85 155 95 C 145 100 138 100 135 95" />
  <path d="M 100 140 L 100 170" />
  <path d="M 60 170 L 140 170" stroke-width="10" />
</svg>""",
}

def main():
    for name, content in DOODLES.items():
        out_path = DOODLE_DIR / f"{name}.svg"
        out_path.write_text(content.strip(), encoding="utf-8")
        print(f"Created doodle: {out_path.name}")

if __name__ == "__main__":
    main()
