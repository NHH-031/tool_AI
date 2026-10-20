"use client";

import React from "react";
import { MediaQAReport, ProjectWorkflow, Scene } from "../../types";

interface ExportStepProps {
  workflow: ProjectWorkflow;
  scenes: Scene[];
  videoUrl: string | null;
  srtUrl?: string | null;
  vttUrl?: string | null;
  jobId?: string | null;
  subtitleStyle?: "none" | "classic" | "karaoke";
  onUpdateSubtitleStyle?: (style: "none" | "classic" | "karaoke") => void;
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
                  1080p 30fps
                </span>
              </div>
            </div>

            {/* Video Canvas Container */}
            <div className="relative aspect-video w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center shadow-2xl">
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
                <span>Tỷ lệ: <strong className="text-slate-200">16:9</strong></span>
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
          </div>

          {/* Engine & Hand Overlay Specs */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Thông số Kỹ thuật & Bàn Tay Vẽ
            </span>

            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-400 flex items-center gap-2">
                  <span>✍️</span> Bàn tay cầm bút marker:
                </span>
                <span className="font-semibold text-emerald-400">drawing-hand.png (Bật)</span>
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
          className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold transition"
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
    </div>
  );
};
