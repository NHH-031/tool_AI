"use client";

import React, { useState, useRef, useEffect } from "react";
import { AudioResult, Scene } from "../../types";
import { uploadCustomAudio } from "../../api-client";

interface VoiceRecorderModalProps {
  isOpen: boolean;
  onClose: () => void;
  scene: Scene;
  projectId?: string;
  onAudioSaved: (result: AudioResult) => void;
}

export const VoiceRecorderModal: React.FC<VoiceRecorderModalProps> = ({
  isOpen,
  onClose,
  scene,
  projectId = "default",
  onAudioSaved,
}) => {
  const [tab, setTab] = useState<"mic" | "file">("mic");
  
  // Microphone recording state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingSeconds, setRecordingSeconds] = useState<number>(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [isPlayingPreview, setIsPlayingPreview] = useState<boolean>(false);
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);

  // Dọn dẹp tài nguyên khi unmount hoặc đóng modal
  useEffect(() => {
    return () => {
      stopRecording();
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
        previewAudioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isOpen) {
      // Reset state khi đóng modal
      stopRecording();
      setRecordedBlob(null);
      setPreviewAudioUrl(null);
      setSelectedFile(null);
      setErrorMessage(null);
      setRecordingSeconds(0);
      setIsPlayingPreview(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const startRecording = async () => {
    setErrorMessage(null);
    setRecordedBlob(null);
    setPreviewAudioUrl(null);
    setRecordingSeconds(0);
    audioChunksRef.current = [];

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Trình duyệt không hỗ trợ truy cập Micro ghi âm trực tiếp.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      let mimeType = "audio/webm";
      if (typeof MediaRecorder.isTypeSupported === "function") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        }
      }

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const fullBlob = new Blob(audioChunksRef.current, { type: mimeType });
        setRecordedBlob(fullBlob);
        const url = URL.createObjectURL(fullBlob);
        setPreviewAudioUrl(url);

        // Dừng toàn bộ tracks micro
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start(250); // Thu thập dữ liệu mỗi 250ms
      setIsRecording(true);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

    } catch (err: any) {
      console.error("[VoiceRecorder] Lỗi mở micro:", err);
      setErrorMessage(err?.message || "Không thể truy cập Micro. Hãy cấp quyền microphone trong trình duyệt.");
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn("[VoiceRecorder] Lỗi khi dừng MediaRecorder:", e);
      }
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    setIsRecording(false);
  };

  const togglePreview = () => {
    if (!previewAudioUrl) return;
    if (isPlayingPreview && previewAudioRef.current) {
      previewAudioRef.current.pause();
      setIsPlayingPreview(false);
      return;
    }

    if (previewAudioRef.current) {
      previewAudioRef.current.pause();
    }

    const audio = new Audio(previewAudioUrl);
    audio.onended = () => setIsPlayingPreview(false);
    audio.onerror = () => setIsPlayingPreview(false);
    audio.play().then(() => {
      previewAudioRef.current = audio;
      setIsPlayingPreview(true);
    }).catch(() => {
      setIsPlayingPreview(false);
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMessage(null);
      const url = URL.createObjectURL(file);
      setPreviewAudioUrl(url);
    }
  };

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const res = reader.result as string;
        resolve(res);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  const handleSaveAudio = async () => {
    let targetBlob: Blob | null = recordedBlob;
    let fileName = `scene_${scene.scene_index}_mic.webm`;

    if (tab === "file") {
      if (!selectedFile) {
        setErrorMessage("Vui lòng chọn 1 file âm thanh từ máy tính");
        return;
      }
      targetBlob = selectedFile;
      fileName = selectedFile.name;
    }

    if (!targetBlob) {
      setErrorMessage("Chưa có đoạn thu âm nào để lưu.");
      return;
    }

    try {
      setIsUploading(true);
      setErrorMessage(null);

      const base64Str = await blobToBase64(targetBlob);
      const result = await uploadCustomAudio({
        projectId,
        sceneId: scene.id,
        sceneIndex: scene.scene_index,
        audioDataBase64: base64Str,
        filename: fileName,
        text: scene.text,
      });

      onAudioSaved(result);
      onClose();
    } catch (err: any) {
      console.error("[VoiceRecorder] Lỗi lưu âm thanh:", err);
      setErrorMessage(err?.message || "Không thể tải âm thanh lên máy chủ.");
    } finally {
      setIsUploading(false);
    }
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl shadow-indigo-950/40 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400">
              🎙️
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Thu Âm Riêng · Cảnh {scene.scene_index}</h2>
              <p className="text-xs text-slate-400">Ghi âm trực tiếp bằng micro hoặc tải file thuyết minh cá nhân</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading || isRecording}
            className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {/* Script Content Cue Card */}
        <div className="px-6 pt-5 pb-2">
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 text-xs">
            <div className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <span>📜 Lời thoại cần đọc:</span>
            </div>
            <p className="text-slate-200 leading-relaxed italic text-sm font-serif">
              &ldquo;{scene.text}&rdquo;
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 flex gap-2">
          <button
            onClick={() => setTab("mic")}
            className={`flex-1 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition ${
              tab === "mic"
                ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>🎙️ Thu âm trực tiếp qua Micro</span>
          </button>
          <button
            onClick={() => setTab("file")}
            className={`flex-1 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border transition ${
              tab === "file"
                ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>📁 Tải file âm thanh (MP3/WAV)</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 flex-1 overflow-y-auto">
          {errorMessage && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
              <span>⚠️</span>
              <span>{errorMessage}</span>
            </div>
          )}

          {tab === "mic" ? (
            <div className="flex flex-col items-center justify-center py-6 px-4 bg-slate-950/40 border border-slate-800/80 rounded-2xl space-y-4 text-center">
              {/* Record Pulsating Visualizer */}
              <div className="relative flex items-center justify-center">
                {isRecording && (
                  <div className="absolute w-24 h-24 rounded-full bg-rose-500/20 animate-ping" />
                )}
                <div
                  className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl transition-all shadow-xl ${
                    isRecording
                      ? "bg-rose-600 text-white shadow-rose-600/50 scale-105"
                      : recordedBlob
                      ? "bg-emerald-600 text-white shadow-emerald-600/40"
                      : "bg-slate-800 text-slate-300 border border-slate-700"
                  }`}
                >
                  {isRecording ? "⏹️" : recordedBlob ? "✅" : "🎙️"}
                </div>
              </div>

              {/* Timer & Status */}
              <div>
                <div className="text-2xl font-mono font-bold text-white tracking-wider">
                  {formatSeconds(recordingSeconds)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {isRecording ? (
                    <span className="text-rose-400 font-medium animate-pulse">
                      🔴 Đang ghi âm... Hãy đọc to và rõ lời thoại phía trên
                    </span>
                  ) : recordedBlob ? (
                    <span className="text-emerald-400 font-medium">
                      Đã ghi âm xong ({formatSeconds(recordingSeconds)}). Bấm nghe thử hoặc lưu lại.
                    </span>
                  ) : (
                    <span>Bấm nút bên dưới để bắt đầu thu âm</span>
                  )}
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-3 pt-2">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 active:scale-95 transition flex items-center gap-2"
                  >
                    <span>🎙️ Bắt đầu ghi âm</span>
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/40 active:scale-95 transition flex items-center gap-2"
                  >
                    <span>⏹️ Dừng ghi âm</span>
                  </button>
                )}

                {previewAudioUrl && !isRecording && (
                  <>
                    <button
                      onClick={togglePreview}
                      className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition flex items-center gap-2"
                    >
                      <span>{isPlayingPreview ? "⏸️ Tạm dừng" : "▶️ Nghe thử"}</span>
                    </button>
                    <button
                      onClick={startRecording}
                      className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition"
                      title="Thu âm lại"
                    >
                      🔄
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <label className="block p-8 border-2 border-dashed border-slate-700 hover:border-indigo-500/70 rounded-2xl bg-slate-950/40 cursor-pointer text-center transition group">
                <input
                  type="file"
                  accept="audio/*,.mp3,.wav,.ogg,.m4a,.aac,.webm"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="w-12 h-12 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-2xl text-indigo-400 group-hover:scale-110 transition mb-3">
                  📁
                </div>
                <div className="text-sm font-semibold text-white mb-1">
                  {selectedFile ? selectedFile.name : "Kéo thả hoặc bấm để chọn file âm thanh"}
                </div>
                <div className="text-xs text-slate-400">
                  Hỗ trợ định dạng MP3, WAV, M4A, OGG, WEBM (Tối đa 25MB)
                </div>
              </label>

              {previewAudioUrl && (
                <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-slate-300 truncate">
                    <span>🎵</span>
                    <span className="truncate">{selectedFile?.name || "File đã chọn"}</span>
                  </div>
                  <button
                    onClick={togglePreview}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                  >
                    {isPlayingPreview ? "⏸️ Dừng" : "▶️ Nghe thử"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isUploading || isRecording}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Hủy bỏ
          </button>

          <button
            onClick={handleSaveAudio}
            disabled={isUploading || isRecording || (!recordedBlob && !selectedFile)}
            className={`px-6 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-2 transition ${
              isUploading || isRecording || (!recordedBlob && !selectedFile)
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 active:scale-95"
            }`}
          >
            {isUploading ? (
              <>
                <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang xử lý & lưu...</span>
              </>
            ) : (
              <>
                <span>💾 Sử dụng âm thanh này</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
