"use client";

import React, { useState, useRef, useEffect } from "react";
import { MusicTrackItem } from "../../types";
import { uploadCustomBgm } from "../../api-client";

interface CustomMusicUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMusicSaved: (track: MusicTrackItem) => void;
}

export const CustomMusicUploadModal: React.FC<CustomMusicUploadModalProps> = ({
  isOpen,
  onClose,
  onMusicSaved,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState<string>("");
  const [mood, setMood] = useState<string>("Tươi Sáng, Hứng Khởi");
  const [genre, setGenre] = useState<string>("Acoustic Folk");
  const [recommendedVolume, setRecommendedVolume] = useState<number>(0.15);
  
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [isPlayingPreview, setIsPlayingPreview] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const previewAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
        previewAudioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isOpen) {
      if (previewAudioRef.current) {
        previewAudioRef.current.pause();
      }
      setSelectedFile(null);
      setTitle("");
      setPreviewAudioUrl(null);
      setIsPlayingPreview(false);
      setErrorMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMessage(null);
      // Gợi ý tiêu đề bài nhạc từ tên file
      const baseName = file.name.replace(/\.[^/.]+$/, "");
      if (!title) {
        setTitle(baseName);
      }
      const url = URL.createObjectURL(file);
      setPreviewAudioUrl(url);
    }
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
    audio.volume = recommendedVolume;
    audio.onended = () => setIsPlayingPreview(false);
    audio.onerror = () => setIsPlayingPreview(false);
    audio.play().then(() => {
      previewAudioRef.current = audio;
      setIsPlayingPreview(true);
    }).catch(() => {
      setIsPlayingPreview(false);
    });
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const res = reader.result as string;
        resolve(res);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleSave = async () => {
    if (!selectedFile) {
      setErrorMessage("Vui lòng chọn 1 file nhạc MP3/WAV từ máy tính.");
      return;
    }
    if (!title.trim()) {
      setErrorMessage("Vui lòng nhập tên bài nhạc nền.");
      return;
    }

    try {
      setIsUploading(true);
      setErrorMessage(null);

      const base64Str = await fileToBase64(selectedFile);
      const track = await uploadCustomBgm({
        title: title.trim(),
        audioDataBase64: base64Str,
        mood,
        genre,
        recommendedVolume,
      });

      onMusicSaved(track);
      onClose();
    } catch (err: any) {
      console.error("[CustomMusicUploadModal] Lỗi upload BGM:", err);
      setErrorMessage(err?.message || "Không thể tải file nhạc lên hệ thống.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl shadow-indigo-950/40 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400">
              🎵
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Tải Nhạc Nền Riêng (BGM)</h2>
              <p className="text-xs text-slate-400">Tải lên bài hát yêu thích định dạng MP3/WAV để làm nhạc nền video</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading}
            className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 flex-1 overflow-y-auto">
          {errorMessage && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
              <span>⚠️</span>
              <span>{errorMessage}</span>
            </div>
          )}

          {/* File Picker */}
          <label className="block p-6 border-2 border-dashed border-slate-700 hover:border-indigo-500/70 rounded-2xl bg-slate-950/40 cursor-pointer text-center transition group">
            <input
              type="file"
              accept="audio/*,.mp3,.wav,.aac,.m4a"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="w-10 h-10 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400 group-hover:scale-110 transition mb-2">
              📤
            </div>
            <div className="text-sm font-semibold text-white mb-1">
              {selectedFile ? selectedFile.name : "Bấm để chọn file nhạc MP3 hoặc WAV"}
            </div>
            <div className="text-xs text-slate-400">
              Hỗ trợ MP3, WAV, AAC, M4A (Tối đa 50MB)
            </div>
          </label>

          {/* Preview Bar */}
          {previewAudioUrl && (
            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-slate-300 truncate">
                <span>🎧</span>
                <span className="truncate">{selectedFile?.name}</span>
              </div>
              <button
                type="button"
                onClick={togglePreview}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
              >
                {isPlayingPreview ? "⏸️ Dừng nghe" : "▶️ Nghe thử"}
              </button>
            </div>
          )}

          {/* Track Details */}
          <div className="space-y-3 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Tên bài nhạc:
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: Nhạc nền truyền cảm hứng nhẹ nhàng"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Tâm trạng (Mood):
                </label>
                <select
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                >
                  <option value="Tươi Sáng, Hứng Khởi">Tươi Sáng, Hứng Khởi</option>
                  <option value="Thư Giãn, Lofi">Thư Giãn, Lofi</option>
                  <option value="Chuyên Nghiệp, Doanh Nghiệp">Chuyên Nghiệp, Doanh Nghiệp</option>
                  <option value="Vui Nhộn, Trẻ Thơ">Vui Nhộn, Trẻ Thơ</option>
                  <option value="Hồi Hộp, Kịch Tính">Hồi Hộp, Kịch Tính</option>
                  <option value="Thanh Bình, Tĩnh Tâm">Thanh Bình, Tĩnh Tâm</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Thể loại (Genre):
                </label>
                <input
                  type="text"
                  value={genre}
                  onChange={(e) => setGenre(e.target.value)}
                  placeholder="VD: Lofi, Acoustic, v.v."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Âm lượng gợi ý:</span>
                <span className="font-mono text-indigo-400">{Math.round(recommendedVolume * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.4}
                step={0.05}
                value={recommendedVolume}
                onChange={(e) => setRecommendedVolume(parseFloat(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isUploading}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Hủy bỏ
          </button>

          <button
            onClick={handleSave}
            disabled={isUploading || !selectedFile || !title.trim()}
            className={`px-6 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-2 transition ${
              isUploading || !selectedFile || !title.trim()
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 active:scale-95"
            }`}
          >
            {isUploading ? (
              <>
                <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang tải lên...</span>
              </>
            ) : (
              <>
                <span>💾 Thêm vào danh mục BGM</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
