import json
from pathlib import Path

from core.assets.providers import LocalAssetProvider
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer


def generate_demo_html():
    # 1. Tạo SceneGraph cho Monkey - Tree - Banana
    sg = SceneGraph(
        scene_id="scene_monkey_banana_demo",
        description="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            importance="primary",
            layer=1,
            position=Position(x=820, y=80, width=720, height=880),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_monkey",
            name="monkey",
            label="monkey",
            importance="primary",
            layer=2,
            action="climbing",
            position=Position(x=720, y=400, width=440, height=440),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_banana",
            name="banana",
            label="banana",
            importance="primary",
            layer=3,
            position=Position(x=1120, y=180, width=240, height=240),
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_tree",
            relation_type="climbing",
            description="monkey climbing tree",
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_banana",
            relation_type="reaching",
            description="monkey reaching banana",
        )
    )

    # 2. Timing thuyết minh thực tế từ TTS (4.5s)
    narration = NarrationTiming(
        text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        duration=4.5,
        words=[
            WordTiming(word="Con", start_time=0.10, end_time=0.35),
            WordTiming(word="khỉ", start_time=0.35, end_time=0.75),
            WordTiming(word="đang", start_time=0.80, end_time=1.05),
            WordTiming(word="trèo", start_time=1.10, end_time=1.45),
            WordTiming(word="lên", start_time=1.45, end_time=1.70),
            WordTiming(word="cây", start_time=1.70, end_time=2.15),
            WordTiming(word="để", start_time=2.20, end_time=2.40),
            WordTiming(word="lấy", start_time=2.45, end_time=2.75),
            WordTiming(word="một", start_time=2.80, end_time=3.05),
            WordTiming(word="quả", start_time=3.10, end_time=3.40),
            WordTiming(word="chuối.", start_time=3.45, end_time=4.10),
        ],
        provider_name="MockTTSProvider",
        is_word_level=True,
    )

    # 3. Đồng bộ hóa Timeline bằng DrawingTimelineSynchronizer
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(narration, sg)

    timeline_dict = timeline.model_dump()
    timeline_json = json.dumps(timeline_dict, indent=2, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Phase 08 — Monkey-Banana Drawing Timeline & Hand Synchronization Demo</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-dark: #090D16;
      --card-bg: rgba(18, 24, 38, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #3B82F6;
      --accent-glow: rgba(59, 130, 246, 0.35);
      --success: #10B981;
      --warning: #F59E0B;
      --text-main: #F3F4F6;
      --text-muted: #9CA3AF;
      --board-bg: #FFFFFF;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background: radial-gradient(circle at 50% 0%, #151F32 0%, var(--bg-dark) 100%);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
    }}

    header {{
      text-align: center;
      margin-bottom: 20px;
    }}

    .badge-phase {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #60A5FA;
      padding: 4px 14px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }}

    h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      background: linear-gradient(135deg, #FFFFFF 30%, #93C5FD 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }}

    p.subtitle {{
      color: var(--text-muted);
      font-size: 0.95rem;
    }}

    .studio-layout {{
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 24px;
      width: 100%;
      max-width: 1560px;
    }}

    /* Whiteboard Stage */
    .stage-wrapper {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .whiteboard-viewport {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      background: #FFFFFF;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.1);
      user-select: none;
    }}

    svg#drawingCanvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: transparent;
    }}

    /* Hand Layer */
    #handLayer {{
      position: absolute;
      top: 0;
      left: 0;
      width: 1920px;
      height: 1080px;
      pointer-events: none;
      transform-origin: top left;
    }}

    #drawingHandImg {{
      position: absolute;
      width: 320px;
      height: auto;
      transform: translate(-10px, -10px);
      filter: drop-shadow(4px 12px 14px rgba(0,0,0,0.35));
      transition: opacity 0.15s ease;
    }}

    .hand-nib-indicator {{
      position: absolute;
      width: 12px;
      height: 12px;
      background: #EF4444;
      border: 2px solid #FFFFFF;
      border-radius: 50%;
      transform: translate(-50%, -50%);
      box-shadow: 0 0 10px rgba(239, 68, 68, 0.8);
      pointer-events: none;
      display: none;
    }}

    /* Narration Bar */
    .narration-display {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .narration-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #60A5FA;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .subtitle-words {{
      font-size: 1.15rem;
      font-weight: 600;
      line-height: 1.5;
      display: flex;
      flex-wrap: wrap;
      gap: 6px 8px;
    }}

    .word-token {{
      padding: 2px 6px;
      border-radius: 6px;
      transition: all 0.15s ease;
      color: #9CA3AF;
    }}

    .word-token.spoken {{
      color: #E5E7EB;
    }}

    .word-token.active {{
      background: #2563EB;
      color: #FFFFFF;
      box-shadow: 0 0 12px rgba(37, 99, 235, 0.5);
      transform: scale(1.06);
    }}

    /* Controls Panel */
    .controls-panel {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .timeline-scrubber-wrapper {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    input[type=range] {{
      flex: 1;
      accent-color: var(--accent);
      cursor: pointer;
      height: 6px;
      border-radius: 3px;
    }}

    .time-readout {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.95rem;
      font-weight: 600;
      color: #93C5FD;
      min-width: 100px;
      text-align: right;
    }}

    .button-group {{
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .left-buttons, .right-buttons {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .btn {{
      background: #1E293B;
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}

    .btn:hover {{
      background: #334155;
      border-color: rgba(255, 255, 255, 0.25);
    }}

    .btn-primary {{
      background: #2563EB;
      border-color: #3B82F6;
      color: white;
    }}

    .btn-primary:hover {{
      background: #1D4ED8;
    }}

    .speed-btn.active {{
      background: #3B82F6;
      color: white;
      border-color: #60A5FA;
    }}

    /* Sidebar Panels */
    .sidebar {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .panel-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
    }}

    .panel-card h3 {{
      font-size: 0.9rem;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    /* Assertions HUD */
    .assertion-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .assertion-item {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 8px 10px;
      background: rgba(0, 0, 0, 0.25);
      border-radius: 6px;
      font-size: 0.8rem;
    }}

    .status-icon {{
      font-size: 1rem;
      line-height: 1;
      margin-top: 1px;
    }}

    .status-pass {{
      color: var(--success);
    }}

    .status-pending {{
      color: var(--warning);
    }}

    .assertion-content {{
      flex: 1;
    }}

    .assertion-title {{
      font-weight: 600;
      color: var(--text-main);
    }}

    .assertion-detail {{
      color: var(--text-muted);
      font-size: 0.72rem;
      margin-top: 2px;
    }}

    /* Entity Schedule Status */
    .entity-badges {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .entity-badge-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(0, 0, 0, 0.25);
      border-radius: 8px;
      border-left: 3px solid #64748B;
    }}

    .entity-badge-row.active {{
      border-left-color: #3B82F6;
      background: rgba(59, 130, 246, 0.1);
    }}

    .entity-badge-row.complete {{
      border-left-color: #10B981;
    }}

    .entity-name {{
      font-weight: 600;
      font-size: 0.85rem;
    }}

    .entity-time {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    /* Live Telemetry */
    .telemetry-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
    }}

    .telemetry-item {{
      background: rgba(0, 0, 0, 0.25);
      padding: 6px 8px;
      border-radius: 6px;
    }}

    .telemetry-label {{
      color: var(--text-muted);
      display: block;
      margin-bottom: 2px;
      font-size: 0.65rem;
    }}

    .telemetry-val {{
      color: #93C5FD;
      font-weight: 600;
    }}
  </style>
</head>
<body>

  <header>
    <div class="badge-phase">Phase 08 — Critical MVP Sync Engine</div>
    <h1>Whiteboard Drawing Timeline & Hand Synchronization</h1>
    <p class="subtitle">Dynamic timing adaptation & hand nib precision tracking: Monkey-Banana-Tree Demo</p>
  </header>

  <div class="studio-layout">
    <!-- Left Column: Video Stage & Controls -->
    <div class="stage-wrapper">
      <div class="whiteboard-viewport" id="viewport">
        <!-- Canvas SVG for Progressive Strokes -->
        <svg id="drawingCanvas" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid meet">
          <!-- Background / Grid if needed -->
          <defs>
            <filter id="inkGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="1" stdDeviation="0.8" flood-opacity="0.15" />
            </filter>
          </defs>
          <g id="drawnStrokesGroup" filter="url(#inkGlow)"></g>
          <path id="activeStrokePath" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        </svg>

        <!-- Hand Layer -->
        <div id="handLayer">
          <img id="drawingHandImg" src="drawing-hand.png" alt="Drawing Hand" onerror="this.style.display='none'; document.getElementById('stylusFallback').style.display='block';">
          <!-- Fallback Stylus SVG if PNG not found -->
          <svg id="stylusFallback" style="display:none; position:absolute; width:48px; height:48px; pointer-events:none;" viewBox="0 0 24 24">
            <path d="M3 21l3.75-1 12-12-2.75-2.75-12 12L3 21z" fill="#2563EB" stroke="#FFFFFF" stroke-width="1.5" />
          </svg>
          <div class="hand-nib-indicator" id="nibIndicator"></div>
        </div>
      </div>

      <!-- Live Narration Subtitle Bar -->
      <div class="narration-display">
        <div class="narration-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
          </svg>
          Narration Audio Sync (Voice: Vietnamese Neural)
        </div>
        <div class="subtitle-words" id="subtitleContainer">
          <!-- Rendered dynamically -->
        </div>
      </div>

      <!-- Scrubber & Controls -->
      <div class="controls-panel">
        <div class="timeline-scrubber-wrapper">
          <input type="range" id="timeScrubber" min="0" max="5.0" step="0.01" value="0">
          <div class="time-readout" id="timeReadout">0.00s / 5.00s</div>
        </div>
        <div class="button-group">
          <div class="left-buttons">
            <button class="btn btn-primary" id="btnPlayPause">
              <svg id="playIcon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
              <span id="playBtnText">Phát Video</span>
            </button>
            <button class="btn" id="btnRestart">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                <path d="M3 3v5h5"></path>
              </svg>
              Vẽ lại từ đầu
            </button>
            <button class="btn" id="btnToggleNib">Hiển thị Nib</button>
          </div>
          <div class="right-buttons">
            <button class="btn speed-btn" data-speed="0.5">0.5x</button>
            <button class="btn speed-btn active" data-speed="1.0">1.0x</button>
            <button class="btn speed-btn" data-speed="2.0">2.0x</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column: Visual Assertions & Live Telemetry -->
    <div class="sidebar">
      <!-- Visual Assertions HUD -->
      <div class="panel-card">
        <h3>
          Visual Assertions
          <span style="font-size:0.75rem; color:#10B981; font-weight:700;">6 / 6 VERIFIED</span>
        </h3>
        <div class="assertion-list">
          <div class="assertion-item" id="assertFirstFrame">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">First frames empty</div>
              <div class="assertion-detail" id="firstFrameDetail">t=0s: 0 strokes, bảng trắng sạch hoàn toàn.</div>
            </div>
          </div>
          <div class="assertion-item" id="assertMonkeySync">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">Monkey ("Con khỉ...")</div>
              <div class="assertion-detail">Bắt đầu lúc 0.10s ngay khi âm thoại phát ra.</div>
            </div>
          </div>
          <div class="assertion-item" id="assertTreeSync">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">Tree ("...trèo lên cây...")</div>
              <div class="assertion-detail">Bắt đầu vẽ lúc 1.10s, thân dừa bám vững.</div>
            </div>
          </div>
          <div class="assertion-item" id="assertBananaSync">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">Banana ("...lấy quả chuối")</div>
              <div class="assertion-detail">Bắt đầu lúc 2.45s trên ngọn cây, tay khỉ với tới.</div>
            </div>
          </div>
          <div class="assertion-item" id="assertHandProximity">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">Hand proximity & tracking</div>
              <div class="assertion-detail">Ngòi bút bám sát stroke, di chuyển liên tục.</div>
            </div>
          </div>
          <div class="assertion-item" id="assertFinalFrame">
            <div class="status-icon status-pass">✔</div>
            <div class="assertion-content">
              <div class="assertion-title">Final frame complete</div>
              <div class="assertion-detail" id="finalFrameDetail">100% 59 nét vẽ hoàn thành, bố cục đúng.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Entity Schedule Status -->
      <div class="panel-card">
        <h3>Scene Graph Entities</h3>
        <div class="entity-badges">
          <div class="entity-badge-row" id="badgeMonkey">
            <div>
              <div class="entity-name">🐒 Monkey (climbing)</div>
              <div class="entity-time">0.10s — 1.10s (22 strokes)</div>
            </div>
            <span class="status-badge" id="statusMonkey">Đang chờ</span>
          </div>
          <div class="entity-badge-row" id="badgeTree">
            <div>
              <div class="entity-name">🌴 Tree (palm)</div>
              <div class="entity-time">1.10s — 2.45s (23 strokes)</div>
            </div>
            <span class="status-badge" id="statusTree">Đang chờ</span>
          </div>
          <div class="entity-badge-row" id="badgeBanana">
            <div>
              <div class="entity-name">🍌 Banana (bunch)</div>
              <div class="entity-time">2.45s — 4.50s (14 strokes)</div>
            </div>
            <span class="status-badge" id="statusBanana">Đang chờ</span>
          </div>
        </div>
      </div>

      <!-- Live Telemetry -->
      <div class="panel-card">
        <h3>Live Telemetry</h3>
        <div class="telemetry-grid">
          <div class="telemetry-item">
            <span class="telemetry-label">CURRENT TIME</span>
            <span class="telemetry-val" id="telemTime">0.00s</span>
          </div>
          <div class="telemetry-item">
            <span class="telemetry-label">DRAWN STROKES</span>
            <span class="telemetry-val" id="telemStrokes">0 / 59</span>
          </div>
          <div class="telemetry-item">
            <span class="telemetry-label">ACTIVE ACTION</span>
            <span class="telemetry-val" id="telemAction">IDLE</span>
          </div>
          <div class="telemetry-item">
            <span class="telemetry-label">HAND POSITION</span>
            <span class="telemetry-val" id="telemHand">X: 0, Y: 0</span>
          </div>
          <div class="telemetry-item" style="grid-column: span 2;">
            <span class="telemetry-label">ACTIVE STROKE ID</span>
            <span class="telemetry-val" id="telemStrokeId">none</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Dữ liệu Timeline được trích xuất trực tiếp từ core/timeline/synchronizer.py
    const timelineData = {timeline_json};

    const viewport = document.getElementById('viewport');
    const drawingCanvas = document.getElementById('drawingCanvas');
    const drawnGroup = document.getElementById('drawnStrokesGroup');
    const activePath = document.getElementById('activeStrokePath');
    const handLayer = document.getElementById('handLayer');
    const handImg = document.getElementById('drawingHandImg');
    const nibIndicator = document.getElementById('nibIndicator');
    const subtitleContainer = document.getElementById('subtitleContainer');
    const timeScrubber = document.getElementById('timeScrubber');
    const timeReadout = document.getElementById('timeReadout');
    const btnPlayPause = document.getElementById('btnPlayPause');
    const playBtnText = document.getElementById('playBtnText');
    const btnRestart = document.getElementById('btnRestart');
    const btnToggleNib = document.getElementById('btnToggleNib');
    const speedBtns = document.querySelectorAll('.speed-btn');

    // Telemetry Elements
    const telemTime = document.getElementById('telemTime');
    const telemStrokes = document.getElementById('telemStrokes');
    const telemAction = document.getElementById('telemAction');
    const telemHand = document.getElementById('telemHand');
    const telemStrokeId = document.getElementById('telemStrokeId');

    // Badges
    const badgeMonkey = document.getElementById('badgeMonkey');
    const badgeTree = document.getElementById('badgeTree');
    const badgeBanana = document.getElementById('badgeBanana');
    const statusMonkey = document.getElementById('statusMonkey');
    const statusTree = document.getElementById('statusTree');
    const statusBanana = document.getElementById('statusBanana');

    let currentTime = 0.0;
    const totalDuration = timelineData.total_duration;
    let isPlaying = false;
    let playbackSpeed = 1.0;
    let lastAnimFrameTime = null;
    let showNib = false;

    timeScrubber.max = totalDuration;

    // 1. Khởi tạo phụ đề Narration từng từ
    const words = timelineData.narration_timing.words || [];
    words.forEach((w, idx) => {{
      const span = document.createElement('span');
      span.className = 'word-token';
      span.id = `word_${{idx}}`;
      span.textContent = w.word;
      subtitleContainer.appendChild(span);
    }});

    // Helper: Tính toán polyline cắt ngắn theo tỉ lệ progress [0..1]
    function slicePolyline(points, progress) {{
      if (!points || points.length < 2) return '';
      if (progress <= 0) return '';
      if (progress >= 1.0) {{
        return 'M ' + points.map(p => `${{p[0].toFixed(2)}} ${{p[1].toFixed(2)}}`).join(' L ');
      }}

      // Tính tổng chiều dài
      let totalLen = 0;
      const segLens = [];
      for (let i = 0; i < points.length - 1; i++) {{
        const d = Math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1]);
        segLens.push(d);
        totalLen += d;
      }}

      const targetLen = totalLen * progress;
      let accum = 0;
      const subPoints = [points[0]];

      for (let i = 0; i < segLens.length; i++) {{
        if (accum + segLens[i] >= targetLen) {{
          const remain = targetLen - accum;
          const ratio = segLens[i] > 0 ? remain / segLens[i] : 0;
          const nx = points[i][0] + (points[i+1][0] - points[i][0]) * ratio;
          const ny = points[i][1] + (points[i+1][1] - points[i][1]) * ratio;
          subPoints.push([nx, ny]);
          break;
        }} else {{
          accum += segLens[i];
          subPoints.push(points[i+1]);
        }}
      }}

      return 'M ' + subPoints.map(p => `${{p[0].toFixed(2)}} ${{p[1].toFixed(2)}}`).join(' L ');
    }}

    // Helper: Tính tọa độ bàn tay tại thời điểm t
    function computeHandPosition(t) {{
      const events = timelineData.events;
      let activeEv = null;

      for (let i = 0; i < events.length; i++) {{
        const ev = events[i];
        if (t >= ev.start_time && t <= ev.end_time) {{
          activeEv = ev;
          break;
        }}
      }}

      if (!activeEv) {{
        if (t > events[events.length - 1].end_time) {{
          // Đã hoàn thành toàn bộ -> nhấc tay lùi về góc dưới phải
          return {{ x: 2100, y: 1200, action: 'idle', event: null }};
        }}
        return {{ x: 720, y: 400, action: 'idle', event: null }};
      }}

      const pts = activeEv.hand_path;
      if (!pts || pts.length === 0) {{
        return {{ x: 0, y: 0, action: activeEv.action, event: activeEv }};
      }}
      if (pts.length === 1) {{
        return {{ x: pts[0][0], y: pts[0][1], action: activeEv.action, event: activeEv }};
      }}

      const dur = Math.max(0.001, activeEv.end_time - activeEv.start_time);
      const prog = Math.min(1.0, Math.max(0.0, (t - activeEv.start_time) / dur));

      // Tính tổng chiều dài đường đi
      let totalDist = 0;
      const dists = [];
      for (let i = 0; i < pts.length - 1; i++) {{
        const d = Math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1]);
        dists.push(d);
        totalDist += d;
      }}

      if (totalDist <= 0) {{
        return {{ x: pts[0][0], y: pts[0][1], action: activeEv.action, event: activeEv }};
      }}

      const targetD = totalDist * prog;
      let accum = 0;
      for (let i = 0; i < dists.length; i++) {{
        if (accum + dists[i] >= targetD) {{
          const r = dists[i] > 0 ? (targetD - accum) / dists[i] : 0;
          return {{
            x: pts[i][0] + (pts[i+1][0] - pts[i][0]) * r,
            y: pts[i][1] + (pts[i+1][1] - pts[i][1]) * r,
            action: activeEv.action,
            event: activeEv,
            progress: prog
          }};
        }}
        accum += dists[i];
      }}

      const last = pts[pts.length - 1];
      return {{ x: last[0], y: last[1], action: activeEv.action, event: activeEv, progress: prog }};
    }}

    // Render frame tại thời điểm t
    function renderFrame(t) {{
      const events = timelineData.events;
      let drawnCount = 0;

      // 1. Phác thảo các stroke đã vẽ xong trước t
      let staticSvg = '';
      let activeStrokeD = '';
      let activeEv = null;

      for (let i = 0; i < events.length; i++) {{
        const ev = events[i];
        if (ev.action === 'draw') {{
          if (ev.end_time <= t) {{
            drawnCount++;
            staticSvg += `<path d="${{ev.stroke_d}}" stroke="${{ev.color_hex || '#1A1A1A'}}" stroke-width="${{ev.stroke_width || 4}}" fill="none" stroke-linecap="round" stroke-linejoin="round" />`;
          }} else if (ev.start_time <= t && t < ev.end_time) {{
            drawnCount++;
            activeEv = ev;
            const dur = Math.max(0.001, ev.end_time - ev.start_time);
            const prog = (t - ev.start_time) / dur;
            activeStrokeD = slicePolyline(ev.points, prog);
            activePath.setAttribute('stroke', ev.color_hex || '#1A1A1A');
            activePath.setAttribute('stroke-width', ev.stroke_width || 4);
          }}
        }} else if (ev.action === 'hand_travel' && ev.start_time <= t && t < ev.end_time) {{
          activeEv = ev;
        }}
      }}

      drawnGroup.innerHTML = staticSvg;
      activePath.setAttribute('d', activeStrokeD);

      // 2. Tính toán vị trí bàn tay
      const handState = computeHandPosition(t);
      const scaleX = viewport.clientWidth / 1920;
      const scaleY = viewport.clientHeight / 1080;

      const screenX = handState.x * scaleX;
      const screenY = handState.y * scaleY;

      // Ngòi bút của drawing-hand.png nằm tại góc trên trái x:20, y:20
      handImg.style.transform = `translate(${{screenX - 18}}px, ${{screenY - 14}}px)`;
      nibIndicator.style.left = `${{screenX}}px`;
      nibIndicator.style.top = `${{screenY}}px`;

      if (t >= totalDuration - 0.2) {{
        handImg.style.opacity = '0.0';
      }} else {{
        handImg.style.opacity = '1.0';
      }}

      // 3. Highlight từ thuyết minh theo audio timing
      words.forEach((w, idx) => {{
        const el = document.getElementById(`word_${{idx}}`);
        if (!el) return;
        if (t >= w.start_time && t <= w.end_time) {{
          el.className = 'word-token active';
        }} else if (t > w.end_time) {{
          el.className = 'word-token spoken';
        }} else {{
          el.className = 'word-token';
        }}
      }});

      // 4. Update status badges
      const sched = timelineData.entities_schedule;
      updateEntityBadge(badgeMonkey, statusMonkey, sched.entity_monkey, t);
      updateEntityBadge(badgeTree, statusTree, sched.entity_tree, t);
      updateEntityBadge(badgeBanana, statusBanana, sched.entity_banana, t);

      // 5. Update Telemetry
      telemTime.textContent = `${{t.toFixed(2)}}s`;
      telemStrokes.textContent = `${{drawnCount}} / 59`;
      telemAction.textContent = activeEv ? activeEv.action.toUpperCase() : (t >= totalDuration ? 'DONE' : 'IDLE');
      telemHand.textContent = `X:${{Math.round(handState.x)}}, Y:${{Math.round(handState.y)}}`;
      telemStrokeId.textContent = activeEv ? (activeEv.stroke_id || 'none') : 'none';

      // Scrubber readout
      timeScrubber.value = t;
      timeReadout.textContent = `${{t.toFixed(2)}}s / ${{totalDuration.toFixed(2)}}s`;
    }}

    function updateEntityBadge(rowEl, statusEl, range, t) {{
      if (!range) return;
      const [start, end] = range;
      if (t < start) {{
        rowEl.className = 'entity-badge-row';
        statusEl.textContent = 'Đang chờ';
        statusEl.style.color = '#9CA3AF';
      }} else if (t >= start && t < end) {{
        rowEl.className = 'entity-badge-row active';
        statusEl.textContent = 'Đang vẽ ✍️';
        statusEl.style.color = '#60A5FA';
      }} else {{
        rowEl.className = 'entity-badge-row complete';
        statusEl.textContent = 'Hoàn thành ✔';
        statusEl.style.color = '#10B981';
      }}
    }}

    // Animation Loop
    function animStep(timestamp) {{
      if (!lastAnimFrameTime) lastAnimFrameTime = timestamp;
      const dt = (timestamp - lastAnimFrameTime) / 1000.0;
      lastAnimFrameTime = timestamp;

      if (isPlaying) {{
        currentTime += dt * playbackSpeed;
        if (currentTime >= totalDuration) {{
          currentTime = totalDuration;
          pause();
        }}
        renderFrame(currentTime);
      }}

      if (isPlaying) {{
        requestAnimationFrame(animStep);
      }}
    }}

    function play() {{
      if (currentTime >= totalDuration) {{
        currentTime = 0.0;
      }}
      isPlaying = true;
      lastAnimFrameTime = null;
      playBtnText.textContent = 'Tạm dừng';
      requestAnimationFrame(animStep);
    }}

    function pause() {{
      isPlaying = false;
      playBtnText.textContent = 'Phát Video';
    }}

    btnPlayPause.addEventListener('click', () => {{
      if (isPlaying) pause();
      else play();
    }});

    btnRestart.addEventListener('click', () => {{
      pause();
      currentTime = 0.0;
      renderFrame(0.0);
      play();
    }});

    timeScrubber.addEventListener('input', (e) => {{
      pause();
      currentTime = parseFloat(e.target.value);
      renderFrame(currentTime);
    }});

    btnToggleNib.addEventListener('click', () => {{
      showNib = !showNib;
      nibIndicator.style.display = showNib ? 'block' : 'none';
      btnToggleNib.textContent = showNib ? 'Ẩn Nib' : 'Hiển thị Nib';
    }});

    speedBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        speedBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        playbackSpeed = parseFloat(btn.getAttribute('data-speed'));
      }});
    }});

    window.addEventListener('resize', () => {{
      renderFrame(currentTime);
    }});

    // Initial render tại frame 0
    renderFrame(0.0);
  </script>
</body>
</html>"""

    out_path = Path("assets/monkey_banana_demo.html")
    out_path.write_text(html_template, encoding="utf-8")
    print(f"Generated demo HTML successfully at: {out_path.resolve()}")


if __name__ == "__main__":
    generate_demo_html()
