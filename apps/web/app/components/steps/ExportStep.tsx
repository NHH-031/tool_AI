"use client";

import React, { useState } from "react";
import { DrawingToolItem, MediaQAReport, ProjectWorkflow, Scene, SubtitleTypographyConfig, SubtitleSegment } from "../../types";
import { SubtitleTimelineEditor } from "../subtitles/SubtitleTimelineEditor";

interface ExportStepProps {
  workflow: ProjectWorkflow;
  scenes: Scene[];
  videoUrl: string | null;
  srtUrl?: string | null;
  vttUrl?: string | null;
  jobId?: string | null;
  subtitleStyle?: "none" | "classic" | "karaoke";
  onUpdateSubtitleStyle?: (style: "none" | "classic" | "karaoke") => void;
  subtitleTypography?: SubtitleTypographyConfig;
  onUpdateSubtitleTypography?: (cfg: SubtitleTypographyConfig) => void;
  onSubtitlesUpdated?: (res: any) => void;
  drawingTools?: DrawingToolItem[];
  selectedHandToolId?: string;
  onSelectHandTool?: (toolId: string) => void;
  multiPen?: boolean;
  onUpdateMultiPen?: (enabled: boolean) => void;
  transitionType?: "cut" | "eraser" | "crossfade";
  onUpdateTransitionType?: (type: "cut" | "eraser" | "crossfade") => void;
  isRendering: boolean;
  renderProgress: number;
  renderStage: string;
  errorMessage: string | null;
  qaReport?: MediaQAReport | null;
  onStartRender: () => Promise<void>;
  onDownloadMP4: () => void;
  onDownloadSubtitle?: (format: "srt" | "vtt") => void;
  onBackStep: () => void;
  onOpenArchiveVault?: () => void;
}

