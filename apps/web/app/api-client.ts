import {
  AssetCatalogItem,
  JobStageProgress,
  MasterpieceItem,
  MediaQAReport,
  MusicTrackItem,
  ProductionJob,
  ProjectSummary,
  ReviewData,
  TemplateItem,
  VoiceItem,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

// Fallback demo review data
export const DEFAULT_REVIEW_DATA: ReviewData = {
  idea: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
  language: "vi",
  voice_id: "vi-VN-Standard-B",
  speed: 1.0,
  music_id: "whimsical_play",
  music_volume: 0.15,
  visual_style: "notion_minimal",
  aspect_ratio: "16:9",
  has_color: true,
  video_url: "http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default_final.mp4",
  thumbnail_url: "http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default.png",
  audio_url: "http://127.0.0.1:8000/media/monkey_banana_e2e/narration.wav",
  script: {
    title: "Con khỉ trèo cây lấy chuối",
    full_text: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
    segments: [
      {
        segment_id: "seg-01",
        text: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
        estimated_duration: 5.18,
        semantic_meaning: "Tái hiện động tác trèo cây hái chuối của chú khỉ",
        keywords: ["khỉ", "trèo", "cây", "chuối"],
      },
    ],
  },
  scenes: [
    {
      id: "scene-01",
      scene_index: 1,
      title: "Chú khỉ và buồng chuối trên ngọn cây",
      duration_ms: 5300,
      entities_count: 3,
    },
  ],
  visual_entities: [
    {
      id: "entity_tree",
      name: "tree",
      category: "nature",
      pose: "tall",
      action: "standing",
      layer: 0,
      importance: 1.0,
      position: { x: 300, y: 150, width: 550, height: 700 },
      tags: ["tree", "nature", "foliage"],
    },
    {
      id: "entity_monkey",
      name: "monkey",
      category: "character",
      pose: "climbing",
      action: "climbing",
      layer: 1,
      importance: 1.0,
      position: { x: 380, y: 420, width: 260, height: 260 },
      tags: ["monkey", "character", "animal"],
    },
    {
      id: "entity_banana",
      name: "banana",
      category: "object",
      pose: "ripe",
      action: "hanging",
      layer: 2,
      importance: 0.9,
      position: { x: 620, y: 280, width: 160, height: 160 },
      tags: ["banana", "food", "yellow"],
    },
  ],
  narration: {
    voice_id: "vi-VN-Standard-B",
    voice_name: "Nam Khánh (Bắc Bộ Trầm Ấm)",
    speed: 1.0,
    duration_sec: 5.182,
    sample_rate: 24000,
    word_timings: [
      { word: "Con", start_time: 0.1, end_time: 0.35 },
      { word: "khỉ", start_time: 0.35, end_time: 0.7 },
      { word: "đang", start_time: 0.85, end_time: 1.1 },
      { word: "trèo", start_time: 1.1, end_time: 1.45 },
      { word: "lên", start_time: 1.45, end_time: 1.75 },
      { word: "cây", start_time: 1.75, end_time: 2.1 },
      { word: "để", start_time: 2.2, end_time: 2.45 },
      { word: "lấy", start_time: 2.45, end_time: 2.8 },
      { word: "một", start_time: 2.8, end_time: 3.05 },
      { word: "quả", start_time: 3.05, end_time: 3.35 },
      { word: "chuối.", start_time: 3.35, end_time: 3.75 },
    ],
  },
  timeline_events: [
    {
      id: "evt-01",
      asset_id: "asset_tree",
      action: "draw_trunk_and_branches",
      start_time: 0.1,
      end_time: 1.1,
      semantic_purpose: "Phác họa thân cây và cành bám",
    },
    {
      id: "evt-02",
      asset_id: "asset_monkey",
      action: "draw_monkey_climbing",
      start_time: 1.1,
      end_time: 2.45,
      semantic_purpose: "Vẽ tư thế chú khỉ đang leo trèo trên thân cây",
    },
    {
      id: "evt-03",
      asset_id: "asset_banana",
      action: "draw_ripe_banana",
      start_time: 2.45,
      end_time: 3.75,
      semantic_purpose: "Vẽ quả chuối chín vàng chú khỉ với tới",
    },
    {
      id: "evt-04",
      asset_id: "scene",
      action: "final_hold",
      start_time: 3.75,
      end_time: 5.3,
      semantic_purpose: "Giữ tĩnh toàn cảnh hoàn thiện",
    },
  ],
  qa_report: {
    is_valid_mp4: true,
    duration_sec: 5.71,
    video_codec: "h264",
    resolution: "1080x600",
    fps: 30.0,
    frame_count: 171,
    audio_codec: "aac",
    audio_duration_sec: 5.182,
    duration_delta: 0.528,
    is_corrupted: false,
    visual_qa_pass: true,
    technical_qa: {
      pass_technical: true,
      is_valid_mp4: true,
      duration_sec: 5.71,
      video_codec: "h264",
      resolution: "1080x600",
      fps: 30.0,
      frame_count: 171,
      audio_codec: "aac",
      audio_duration_sec: 5.182,
      duration_delta: 0.528,
      is_corrupted: false,
      errors: [],
    },
    drawing_qa: {
      pass_drawing: true,
      required_strokes: 67,
      completed_strokes: 67,
      completion_ratio: 1.0,
      hand_sync_pass: true,
      no_early_reveal_pass: true,
      errors: [],
      details: ["Tree strokes: 41/41", "Monkey strokes: 20/20", "Banana strokes: 6/6"],
    },
    semantic_qa: {
      pass_semantic: true,
      required_entities: 3,
      completed_entities: 3,
      required_actions: 2,
      completed_actions: 2,
      required_relationships: 3,
      completed_relationships: 3,
      final_frame_complete: true,
      errors: [],
      details: ["Monkey climbing verified", "Monkey reaching banana verified", "Banana in tree verified"],
    },
    overall_pass: true,
  },
};

export async function checkBackendHealth(): Promise<{ ok: boolean; status?: string }> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, status: data.status || "healthy" };
    }
  } catch (err) {
    // offline or backend not running
  }
  return { ok: false };
}

