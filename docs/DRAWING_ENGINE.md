# Drawing Stroke Engine

## 1. Overview & Core Philosophy

The **Drawing Stroke Engine** transforms visual SVG assets into authentic, ordered vector strokes and drawable timeline units.
In strict compliance with the core whiteboard animation principles:
- **NO simple SVG display** (`show SVG`).
- **NO alpha fading** (`fade image`).
- **NO crude image reveal masks** (`reveal image mask`).

Instead, the engine performs true procedural vector stroke extraction, semantic grouping, natural artist stroke ordering, continuous hand tip trajectory calculation, and keyframe-based progressive stroke drawing animations.

```
SVG Asset
   │
   ▼
[SVGStrokeExtractor] ──> Extracts geometry, samples Bézier curves, calculates lengths & endpoints
   │
   ▼
[StrokeOrderPlanner] ──> Orders strokes hierarchically (Trunk -> Branches -> Leaves, Body -> Limbs)
   │
   ▼
[HandPathPlanner]    ──> Maps real-time (x(t), y(t)) nib positions, pen-down drawing & pen-up travel
   │
   ▼
[DebugRenderer]      ──> Generates Modes A, B, C, D, E & HTML Scrubber Visual Debugger
```

---

## 2. Drawing Stroke Data Model

Defined in [`core/schemas/drawing.py`](file:///d:/Tool/core/schemas/drawing.py) with full camelCase and snake_case alias interoperability:

```python
class DrawingStroke(BaseModel):
    stroke_id: str = Field(alias="strokeId")
    asset_id: str = Field(alias="assetId")
    path: str
    order: int
    duration: float
    start_point: Tuple[float, float] = Field(alias="startPoint")
    end_point: Tuple[float, float] = Field(alias="endPoint")
    semantic_purpose: str = Field(alias="semanticPurpose")
    points: List[Tuple[float, float]] = Field(default_factory=list)
    length: float = 0.0
    color_hex: str = "#1A1A1A"
    stroke_width: float = 6.0
```

Each stroke represents an atomic, timed drawing trajectory with continuous sample points, physical path length, and semantic metadata.

---

## 3. Path Parsing & Geometry Sampling

Implemented in [`core/drawing/path_parser.py`](file:///d:/Tool/core/drawing/path_parser.py):
- **Shape Normalizer**: Translates basic SVG elements (`<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polyline>`, `<polygon>`) into equivalent standard SVG path `d` strings.
- **Bézier Curves & Arc Length**: Implements De Casteljau sampling for cubic (`C`) and quadratic (`Q`) Bézier segments, calculating precise arc lengths $L = \sum \|\mathbf{p}_{i} - \mathbf{p}_{i-1}\|$.
- **Coordinate Transformations**: Supports scaling and translation from asset local viewBox coordinates $(x_{local}, y_{local})$ to target whiteboard canvas coordinates $(x_{canvas}, y_{canvas})$.

---

## 4. Semantic Stroke Ordering Rules

Implemented in [`core/drawing/sorter.py`](file:///d:/Tool/core/drawing/sorter.py):
Mimics how a human whiteboard artist naturally constructs a subject:

### Tree Ordering
1. `trunk` (Priority 10): Base anchor, root flare, ground mound, main curved trunk.
2. `branches` (Priority 20): Trunk bark texture rings and structural boughs.
3. `leaves` (Priority 30): Canopy fronds, palm leaf leaflets.
4. `fruits` (Priority 40): Coconuts, hanging clusters.

### Monkey Ordering
1. `body` (Priority 10): Torso ellipse, belly patch contour.
2. `head` (Priority 20): Head outline, outer and inner ears.
3. `face` (Priority 30): Face mask, eyes, snout, mouth smile.
4. `arms` (Priority 40): Reaching arms, hands, fingers.
5. `legs` (Priority 50): Climbing legs, bent knees, feet.
6. `tail` (Priority 60): Prehensile tail wrapped around the branch.

### Banana Ordering
1. `banana_body` (Priority 10): Main outer and inner curves, longitudinal facet ridges.
2. `tip` (Priority 20): Darkened bottom blossom tips.
3. `stem` (Priority 30): Top crown cap stalk connecting cluster.

---

## 5. Hand Path & Trajectory Computation

Implemented in [`core/drawing/hand_path.py`](file:///d:/Tool/core/drawing/hand_path.py):
- **Hand Tip Alignment**: Built-in asset `assets/drawing-hand.png` (dimensions 1069x1472) has its pen nib anchored at the top-left $(0, 0)$ coordinate relative to the drawing tip.
- **Continuous State Tracking**:
  - `is_drawing = True`: Pen nib pressed on paper, actively tracing along stroke sample points at speed $v = L / \Delta t$.
  - `is_drawing = False`: Pen lifted, traversing in air from stroke $k$ `end_point` to stroke $k+1$ `start_point` over an allocated travel duration (typically 0.15s–0.25s).
- **Time Inversion**: `get_hand_state_at_time(t)` deterministically computes $(x, y, \text{is\_drawing}, \text{current\_stroke})$ for any arbitrary timestamp $t \in [0, T_{total}]$.

---

## 6. Debug Renderer & Verification Modes

Implemented in [`core/drawing/debug_renderer.py`](file:///d:/Tool/core/drawing/debug_renderer.py) and interactive viewer [`assets/drawing_debugger.html`](file:///d:/Tool/assets/drawing_debugger.html):

| Mode | Name | Description |
|---|---|---|
| **Mode A** | Original SVG | Renders raw source SVG geometry without modifications. |
| **Mode B** | Stroke Order | Color-codes strokes across an HSL hue spectrum with circular numbered badges showing the exact draw sequence. |
| **Mode C** | Animated Stroke Drawing | True vector whiteboard animation using dynamic CSS keyframes with `stroke-dasharray` and `stroke-dashoffset`. Strokes appear progressively one by one without masking or fading. |
| **Mode D** | Hand Following Stroke | Mode C synchronized with the real whiteboard hand overlay (`drawing-hand.png`), keeping the pen tip locked onto the drawing head. |
| **Mode E** | Final Drawing | Crisp, completed whiteboard illustration in its finished resting state. |

---

## 7. Interactive Debugger

Open `assets/drawing_debugger.html` in any modern web browser to access:
- **Asset Selector**: Toggle between `tree_palm.svg`, `monkey_climbing.svg`, `monkey_standing.svg`, `banana_bunch.svg`, and `banana_single.svg`.
- **Mode Buttons**: Instant switching between Modes A, B, C, D, and E.
- **Timeline Scrubber**: Real-time seek bar with Play/Pause, 0.5x/1x/2x speed controls, and current time readout.
- **Stroke Inspector Table**: Real-time highlighting of current active stroke ID, semantic purpose, length, and duration.
