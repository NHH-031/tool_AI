"use client";

import React, { useState } from "react";
import { VoiceItem } from "../types";

interface VoicesViewProps {
  voices: VoiceItem[];
}

export const VoicesView: React.FC<VoicesViewProps> = ({ voices }) => {
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);

  const handlePlayPreview = (id: string) => {
    if (playingVoiceId === id) {
      setPlayingVoiceId(null);
    } else {
      setPlayingVoiceId(id);
      setTimeout(() => setPlayingVoiceId(null), 3500);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Voices & Narration Catalog</h1>
        <p className="text-xs text-slate-400 mt-1">
          Danh mục giọng đọc Text-to-Speech đa ngôn ngữ với độ truyền cảm tự nhiên và căn chỉnh mốc thời gian từ vựng
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {voices.map((voice) => (
          <div
            key={voice.id}
            id={`voice-entry-${voice.id}`}
            className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 hover:border-indigo-500/50 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl">
                    {voice.gender === "female" ? "👩" : "👨"}
                  </div>
                  <div>
                    <h2 className="font-bold text-white text-base">{voice.name}</h2>
                    <span className="text-[11px] text-slate-400">{voice.language} ({voice.locale})</span>
                  </div>
                </div>

                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Neural TTS
                </span>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 italic mb-4">
                "{voice.sample_text}"
              </div>

              <div className="text-xs text-slate-400 space-y-1.5">
                <div>Chất giọng (Accent): <strong className="text-white">{voice.accent}</strong></div>
                <div>Tốc độ hỗ trợ: <span className="font-mono text-indigo-400">0.8x, 1.0x, 1.2x, 1.5x</span></div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {voice.tags.map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
                    #{t}
                  </span>
                ))}
              </div>

              <button
                onClick={() => handlePlayPreview(voice.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 active:scale-95 ${
                  playingVoiceId === voice.id
                    ? "bg-amber-500 text-black animate-pulse"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                }`}
              >
                <span>{playingVoiceId === voice.id ? "⏸️" : "▶️"}</span>
                <span>{playingVoiceId === voice.id ? "Đang phát..." : "Nghe thử"}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
