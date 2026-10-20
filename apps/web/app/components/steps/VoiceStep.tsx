"use client";

import React, { useState, useRef, useEffect } from "react";
import { AudioResult, MusicTrackItem, Scene, VoiceItem } from "../../types";
import { getMusicPreviewUrl } from "../../api-client";

interface VoiceStepProps {
  scenes: Scene[];
  audios: AudioResult[];
  voices: VoiceItem[];
  selectedVoiceId: string;
  onSelectVoice: (voiceId: string) => void;
  speed: number;
  onUpdateSpeed: (speed: number) => void;
  musicTracks: MusicTrackItem[];
  selectedMusicId: string;
  onSelectMusic: (musicId: string) => void;
  musicVolume: number;
  onUpdateMusicVolume: (volume: number) => void;
  onSynthesizeSingle: (scene: Scene) => Promise<void>;
  onSynthesizeAll: () => Promise<void>;
  isSynthesizing: boolean;
  synthesizingSceneId: string | null;
  onBackStep: () => void;
  onNextStep: () => void;
}

export const VoiceStep: React.FC<VoiceStepProps> = ({
  scenes,
  audios,
  voices,
  selectedVoiceId,
  onSelectVoice,
  speed,
  onUpdateSpeed,
  musicTracks,
  selectedMusicId,
  onSelectMusic,
  musicVolume,
  onUpdateMusicVolume,
  onSynthesizeSingle,
  onSynthesizeAll,
  isSynthesizing,
  synthesizingSceneId,
  onBackStep,
  onNextStep,
}) => {
  const [playingAudioUrl, setPlayingAudioUrl] = useState<string | null>(null);
  const [isPlayingMusicPreview, setIsPlayingMusicPreview] = useState<boolean>(false);
  const musicAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (musicAudioRef.current) {
        musicAudioRef.current.pause();
        musicAudioRef.current = null;
      }
    };
  }, []);

  const toggleMusicPreview = () => {
    if (selectedMusicId === "none") return;
    if (isPlayingMusicPreview) {
      if (musicAudioRef.current) {
        musicAudioRef.current.pause();
      }
      setIsPlayingMusicPreview(false);
      return;
    }

    if (musicAudioRef.current) {
      musicAudioRef.current.pause();
    }

    const track = musicTracks.find((m) => m.id === selectedMusicId);
    const previewUrl = track?.preview_url || getMusicPreviewUrl(selectedMusicId);
    const audio = new Audio(previewUrl);
    audio.volume = musicVolume || 0.2;
    audio.onended = () => setIsPlayingMusicPreview(false);
    audio.onerror = () => setIsPlayingMusicPreview(false);

    audio.play().then(() => {
      musicAudioRef.current = audio;
      setIsPlayingMusicPreview(true);
    }).catch(() => {
      setIsPlayingMusicPreview(false);
    });
  };

  // Helper to find audio result for scene
  const getAudioForScene = (scene: Scene) => {
    const found = audios.find((a) => a.scene_id === scene.id || a.scene_index === scene.scene_index);
    if (found?.audio_url) return found;
    if (scene.audio_url) {
      return {
        scene_id: scene.id,
        scene_index: scene.scene_index,
        audio_url: scene.audio_url,
        duration_sec: scene.duration_sec || 4,
        voice_id: selectedVoiceId,
        status: "completed" as const,
      };
    }
    return null;
  };

  const completedAudiosCount = scenes.filter((sc) => Boolean(getAudioForScene(sc))).length;
  const allAudiosReady = scenes.length > 0 && completedAudiosCount === scenes.length;

  const totalDuration = scenes.reduce((acc, sc) => {
    const aud = getAudioForScene(sc);
    return acc + (aud?.duration_sec || sc.duration_sec || 4);
  }, 0);

  // Default fallback voices if empty
  const defaultVoices: VoiceItem[] = voices.length > 0 ? voices : [
    {
      id: "vieneu-local-1",
      name: "VieNeu AI (Local · Bắc Bộ Tự Nhiên)",
      language: "vi",
      locale: "vi-VN",
      gender: "Male",
      accent: "Northern",
      sample_text: "Xin chào các bạn",
      supported_speeds: [0.8, 1.0, 1.2],
      is_neural: true,
      tags: ["Local", "VieNeu"],
    },
    {
      id: "voicestudio-local-1",
      name: "VoiceStudio (Local · Nữ Nam Bộ Truyền Cảm)",
      language: "vi",
      locale: "vi-VN",
      gender: "Female",
      accent: "Southern",
      sample_text: "Chào mừng bạn đến với kênh",
      supported_speeds: [0.8, 1.0, 1.2],
      is_neural: true,
      tags: ["Local", "VoiceStudio"],
    },
    {
      id: "vi-VN-HoaiMyNeural",
      name: "Hoài My (Edge TTS · Nữ)",
      language: "vi",
      locale: "vi-VN",
      gender: "Female",
      accent: "Northern",
      sample_text: "Kính chào quý khán giả",
      supported_speeds: [0.8, 1.0, 1.2],
      is_neural: true,
      tags: ["Cloud", "EdgeTTS"],
    },
    {
      id: "vi-VN-NamMinhNeural",
      name: "Nam Minh (Edge TTS · Nam)",
      language: "vi",
      locale: "vi-VN",
      gender: "Male",
      accent: "Northern",
      sample_text: "Kính chào quý khán giả",
      supported_speeds: [0.8, 1.0, 1.2],
      is_neural: true,
      tags: ["Cloud", "EdgeTTS"],
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Guidance Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">Bước 3:</span> Giọng Đọc AI & Nhạc Nền (VieNeu / VoiceStudio)
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Tạo giọng đọc tiếng Việt mượt mà cho từng cảnh và phối nhạc nền phù hợp với phong cách whiteboard.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">
              Tổng thời lượng: <strong className="text-emerald-400 font-mono">{totalDuration.toFixed(1)}s</strong>
            </span>
            <button
              id="btn-synth-all-voice"
              onClick={onSynthesizeAll}
              disabled={isSynthesizing || scenes.length === 0}
              className={`px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition shadow-lg ${
                isSynthesizing || scenes.length === 0
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25 active:scale-95"
              }`}
            >
              {isSynthesizing ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Đang tổng hợp giọng nói...</span>
                </>
              ) : (
                <>
                  <span>🎙️</span>
                  <span>Thu âm tất cả các cảnh</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Voice & Music Global Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Voice Selection Card */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <span>🎙️</span> Giọng Đọc AI (VieNeu / VoiceStudio)
            </span>
            <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              Local TTS Ready
            </span>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Chọn giọng đọc mẫu:</label>
            <select
              value={selectedVoiceId}
              onChange={(e) => onSelectVoice(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-indigo-500 text-sm text-slate-100 outline-none transition"
            >
              {defaultVoices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.gender === "Male" ? "Nam" : "Nữ"})
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
              <span>Tốc độ đọc:</span>
              <span className="font-mono text-indigo-400">{speed.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min={0.75}
              max={1.5}
              step={0.05}
              value={speed}
              onChange={(e) => onUpdateSpeed(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.75x (Chậm rãi)</span>
              <span>1.0x (Tự nhiên)</span>
              <span>1.5x (Nhanh)</span>
            </div>
          </div>
        </div>

        {/* Music Selection Card */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <span>🎵</span> Nhạc Nền Whiteboard
            </span>
            <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
              Auto Loop & Fade
            </span>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs text-slate-400 font-medium">Giai điệu chủ đạo:</label>
              {selectedMusicId !== "none" && (
                <button
                  type="button"
                  onClick={toggleMusicPreview}
                  className={`text-[11px] px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1 transition active:scale-95 ${
                    isPlayingMusicPreview
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 animate-pulse"
                      : "bg-slate-800 hover:bg-slate-700 text-indigo-300"
                  }`}
                >
                  <span>{isPlayingMusicPreview ? "⏸️" : "▶️"}</span>
                  <span>{isPlayingMusicPreview ? "Dừng thử" : "Nghe thử"}</span>
                </button>
              )}
            </div>
            <select
              value={selectedMusicId}
              onChange={(e) => onSelectMusic(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-indigo-500 text-sm text-slate-100 outline-none transition"
            >
              <option value="none">-- Không dùng nhạc nền --</option>
              {musicTracks.length > 0 ? (
                musicTracks.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title} ({m.mood} · {m.genre})
                  </option>
                ))
              ) : (
                <>
                  <option value="whimsical_play">Whimsical Play (Vui tươi · Whiteboard)</option>
                  <option value="acoustic_uplift">Sunny Morning Ukulele (Hứng khởi · Acoustic)</option>
                  <option value="lofi_chill">Late Night Whiteboard Lofi (Thư giãn · Lofi)</option>
                  <option value="corporate_inspire">Inspiring Innovation (Chuyên nghiệp)</option>
                  <option value="ambient_minimal">Subtle Clarity Wave (Trực quan · Ambient)</option>
                </>
              )}
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
              <span>Âm lượng nhạc nền:</span>
              <span className="font-mono text-indigo-400">{Math.round(musicVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min={0.0}
              max={0.5}
              step={0.05}
              value={musicVolume}
              onChange={(e) => onUpdateMusicVolume(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0% (Tắt)</span>
              <span>15% (Chuẩn lời dẫn)</span>
              <span>50% (Sôi động)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Per-Scene Audio List */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <span className="font-semibold text-sm text-slate-200">
            Chi tiết audio từng phân cảnh ({completedAudiosCount}/{scenes.length} đã thu)
          </span>
          <span className="text-xs text-slate-400">
            Nghe thử và kiểm tra timing khớp với nét vẽ
          </span>
        </div>

        <div className="space-y-3">
          {scenes.map((scene, idx) => {
            const audio = getAudioForScene(scene);
            const isSynthesizingThis = synthesizingSceneId === scene.id;

            return (
              <div
                key={scene.id || idx}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <span className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-slate-200">Cảnh {idx + 1}</span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        ~{(audio?.duration_sec || scene.duration_sec || 4).toFixed(1)}s
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed italic truncate sm:whitespace-normal">
                      &ldquo;{scene.text}&rdquo;
                    </p>
                  </div>
                </div>

                {/* Audio Player or Action */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  {audio?.audio_url ? (
                    <div className="flex items-center gap-2 bg-slate-900 p-2 rounded-xl border border-slate-800">
                      <audio
                        controls
                        src={audio.audio_url}
                        className="h-8 max-w-[220px]"
                      />
                      <button
                        onClick={() => onSynthesizeSingle(scene)}
                        disabled={isSynthesizingThis}
                        className="p-1.5 text-slate-400 hover:text-indigo-400 transition"
                        title="Thu âm lại cảnh này"
                      >
                        {isSynthesizingThis ? (
                          <svg className="animate-spin w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                        ) : (
                          "🔄"
                        )}
                      </button>
                    </div>
                  ) : isSynthesizingThis ? (
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                      </svg>
                      <span>Đang thu âm...</span>
                    </div>
                  ) : (
                    <button
                      onClick={() => onSynthesizeSingle(scene)}
                      className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-md shadow-indigo-600/20"
                    >
                      🎙️ Thu âm cảnh này
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
        <button
          onClick={onBackStep}
          className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold transition"
        >
          ← Quay lại Storyboard
        </button>

        <div className="flex items-center gap-3">
          {!allAudiosReady && (
            <span className="text-xs text-amber-400/90 hidden sm:inline">
              ⚠️ Cần thu âm cho tất cả các cảnh để kết xuất video
            </span>
          )}
          <button
            id="btn-voice-next"
            onClick={onNextStep}
            disabled={!allAudiosReady}
            className={`px-6 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition ${
              !allAudiosReady
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 active:scale-95"
            }`}
          >
            <span>Tiếp tục sang Xuất video (Bước 4)</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};
