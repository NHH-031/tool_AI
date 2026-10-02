"use client";

import React, { useState } from "react";
import { MusicTrackItem, TemplateItem, VoiceItem } from "../types";

interface CreateVideoViewProps {
  initialPrompt?: string;
  voices: VoiceItem[];
  musicTracks: MusicTrackItem[];
  templates: TemplateItem[];
  onGenerate: (config: {
    title: string;
    prompt: string;
    script: string;
    input_mode: string;
    language: string;
    voice_id: string;
    speed: number;
    music_id: string;
    music_volume: number;
    visual_style: string;
    aspect_ratio: string;
  }) => void;
  isGenerating: boolean;
}

export const CreateVideoView: React.FC<CreateVideoViewProps> = ({
  initialPrompt = "",
  voices,
  musicTracks,
  templates,
  onGenerate,
  isGenerating,
}) => {
  // 1. Idea & Script Input
  const [inputMode, setInputMode] = useState<"SCRIPT" | "IDEA">("SCRIPT");
  const [title, setTitle] = useState(
    initialPrompt ? initialPrompt.slice(0, 30) : "Video Hoạt Hình Bảng Trắng"
  );
  const [prompt, setPrompt] = useState(initialPrompt || "");

  // 2. Language
  const [language, setLanguage] = useState<string>("vi");

  // 3. Voice
  const [voiceId, setVoiceId] = useState<string>("vi-VN-Standard-B");

  // 4. Speed
  const [speed, setSpeed] = useState<number>(1.0);

  // 5. Music
  const [musicId, setMusicId] = useState<string>("whimsical_play");

  // 6. Music Volume
  const [musicVolume, setMusicVolume] = useState<number>(15);

  // 7. Visual Style
  const [visualStyle, setVisualStyle] = useState<string>("notion_minimal");

  // 8. Aspect Ratio
  const [aspectRatio, setAspectRatio] = useState<string>("16:9");

  // Sample Audio Player State
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);

  const handleVoicePreview = (vId: string) => {
    if (playingVoice === vId) {
      setPlayingVoice(null);
    } else {
      setPlayingVoice(vId);
      setTimeout(() => setPlayingVoice(null), 3000);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    onGenerate({
      title: title.trim() || "Whiteboard Story",
      prompt: prompt.trim(),
      script: prompt.trim(),
      input_mode: inputMode,
      language,
      voice_id: voiceId,
      speed,
      music_id: musicId,
      music_volume: musicVolume / 100,
      visual_style: visualStyle,
      aspect_ratio: aspectRatio,
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
          <span>🎬</span> Step-by-Step Production Wizard
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Create New Whiteboard Video
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Cấu hình toàn diện quy trình 10 bước: Idea → Script → Voice → Timing → Visual Style → MP4
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* STEP 1: SCRIPT & IDEA INPUT */}
        <section className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 sm:p-7 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
                1
              </span>
              <h2 className="text-base font-bold text-white">Input Source & Script</h2>
            </div>
            {/* Input Mode Selector */}
            <div className="flex gap-1.5 p-1 bg-slate-950/80 rounded-xl border border-slate-800 w-fit">
              <button
                type="button"
                id="btn-mode-script"
                onClick={() => setInputMode("SCRIPT")}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  inputMode === "SCRIPT"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                📝 Kịch bản trực tiếp (Source of Truth)
              </button>
              <button
                type="button"
                id="btn-mode-idea"
                onClick={() => setInputMode("IDEA")}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  inputMode === "IDEA"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                💡 Ý tưởng ngắn (AI Sinh Kịch Bản)
              </button>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Tiêu đề video
              </label>
              <input
                id="input-create-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Nhập tiêu đề dự án"
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-medium text-slate-300">
                  {inputMode === "SCRIPT" ? "Nội dung kịch bản lời thoại (User Script)" : "Ý tưởng kịch bản (Story Idea)"}
                </label>
                <span className="text-[11px] text-indigo-400">
                  {inputMode === "SCRIPT" ? "✓ Source of Truth (Đi xuyên suốt pipeline)" : "AI mở rộng phân cảnh"}
                </span>
              </div>
              <textarea
                id="input-create-prompt"
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={
                  inputMode === "SCRIPT"
                    ? "Nhập kịch bản chi tiết (ví dụ: Con chó đang chạy theo quả bóng...)"
                    : "Mô tả ý tưởng ngắn gọn để AI phát triển kịch bản..."
                }
                className="w-full bg-slate-950/80 border border-slate-800 rounded-2xl p-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed resize-none"
                required
              />
            </div>
          </div>
        </section>

        {/* STEP 2: LANGUAGE */}
        <section className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 sm:p-7 space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
              2
            </span>
            <h2 className="text-base font-bold text-white">Language / Ngôn Ngữ</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { id: "vi", label: "Tiếng Việt", flag: "🇻🇳", desc: "Giọng đọc chuẩn Việt" },
              { id: "en", label: "English", flag: "🇺🇸", desc: "US / UK Natural" },
              { id: "ja", label: "Japanese", flag: "🇯🇵", desc: "Natural Voice" },
              { id: "fr", label: "Français", flag: "🇫🇷", desc: "Parisiènne" },
            ].map((lang) => (
              <button
                type="button"
                key={lang.id}
                id={`btn-lang-${lang.id}`}
                onClick={() => setLanguage(lang.id)}
                className={`p-3.5 rounded-2xl border text-left transition flex items-center gap-3 ${
                  language === lang.id
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <span className="text-2xl">{lang.flag}</span>
                <div>
                  <div className="font-bold text-xs">{lang.label}</div>
                  <div className="text-[10px] text-slate-400">{lang.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* STEP 3 & 4: VOICE & SPEED */}
        <section className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 sm:p-7 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
                3
              </span>
              <h2 className="text-base font-bold text-white">Voice & Narration Speed</h2>
            </div>
          </div>

          {/* Voice Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {voices.map((v) => (
              <div
                key={v.id}
                id={`voice-card-${v.id}`}
                onClick={() => setVoiceId(v.id)}
                className={`p-4 rounded-2xl border cursor-pointer transition flex items-start justify-between ${
                  voiceId === v.id
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-lg">
                    {v.gender === "female" ? "👩" : "👨"}
                  </div>
                  <div>
                    <div className="font-bold text-xs text-white flex items-center gap-1.5">
                      <span>{v.name}</span>
                      <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                        {v.locale}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">{v.accent}</p>
                    <p className="text-[10px] text-slate-500 mt-1 italic line-clamp-1">
                      "{v.sample_text}"
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  id={`btn-voice-preview-${v.id}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleVoicePreview(v.id);
                  }}
                  className={`p-1.5 rounded-lg text-xs transition ${
                    playingVoice === v.id
                      ? "bg-amber-500 text-black animate-pulse"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                  }`}
                  title="Nghe thử giọng đọc"
                >
                  {playingVoice === v.id ? "🔊" : "▶️"}
                </button>
              </div>
            ))}
          </div>

          {/* Speed Slider */}
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-slate-300 mb-2">
              <span className="font-medium">Tốc độ thuyết minh: <strong className="text-indigo-400 font-mono">{speed.toFixed(1)}x</strong></span>
              <span className="text-slate-500">(0.8x Chậm - 1.5x Nhanh)</span>
            </div>
            <input
              id="slider-voice-speed"
              type="range"
              min="0.8"
              max="1.5"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>0.8x</span>
              <span>1.0x (Chuẩn)</span>
              <span>1.2x</span>
              <span>1.5x</span>
            </div>
          </div>
        </section>

        {/* STEP 5 & 6: MUSIC & VOLUME */}
        <section className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 sm:p-7 space-y-5">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
              4
            </span>
            <h2 className="text-base font-bold text-white">Background Music (BGM) & Volume</h2>
          </div>

          {/* Music Track Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {musicTracks.map((m) => (
              <div
                key={m.id}
                id={`music-card-${m.id}`}
                onClick={() => setMusicId(m.id)}
                className={`p-4 rounded-2xl border cursor-pointer transition flex items-center justify-between ${
                  musicId === m.id
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-lg">
                    🎵
                  </div>
                  <div>
                    <div className="font-bold text-xs text-white">{m.title}</div>
                    <div className="text-[11px] text-slate-400">{m.mood} · {m.bpm} BPM</div>
                  </div>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {Math.floor(m.duration_sec / 60)}:{(m.duration_sec % 60).toString().padStart(2, "0")}
                </span>
              </div>
            ))}
          </div>

          {/* Volume Slider */}
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-slate-300 mb-2">
              <span className="font-medium">Âm lượng nhạc nền: <strong className="text-indigo-400 font-mono">{musicVolume}%</strong></span>
              <span className="text-slate-500 font-sans">Khuyến nghị 15% (không lấn giọng đọc)</span>
            </div>
            <input
              id="slider-music-volume"
              type="range"
              min="0"
              max="100"
              step="5"
              value={musicVolume}
              onChange={(e) => setMusicVolume(parseInt(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        </section>

        {/* STEP 7 & 8: VISUAL STYLE & ASPECT RATIO */}
        <section className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 sm:p-7 space-y-6">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
              5
            </span>
            <h2 className="text-base font-bold text-white">Visual Style & Aspect Ratio</h2>
          </div>

          {/* Style Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-3">
              Phong cách mỹ thuật Whiteboard
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {templates.map((tpl) => (
                <div
                  key={tpl.id}
                  id={`style-card-${tpl.id}`}
                  onClick={() => setVisualStyle(tpl.id)}
                  className={`p-3.5 rounded-2xl border cursor-pointer transition flex flex-col justify-between ${
                    visualStyle === tpl.id
                      ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                      : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-xs text-white">{tpl.name}</span>
                    <span
                      className="w-3 h-3 rounded-full border border-slate-600"
                      style={{ backgroundColor: tpl.bg_color_hex }}
                    ></span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{tpl.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Aspect Ratio Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-3">
              Tỉ lệ khung hình (Aspect Ratio)
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "16:9", label: "16:9 Landscape", desc: "YouTube / TV / Web", icon: "🖥️" },
                { id: "9:16", label: "9:16 Vertical", desc: "TikTok / Reels / Shorts", icon: "📱" },
                { id: "1:1", label: "1:1 Square", desc: "Instagram / Feed", icon: "⏹️" },
              ].map((ratio) => (
                <button
                  type="button"
                  key={ratio.id}
                  id={`btn-ratio-${ratio.id.replace(":", "-")}`}
                  onClick={() => setAspectRatio(ratio.id)}
                  className={`p-3.5 rounded-2xl border text-center transition flex flex-col items-center justify-center gap-1 ${
                    aspectRatio === ratio.id
                      ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                      : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                  }`}
                >
                  <span className="text-xl">{ratio.icon}</span>
                  <span className="font-bold text-xs">{ratio.label}</span>
                  <span className="text-[10px] text-slate-500">{ratio.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* GENERATE ACTION BUTTON */}
        <div className="pt-2">
          <button
            id="btn-generate-pipeline"
            type="submit"
            disabled={isGenerating}
            className={`w-full py-4 rounded-2xl font-extrabold text-sm sm:text-base text-white shadow-2xl transition flex items-center justify-center gap-3 ${
              isGenerating
                ? "bg-indigo-700 cursor-not-allowed opacity-80"
                : "bg-gradient-to-r from-indigo-500 via-violet-600 to-indigo-600 hover:from-indigo-600 hover:to-violet-700 active:scale-[0.99] shadow-indigo-600/30"
            }`}
          >
            {isGenerating ? (
              <>
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Đang điều phối AI Agents & Media Engine...</span>
              </>
            ) : (
              <>
                <span>✨</span>
                <span>Generate Video (Review & Render)</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