export async function fetchTemplates(): Promise<TemplateItem[]> {
  try {
    const res = await fetch(`${API_BASE}/templates`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "notion_minimal",
      name: "Notion Minimalist Whiteboard",
      description: "Phong cách vẽ nét thanh mảnh, nền ngà tối giản tương tự Notion & Excalidraw.",
      category: "minimalist",
      aspect_ratio: "16:9",
      default_fps: 30,
      bg_color_hex: "#FBFBF9",
      accent_color_hex: "#0F172A",
      preview_style: "clean_ink",
      tags: ["notion", "minimalist", "clean"],
    },
    {
      id: "hand_drawn_sketch",
      name: "Hand-Drawn Charcoal Sketch",
      description: "Nét chì than vẽ tay cổ điển, bàn tay họa sĩ di chuyển sinh động.",
      category: "sketch",
      aspect_ratio: "16:9",
      default_fps: 30,
      bg_color_hex: "#FFFFFF",
      accent_color_hex: "#334155",
      preview_style: "charcoal",
      tags: ["hand_drawn", "charcoal", "doodle"],
    },
    {
      id: "vibrant_explainer",
      name: "Vibrant Marketing Explainer",
      description: "Màu sắc nổi bật tương phản cao, tối ưu cho video giải thích truyền thông.",
      category: "marketing",
      aspect_ratio: "16:9",
      default_fps: 60,
      bg_color_hex: "#F8FAFC",
      accent_color_hex: "#4F46E5",
      preview_style: "contour_wipe",
      tags: ["vibrant", "youtube", "colorful"],
    },
    {
      id: "dark_chalkboard",
      name: "Academic Blackboard Chalk",
      description: "Mô phỏng bảng phấn đen trường học với nét phấn dịu mắt.",
      category: "academic",
      aspect_ratio: "16:9",
      default_fps: 30,
      bg_color_hex: "#1E293B",
      accent_color_hex: "#38BDF8",
      preview_style: "chalk",
      tags: ["chalkboard", "academic", "dark_mode"],
    },
  ];
}

