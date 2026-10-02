export type ActiveTab =
  | "dashboard"
  | "create"
  | "review"
  | "templates"
  | "assets"
  | "voices"
  | "music"
  | "jobs";

export type GenerationState =
  | "idle"
  | "loading"
  | "generating"
  | "retrying"
  | "completed"
  | "failed";

export type RegenerateTarget = "script" | "scene" | "asset" | "voice" | "drawing";

export interface ProjectSummary {
  id: string;
  title: string;
  description: string;
  aspect_ratio: string;
  template_id: string;
  status: "draft" | "rendering" | "completed" | "failed";
  video_url: string | null;
  thumbnail_url: string | null;
  duration_sec: number;
  scene_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateItem {
  id: string;
  name: string;
  description: string;
  category: string;
  aspect_ratio: string;
  default_fps: number;
  bg_color_hex: string;
  accent_color_hex: string;
  preview_style: string;
  tags: string[];
}

export interface AssetCatalogItem {
  id: string;
  name: string;
  category: string;
  tags: string[];
  format: string;
  path: string;
  poses: Record<string, { name: string; description: string; file_path: string }>;
  actions: string[];
  metadata: Record<string, any>;
}

export interface VoiceItem {
  id: string;
  name: string;
  language: string;
  locale: string;
  gender: string;
  accent: string;
  sample_text: string;
  supported_speeds: number[];
  is_neural: boolean;
  tags: string[];
}

export interface MusicTrackItem {
  id: string;
  title: string;
  artist: string;
  mood: string;
  genre: string;
  duration_sec: number;
  bpm: number;
  recommended_volume: number;
  preview_url: string;
  tags: string[];
}

export interface JobStageProgress {
  stage: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
  details?: Record<string, any>;
}

export interface ProductionJob {
  id: string;
  title: string;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  current_stage: string;
  progress_percent: number;
  stages: JobStageProgress[];
  created_at: string;
  updated_at: string;
  artifacts: Record<string, string>;
  error_message?: string | null;
}

export interface ScriptSegment {
  segment_id: string;
  text: string;
  estimated_duration: number;
  semantic_meaning: string;
  keywords: string[];
}

export interface VisualEntity {
  id: string;
  name: string;
  category: string;
  pose: string;
  action: string;
  layer: number;
  importance: number;
  position: { x: number; y: number; width: number; height: number };
  tags: string[];
}

export interface WordTiming {
  word: string;
  start_time: number;
  end_time: number;
}

export interface TimelineEventItem {
  id: string;
  asset_id: string;
  action: string;
  start_time: number;
  end_time: number;
  semantic_purpose: string;
}

export interface MediaQAReport {
  is_valid_mp4: boolean;
  duration_sec: number;
  video_codec: string;
  resolution: string;
  fps: number;
  frame_count: number;
  audio_codec: string;
  audio_duration_sec?: number;
  duration_delta?: number;
  is_corrupted: boolean;
  visual_qa_pass: boolean;
}

export interface ReviewData {
  idea: string;
  language: string;
  voice_id: string;
  speed: number;
  music_id: string;
  music_volume: number;
  visual_style: string;
  aspect_ratio: string;
  video_url: string;
  thumbnail_url: string;
  audio_url: string;
  script: {
    title: string;
    full_text: string;
    segments: ScriptSegment[];
  };
  scenes: Array<{
    id: string;
    scene_index: number;
    title: string;
    duration_ms: number;
    entities_count: number;
  }>;
  visual_entities: VisualEntity[];
  narration: {
    voice_id: string;
    voice_name?: string;
    speed: number;
    duration_sec: number;
    sample_rate: number;
    word_timings: WordTiming[];
  };
  timeline_events: TimelineEventItem[];
  qa_report: MediaQAReport;
  regeneration_history?: Array<{
    target: string;
    instructions?: string;
    timestamp: string;
    status: string;
  }>;
}
