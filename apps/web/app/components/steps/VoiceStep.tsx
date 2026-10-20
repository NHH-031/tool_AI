"use client";

import React, { useState, useRef, useEffect } from "react";
import { AudioResult, MusicTrackItem, Scene, VoiceItem } from "../../types";
import { getMusicPreviewUrl } from "../../api-client";
import { VoiceRecorderModal } from "../audio/VoiceRecorderModal";
import { CustomMusicUploadModal } from "../audio/CustomMusicUploadModal";

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
  musicStartOffset?: number;
  onUpdateMusicStartOffset?: (offset: number) => void;
  musicFadeDuration?: number;
  onUpdateMusicFadeDuration?: (fade: number) => void;
  onUpdateSceneVoice?: (sceneId: string, voiceId: string, speakerTag?: string) => void;
  onUpdateSceneAudioResult?: (result: AudioResult) => void;
  onSynthesizeSingle: (scene: Scene) => Promise<void>;
  onSynthesizeAll: () => Promise<void>;
  isSynthesizing: boolean;
  synthesizingSceneId: string | null;
  onBackStep: () => void;
  onNextStep: () => void;
  projectId?: string;
  onAddCustomMusicTrack?: (track: MusicTrackItem) => void;
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
  musicStartOffset = 0,
  onUpdateMusicStartOffset,
  musicFadeDuration = 2,
  onUpdateMusicFadeDuration,
  onUpdateSceneVoice,
  onUpdateSceneAudioResult,
  onSynthesizeSingle,
  onSynthesizeAll,
  isSynthesizing,
  synthesizingSceneId,
  onBackStep,
  onNextStep,
  projectId = "default",
  onAddCustomMusicTrack,
}) => {
  const [isPlayingMusicPreview, setIsPlayingMusicPreview] = useState<boolean>(false);
  const musicAudioRef = useRef<HTMLAudioElement | null>(null);

  // Modal states
  const [recordingScene, setRecordingScene] = useState<Scene | null>(null);
  const [isCustomMusicModalOpen, setIsCustomMusicModalOpen] = useState<boolean>(false);

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
    if (musicStartOffset > 0) {
      audio.currentTime = musicStartOffset;
    }
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
        voice_id: scene.voice_id || selectedVoiceId,
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

  // Phân nhóm giọng đọc
  const elevenVoices = voices.filter((v) => v.id.startsWith("eleven-"));
  const edgeVoices = voices.filter((v) => v.id.includes("Neural") || v.id.startsWith("vi-VN-Standard"));
  const localVoices = voices.filter((v) => v.id.includes("local"));
  const otherVoices = voices.filter((v) => !v.id.startsWith("eleven-") && !v.id.includes("Neural") && !v.id.includes("local") && !v.id.startsWith("vi-VN-Standard"));

  // Tự động nhận diện nhãn nhân vật từ lời thoại (Task 8.1)
  const handleAutoDetectSpeakers = () => {
    let detectedCount = 0;
    scenes.forEach((sc) => {
      const match = sc.text.match(/^\[?(Nam|Nữ|Nu|Dẫn chuyện|Người dẫn|Narrator|Khách hàng|Chuyên gia|Thầy giáo|Cô giáo)\]?[:\-\s]/i);
      if (match) {
        const rawTag = match[1].toLowerCase();
        let targetVoice = "vi-VN-NamMinhNeural";
        let displayTag = "Nam";

        if (rawTag.includes("nữ") || rawTag.includes("nu") || rawTag.includes("cô")) {
          targetVoice = "vi-VN-HoaiMyNeural";
          displayTag = "Nữ";
        } else if (rawTag.includes("nam") || rawTag.includes("thầy")) {
          targetVoice = "vi-VN-NamMinhNeural";
          displayTag = "Nam";
        } else if (rawTag.includes("dẫn") || rawTag.includes("người") || rawTag.includes("narrator")) {
          targetVoice = elevenVoices.length > 0 ? "eleven-adam" : "vi-VN-Standard-B";
          displayTag = "Dẫn chuyện";
        }

        if (onUpdateSceneVoice) {
          onUpdateSceneVoice(sc.id, targetVoice, displayTag);
          detectedCount++;
        }
      }
    });

    if (detectedCount > 0) {
      alert(`Đã tự động nhận diện và gán giọng đọc cho ${detectedCount} phân cảnh đối thoại!`);
    } else {
      alert("Không tìm thấy nhãn nhân vật dạng [Nam]:, [Nữ]:, [Dẫn chuyện]: ở đầu câu thoại.");
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Guidance Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">Bước 3:</span> Giọng Đọc Đa Nhân Vật & Nhạc Nền Riêng
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Hỗ trợ giọng đọc biểu cảm ElevenLabs, EdgeTTS, thu âm trực tiếp bằng micro và tải nhạc nền cá nhân (Phase 8).
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
                  <span>Đang thu âm hàng loạt...</span>
                </>
              ) : (
                <>
                  <span>🎙️ Thu âm toàn bộ ({scenes.length} cảnh)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Voice and Music Global Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Global Voice Engine */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-lg">🗣️</span>
              <span className="font-semibold text-sm text-slate-200">Giọng đọc chính (Mặc định toàn bài)</span>
            </div>
            <button
              type="button"
              onClick={handleAutoDetectSpeakers}
              className="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition"
              title="Tìm nhãn [Nam], [Nữ], [Dẫn chuyện] trong kịch bản và gán giọng tương ứng"
            >
              🤖 Tự phát hiện nhân vật
            </button>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">
              Chọn giọng đọc thuyết minh:
            </label>
            <select
              value={selectedVoiceId}
              onChange={(e) => onSelectVoice(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              {elevenVoices.length > 0 && (
                <optgroup label="🌟 ElevenLabs · Biểu Cảm Cao Cấp (Multilingual)">
                  {elevenVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.accent})
                    </option>
                  ))}
                </optgroup>
              )}

              <optgroup label="🇻🇳 Edge TTS · Tiếng Việt Truyền Cảm">
                {edgeVoices.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.accent})
                  </option>
                ))}
              </optgroup>

              {localVoices.length > 0 && (
                <optgroup label="🤖 AI Cục Bộ (VieNeu / VoiceStudio)">
                  {localVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </optgroup>
              )}

              {otherVoices.length > 0 && (
                <optgroup label="🌐 Giọng Đọc Khác">
                  {otherVoices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.accent})
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
              <span>Tốc độ đọc (Speed):</span>
              <span className="font-mono text-indigo-400">{speed}x</span>
            </div>
            <input
              type="range"
              min={0.8}
              max={1.5}
              step={0.1}
              value={speed}
              onChange={(e) => onUpdateSpeed(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.8x (Chậm rãi)</span>
              <span>1.0x (Chuẩn)</span>
              <span>1.5x (Nhanh)</span>
            </div>
          </div>
        </div>

        {/* Right: BGM & Audio Trimmer Engine (Task 8.3) */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-lg">🎵</span>
              <span className="font-semibold text-sm text-slate-200">Nhạc nền & Cắt gọt BGM (Trimmer)</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsCustomMusicModalOpen(true)}
                className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition flex items-center gap-1"
              >
                <span>📤 Tải nhạc riêng</span>
              </button>
              {selectedMusicId !== "none" && (
                <button
                  type="button"
                  onClick={toggleMusicPreview}
                  className="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition"
                >
                  {isPlayingMusicPreview ? "⏸️ Dừng" : "▶️ Nghe BGM"}
                </button>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">
              Chọn bản nhạc nền:
            </label>
            <select
              value={selectedMusicId}
              onChange={(e) => onSelectMusic(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="none">-- Không sử dụng nhạc nền --</option>
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

          {/* BGM Trimmer Sliders: Start Offset & Fade Duration */}
          {selectedMusicId !== "none" && (
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Cắt đầu bài (Offset):</span>
                  <span className="font-mono text-emerald-400">{musicStartOffset}s</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={30}
                  step={1}
                  value={musicStartOffset}
                  onChange={(e) => onUpdateMusicStartOffset && onUpdateMusicStartOffset(parseInt(e.target.value, 10))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>0s</span>
                  <span>15s</span>
                  <span>30s</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Mờ dần cuối (Fade-out):</span>
                  <span className="font-mono text-emerald-400">{musicFadeDuration}s</span>
                </div>
                <input
                  type="range"
                  min={0.5}
                  max={5.0}
                  step={0.5}
                  value={musicFadeDuration}
                  onChange={(e) => onUpdateMusicFadeDuration && onUpdateMusicFadeDuration(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>0.5s</span>
                  <span>2.0s</span>
                  <span>5.0s</span>
                </div>
              </div>
            </div>
          )}

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

      {/* Per-Scene Audio List with Multi-Speaker & Mic Recording (Task 8.1 & 8.2) */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <span className="font-semibold text-sm text-slate-200">
              Chi tiết audio từng phân cảnh ({completedAudiosCount}/{scenes.length} đã thu)
            </span>
            <p className="text-xs text-slate-400 mt-0.5">
              Chỉ định giọng nói riêng cho từng nhân vật hoặc ghi âm bằng micro thật
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {allAudiosReady ? "✅ Đầy đủ audio" : "⚠️ Cần thu âm thêm"}
          </span>
        </div>

        <div className="space-y-3">
          {scenes.map((scene, idx) => {
            const audio = getAudioForScene(scene);
            const isSynthesizingThis = synthesizingSceneId === scene.id;
            const sceneVoiceId = scene.voice_id || selectedVoiceId;

            return (
              <div
                key={scene.id || idx}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
              >
                {/* Scene Script & Role */}
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <span className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-slate-200">Cảnh {idx + 1}</span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        ~{(audio?.duration_sec || scene.duration_sec || 4).toFixed(1)}s
                      </span>
                      {scene.speaker_tag && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          🎭 {scene.speaker_tag}
                        </span>
                      )}
                      {scene.is_custom_audio && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          🎤 Bản thu âm riêng
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed italic truncate sm:whitespace-normal">
                      &ldquo;{scene.text}&rdquo;
                    </p>
                  </div>
                </div>

                {/* Multi-speaker dropdown for this scene */}
                <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
                  <div className="w-40 sm:w-48">
                    <select
                      value={scene.voice_id || ""}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (onUpdateSceneVoice) {
                          onUpdateSceneVoice(scene.id, v || selectedVoiceId);
                        }
                      }}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 transition"
                      title="Chọn giọng đọc riêng cho cảnh này (Hội thoại đa nhân vật)"
                    >
                      <option value="">(Mặc định: {voices.find(v => v.id === selectedVoiceId)?.name || selectedVoiceId})</option>
                      {voices.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Micro record button */}
                  <button
                    type="button"
                    onClick={() => setRecordingScene(scene)}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 text-xs font-medium transition flex items-center gap-1.5"
                    title="Ghi âm giọng của bạn qua micro hoặc tải file âm thanh"
                  >
                    <span>🎙️ Thu âm riêng</span>
                  </button>

                  {/* Audio Player or Synthesis Action */}
                  {audio?.audio_url ? (
                    <div className="flex items-center gap-1.5 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
                      <audio
                        controls
                        src={audio.audio_url}
                        className="h-8 max-w-[180px] sm:max-w-[210px]"
                      />
                      <button
                        onClick={() => onSynthesizeSingle(scene)}
                        disabled={isSynthesizingThis}
                        className="p-1.5 text-slate-400 hover:text-indigo-400 transition"
                        title="Tạo lại giọng AI cho cảnh này"
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
                    <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                      </svg>
                      <span>Đang thu...</span>
                    </div>
                  ) : (
                    <button
                      onClick={() => onSynthesizeSingle(scene)}
                      className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-md shadow-indigo-600/20"
                    >
                      🗣️ Tạo giọng AI
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
          disabled={isSynthesizing || !!synthesizingSceneId}
          className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition ${
            isSynthesizing || !!synthesizingSceneId
              ? "bg-slate-800 text-slate-500 cursor-not-allowed opacity-50"
              : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white"
          }`}
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
            disabled={!allAudiosReady || isSynthesizing || !!synthesizingSceneId}
            className={`px-6 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition ${
              !allAudiosReady || isSynthesizing || !!synthesizingSceneId
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 active:scale-95"
            }`}
          >
            <span>Tiếp tục sang Xuất video (Bước 4)</span>
            <span>→</span>
          </button>
        </div>
      </div>

      {/* Modal ghi âm Micro & Tải audio phân cảnh (Task 8.2) */}
      {recordingScene && (
        <VoiceRecorderModal
          isOpen={!!recordingScene}
          onClose={() => setRecordingScene(null)}
          scene={recordingScene}
          projectId={projectId}
          onAudioSaved={(res) => {
            if (onUpdateSceneAudioResult) {
              onUpdateSceneAudioResult(res);
            }
          }}
        />
      )}

      {/* Modal tải nhạc nền BGM riêng (Task 8.3) */}
      {isCustomMusicModalOpen && (
        <CustomMusicUploadModal
          isOpen={isCustomMusicModalOpen}
          onClose={() => setIsCustomMusicModalOpen(false)}
          onMusicSaved={(newTrack) => {
            if (onAddCustomMusicTrack) {
              onAddCustomMusicTrack(newTrack);
            }
            onSelectMusic(newTrack.id);
            onUpdateMusicVolume(newTrack.recommended_volume);
          }}
        />
      )}
    </div>
  );
};
