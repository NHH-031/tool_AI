"use client";

import React, { useState, useEffect, useRef } from "react";
import { SubtitleSegment, SubtitleTypographyConfig } from "../../types";
import { fetchJobSubtitles, updateJobSubtitles } from "../../api-client";

interface SubtitleTimelineEditorProps {
  jobId: string;
  videoUrl?: string | null;
  aspectRatio?: string;
  initialTypography?: SubtitleTypographyConfig;
  isOpen: boolean;
  onClose: () => void;
  onApplied?: (updatedData: {
    video_url: string;
    srt_url: string;
    vtt_url: string;
    segments: SubtitleSegment[];
  }) => void;
}

export function SubtitleTimelineEditor({
  jobId,
  videoUrl,
  aspectRatio = "16:9",
  initialTypography,
  isOpen,
  onClose,
  onApplied,
}: SubtitleTimelineEditorProps) {
  const [segments, setSegments] = useState<SubtitleSegment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [reburnVideo, setReburnVideo] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"segments" | "preview">("segments");
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!isOpen || !jobId) return;

    let isMounted = true;
    setLoading(true);
    setStatusMsg(null);

    fetchJobSubtitles(jobId)
      .then((data) => {
        if (!isMounted) return;
        const sorted = (data.segments || []).sort((a, b) => a.start_sec - b.start_sec);
        setSegments(sorted);
        if (sorted.length > 0) {
          const maxEnd = Math.max(...sorted.map((s) => s.end_sec));
          setDuration(maxEnd);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setStatusMsg({ type: "error", text: `Không thể tải phụ đề: ${err.message}` });
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, jobId]);

  if (!isOpen) return null;

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const t = videoRef.current.currentTime;
      setCurrentTime(t);
      if (videoRef.current.duration && !isNaN(videoRef.current.duration)) {
        setDuration(videoRef.current.duration);
      }
      // Highlight matching segment
      const curIdx = segments.findIndex((s) => s.start_sec <= t && t <= s.end_sec);
      if (curIdx !== -1 && curIdx !== selectedIdx) {
        setSelectedIdx(curIdx);
      }
    }
  };

  const seekTo = (sec: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, sec);
      videoRef.current.play().catch(() => {});
    }
    setCurrentTime(sec);
  };

  const handleSegmentChange = (idx: number, field: keyof SubtitleSegment, val: any) => {
    setSegments((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: val };
      return copy;
    });
  };

  const handleAdjustTime = (idx: number, field: "start_sec" | "end_sec", delta: number) => {
    setSegments((prev) => {
      const copy = [...prev];
      const cur = copy[idx][field];
      const next = Math.max(0, Math.round((cur + delta) * 10) / 10);
      copy[idx] = { ...copy[idx], [field]: next };
      return copy;
    });
  };

  const handleAddSegment = () => {
    const lastSeg = segments[segments.length - 1];
    const newStart = lastSeg ? Math.round((lastSeg.end_sec + 0.3) * 10) / 10 : 0.0;
    const newEnd = Math.round((newStart + 3.0) * 10) / 10;
    const newSeg: SubtitleSegment = {
      index: segments.length + 1,
      start_sec: newStart,
      end_sec: newEnd,
      text: "Nhập phụ đề mới tại đây...",
      words: [],
    };
    setSegments((prev) => [...prev, newSeg]);
    setSelectedIdx(segments.length);
  };

  const handleDeleteSegment = (idx: number) => {
    setSegments((prev) => prev.filter((_, i) => i !== idx));
    if (selectedIdx >= idx) {
      setSelectedIdx(Math.max(0, selectedIdx - 1));
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatusMsg(null);
    try {
      const res = await updateJobSubtitles(jobId, {
        segments,
        reburn_video: reburnVideo,
        typography: initialTypography,
      });

      setStatusMsg({
        type: "success",
        text: res.video_reburnt
          ? "✅ Đã lưu và Fast Re-burn phụ đề lên Video thành công (~1.8s)!"
          : "✅ Đã lưu cập nhật file .SRT/.VTT thành công!",
      });

      if (onApplied) {
        onApplied(res);
      }
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: `Lỗi cập nhật: ${err.message || err}`,
      });
    } finally {
      setSaving(false);
    }
  };

  const formatSec = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = Math.floor(s % 60);
    const ms = Math.floor((s % 1) * 10);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms}`;
  };

  const totalDuration = duration > 0 ? duration : (segments.length > 0 ? Math.max(...segments.map((s) => s.end_sec)) : 10);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-5xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl shadow-indigo-950/40 overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-lg">
              ⏱️
            </span>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                <span>Trình biên tập Mốc thời gian & Phụ đề trực quan</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Phase 9 Ready
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Sửa lỗi chính tả tức thì không cần render lại tranh vẽ · Fast Re-burn vào video chỉ 1-2 giây
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Đóng"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Status notification toast */}
        {statusMsg && (
          <div
            className={`px-4 py-2.5 text-xs font-medium flex items-center justify-between border-b ${
              statusMsg.type === "success"
                ? "bg-emerald-950/70 text-emerald-300 border-emerald-800/60"
                : "bg-rose-950/70 text-rose-300 border-rose-800/60"
            }`}
          >
            <span>{statusMsg.text}</span>
            <button
              onClick={() => setStatusMsg(null)}
              className="text-xs underline hover:text-white opacity-80"
            >
              Đóng
            </button>
          </div>
        )}

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-5">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-3">
              <svg className="animate-spin w-8 h-8 text-indigo-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-xs text-slate-400 font-medium">Đang tải cấu trúc mốc phụ đề...</p>
            </div>
          ) : (
            <>
              {/* Media Player & Scrubbing Row */}
              {videoUrl && (
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
                  <div className="md:col-span-5 flex flex-col justify-center items-center">
                    <div className="w-full max-h-[180px] bg-black rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
                      <video
                        ref={videoRef}
                        src={videoUrl}
                        onTimeUpdate={handleTimeUpdate}
                        controls
                        className="max-h-[180px] w-full object-contain"
                      />
                    </div>
                  </div>

                  <div className="md:col-span-7 flex flex-col justify-between space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-300">
                      <span className="font-semibold text-white flex items-center gap-1.5">
                        <span>▶️</span> Đang phát: <span className="font-mono text-indigo-400">{formatSec(currentTime)}</span> / <span className="font-mono text-slate-400">{formatSec(totalDuration)}</span>
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {segments.length} đoạn phụ đề
                      </span>
                    </div>

                    {/* Active subtitle preview bubble */}
                    <div className="flex-1 min-h-[50px] p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-center">
                      {segments[selectedIdx] ? (
                        <p className="text-xs sm:text-sm font-semibold text-amber-300">
                          &ldquo;{segments[selectedIdx].text}&rdquo;
                        </p>
                      ) : (
                        <p className="text-xs text-slate-500 italic">Không có phụ đề tại mốc này</p>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Click vào từng khối bên dưới để nhảy video tới thời điểm đó</span>
                      <button
                        onClick={handleAddSegment}
                        className="px-2.5 py-1 rounded bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 transition text-xs font-semibold flex items-center gap-1"
                      >
                        <span>➕</span> Thêm câu
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Visual Timeline Scrubbing Bar */}
              <div className="space-y-1.5 bg-slate-950/80 border border-slate-800 p-3 rounded-xl">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>00:00.0</span>
                  <span>Timeline Tracks ({formatSec(totalDuration)})</span>
                  <span>{formatSec(totalDuration)}</span>
                </div>

                {/* Blocks Container */}
                <div className="relative w-full h-10 bg-slate-900 rounded-lg border border-slate-800 overflow-hidden flex items-center">
                  {/* Current playback needle */}
                  {totalDuration > 0 && (
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-rose-500 z-20 pointer-events-none shadow-sm shadow-rose-500"
                      style={{
                        left: `${Math.min(100, Math.max(0, (currentTime / totalDuration) * 100))}%`,
                      }}
                    />
                  )}

                  {segments.map((seg, idx) => {
                    const leftPct = totalDuration > 0 ? (seg.start_sec / totalDuration) * 100 : 0;
                    const widthPct = totalDuration > 0 ? ((seg.end_sec - seg.start_sec) / totalDuration) * 100 : 10;
                    const isSelected = selectedIdx === idx;

                    return (
                      <div
                        key={idx}
                        onClick={() => {
                          setSelectedIdx(idx);
                          seekTo(seg.start_sec);
                        }}
                        style={{
                          left: `${leftPct}%`,
                          width: `${Math.max(2, widthPct)}%`,
                        }}
                        title={`#${idx + 1}: ${seg.text} (${formatSec(seg.start_sec)} - ${formatSec(seg.end_sec)})`}
                        className={`absolute top-1 bottom-1 rounded px-1 flex items-center justify-center cursor-pointer text-[10px] font-medium truncate transition select-none ${
                          isSelected
                            ? "bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/30 ring-1 ring-white z-10"
                            : "bg-indigo-600/70 hover:bg-indigo-500 text-white border border-indigo-400/30"
                        }`}
                      >
                        <span className="truncate">{seg.text}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Segment List & In-Place Text Editor */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Danh sách các câu phụ đề ({segments.length})
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Sửa trực tiếp nội dung để sửa lỗi chính tả ngay lập tức
                  </span>
                </div>

                <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
                  {segments.map((seg, idx) => {
                    const isSelected = selectedIdx === idx;
                    const dur = Math.max(0.1, Math.round((seg.end_sec - seg.start_sec) * 10) / 10);

                    return (
                      <div
                        key={idx}
                        onClick={() => setSelectedIdx(idx)}
                        className={`p-3 rounded-xl border transition space-y-2 ${
                          isSelected
                            ? "bg-indigo-950/40 border-indigo-500/80 shadow-md ring-1 ring-indigo-500/30"
                            : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">
                              #{idx + 1}
                            </span>
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                              {dur}s
                            </span>
                          </div>

                          {/* Time controls */}
                          <div className="flex items-center gap-2">
                            {/* Start Sec */}
                            <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1">
                              <span className="text-[10px] text-slate-400">Bắt đầu:</span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAdjustTime(idx, "start_sec", -0.1);
                                }}
                                className="w-4 h-4 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center"
                              >
                                -
                              </button>
                              <input
                                type="number"
                                step="0.1"
                                value={seg.start_sec}
                                onChange={(e) =>
                                  handleSegmentChange(idx, "start_sec", parseFloat(e.target.value) || 0)
                                }
                                onClick={(e) => e.stopPropagation()}
                                className="w-14 bg-transparent text-center text-xs font-mono text-white focus:outline-none"
                              />
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAdjustTime(idx, "start_sec", 0.1);
                                }}
                                className="w-4 h-4 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center"
                              >
                                +
                              </button>
                            </div>

                            {/* End Sec */}
                            <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1">
                              <span className="text-[10px] text-slate-400">Kết thúc:</span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAdjustTime(idx, "end_sec", -0.1);
                                }}
                                className="w-4 h-4 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center"
                              >
                                -
                              </button>
                              <input
                                type="number"
                                step="0.1"
                                value={seg.end_sec}
                                onChange={(e) =>
                                  handleSegmentChange(idx, "end_sec", parseFloat(e.target.value) || 0)
                                }
                                onClick={(e) => e.stopPropagation()}
                                className="w-14 bg-transparent text-center text-xs font-mono text-white focus:outline-none"
                              />
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAdjustTime(idx, "end_sec", 0.1);
                                }}
                                className="w-4 h-4 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 flex items-center justify-center"
                              >
                                +
                              </button>
                            </div>

                            {/* Play preview */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                seekTo(seg.start_sec);
                              }}
                              className="px-2 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/20 text-xs flex items-center gap-1 transition"
                              title="Xem thử đoạn này"
                            >
                              <span>▶️</span>
                              <span className="text-[10px]">Xem</span>
                            </button>

                            {/* Delete button */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteSegment(idx);
                              }}
                              className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                              title="Xóa đoạn này"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>

                        {/* In-place Text Area */}
                        <div>
                          <textarea
                            rows={2}
                            value={seg.text}
                            onChange={(e) => handleSegmentChange(idx, "text", e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            placeholder="Nhập nội dung phụ đề tiếng Việt..."
                            className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none leading-relaxed"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-4 border-t border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 select-none">
              <input
                type="checkbox"
                checked={reburnVideo}
                onChange={(e) => setReburnVideo(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-0"
              />
              <span>Tự động Re-burn đè lên Video MP4 (~1.8s)</span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
            >
              Hủy
            </button>

            <button
              id="btn-apply-subtitles"
              onClick={handleSave}
              disabled={saving || segments.length === 0}
              className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition active:scale-95"
            >
              {saving ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" strokeWidth="4" stroke="currentColor" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Đang Re-burn phụ đề...</span>
                </>
              ) : (
                <>
                  <span>💾</span>
                  <span>Lưu & Áp dụng ngay</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
