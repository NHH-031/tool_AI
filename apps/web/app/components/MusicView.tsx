"use client";

import React, { useState, useRef, useEffect } from "react";
import { MusicTrackItem } from "../types";
import { getMusicPreviewUrl } from "../api-client";

interface MusicViewProps {
  musicTracks: MusicTrackItem[];
}

export const MusicView: React.FC<MusicViewProps> = ({ musicTracks }) => {
  const [playingTrackId, setPlayingTrackId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Dọn dẹp audio khi component unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const toggleTrack = (track: MusicTrackItem) => {
    if (playingTrackId === track.id) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setPlayingTrackId(null);
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    const previewUrl = track.preview_url || getMusicPreviewUrl(track.id);
    const audio = new Audio(previewUrl);
    audio.volume = track.recommended_volume || 0.2;

    audio.onended = () => {
      setPlayingTrackId(null);
    };

    audio.onerror = () => {
      console.warn(`[MusicView] Không thể phát nhạc thử cho track: ${track.id}`);
      setPlayingTrackId(null);
    };

    audio.play().then(() => {
      audioRef.current = audio;
      setPlayingTrackId(track.id);
    }).catch((err) => {
      console.warn("[MusicView] Audio playback error:", err);
      setPlayingTrackId(null);
    });
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>🎵</span> Royalty-Free Background Music (BGM)
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Thư viện âm nhạc nền bản quyền được tối ưu âm lượng và Auto-Ducking không lấn át giọng thuyết minh Whiteboard
          </p>
        </div>
        <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono w-fit">
          5 Bản Nhạc Bản Quyền Sẵn Sàng
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {musicTracks.map((track) => (
          <div
            key={track.id}
            id={`music-entry-${track.id}`}
            className={`border rounded-3xl p-6 transition flex flex-col justify-between ${
              playingTrackId === track.id
                ? "bg-slate-900 border-indigo-500/80 shadow-xl shadow-indigo-500/10"
                : "bg-slate-900/50 border-slate-800/80 hover:border-indigo-500/40"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-11 h-11 rounded-2xl flex items-center justify-center text-xl transition ${
                    playingTrackId === track.id
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/40 animate-pulse"
                      : "bg-indigo-600/20 border border-indigo-500/30 text-indigo-300"
                  }`}>
                    {playingTrackId === track.id ? "🔊" : "🎵"}
                  </div>
                  <div>
                    <h2 className="font-bold text-white text-base">{track.title}</h2>
                    <span className="text-[11px] text-slate-400">{track.artist}</span>
                  </div>
                </div>

                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                  {Math.floor(track.duration_sec / 60)}:{(track.duration_sec % 60).toString().padStart(2, "0")}
                </span>
              </div>

              <div className="text-xs text-slate-400 space-y-1.5 mt-2">
                <div>Tâm trạng: <strong className="text-white">{track.mood}</strong></div>
                <div>Thể loại: <span className="text-slate-300">{track.genre}</span></div>
                <div>Nhịp điệu: <span className="font-mono text-indigo-400">{track.bpm} BPM</span></div>
                <div>Âm lượng chuẩn: <span className="font-mono text-emerald-400 font-bold">{Math.round(track.recommended_volume * 100)}%</span></div>
              </div>

              {/* Waveform Visualization */}
              <div className="mt-4 p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-between gap-1">
                {[12, 24, 40, 18, 55, 30, 48, 62, 35, 20, 45, 58, 25, 38, 50, 15, 30, 42].map(
                  (h, i) => (
                    <div
                      key={i}
                      className={`w-1 rounded-full transition-all duration-200 ${
                        playingTrackId === track.id
                          ? "bg-indigo-400 animate-pulse"
                          : "bg-slate-700"
                      }`}
                      style={{
                        height: playingTrackId === track.id ? `${Math.max(8, h * 0.45)}px` : `${h * 0.3}px`,
                      }}
                    ></div>
                  )
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between gap-2">
              <div className="flex flex-wrap gap-1">
                {track.tags.slice(0, 3).map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
                    #{t}
                  </span>
                ))}
              </div>

              <button
                onClick={() => toggleTrack(track)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 active:scale-95 shadow ${
                  playingTrackId === track.id
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                }`}
              >
                <span>{playingTrackId === track.id ? "⏸️" : "▶️"}</span>
                <span>{playingTrackId === track.id ? "Dừng" : "Nghe thử"}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

