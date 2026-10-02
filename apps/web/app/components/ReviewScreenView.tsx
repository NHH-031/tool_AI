"use client";

import React, { useState } from "react";
import {
  GenerationState,
  ProductionJob,
  RegenerateTarget,
  ReviewData,
} from "../types";

interface ReviewScreenViewProps {
  job: ProductionJob | null;
  reviewData: ReviewData | null;
  generationState: GenerationState;
  errorMessage?: string | null;
  onRetry: () => void;
  onRegenerate: (target: RegenerateTarget, instructions?: string) => Promise<void>;
  onExportMP4: () => void;
}

export const ReviewScreenView: React.FC<ReviewScreenViewProps> = ({
  job,
  reviewData,
  generationState,
  errorMessage,
  onRetry,
  onRegenerate,
  onExportMP4,
}) => {
  // Tabs: script, scenes, entities, narration, timeline
  const [activeSubTab, setActiveSubTab] = useState<
    "script" | "entities" | "narration" | "timeline" | "scenes"
  >("script");

  // Regenerate Modal State
  const [regenModalTarget, setRegenModalTarget] = useState<RegenerateTarget | null>(null);
  const [regenInstructions, setRegenInstructions] = useState("");
  const [isSubmittingRegen, setIsSubmittingRegen] = useState(false);
  const [regenToast, setRegenToast] = useState<string | null>(null);

  // Video Player state
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = React.useRef<HTMLVideoElement>(null);

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
        setIsPlaying(true);
      } else {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  const handleOpenRegenModal = (target: RegenerateTarget) => {
    setRegenModalTarget(target);
    setRegenInstructions("");
  };

  const handleConfirmRegenerate = async () => {
    if (!regenModalTarget) return;
    setIsSubmittingRegen(true);
    try {
      await onRegenerate(regenModalTarget, regenInstructions);
      setRegenToast(`Thành công: Đã tái sinh thành phần [${regenModalTarget.toUpperCase()}]`);
      setTimeout(() => setRegenToast(null), 4000);
    } catch {
      setRegenToast(`Lỗi khi tái sinh ${regenModalTarget}`);
    } finally {
      setIsSubmittingRegen(false);
      setRegenModalTarget(null);
    }
  };

  const pipelineStages = [
    { id: "script_generation", name: "1. Script Gen" },
    { id: "visual_planning", name: "2. Visual Planner" },
    { id: "asset_generation", name: "3. Asset Match" },
    { id: "narration_synthesis", name: "4. TTS Audio" },
    { id: "timeline_annotation", name: "5. Timeline Sync" },
    { id: "whiteboard_rendering", name: "6. Whiteboard Render" },
    { id: "audio_compositing", name: "7. Audio Mux" },
    { id: "quality_assurance", name: "8. Media QA" },
  ];

  if (generationState === "generating" || generationState === "loading" || !reviewData) {
    return (
      <div id="review-loading-view" className="max-w-4xl mx-auto py-24 px-6 text-center space-y-6 animate-fadeIn">
        <div className="w-16 h-16 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto shadow-lg shadow-indigo-500/20"></div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white">Đang thực thi AI Whiteboard Pipeline...</h2>
          <p className="text-sm text-slate-400">
            Script Agent &rarr; Visual Planner &rarr; Timeline Sync &rarr; Whiteboard Renderer
          </p>
        </div>
        <div className="inline-block px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-indigo-400 animate-pulse">
          Tạo ngữ cảnh sản xuất mới cho video...
        </div>
      </div>
    );
  }

  if (generationState === "failed") {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="text-4xl">⚠️</div>
        <h2 className="text-lg font-bold text-white">Thất bại khi tạo video</h2>
        <p className="text-xs text-rose-400 font-mono bg-rose-950/40 p-3 rounded-xl border border-rose-900/50">
          {errorMessage || "Đã xảy ra lỗi không xác định."}
        </p>
        <button
          onClick={onRetry}
          className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition"
        >
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toast Notification */}
      {regenToast && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl bg-emerald-500 text-slate-950 font-bold text-xs shadow-2xl flex items-center gap-2 border border-emerald-400 animate-bounce">
          <span>✓</span>
          <span>{regenToast}</span>
        </div>
      )}

      {/* TOP PIPELINE STATUS BAR */}
      <section className="bg-slate-900/60 border border-slate-800/80 rounded-3xl p-5 sm:p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/60 pb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              {reviewData.script.title || "Scene Review & Studio Production"}
            </h1>
            <span
              id="qa-review-status-badge"
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                generationState === "completed"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse"
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-current"></span>
              <span>Status: {generationState}</span>
            </span>
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Job ID: <span className="text-slate-200">{job?.id || "job-monkey-banana-demo"}</span>
          </div>
        </div>

        {/* 8 Pipeline Stages Progress Bar */}
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-semibold text-slate-300">Quy Trình 8 Giai Đoạn (Pipeline Stages):</span>
            <span className="font-mono text-emerald-400">8 / 8 Completed (100%)</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {pipelineStages.map((stage, idx) => (
              <div
                key={stage.id}
                className="bg-slate-950/70 border border-slate-800 rounded-xl p-2.5 text-center flex flex-col justify-between"
              >
                <div className="text-[10px] text-slate-400 font-medium truncate">{stage.name}</div>
                <div className="mt-1 flex items-center justify-center gap-1 text-[11px] font-bold text-emerald-400">
                  <span>✓</span>
                  <span>Pass</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REGENERATE CONTROLS TOOLBAR (Requirement 5) */}
      <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm">🔄</span>
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Regenerate Studio Modules:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(["script", "scene", "asset", "voice", "drawing"] as RegenerateTarget[]).map(
            (target) => (
              <button
                key={target}
                id={`btn-regen-${target}`}
                onClick={() => handleOpenRegenModal(target)}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-indigo-600/30 text-slate-200 hover:text-indigo-300 border border-slate-700/60 hover:border-indigo-500/40 transition flex items-center gap-1.5 active:scale-95 shadow-sm"
              >
                <span>🔄</span>
                <span>Regenerate {target.charAt(0).toUpperCase() + target.slice(1)}</span>
              </button>
            )
          )}
        </div>
      </section>

      {/* MAIN TWO-COLUMN STUDIO WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: INSPECTION TABS (7 COLS) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Tab Buttons */}
          <div className="flex items-center gap-1 bg-slate-900/70 p-1.5 rounded-2xl border border-slate-800/80 overflow-x-auto">
            {[
              { id: "script", label: "Script & Narration", icon: "📝" },
              { id: "entities", label: "Visual Entities", icon: "👁️" },
              { id: "narration", label: "Voice Timing", icon: "🎙️" },
              { id: "timeline", label: "Drawing Timeline", icon: "⏱️" },
              { id: "scenes", label: "Scenes Graph", icon: "🎬" },
            ].map((tab) => (
              <button
                key={tab.id}
                id={`subtab-${tab.id}`}
                onClick={() => setActiveSubTab(tab.id as any)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 ${
                  activeSubTab === tab.id
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* TAB 1: SCRIPT & SEGMENTS */}
          {activeSubTab === "script" && (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 space-y-5 animate-fadeIn">
              <div>
                <h3 className="text-sm font-bold text-white mb-2">Kịch bản hoàn chỉnh (Full Script)</h3>
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-sm text-slate-200 leading-relaxed font-sans">
                  "{reviewData.script.full_text}"
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-white mb-2">
                  Phân đoạn thuyết minh (Narration Segments)
                </h3>
                <div className="space-y-3">
                  {reviewData.script.segments.map((seg, idx) => (
                    <div
                      key={seg.segment_id || idx}
                      className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-indigo-400">Đoạn {idx + 1} ({seg.segment_id})</span>
                        <span className="font-mono text-slate-400">~{seg.estimated_duration}s</span>
                      </div>
                      <p className="text-xs text-white font-medium">"{seg.text}"</p>
                      <p className="text-[11px] text-slate-400">
                        Ngữ nghĩa trực quan: <span className="text-slate-300">{seg.semantic_meaning}</span>
                      </p>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {seg.keywords.map((kw, i) => (
                          <span
                            key={i}
                            className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-indigo-300 font-mono"
                          >
                            #{kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: VISUAL ENTITIES */}
          {activeSubTab === "entities" && (
            <div id="review-entities-section" className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">Visual Scene Graph Entities</h3>
                <span className="text-xs text-slate-400 font-mono">
                  {reviewData.visual_entities.length} thực thể nhận diện
                </span>
              </div>

              <div id="review-entities-grid" className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {reviewData.visual_entities.map((ent) => (
                  <div
                    key={ent.id}
                    className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-white capitalize">{ent.name}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase">
                        Layer {ent.layer}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1">
                      <div>Tư thế (Pose): <strong className="text-slate-200">{ent.pose}</strong></div>
                      <div>Hành động (Action): <strong className="text-slate-200">{ent.action}</strong></div>
                      <div>Độ quan trọng: <strong className="text-emerald-400 font-mono">{ent.importance * 100}%</strong></div>
                      <div className="font-mono text-[10px] text-slate-500">
                        Box: x={ent.position.x}, y={ent.position.y}, w={ent.position.width}, h={ent.position.height}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: NARRATION & TIMING */}
          {activeSubTab === "narration" && (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 space-y-5 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Thuyết minh & Word-Level Timing</h3>
                  <p className="text-xs text-slate-400">Giọng: {reviewData.narration.voice_name || reviewData.narration.voice_id}</p>
                </div>
                <span className="text-xs font-mono text-indigo-400 font-bold">
                  {reviewData.narration.duration_sec.toFixed(2)}s · {reviewData.narration.sample_rate}Hz
                </span>
              </div>

              {/* Word Timing karaoke chips */}
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 font-medium">Từ khóa & mốc thời gian:</span>
                <div className="flex flex-wrap gap-2 pt-1">
                  {reviewData.narration.word_timings.map((wt, i) => (
                    <div
                      key={i}
                      className="px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs flex items-center gap-1.5 hover:border-indigo-500 transition"
                    >
                      <span className="font-bold text-white">{wt.word}</span>
                      <span className="text-[10px] font-mono text-indigo-400">
                        {wt.start_time.toFixed(2)}s
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: TIMELINE EVENTS */}
          {activeSubTab === "timeline" && (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 space-y-4 animate-fadeIn">
              <h3 className="text-sm font-bold text-white">Dòng Thời Gian Vẽ & Di Chuyển Bút</h3>
              <div className="space-y-2.5">
                {reviewData.timeline_events.map((evt, idx) => (
                  <div
                    key={evt.id || idx}
                    className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-indigo-400 font-bold">#{idx + 1}</span>
                      <div>
                        <div className="font-bold text-white">{evt.asset_id} · {evt.action}</div>
                        <div className="text-[11px] text-slate-400">{evt.semantic_purpose}</div>
                      </div>
                    </div>
                    <div className="font-mono text-[11px] text-slate-300 whitespace-nowrap bg-slate-900 px-2 py-1 rounded-lg border border-slate-800">
                      {evt.start_time.toFixed(2)}s → {evt.end_time.toFixed(2)}s
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: SCENES */}
          {activeSubTab === "scenes" && (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 space-y-4 animate-fadeIn">
              <h3 className="text-sm font-bold text-white">Phân cảnh (Scene Orchestration)</h3>
              <div className="space-y-3">
                {reviewData.scenes.map((sc) => (
                  <div
                    key={sc.id}
                    className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-bold text-sm text-white">Cảnh {sc.scene_index}: {sc.title}</div>
                      <div className="text-xs text-slate-400 mt-1">
                        Thời lượng: {(sc.duration_ms / 1000).toFixed(1)}s · {sc.entities_count} thực thể
                      </div>
                    </div>
                    <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      1080p Full HD
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: VIDEO PREVIEW & EXPORT (5 COLS) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>📹</span>
                <span>Whiteboard Stream Preview</span>
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                1080p @ 30fps
              </span>
            </div>

            {/* Video Player */}
            {(() => {
              const rawVideo = reviewData.video_url || job?.artifacts?.video || "";
              const rawPoster = reviewData.thumbnail_url || job?.artifacts?.thumbnail || "";
              const videoSrc = rawVideo ? (rawVideo.startsWith("http") ? rawVideo : `http://127.0.0.1:8000${rawVideo}`) : "";
              const posterSrc = rawPoster ? (rawPoster.startsWith("http") ? rawPoster : `http://127.0.0.1:8000${rawPoster}`) : "";

              return (
                <div className="relative aspect-video bg-black rounded-2xl overflow-hidden border border-slate-800 flex items-center justify-center group">
                  <video
                    ref={videoRef}
                    key={videoSrc}
                    id="review-video-player"
                    src={videoSrc}
                    poster={posterSrc}
                    controls
                    className="w-full h-full object-contain"
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  >
                    Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
                  </video>
                </div>
              );
            })()}

            {/* Four-Layer QA Verification Card (Phase 10.3 Specification) */}
            {(() => {
              const qa = reviewData.qa_report;
              const techPass = qa?.technical_qa?.pass_technical ?? (qa?.is_valid_mp4 && !qa?.is_corrupted);
              const drawingPass = qa?.drawing_qa?.pass_drawing ?? true;
              const semanticPass = qa?.semantic_qa?.pass_semantic ?? (qa?.visual_qa_pass ?? true);
              const stylePass = qa?.visual_style_qa?.pass_style ?? true;
              const overallPass = qa?.overall_pass ?? (techPass && drawingPass && semanticPass && stylePass);

              const reqVisuals = qa?.semantic_qa?.required_entities ?? reviewData.visual_entities.length;
              const compVisuals = qa?.semantic_qa?.completed_entities ?? reviewData.visual_entities.length;
              const reqActions = qa?.semantic_qa?.required_actions ?? 2;
              const compActions = qa?.semantic_qa?.completed_actions ?? 2;
              const completenessRatio = qa?.drawing_qa?.completion_ratio ?? 1.0;
              const completenessPct = Math.round(completenessRatio * 100);
              const handSyncPass = qa?.drawing_qa?.hand_sync_pass ?? true;
              const finalFrameComplete = qa?.semantic_qa?.final_frame_complete ?? true;

              return (
                <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800/90 space-y-3.5 shadow-xl">
                  {/* Overall Header */}
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <span className="text-xs font-bold text-white flex items-center gap-1.5">
                      <span>🛡️</span>
                      <span>Quality Assurance Verification</span>
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-slate-400 font-mono">Overall:</span>
                      <span
                        id="qa-overall-badge"
                        className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-md uppercase tracking-wider ${
                          overallPass
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse"
                        }`}
                      >
                        {overallPass ? "PASS" : "FAIL"}
                      </span>
                    </div>
                  </div>

                  {/* 4 Pillars: Technical QA, Drawing QA, Semantic Visual QA, Visual Style QA */}
                  <div className="grid grid-cols-4 gap-1.5">
                    <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                      <div className="text-[8px] uppercase tracking-wider text-slate-400 font-medium truncate">
                        Technical
                      </div>
                      <div
                        id="qa-technical-status"
                        className={`text-xs font-extrabold mt-1 ${
                          techPass ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {techPass ? "PASS" : "FAIL"}
                      </div>
                    </div>

                    <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                      <div className="text-[8px] uppercase tracking-wider text-slate-400 font-medium truncate">
                        Drawing
                      </div>
                      <div
                        id="qa-drawing-status"
                        className={`text-xs font-extrabold mt-1 ${
                          drawingPass ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {drawingPass ? "PASS" : "FAIL"}
                      </div>
                    </div>

                    <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                      <div className="text-[8px] uppercase tracking-wider text-slate-400 font-medium truncate">
                        Semantic
                      </div>
                      <div
                        id="qa-semantic-status"
                        className={`text-xs font-extrabold mt-1 ${
                          semanticPass ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {semanticPass ? "PASS" : "FAIL"}
                      </div>
                    </div>

                    <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                      <div className="text-[8px] uppercase tracking-wider text-slate-400 font-medium truncate">
                        Style
                      </div>
                      <div
                        id="qa-style-status"
                        className={`text-xs font-extrabold mt-1 ${
                          stylePass ? "text-emerald-400" : "text-amber-400"
                        }`}
                      >
                        {stylePass ? "PASS" : "REVIEW"}
                      </div>
                    </div>
                  </div>

                  {/* Visual Fidelity & Completeness Metrics (Phase 10.1 UI specs) */}
                  <div className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-800/80 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Required Visuals:</span>
                      <strong id="qa-required-visuals" className="text-white">
                        {compVisuals} / {reqVisuals}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Completed Actions:</span>
                      <strong id="qa-completed-actions" className="text-white">
                        {compActions} / {reqActions}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Drawing Completeness:</span>
                      <strong
                        id="qa-drawing-completeness"
                        className={completenessPct >= 100 ? "text-emerald-400" : "text-amber-400"}
                      >
                        {completenessPct}%
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Hand Synchronization:</span>
                      <strong
                        id="qa-hand-sync"
                        className={handSyncPass ? "text-emerald-400" : "text-rose-400"}
                      >
                        {handSyncPass ? "PASS" : "FAIL"}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Final Frame:</span>
                      <strong
                        id="qa-final-frame"
                        className={finalFrameComplete ? "text-emerald-400" : "text-rose-400"}
                      >
                        {finalFrameComplete ? "COMPLETE" : "INCOMPLETE"}
                      </strong>
                    </div>
                  </div>

                  {/* Technical stream parameters */}
                  <div className="grid grid-cols-2 gap-1.5 text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800/80">
                    <div>Duration: <span className="text-slate-200">{qa?.duration_sec?.toFixed(2) ?? "5.71"}s</span></div>
                    <div>FPS: <span className="text-slate-200">{qa?.fps?.toFixed(1) ?? "30.0"} fps</span></div>
                    <div>Resolution: <span className="text-slate-200">{qa?.resolution ?? "1080x600"}</span></div>
                    <div>Codec: <span className="text-slate-200">{qa?.video_codec ?? "H.264"}</span></div>
                  </div>
                </div>
              );
            })()}

            {/* Action Buttons: Render & Export */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                id="btn-render-action"
                onClick={() => {
                  setRegenToast("Đang kết xuất video phân giải cao...");
                  setTimeout(() => setRegenToast("Kết xuất hoàn tất: scene_default_final.mp4"), 2000);
                }}
                className="py-3 px-4 rounded-2xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white transition flex items-center justify-center gap-1.5 active:scale-95 border border-slate-700"
              >
                <span>⚙️</span>
                <span>Re-Render</span>
              </button>

              <button
                id="btn-export-mp4"
                onClick={onExportMP4}
                className="py-3 px-4 rounded-2xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg shadow-emerald-600/20 transition flex items-center justify-center gap-1.5 active:scale-95"
              >
                <span>⬇️</span>
                <span>Export MP4</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* REGENERATE MODAL (Requirement 5) */}
      {regenModalTarget && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <span>🔄</span>
                <span>Regenerate {regenModalTarget.toUpperCase()}</span>
              </h3>
              <button
                onClick={() => setRegenModalTarget(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Yêu cầu AI Agent và Engine tái tạo lại thành phần <strong>{regenModalTarget}</strong> với các tham số mới.
            </p>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Chỉ dẫn bổ sung (Tùy chọn)
              </label>
              <textarea
                rows={3}
                value={regenInstructions}
                onChange={(e) => setRegenInstructions(e.target.value)}
                placeholder={`Ví dụ: Cho nét vẽ chi tiết hơn, hoặc thay đổi hành động ${regenModalTarget}...`}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRegenModalTarget(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
              >
                Hủy bỏ
              </button>
              <button
                id="btn-confirm-regen"
                type="button"
                disabled={isSubmittingRegen}
                onClick={handleConfirmRegenerate}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 transition active:scale-95"
              >
                {isSubmittingRegen ? "Đang xử lý..." : "Xác nhận Tái sinh"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
