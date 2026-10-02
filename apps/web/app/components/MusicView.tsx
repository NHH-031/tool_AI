"use client";

import React, { useState } from "react";
import { MusicTrackItem } from "../types";

interface MusicViewProps {
  musicTracks: MusicTrackItem[];
}

export const MusicView: React.FC<MusicViewProps> = ({ musicTracks }) => {
  const [playingTrackId, setPlayingTrackId] = useState<string | null>(null);

  const toggleTrack = (id: string) => {
    if (playingTrackId === id) {
      setPlayingTrackId(null);
    } else {
      setPlayingTrackId(id);
      setTimeout(() => setPlayingTrackId(null), 4000);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">
          Royalty-Free Background Music (BGM)
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Thư viện âm nhạc nền bản quyền được tối ưu âm lượng để không lấn át giọng thuyết minh của Whiteboard Video
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {musicTracks.map((track) => (
          <div
            key={track.id}
            id={`music-entry-${track.id}`}
            className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 hover:border-indigo-500/50 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl">
                    🎵
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
                <div>Tâm trạng (Mood): <strong className="text-white">{track.mood}</strong></div>
                <div>Thể loại: <span className="text-slate-300">{track.genre}</span></div>
                <div>Nhịp điệu: <span className="font-mono text-indigo-400">{track.bpm} BPM</span></div>
                <div>Âm lượng đề xuất: <span className="font-mono text-emerald-400 font-bold">{track.recommended_volume * 100}%</span></div>
              </div>

              {/* Waveform Visualization Simulation */}
              <div className="mt-4 p-3 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-between gap-1">
                {[12, 24, 40, 18, 55, 30, 48, 62, 35, 20, 45, 58, 25, 38, 50, 15, 30, 42].map(
                  (h, i) => (
                    <div
                      key={i}
                      className={`w-1 rounded-full transition-all duration-300 ${
                        playingTrackId === track.id
                          ? "bg-indigo-400 animate-pulse"
                          : "bg-slate-700"
                      }`}
                      style={{ height: `${h * 0.4}px` }}
                    ></div>
                  )
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {track.tags.map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
                    #{t}
                  </span>
                ))}
              </div>

              <button
                onClick={() => toggleTrack(track.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 active:scale-95 ${
                  playingTrackId === track.id
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                }`}
              >
                <span>{playingTrackId === track.id ? "⏸️" : "▶️"}</span>
                <span>{playingTrackId === track.id ? "Pause" : "Play Preview"}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
