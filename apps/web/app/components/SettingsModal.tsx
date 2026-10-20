"use client";

import React, { useState, useEffect } from "react";
import { DrawingToolItem, VoiceItem } from "../types";

export interface StudioSettings {
  geminiApiKey: string;
  elevenLabsApiKey?: string;
  defaultVoiceId: string;
  defaultSpeed: number;
  defaultAspectRatio: "16:9" | "9:16";
  defaultHandToolId: string;
  defaultSubtitleStyle: "none" | "classic" | "karaoke";
}

export const SETTINGS_STORAGE_KEY = "whiteboard_studio_settings_v1";

export const DEFAULT_SETTINGS: StudioSettings = {
  geminiApiKey: "",
  elevenLabsApiKey: "",
  defaultVoiceId: "vi-VN-Standard-B",
  defaultSpeed: 1.0,
  defaultAspectRatio: "16:9",
  defaultHandToolId: "hand-pen-modern",
  defaultSubtitleStyle: "classic",
};


interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  voices?: VoiceItem[];
  drawingTools?: DrawingToolItem[];
  onSettingsSaved?: (newSettings: StudioSettings) => void;
  onClearDrafts?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  voices = [],
  drawingTools = [],
  onSettingsSaved,
  onClearDrafts,
}) => {
  const [settings, setSettings] = useState<StudioSettings>(DEFAULT_SETTINGS);
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      try {
        const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          setSettings({ ...DEFAULT_SETTINGS, ...parsed });
        }
      } catch (e) {
        console.warn("[SettingsModal] Lỗi đọc cài đặt:", e);
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
      setSaveSuccess(true);
      if (onSettingsSaved) {
        onSettingsSaved(settings);
      }
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 800);
    } catch (e) {
      console.error("[SettingsModal] Lỗi lưu cài đặt:", e);
    }
  };

  const handleClearAllStorage = () => {
    if (confirm("Bạn có chắc chắn muốn xóa toàn bộ bản nháp và cài đặt lưu trên trình duyệt?")) {
      localStorage.clear();
      if (onClearDrafts) onClearDrafts();
      setSettings(DEFAULT_SETTINGS);
      alert("Đã xóa toàn bộ bộ nhớ tạm trên trình duyệt.");
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl shadow-indigo-950/40 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400">
              ⚙️
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Cài Đặt Studio & Cấu Hình Mặc Định</h2>
              <p className="text-xs text-slate-400">Tùy biến tham số, API key và quy cách dựng video</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 overflow-y-auto custom-scrollbar flex-1">
          {/* Section: Gemini API Key */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Google Gemini API Key (Tùy chọn)</span>
              <span className="text-[10px] text-emerald-400 font-normal">Hỗ trợ phân đoạn kịch bản sâu</span>
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                placeholder="AIzaSy..."
                value={settings.geminiApiKey}
                onChange={(e) => setSettings({ ...settings, geminiApiKey: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm font-mono text-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition pr-10"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs"
              >
                {showApiKey ? "Ẩn" : "Hiện"}
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              * Không bắt buộc. Studio đã tích hợp bộ dịch tự động miễn phí không cần API key.
            </p>
          </div>

          {/* Section: ElevenLabs API Key (Task 8.4) */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>ElevenLabs API Key (Giọng Biểu Cảm Cao Cấp)</span>
              <span className="text-[10px] text-indigo-400 font-normal">Task 8.4 · Multilingual v2</span>
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                placeholder="xi-api-key..."
                value={settings.elevenLabsApiKey || ""}
                onChange={(e) => setSettings({ ...settings, elevenLabsApiKey: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm font-mono text-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition pr-10"
              />
            </div>
            <p className="text-[11px] text-slate-500">
              * Tùy chọn. Nếu chưa điền key, hệ thống tự động sử dụng EdgeTTS miễn phí không giới hạn.
            </p>
          </div>


          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tỷ lệ khung hình mặc định */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Tỷ Lệ Video Mặc Định
              </label>
              <select
                value={settings.defaultAspectRatio}
                onChange={(e) =>
                  setSettings({ ...settings, defaultAspectRatio: e.target.value as "16:9" | "9:16" })
                }
                className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="16:9">16:9 Widescreen (YouTube, Máy tính)</option>
                <option value="9:16">9:16 Dọc (TikTok, Shorts, Reels)</option>
              </select>
            </div>

            {/* Bút vẽ mặc định */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Bút Vẽ & Bàn Tay Mặc Định
              </label>
              <select
                value={settings.defaultHandToolId}
                onChange={(e) => setSettings({ ...settings, defaultHandToolId: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="hand-pen-modern">✍️ Bút dạ đen hiện đại</option>
                <option value="hand-marker">🖍️ Bút viết bảng Whiteboard</option>
                <option value="hand-quill-vintage">🪶 Bút lông ngỗng cổ điển</option>
                <option value="hand-calligraphy">🖌️ Bút lông thư pháp Á Đông</option>
                <option value="no_hand">✨ Ẩn bàn tay (Nét tự hiện)</option>
              </select>
            </div>

            {/* Giọng đọc mặc định */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Giọng Đọc Mặc Định
              </label>
              <select
                value={settings.defaultVoiceId}
                onChange={(e) => setSettings({ ...settings, defaultVoiceId: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="vi-VN-Standard-B">Nam Khánh (Bắc Bộ Trầm Ấm)</option>
                <option value="vi-VN-Standard-A">Thu Ngân (Bắc Bộ Ngọt Ngào)</option>
                <option value="vi-VN-Wavenet-A">Mai Phương (Bắc Bộ Trong Trẻo)</option>
                <option value="vi-VN-Standard-C">Minh Quang (Nam Bộ Truyền Cảm)</option>
              </select>
            </div>

            {/* Kiểu phụ đề mặc định */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Kiểu Phụ Đề Mặc Định
              </label>
              <select
                value={settings.defaultSubtitleStyle}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    defaultSubtitleStyle: e.target.value as "none" | "classic" | "karaoke",
                  })
                }
                className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:border-indigo-500 outline-none"
              >
                <option value="classic">Phụ đề chuẩn (Classic Subtitles)</option>
                <option value="karaoke">Phụ đề chạy chữ (TikTok Karaoke)</option>
                <option value="none">Không đính kèm phụ đề</option>
              </select>
            </div>
          </div>

          {/* Tốc độ đọc */}
          <div className="space-y-2 bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
            <div className="flex justify-between text-xs font-medium text-slate-300">
              <span>Tốc độ đọc giọng AI mặc định:</span>
              <span className="font-mono text-indigo-400 font-bold">{settings.defaultSpeed}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.4"
              step="0.05"
              value={settings.defaultSpeed}
              onChange={(e) => setSettings({ ...settings, defaultSpeed: parseFloat(e.target.value) })}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.8x (Chậm rãi)</span>
              <span>1.0x (Tự nhiên)</span>
              <span>1.4x (Nhanh)</span>
            </div>
          </div>

          {/* Dọn dẹp bộ nhớ */}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-rose-400">Bộ nhớ tạm & Bản nháp</div>
              <div className="text-[11px] text-slate-500">Xóa sạch các bản lưu nháp tự động trên trình duyệt này</div>
            </div>
            <button
              onClick={handleClearAllStorage}
              className="px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs transition"
            >
              🗑️ Xóa bản nháp
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800/80 flex items-center justify-between bg-slate-950/60">
          <div className="text-xs text-slate-500">
            {saveSuccess ? (
              <span className="text-emerald-400 font-medium">✓ Đã lưu cài đặt thành công!</span>
            ) : (
              <span>Cài đặt lưu tự động vào trình duyệt</span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              Hủy
            </button>
            <button
              onClick={handleSave}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition shadow-lg shadow-indigo-600/30 active:scale-95"
            >
              Lưu Cài Đặt
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