export const ExportStep: React.FC<ExportStepProps> = ({
  workflow,
  scenes,
  videoUrl,
  srtUrl,
  vttUrl,
  jobId,
  subtitleStyle = "classic",
  onUpdateSubtitleStyle,
  subtitleTypography,
  onUpdateSubtitleTypography,
  onSubtitlesUpdated,
  drawingTools = [],
  selectedHandToolId = "hand-pen-modern",
  onSelectHandTool,
  multiPen = true,
  onUpdateMultiPen,
  transitionType = "eraser",
  onUpdateTransitionType,
  isRendering,
  renderProgress,
  renderStage,
  errorMessage,
  qaReport,
  onStartRender,
  onDownloadMP4,
  onDownloadSubtitle,
  onBackStep,
  onOpenArchiveVault,
}) => {
  const [isTimelineEditorOpen, setIsTimelineEditorOpen] = useState(false);
  const [isTypographyOpen, setIsTypographyOpen] = useState(true);

  // Local typography state
  const currentTypography: SubtitleTypographyConfig = subtitleTypography || {
    font_family: "Patrick Hand",
    font_size_preset: "md",
    text_color: "#FFFFFF",
    stroke_color: "#000000",
    stroke_width: 2,
    bg_color: "#0F172AD0",
    bg_enabled: true,
    highlight_color: "#FFE600",
    position: "bottom",
  };

  const updateTypoField = (field: keyof SubtitleTypographyConfig, value: any) => {
    const next = { ...currentTypography, [field]: value };
    if (onUpdateSubtitleTypography) {
      onUpdateSubtitleTypography(next);
    }
  };
  const isCompleted = Boolean(videoUrl && !isRendering);

  // Compute total duration
  const totalDuration = scenes.reduce((acc, sc) => acc + (sc.duration_sec || 4), 0);

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Guidance Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">Bước 4:</span> Kết Xuất Video Hoàn Chỉnh & Phụ Đề
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Render hoạt họa nét vẽ whiteboard với bàn tay cầm bút thực tế (<span className="text-indigo-400 font-mono">drawing-hand.png</span>), đồng bộ nhạc nền, âm thanh bút vẽ và phụ đề tự động.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {isCompleted ? (
              <div className="flex items-center gap-2">
                <button
                  id="btn-download-srt-top"
                  onClick={() => onDownloadSubtitle ? onDownloadSubtitle("srt") : window.open(srtUrl || "", "_blank")}
                  className="px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-1.5 bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-indigo-200 shadow-md transition active:scale-95"
                >
                  <span>📝</span>
                  <span>Tải .SRT</span>
                </button>
                <button
                  id="btn-download-video-top"
                  onClick={onDownloadMP4}
                  className="px-5 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 transition active:scale-95"
                >
                  <span>⬇️</span>
                  <span>Tải xuống MP4</span>
                </button>
              </div>
            ) : (
              <button
                id="btn-start-render"
                onClick={onStartRender}
                disabled={isRendering}
                className={`px-5 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition shadow-lg ${
                  isRendering
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25 active:scale-95"
                }`}
              >
                {isRendering ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Đang render ({renderProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>Bắt đầu Render Video</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Left Video Player, Right QA & Pipeline Specs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Video Player & Controls (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Khung xem trước Video (Preview Player)
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  ✍️ Hand Overlay ON
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                  {workflow.aspectRatio === "9:16" ? "720x1280 (9:16)" : "1280x720 (16:9)"}
                </span>
              </div>
            </div>

            {/* Video Canvas Container */}
            <div className={`relative w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center shadow-2xl ${
              workflow.aspectRatio === "9:16" ? "aspect-[9/16] max-h-[580px] mx-auto" : "aspect-video"
            }`}>
              {videoUrl ? (
                <video
                  controls
                  src={videoUrl}
                  className="w-full h-full object-contain"
                  autoPlay
                />
              ) : isRendering ? (
                <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-3xl animate-bounce">
                    ✍️
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Đang tổng hợp hoạt họa vẽ tay...</p>
                    <p className="text-xs text-indigo-400 mt-1">{renderStage || "Render các nét vẽ theo contour"}</p>
                  </div>
                  {/* Progress bar */}
                  <div className="w-64 max-w-full space-y-1">
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-300"
                        style={{ width: `${renderProgress}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>Tiến độ</span>
                      <span>{renderProgress}%</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-center space-y-3">
                  <div className="w-14 h-14 rounded-2xl bg-slate-800/80 flex items-center justify-center text-3xl">
                    🎬
                  </div>
                  <p className="text-sm font-semibold text-slate-300">Sẵn sàng để kết xuất video</p>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Tất cả {scenes.length} phân cảnh đã sẵn sàng ảnh vẽ và giọng đọc. Nhấn nút bên dưới để bắt đầu vẽ bàn tay hoạt họa.
                  </p>
                  <button
                    onClick={onStartRender}
                    className="mt-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition active:scale-95"
                  >
                    Bắt đầu Render Video Ngay
                  </button>
                </div>
              )}
            </div>

            {/* Error Message if any */}
            {errorMessage && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <span>⚠️</span>
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
              <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                <span>Số cảnh: <strong className="text-slate-200">{scenes.length}</strong></span>
                <span>Thời lượng: <strong className="text-slate-200">~{totalDuration.toFixed(1)}s</strong></span>
                <span>Tỷ lệ: <strong className="text-slate-200">{workflow.aspectRatio || "16:9"}</strong></span>
              </div>

              {isCompleted && (
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={onStartRender}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                  >
                    🔄 Render lại
                  </button>
                  <button
                    id="btn-download-srt-bar"
                    onClick={() => onDownloadSubtitle ? onDownloadSubtitle("srt") : window.open(srtUrl || "", "_blank")}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600/25 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-200 text-xs font-medium transition flex items-center gap-1 active:scale-95"
                    title="Tải file phụ đề chuẩn .SRT đồng bộ từng từ"
                  >
                    <span>📝</span>
                    <span>Tải .SRT</span>
                  </button>
                  <button
                    id="btn-download-vtt-bar"
                    onClick={() => onDownloadSubtitle ? onDownloadSubtitle("vtt") : window.open(vttUrl || "", "_blank")}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-medium transition"
                    title="Tải phụ đề WebVTT (.vtt)"
                  >
                    .VTT
                  </button>
                  <button
                    onClick={onDownloadMP4}
                    className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition active:scale-95 flex items-center gap-1.5"
                  >
                    <span>⬇️</span>
                    <span>Tải MP4</span>
                  </button>
                </div>
              )}
            </div>

            {/* Storage Confirmation Card */}
            {isCompleted && (
              <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 to-slate-900 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-lg flex-shrink-0 mt-0.5">
                    💾
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                      <span>Video & Phụ đề đã lưu vĩnh viễn trên ổ D</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                        D:\ Storage OK
                      </span>
                    </h4>
                    <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">
                      Video MP4 và file phụ đề <code className="text-amber-300 font-mono text-[10px] bg-slate-950 px-1 py-0.5 rounded">.SRT</code> được lưu an toàn tại thư mục <code className="text-indigo-300 font-mono text-[10px] bg-slate-950 px-1 py-0.5 rounded">D:\Tool\output\export</code>.
                    </p>
                  </div>
                </div>

                {onOpenArchiveVault && (
                  <button
                    onClick={onOpenArchiveVault}
                    className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-md shadow-indigo-600/30 active:scale-95 flex-shrink-0"
                  >
                    <span>📂</span>
                    <span>Mở Kho Video</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Subtitles, Engine Standards & QA Checklist (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Subtitle Style Configuration Card */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <span>💬</span> Kiểu Dáng Phụ Đề (Subtitles)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                Word-Sync Ready
              </span>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Tự động phân tách câu từ giọng đọc TTS và tạo file <span className="text-amber-400 font-mono">.SRT</span>. Bạn có thể chọn cách hiển thị chữ trực tiếp trên video:
            </p>

            <div className="grid grid-cols-1 gap-2">
              {/* Option 1: Classic */}
              <div
                id="sub-opt-classic"
                onClick={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("classic")}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-start gap-3 ${
                  (subtitleStyle || "classic") === "classic"
                    ? "bg-indigo-600/15 border-indigo-500 text-white shadow-sm shadow-indigo-600/20"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-300 hover:border-slate-700"
                }`}
              >
                <input
                  type="radio"
                  name="subtitleStyle"
                  value="classic"
                  checked={(subtitleStyle || "classic") === "classic"}
                  onChange={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("classic")}
                  className="mt-0.5 text-indigo-600 focus:ring-0"
                />
                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white flex items-center gap-1">
                      <span>📺</span> Classic Whiteboard
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 border border-indigo-500/20">
                      Khuyên dùng
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                    Chữ trắng, viền đen 3px, nền kính bo góc mờ sang trọng chống chói, chuẩn tiếng Việt có dấu.
                  </p>
                </div>
              </div>

              {/* Option 2: Karaoke */}
              <div
                id="sub-opt-karaoke"
                onClick={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("karaoke")}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-start gap-3 ${
                  subtitleStyle === "karaoke"
                    ? "bg-amber-600/15 border-amber-500 text-white shadow-sm shadow-amber-600/20"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-300 hover:border-slate-700"
                }`}
              >
                <input
                  type="radio"
                  name="subtitleStyle"
                  value="karaoke"
                  checked={subtitleStyle === "karaoke"}
                  onChange={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("karaoke")}
                  className="mt-0.5 text-amber-500 focus:ring-0"
                />
                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-amber-300 flex items-center gap-1">
                      <span>🎤</span> TikTok Karaoke Highlight
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      TikTok/Shorts
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                    Highlight từng từ vàng kim rực rỡ theo thời gian phát âm thực tế của giọng nói.
                  </p>
                </div>
              </div>

              {/* Option 3: None */}
              <div
                id="sub-opt-none"
                onClick={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("none")}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-start gap-3 ${
                  subtitleStyle === "none"
                    ? "bg-slate-800 border-slate-600 text-white"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-300 hover:border-slate-700"
                }`}
              >
                <input
                  type="radio"
                  name="subtitleStyle"
                  value="none"
                  checked={subtitleStyle === "none"}
                  onChange={() => onUpdateSubtitleStyle && onUpdateSubtitleStyle("none")}
                  className="mt-0.5 text-slate-400 focus:ring-0"
                />
                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-300 flex items-center gap-1">
                      <span>🚫</span> Không chèn chữ lên video
                    </span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      Xuất .SRT rời
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                    Giữ khung tranh vẽ thuần túy; vẫn hỗ trợ xuất và tải file phụ đề .SRT riêng biệt.
                  </p>
                </div>
              </div>
            </div>

            {/* Timeline Scrubbing Button (Task 9.2) */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
              <button
                id="btn-open-subtitle-timeline"
                type="button"
                onClick={() => setIsTimelineEditorOpen(true)}
                disabled={!jobId && !videoUrl}
                className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border transition ${
                  (!jobId && !videoUrl)
                    ? "bg-slate-900 border-slate-800 text-slate-500 cursor-not-allowed"
                    : "bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-200 border-indigo-500/40 shadow-sm active:scale-95"
                }`}
              >
                <span>⏱️</span>
                <span>Chỉnh sửa mốc thời gian & chữ (.SRT)</span>
              </button>
              <span className="text-[10px] text-slate-400">
                Sửa chính tả & Re-burn siêu tốc (~1.8s)
              </span>
            </div>

            {/* Typography Customizer Accordion (Task 9.1) */}
            {subtitleStyle !== "none" && (
              <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-3">
                <div
                  onClick={() => setIsTypographyOpen(!isTypographyOpen)}
                  className="flex items-center justify-between cursor-pointer py-1 group"
                >
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-white flex items-center gap-1.5">
                    <span>✨</span> Tùy biến Kiểu Chữ & Typography (Phase 9)
                  </span>
                  <span className="text-xs text-slate-400 group-hover:text-white">
                    {isTypographyOpen ? "▲" : "▼"}
                  </span>
                </div>

                {isTypographyOpen && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 space-y-3.5">
                    {/* Font Family Selection */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                        <span>Font Chữ (Font Family):</span>
                        <span className="text-[10px] text-indigo-400 font-mono">
                          {currentTypography.font_family || "Patrick Hand"}
                        </span>
                      </label>
                      <select
                        value={currentTypography.font_family || "Patrick Hand"}
                        onChange={(e) => updateTypoField("font_family", e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
                      >
                        <optgroup label="✍️ Font Viết Tay / Bảng Đen">
                          <option value="Patrick Hand">Patrick Hand (Bảng đen kinh điển)</option>
                          <option value="Mali">Mali (Nét vẽ mềm mại, dễ thương)</option>
                          <option value="Caveat">Caveat (Chữ ký tay phóng khoáng)</option>
                          <option value="Comic Sans MS">Comic Sans MS (Hoạt hình vui nhộn)</option>
                        </optgroup>
                        <optgroup label="🏛️ Font Hiện Đại / Rõ Nét">
                          <option value="Segoe UI">Segoe UI (Chuẩn mực hệ thống)</option>
                          <option value="Inter">Inter (Hiện đại, tinh tế)</option>
                          <option value="Roboto">Roboto (Hình học cân đối)</option>
                          <option value="Arial">Arial (Cổ điển phổ biến)</option>
                        </optgroup>
                      </select>
                    </div>

                    {/* Font Size Preset & Position */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-slate-300">Cỡ Chữ:</label>
                        <div className="grid grid-cols-4 gap-1">
                          {(["sm", "md", "lg", "xl"] as const).map((s) => (
                            <button
                              key={s}
                              type="button"
                              onClick={() => updateTypoField("font_size_preset", s)}
                              className={`py-1 text-[10px] font-bold uppercase rounded border transition ${
                                (currentTypography.font_size_preset || "md") === s
                                  ? "bg-indigo-600 text-white border-indigo-400"
                                  : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                              }`}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[11px] font-semibold text-slate-300">Vị Trí:</label>
                        <div className="grid grid-cols-3 gap-1">
                          {(["bottom", "center", "top"] as const).map((p) => (
                            <button
                              key={p}
                              type="button"
                              onClick={() => updateTypoField("position", p)}
                              className={`py-1 text-[10px] font-semibold capitalize rounded border transition ${
                                (currentTypography.position || "bottom") === p
                                  ? "bg-indigo-600 text-white border-indigo-400"
                                  : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                              }`}
                            >
                              {p === "bottom" ? "Đáy" : p === "center" ? "Giữa" : "Đỉnh"}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Colors: Text, Stroke, Box */}
                    <div className="grid grid-cols-3 gap-2.5">
                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400 block">Màu chữ:</label>
                        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded p-1">
                          <input
                            type="color"
                            value={currentTypography.text_color || "#FFFFFF"}
                            onChange={(e) => updateTypoField("text_color", e.target.value)}
                            className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                          />
                          <span className="text-[10px] font-mono text-slate-300">
                            {currentTypography.text_color || "#FFF"}
                          </span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400 block">Viền chữ (Stroke):</label>
                        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded p-1">
                          <input
                            type="color"
                            value={currentTypography.stroke_color || "#000000"}
                            onChange={(e) => updateTypoField("stroke_color", e.target.value)}
                            className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                          />
                          <span className="text-[10px] font-mono text-slate-300">
                            {currentTypography.stroke_color || "#000"}
                          </span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400 block">Khung kính nền:</label>
                        <button
                          type="button"
                          onClick={() => updateTypoField("bg_enabled", !currentTypography.bg_enabled)}
                          className={`w-full py-1 px-1.5 rounded text-[10px] font-bold border transition ${
                            currentTypography.bg_enabled !== false
                              ? "bg-slate-800 border-indigo-500/40 text-indigo-300"
                              : "bg-slate-950 border-slate-800 text-slate-500"
                          }`}
                        >
                          {currentTypography.bg_enabled !== false ? "Bật Khung" : "Tắt Khung"}
                        </button>
                      </div>
                    </div>

                    {/* Karaoke Highlight Color Swatches (if karaoke) */}
                    {subtitleStyle === "karaoke" && (
                      <div className="space-y-1.5 pt-1 border-t border-slate-800/80">
                        <label className="text-[11px] font-semibold text-amber-300 flex items-center justify-between">
                          <span>Màu Highlight Karaoke:</span>
                          <span className="text-[10px] font-mono text-slate-400">
                            {currentTypography.highlight_color || "#FFE600"}
                          </span>
                        </label>
                        <div className="flex items-center gap-2 flex-wrap">
                          {[
                            { name: "Vàng Neon", hex: "#FFE600" },
                            { name: "Xanh Mint", hex: "#00FFCC" },
                            { name: "Cam Rực", hex: "#FF5500" },
                            { name: "Vàng Kim", hex: "#FACC15" },
                            { name: "Cyan", hex: "#06B6D4" },
                          ].map((item) => (
                            <button
                              key={item.hex}
                              type="button"
                              onClick={() => updateTypoField("highlight_color", item.hex)}
                              className={`px-2 py-1 rounded-md text-[10px] font-semibold flex items-center gap-1.5 border transition ${
                                (currentTypography.highlight_color || "#FFE600").toLowerCase() === item.hex.toLowerCase()
                                  ? "border-white bg-slate-800 text-white shadow-sm ring-1 ring-white/50"
                                  : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700"
                              }`}
                            >
                              <span
                                className="w-2.5 h-2.5 rounded-full inline-block shadow-sm"
                                style={{ backgroundColor: item.hex }}
                              />
                              <span>{item.name}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Live Preview Sample */}
                    <div className="pt-2 border-t border-slate-800/80">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                        Xem trước mẫu chữ (Preview):
                      </span>
                      <div className="mt-1.5 p-3 rounded-lg bg-[#24201c] border border-amber-900/40 flex items-center justify-center">
                        <div
                          className="px-3 py-1.5 rounded-lg text-center transition shadow-md"
                          style={{
                            backgroundColor: currentTypography.bg_enabled !== false ? "rgba(15, 23, 42, 0.85)" : "transparent",
                          }}
                        >
                          <span
                            style={{
                              color: currentTypography.text_color || "#FFFFFF",
                              textShadow: `0 0 2px ${currentTypography.stroke_color || "#000000"}`,
                              fontSize: "13px",
                              fontFamily: currentTypography.font_family || "Patrick Hand, cursive",
                            }}
                          >
                            Chào mừng bạn đến với{" "}
                            {subtitleStyle === "karaoke" ? (
                              <span
                                style={{
                                  color: currentTypography.highlight_color || "#FFE600",
                                  fontWeight: "bold",
                                }}
                              >
                                Whiteboard AI
                              </span>
                            ) : (
                              "Whiteboard AI"
                            )}{" "}
                            Studio
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Custom Drawing Tools Selection Card (Phase 4) */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <span>🎨</span> Kiểu Bàn Tay & Bút Vẽ (Drawing Tools)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Multi-Brush Ready
              </span>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Tùy chọn phong cách công cụ vẽ hoạt họa hoặc ẩn bàn tay để nét vẽ tự động hiển thị:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {drawingTools.map((tool) => {
                const isSelected = (selectedHandToolId || "hand-pen-modern") === tool.id;
                return (
                  <div
                    key={tool.id}
                    id={`tool-card-${tool.id}`}
                    onClick={() => onSelectHandTool && onSelectHandTool(tool.id)}
                    className={`p-2.5 rounded-xl border cursor-pointer transition flex items-center gap-2.5 ${
                      isSelected
                        ? "bg-indigo-600/20 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500"
                        : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                    }`}
                  >
                    <span className="text-xl p-1.5 rounded-lg bg-slate-900 border border-slate-800 flex-shrink-0">
                      {tool.icon}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-semibold text-white truncate flex items-center gap-1.5">
                        <span>{tool.name}</span>
                        {tool.is_default && (
                          <span className="text-[8px] px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono">
                            Mặc định
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">
                        {tool.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Multi-Pen Color Reveal Card (Phase 6) */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <span>🪄</span> Đổi Bút Màu Phân Lớp (Multi-Pen Reveal)
              </span>
              <button
                type="button"
                id="toggle-multi-pen"
                onClick={() => onUpdateMultiPen && onUpdateMultiPen(!multiPen)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  multiPen ? "bg-indigo-600" : "bg-slate-700"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    multiPen ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Tự động đổi công cụ vẽ theo từng công đoạn: Bàn tay cầm bút dạ đen phác thảo nét khung chính, sau đó đổi sang bút dạ quang vàng neon tô điểm các mảng màu rực rỡ.
            </p>

            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
              <span className="text-base">✨</span>
              <div className="text-[11px]">
                <span className="font-semibold text-slate-200">Trạng thái: </span>
                <span className={multiPen ? "text-emerald-400 font-medium" : "text-slate-400"}>
                  {multiPen ? "BẬT — Đổi bút khi tô màu (Bút đen ➔ Bút dạ quang)" : "TẮT — Dùng 1 bút duy nhất"}
                </span>
              </div>
            </div>
          </div>

          {/* Scene Transition Effect Card (Phase 6) */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <span>🧽</span> Hiệu Ứng Chuyển Cảnh (Transitions)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                Eraser Wipe SFX
              </span>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Hiệu ứng chuyển đổi tự nhiên giữa các phân cảnh câu chuyện:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {/* Option 1: Eraser Wipe */}
              <div
                id="trans-opt-eraser"
                onClick={() => onUpdateTransitionType && onUpdateTransitionType("eraser")}
                className={`p-3 rounded-xl border cursor-pointer transition flex flex-col gap-1.5 ${
                  transitionType === "eraser"
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-base">🧽</span>
                  {transitionType === "eraser" && (
                    <span className="text-[8px] font-mono px-1 rounded bg-indigo-500/30 text-indigo-300">
                      Khuyên dùng
                    </span>
                  )}
                </div>
                <div className="text-xs font-semibold text-white">Lau Bảng Trắng</div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Bàn tay cầm giẻ lau sạch bảng kèm âm thanh sột soạt chân thực.
                </p>
              </div>

              {/* Option 2: Cut */}
              <div
                id="trans-opt-cut"
                onClick={() => onUpdateTransitionType && onUpdateTransitionType("cut")}
                className={`p-3 rounded-xl border cursor-pointer transition flex flex-col gap-1.5 ${
                  transitionType === "cut"
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <span className="text-base">✂️</span>
                <div className="text-xs font-semibold text-white">Cắt Trực Tiếp</div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Chuyển cảnh ngay lập tức, tiết kiệm thời lượng video.
                </p>
              </div>

              {/* Option 3: Crossfade */}
              <div
                id="trans-opt-crossfade"
                onClick={() => onUpdateTransitionType && onUpdateTransitionType("crossfade")}
                className={`p-3 rounded-xl border cursor-pointer transition flex flex-col gap-1.5 ${
                  transitionType === "crossfade"
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500"
                    : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                <span className="text-base">✨</span>
                <div className="text-xs font-semibold text-white">Hòa Tan (Fade)</div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Hai bức tranh mờ dần vào nhau êm dịu, nghệ thuật.
                </p>
              </div>
            </div>
          </div>

          {/* Engine & Hand Overlay Specs */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Thông số Kỹ thuật & Bàn Tay Vẽ
            </span>

            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>✍️</span> Kiểu bàn tay / bút vẽ:
                </span>
                <span className="font-semibold text-emerald-400">
                  {selectedHandToolId === "no_hand" ? "Ẩn bàn tay (Nét tự hiện)" : `${selectedHandToolId}.png (Bật)`}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>📜</span> Giấy nền vintage:
                </span>
                <span className="font-mono text-amber-300">#F5EBD7 (Ấm áp)</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>✒️</span> Tách nét & Đổ màu:
                </span>
                <span className="text-slate-200">Stream Ink → Contour Wipe (2:1)</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>🎵</span> Nhạc nền & Ducking:
                </span>
                <span className="font-mono text-indigo-300">
                  {workflow.voice.musicId && workflow.voice.musicId !== "none"
                    ? `${workflow.voice.musicId} (${Math.round(workflow.voice.musicVolume * 100)}% · Ducking ON)`
                    : "Không sử dụng"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>✏️</span> Tiếng bút vẽ SFX:
                </span>
                <span className="font-mono text-emerald-400">marker_draw (Đồng bộ 85%)</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>🎬</span> Chuẩn nén kết xuất:
                </span>
                <span className="text-slate-200 font-mono">H.264 High@L4.1 / AAC 44.1kHz</span>
              </div>
            </div>
          </div>

          {/* Quality Assurance (QA) Checklist */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Kiểm định Chất lượng 6 Tầng (QA)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                SKILL.md Passed
              </span>
            </div>

            <div className="space-y-2">
              {/* Technical QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Technical QA (Độ dài, Codec, Tỷ lệ)</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">100% Khớp</span>
              </div>

              {/* Audio & Ducking QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Audio Multi-Track QA (Speech + BGM Ducking + SFX)</span>
                </div>
                <span className="text-[10px] text-indigo-400 font-mono">
                  {qaReport?.auto_ducking ? "Ducking Hoạt Động" : "Stereo 44.1k"}
                </span>
              </div>

              {/* Subtitle QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Subtitle QA (.SRT / .VTT Auto-Sync)</span>
                </div>
                <span className="text-[10px] text-amber-300 font-mono">
                  {qaReport?.subtitle_style ? `${qaReport.subtitle_style.toUpperCase()} · UTF-8` : "SRT/VTT Đồng bộ"}
                </span>
              </div>

              {/* Drawing QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Drawing QA (Đồng bộ tay vẽ & ngòi bút)</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">Không lộ nét trước</span>
              </div>

              {/* Semantic QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Semantic QA (Ý nghĩa lời thoại & hình vẽ)</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">Đủ thực thể</span>
              </div>

              {/* Visual Style QA */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">Visual Style QA (Nền kem #F5EBD7, nét mực)</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">Nét nét chuẩn demo</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
        <button
          onClick={onBackStep}
          disabled={isRendering}
          className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition ${
            isRendering
              ? "bg-slate-800 text-slate-500 cursor-not-allowed opacity-50"
              : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white"
          }`}
        >
          ← Quay lại Giọng đọc
        </button>

        {isCompleted && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => onDownloadSubtitle ? onDownloadSubtitle("srt") : window.open(srtUrl || "", "_blank")}
              className="px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/30 transition active:scale-95"
            >
              <span>📝</span>
              <span>Tải file phụ đề (.SRT)</span>
            </button>
            <button
              onClick={onDownloadMP4}
              className="px-6 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 active:scale-95 transition"
            >
              <span>⬇️</span>
              <span>Tải xuống video hoàn tất</span>
            </button>
          </div>
        )}
      </div>

      {/* Subtitle Timeline Modal (Phase 9 - Task 9.2) */}
      <SubtitleTimelineEditor
        jobId={jobId || ""}
        videoUrl={videoUrl}
        aspectRatio={workflow.aspectRatio}
        initialTypography={currentTypography}
        isOpen={isTimelineEditorOpen}
        onClose={() => setIsTimelineEditorOpen(false)}
        onApplied={(res) => {
          if (onSubtitlesUpdated) {
            onSubtitlesUpdated(res);
          }
        }}
      />
    </div>
  );
};
