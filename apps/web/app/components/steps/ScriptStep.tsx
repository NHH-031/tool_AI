"use client";

import React, { useState } from "react";
import { Scene, TemplateItem } from "../../types";

interface ScriptStepProps {
  projectTitle: string;
  onUpdateTitle: (title: string) => void;
  rawText: string;
  onUpdateRawText: (text: string) => void;
  inputMode: "text" | "srt";
  onUpdateInputMode: (mode: "text" | "srt") => void;
  scenes: Scene[];
  onUpdateScenes: (scenes: Scene[]) => void;
  templates: TemplateItem[];
  selectedTemplateId: string;
  onSelectTemplate: (tplId: string) => void;
  onAnalyze: (text: string, mode: "text" | "srt", targetScenes?: number) => Promise<void>;
  isAnalyzing: boolean;
  onNextStep: () => void;
}

export const ScriptStep: React.FC<ScriptStepProps> = ({
  projectTitle,
  onUpdateTitle,
  rawText,
  onUpdateRawText,
  inputMode,
  onUpdateInputMode,
  scenes,
  onUpdateScenes,
  templates,
  selectedTemplateId,
  onSelectTemplate,
  onAnalyze,
  isAnalyzing,
  onNextStep,
}) => {
  const [targetSceneCount, setTargetSceneCount] = useState<number>(scenes.length > 0 ? scenes.length : 3);
  const [autoSplitMode, setAutoSplitMode] = useState<boolean>(true);
  const [editingSceneId, setEditingSceneId] = useState<string | null>(null);

  const sampleIdeas = [
    {
      title: "Pin năng lượng mặt trời hoạt động thế nào?",
      text: "Pin năng lượng mặt trời hấp thụ photon từ ánh sáng mặt trời. Các photon này giải phóng electron bên trong tinh thể silic, tạo ra dòng điện một chiều. Bộ biến tần inverter sau đó chuyển đổi thành dòng điện xoay chiều để thắp sáng ngôi nhà bạn.",
    },
    {
      title: "Vòng tuần hoàn của nước",
      text: "Nước từ đại dương và sông hồ bốc hơi dưới ánh nắng mặt trời tạo thành mây. Khi mây tích tụ đủ nặng, những giọt nước rơi xuống tạo thành mưa. Nước mưa ngấm vào lòng đất và chảy ngược ra biển, hoàn tất chu trình tuần hoàn vĩnh cửu.",
    },
    {
      title: "Chú khỉ và buồng chuối",
      text: "Một chú khỉ tinh nghịch đang quan sát buồng chuối vàng ươm trên ngọn cây cao. Chú thoăn thoắt chuyền cành, vươn tay hái lấy quả chuối ngọt ngào và thưởng thức ngon lành.",
    },
  ];

  const handleApplySample = (sample: { title: string; text: string }) => {
    onUpdateTitle(sample.title);
    onUpdateRawText(sample.text);
  };

  const handleUpdateSceneText = (index: number, newText: string) => {
    const updated = [...scenes];
    updated[index] = { ...updated[index], text: newText };
    onUpdateScenes(updated);
  };

  const handleUpdateScenePrompt = (index: number, newPrompt: string) => {
    const updated = [...scenes];
    updated[index] = { ...updated[index], prompt: newPrompt };
    onUpdateScenes(updated);
  };

  const handleDeleteScene = (index: number) => {
    const updated = scenes.filter((_, i) => i !== index).map((sc, i) => ({
      ...sc,
      scene_index: i + 1,
    }));
    onUpdateScenes(updated);
  };

  const handleAddScene = () => {
    const newScene: Scene = {
      id: `scene-${Date.now()}`,
      scene_index: scenes.length + 1,
      text: "Lời thoại mới cho cảnh này...",
      prompt: "whiteboard doodle on warm vintage cream paper #F5EBD7, crisp dark ink outlines",
      duration_sec: 4,
      image_status: "idle",
      audio_status: "idle",
    };
    onUpdateScenes([...scenes, newScene]);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Banner / Guidance */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">Bước 1:</span> Soạn thảo Kịch bản & Phân cảnh
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Nhập văn bản hoặc SRT. AI Local sẽ chia 2–3 câu/cảnh và tạo prompt hình ảnh theo chuẩn SKILL.md.
            </p>
          </div>

          {/* Quick Idea Presets */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500 font-medium">Mẫu gợi ý:</span>
            {sampleIdeas.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleApplySample(s)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition"
              >
                {s.title.slice(0, 20)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Left editor, Right config & preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Script Text Editor (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
            {/* Title & Mode */}
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Tên dự án / Video
                </label>
                <input
                  type="text"
                  value={projectTitle}
                  onChange={(e) => onUpdateTitle(e.target.value)}
                  placeholder="Ví dụ: Pin năng lượng mặt trời hoạt động thế nào"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-100 placeholder-slate-500 text-sm outline-none transition"
                />
              </div>

              {/* Mode Selector Tabs */}
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs font-medium text-slate-400">Định dạng kịch bản:</span>
                <div className="flex p-0.5 rounded-lg bg-slate-950 border border-slate-800">
                  <button
                    onClick={() => onUpdateInputMode("text")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                      inputMode === "text"
                        ? "bg-indigo-600 text-white shadow"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    📝 Văn bản thường
                  </button>
                  <button
                    onClick={() => onUpdateInputMode("srt")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                      inputMode === "srt"
                        ? "bg-indigo-600 text-white shadow"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    ⏱️ Phụ đề SRT
                  </button>
                </div>
              </div>
            </div>

            {/* Script Textarea */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Nội dung lời thoại {inputMode === "srt" ? "(Định dạng SRT với timestamp)" : "(Văn bản tự nhiên)"}
              </label>
              <textarea
                rows={9}
                value={rawText}
                onChange={(e) => onUpdateRawText(e.target.value)}
                placeholder={
                  inputMode === "text"
                    ? "Nhập ý tưởng hoặc lời thoại hoàn chỉnh của video tại đây...\nVí dụ: Giới thiệu về quy trình sản xuất năng lượng sạch từ mặt trời..."
                    : "1\n00:00:01,000 --> 00:00:04,500\nPin năng lượng mặt trời đón ánh sáng...\n\n2\n00:00:04,500 --> 00:00:08,000\nCác photon biến thành dòng điện xoay chiều..."
                }
                className="w-full p-4 rounded-xl bg-slate-950/80 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-100 placeholder-slate-600 text-sm leading-relaxed outline-none transition font-sans custom-scrollbar"
              />
              <div className="flex items-center justify-between text-xs text-slate-500 mt-2 px-1">
                <span>{rawText.trim().split(/\s+/).filter(Boolean).length} từ · {rawText.length} ký tự</span>
                <span>Ước tính thời lượng: ~{Math.ceil(rawText.trim().split(/\s+/).filter(Boolean).length / 2.5)} giây</span>
              </div>
            </div>

            {/* Split Settings */}
            <div className="pt-2 border-t border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Tùy chọn phân cảnh AI</span>
                <button
                  type="button"
                  onClick={() => setAutoSplitMode(!autoSplitMode)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition"
                >
                  {autoSplitMode ? "Tự động (2–3 câu/cảnh)" : "Chỉ định số cảnh cụ thể"}
                </button>
              </div>

              {!autoSplitMode && (
                <div className="space-y-1 bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Số cảnh mong muốn:</span>
                    <span className="font-bold text-indigo-400">{targetSceneCount} cảnh</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={15}
                    step={1}
                    value={targetSceneCount}
                    onChange={(e) => setTargetSceneCount(parseInt(e.target.value, 10))}
                    className="w-full accent-indigo-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>1 cảnh ngắn</span>
                    <span>15 cảnh chi tiết</span>
                  </div>
                </div>
              )}
            </div>

            {/* Action Analyze Button */}
            <div className="pt-2">
              <button
                id="btn-analyze-script"
                onClick={() => onAnalyze(rawText, inputMode, autoSplitMode ? undefined : targetSceneCount)}
                disabled={isAnalyzing || !rawText.trim()}
                className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition active:scale-[0.99] ${
                  isAnalyzing || !rawText.trim()
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                    : "bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-indigo-600/30"
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>AI Local đang phân tích & tạo prompt vẽ tay...</span>
                  </>
                ) : (
                  <>
                    <span>🤖</span>
                    <span>Phân tích kịch bản & Tạo phân cảnh</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Scene Breakdown Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 flex flex-col h-full min-h-[460px]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-200">Danh sách phân cảnh</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {scenes.length} cảnh
                </span>
              </div>
              {scenes.length > 0 && (
                <button
                  onClick={handleAddScene}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium transition"
                >
                  <span>+ Thêm cảnh</span>
                </button>
              )}
            </div>

            {/* Scenes List or Empty Placeholder */}
            <div className="flex-1 overflow-y-auto space-y-3 py-3 custom-scrollbar max-h-[500px]">
              {scenes.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
                  <div className="w-12 h-12 rounded-2xl bg-slate-800/60 flex items-center justify-center text-2xl mb-3">
                    📜
                  </div>
                  <p className="text-xs sm:text-sm font-medium text-slate-400">Chưa có phân cảnh nào</p>
                  <p className="text-xs text-slate-500 max-w-xs mt-1">
                    Nhập nội dung ở cột bên trái và bấm &quot;Phân tích kịch bản&quot; để AI chia cảnh và viết prompt ảnh tự động.
                  </p>
                </div>
              ) : (
                scenes.map((scene, idx) => (
                  <div
                    key={scene.id || idx}
                    className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition space-y-2 group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold">
                          {idx + 1}
                        </span>
                        <span className="text-xs font-semibold text-slate-200">Cảnh {idx + 1}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500">~{scene.duration_sec || 4}s</span>
                        <button
                          onClick={() => handleDeleteScene(idx)}
                          className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 text-xs transition"
                          title="Xóa cảnh"
                        >
                          ✕
                        </button>
                      </div>
                    </div>

                    {/* Dialogue Text */}
                    <div>
                      <div className="text-[10px] uppercase font-bold text-slate-500">Lời thoại:</div>
                      <textarea
                        rows={2}
                        value={scene.text}
                        onChange={(e) => handleUpdateSceneText(idx, e.target.value)}
                        className="w-full mt-1 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800/80 focus:border-indigo-500 text-xs text-slate-200 outline-none resize-none transition"
                      />
                    </div>

                    {/* Prompt Preview */}
                    <div>
                      <div className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
                        <span>Prompt ảnh (SKILL.md):</span>
                        <span className="text-[9px] text-emerald-400/80 font-mono">#F5EBD7 ink</span>
                      </div>
                      <textarea
                        rows={2}
                        value={scene.prompt}
                        onChange={(e) => handleUpdateScenePrompt(idx, e.target.value)}
                        className="w-full mt-1 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800/80 focus:border-indigo-500 text-[11px] text-slate-300 font-mono outline-none resize-none transition"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Bottom Next Step Button */}
            <div className="pt-3 border-t border-slate-800">
              <button
                id="btn-script-next"
                onClick={onNextStep}
                disabled={scenes.length === 0}
                className={`w-full py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition ${
                  scenes.length === 0
                    ? "bg-slate-800 text-slate-600 cursor-not-allowed"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/25 active:scale-[0.99]"
                }`}
              >
                <span>Tiếp tục sang Storyboard (Bước 2)</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