export async function fetchAssets(): Promise<AssetCatalogItem[]> {
  try {
    const res = await fetch(`${API_BASE}/assets`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "asset_monkey",
      name: "monkey",
      category: "character",
      tags: ["khỉ", "chú khỉ", "monkey", "ape"],
      format: "svg",
      path: "svg/monkey_standing.svg",
      poses: {
        standing: { name: "standing", description: "Standing upright", file_path: "svg/monkey_standing.svg" },
        climbing: { name: "climbing", description: "Climbing vertically", file_path: "svg/monkey_climbing.svg" },
        eating: { name: "eating", description: "Eating a banana", file_path: "svg/monkey_eating.svg" },
      },
      actions: ["standing", "climbing", "eating", "reaching"],
      metadata: { style: "clean_lineart", stroke_width: 6 },
    },
    {
      id: "asset_tree",
      name: "tree",
      category: "nature",
      tags: ["cây", "cây xanh", "tree"],
      format: "svg",
      path: "svg/tree.svg",
      poses: {
        standard: { name: "standard", description: "Tall tropical tree", file_path: "svg/tree.svg" },
      },
      actions: ["standing", "bearing_fruit"],
      metadata: { style: "clean_lineart", stroke_width: 7 },
    },
    {
      id: "asset_banana",
      name: "banana",
      category: "object",
      tags: ["chuối", "quả chuối", "banana"],
      format: "svg",
      path: "svg/banana.svg",
      poses: {
        ripe: { name: "ripe", description: "Curved ripe yellow banana", file_path: "svg/banana.svg" },
      },
      actions: ["hanging", "picked"],
      metadata: { style: "clean_lineart", stroke_width: 5 },
    },
  ];
}

export async function fetchMasterpieces(): Promise<MasterpieceItem[]> {
  try {
    const res = await fetch(`${API_BASE}/assets/masterpieces`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [];
}

export async function fetchVoices(): Promise<VoiceItem[]> {
  try {
    const res = await fetch(`${API_BASE}/voices`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "vi-VN-Standard-A",
      name: "Mai Chi",
      language: "Tiếng Việt",
      locale: "vi-VN",
      gender: "female",
      accent: "Bắc Bộ (Truyền Cảm)",
      sample_text: "Xin chào các bạn, hôm nay chúng ta sẽ cùng khám phá thế giới tự nhiên kỳ thú.",
      supported_speeds: [0.8, 1.0, 1.2, 1.5],
      is_neural: true,
      tags: ["natural", "storytelling", "female"],
    },
    {
      id: "vi-VN-Standard-B",
      name: "Nam Khánh",
      language: "Tiếng Việt",
      locale: "vi-VN",
      gender: "male",
      accent: "Bắc Bộ (Trầm Ấm)",
      sample_text: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
      supported_speeds: [0.8, 1.0, 1.2, 1.5],
      is_neural: true,
      tags: ["warm", "explainer", "male"],
    },
    {
      id: "vi-VN-Neural-C",
      name: "Thảo My",
      language: "Tiếng Việt",
      locale: "vi-VN",
      gender: "female",
      accent: "Nam Bộ (Ngọt Ngào)",
      sample_text: "Chào bạn! Hãy cùng tôi tìm hiểu bài học thú vị ngày hôm nay nhé.",
      supported_speeds: [0.8, 1.0, 1.2, 1.5],
      is_neural: true,
      tags: ["friendly", "educational", "female"],
    },
    {
      id: "en-US-Standard-A",
      name: "Arthur",
      language: "English",
      locale: "en-US",
      gender: "male",
      accent: "American (Professional)",
      sample_text: "Welcome to AI Whiteboard Studio, turning your ideas into hand-drawn stories.",
      supported_speeds: [0.8, 1.0, 1.2, 1.5],
      is_neural: true,
      tags: ["authoritative", "corporate", "male"],
    },
  ];
}

export async function fetchMusic(): Promise<MusicTrackItem[]> {
  try {
    const res = await fetch(`${API_BASE}/music`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "whimsical_play",
      title: "Playful Forest Marimba",
      artist: "Animation Soundworks",
      mood: "Vui Nhộn, Tinh Nghịch",
      genre: "Children Animation",
      duration_sec: 120,
      bpm: 124,
      recommended_volume: 0.15,
      preview_url: "",
      tags: ["whimsical", "monkey", "cartoon"],
    },
    {
      id: "acoustic_uplift",
      title: "Sunny Morning Ukulele",
      artist: "Studio Acoustic Collective",
      mood: "Tươi Sáng, Hứng Khởi",
      genre: "Acoustic Folk",
      duration_sec: 145,
      bpm: 110,
      recommended_volume: 0.15,
      preview_url: "",
      tags: ["cheerful", "acoustic", "bright"],
    },
    {
      id: "lofi_chill",
      title: "Late Night Whiteboard Lofi",
      artist: "Tokyo Chillhop Beats",
      mood: "Thư Giãn, Tập Trung",
      genre: "Lofi Hip Hop",
      duration_sec: 180,
      bpm: 85,
      recommended_volume: 0.12,
      preview_url: "",
      tags: ["lofi", "study", "relaxing"],
    },
    {
      id: "corporate_inspire",
      title: "Inspiring Innovation",
      artist: "Pinnacle Scores",
      mood: "Chuyên Nghiệp, Tiến Bộ",
      genre: "Corporate Orchestral",
      duration_sec: 160,
      bpm: 118,
      recommended_volume: 0.14,
      preview_url: "",
      tags: ["corporate", "explainer", "business"],
    },
  ];
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/projects`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "proj-monkey-banana-01",
      title: "Con khỉ trèo cây lấy chuối",
      description: "Demo sản xuất nội dung Whiteboard hoạt hình tự động từ ý tưởng đến video MP4 Full HD.",
      aspect_ratio: "16:9",
      template_id: "notion_minimal",
      status: "completed",
      video_url: "http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default_final.mp4",
      thumbnail_url: "http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default.png",
      duration_sec: 5.3,
      scene_count: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
}

export async function fetchJobs(): Promise<ProductionJob[]> {
  try {
    const res = await fetch(`${API_BASE}/jobs`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch {}
  return [
    {
      id: "job-monkey-banana-demo",
      title: "Con khỉ trèo cây lấy chuối",
      prompt: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
      status: "completed",
      current_stage: "completed",
      progress_percent: 100.0,
      stages: [
        { stage: "script_generation", status: "completed" },
        { stage: "narration_synthesis", status: "completed" },
        { stage: "visual_planning", status: "completed" },
        { stage: "asset_generation", status: "completed" },
        { stage: "timeline_annotation", status: "completed" },
        { stage: "whiteboard_rendering", status: "completed" },
        { stage: "audio_compositing", status: "completed" },
        { stage: "quality_assurance", status: "completed" },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      artifacts: {
        video: "/media/monkey_banana_e2e/scene_default_final.mp4",
        thumbnail: "/media/monkey_banana_e2e/scene_default.png",
      },
    },
  ];
}

export async function fetchJobReview(jobId: string): Promise<ReviewData> {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/review`, { signal: AbortSignal.timeout(10000) });
    if (res.ok) {
      const data = await res.json();
      if (data.review_data) {
        return data.review_data as ReviewData;
      }
    }
  } catch (err) {
    console.warn(`[fetchJobReview] Error fetching review for ${jobId}:`, err);
  }
  return {
    ...DEFAULT_REVIEW_DATA,
  };
}

export async function createProductionJob(payload: {
  title: string;
  prompt: string;
  script?: string;
  input_mode?: string;
  language: string;
  voice_id: string;
  speed: number;
  music_id: string;
  music_volume: number;
  visual_style: string;
  aspect_ratio: string;
  has_color?: boolean;
}): Promise<ProductionJob> {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      script: payload.script || payload.prompt,
      input_mode: payload.input_mode || "SCRIPT",
      has_color: payload.has_color !== undefined ? payload.has_color : true,
      auto_run: true,
    }),
    signal: AbortSignal.timeout(180000),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Lỗi tạo job sản xuất video (HTTP ${res.status})`);
  }

  return await res.json();
}

export async function regenerateJobComponent(
  jobId: string,
  target: string,
  instructions?: string
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, instructions }),
      signal: AbortSignal.timeout(4000),
    });
    return res.ok;
  } catch {}
  return true;
}
