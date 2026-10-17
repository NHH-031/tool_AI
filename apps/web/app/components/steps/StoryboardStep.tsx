"use client";

import React, { useState } from "react";
import { Scene, StoryboardImage } from "../../types";

interface StoryboardStepProps {
  scenes: Scene[];
  images: StoryboardImage[];
  onUpdateScenePrompt: (sceneIndex: number, newPrompt: string) => void;
  onGenerateSingleImage: (scene: Scene) => Promise<void>;
  onGenerateAllImages: () => Promise<void>;
  isGeneratingAll: boolean;
  generatingSceneId: string | null;
  onBackStep: () => void;
  onNextStep: () => void;
}

export const StoryboardStep: React.FC<StoryboardStepProps> = ({
  scenes,
  images,
  onUpdateScenePrompt,
  onGenerateSingleImage,
  onGenerateAllImages,
  isGeneratingAll,
  generatingSceneId,
  onBackStep,
  onNextStep,
}) => {
  const [selectedSceneModal, setSelectedSceneModal] = useState<Scene | null>(null);

  // Helper to find image for scene
  const getImageForScene = (scene: Scene) => {
    const found = images.find((img) => img.scene_id === scene.id || img.scene_index === scene.scene_index);
    if (found?.image_url) return found.image_url;
    if (scene.image_url) return scene.image_url;
    return null;
  };

  const allImagesReady =
    scenes.length > 0 &&
    scenes.every((sc) => {
      const url = getImageForScene(sc);
      return Boolean(url);
    });

  const completedCount = scenes.filter((sc) => Boolean(getImageForScene(sc))).length;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Controls Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">Bước 2:</span> Tạo Ảnh Storyboard Vẽ Tay (AI FLUX.2 Klein)
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Mỗi cảnh được tạo 1 hình ảnh vẽ nét mực trên nền giấy kem <span className="text-amber-300 font-mono">#F5EBD7</span>. Bạn có thể chỉnh sửa prompt hoặc vẽ lại từng cảnh.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">
              Tiến độ: <strong className="text-emerald-400">{completedCount}/{scenes.length}</strong> ảnh
            </span>
            <button
              id="btn-gen-all-images"
              onClick={onGenerateAllImages}
              disabled={isGeneratingAll || scenes.length === 0}
              className={`px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition shadow-lg ${
                isGeneratingAll || scenes.length === 0
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25 active:scale-95"
              }`}
            >
              {isGeneratingAll ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Đang vẽ tất cả cảnh...</span>
                </>
              ) : (
                <>
                  <span>✨</span>
                  <span>Vẽ tất cả các cảnh</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Grid of Storyboard Scenes */}
      {scenes.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <p className="text-base font-medium">Chưa có phân cảnh nào từ kịch bản</p>
          <p className="text-xs text-slate-500 mt-1">Vui lòng quay lại Bước 1 để nhập nội dung và phân tích kịch bản trước.</p>
          <button
            onClick={onBackStep}
            className="mt-4 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
          >
            ← Quay lại Bước 1
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenes.map((scene, idx) => {
            const imageUrl = getImageForScene(scene);
            const isGeneratingThis = generatingSceneId === scene.id;
            const isQueuedInAll = isGeneratingAll && !isGeneratingThis;

            return (
              <div
                key={scene.id || idx}
                className={`bg-slate-900/70 border rounded-2xl overflow-hidden flex flex-col transition shadow-lg group ${
                  isGeneratingThis
                    ? "border-indigo-500/70 ring-1 ring-indigo-500/40"
                    : "border-slate-800 hover:border-slate-700"
                }`}
              >
                {/* Scene Header */}
                <div className="px-4 py-3 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">Cảnh {idx + 1}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    ~{scene.duration_sec || 4}s
                  </span>
                </div>

                {/* Image Preview Canvas */}
                <div className="relative aspect-video w-full bg-[#F5EBD7]/10 flex items-center justify-center overflow-hidden border-b border-slate-800/80">
                  {/* Hiển thị ảnh nếu đã có */}
                  {imageUrl && (
                    <div className="w-full h-full relative group/img">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={imageUrl}
                        alt={`Storyboard cảnh ${idx + 1}`}
                        className={`w-full h-full object-cover transition duration-300 ${
                          isGeneratingThis ? "opacity-25 filter blur-[2px] scale-95" : "group-hover/img:scale-105"
                        }`}
                      />
                      {!isGeneratingThis && !isGeneratingAll && (
                        <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover/img:opacity-100 transition flex items-center justify-center gap-2 backdrop-blur-xs">
                          <button
                            onClick={() => onGenerateSingleImage(scene)}
                            disabled={isGeneratingThis || isGeneratingAll}
                            className="px-3 py-1.5 rounded-lg bg-slate-900/90 text-white text-xs font-medium border border-slate-700 hover:bg-indigo-600 transition shadow flex items-center gap-1.5 active:scale-95"
                          >
                            <span>🔄</span>
                            <span>Sinh lại</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Vòng tròn xoay Loading Overlay khi đang sinh ảnh cho cảnh này */}
                  {isGeneratingThis && (
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center p-4 text-center space-y-3 animate-in fade-in duration-200">
                      <div className="relative flex items-center justify-center">
                        {/* Vòng tròn loading xoay mượt mà */}
                        <div className="w-12 h-12 rounded-full border-3 border-indigo-500/20 border-t-indigo-400 animate-spin" />
                        <span className="absolute inset-0 flex items-center justify-center text-sm animate-pulse">
                          🎨
                        </span>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs font-bold text-indigo-300 animate-pulse flex items-center justify-center gap-1.5">
                          <span>{imageUrl ? "Đang sinh lại ảnh phân cảnh..." : "Đang tạo ảnh nét vẽ tay..."}</span>
                        </p>
                        <p className="text-[10px] text-slate-400 font-mono">
                          FLUX.2 Klein / ComfyUI (1080p)
                        </p>
                        <div className="flex items-center justify-center gap-1 pt-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "150ms" }}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "300ms" }}></span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Đang trong hàng đợi vẽ khi vẽ tất cả các cảnh */}
                  {!imageUrl && isQueuedInAll && !isGeneratingThis && (
                    <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
                      <div className="w-10 h-10 rounded-xl bg-slate-800/60 flex items-center justify-center text-xl animate-pulse">
                        ⏳
                      </div>
                      <p className="text-xs text-amber-300 font-medium">Đang xếp hàng vẽ...</p>
                      <p className="text-[10px] text-slate-500">Chờ hoàn thành cảnh trước</p>
                    </div>
                  )}

                  {/* Chưa có ảnh và không trong trạng thái sinh */}
                  {!imageUrl && !isGeneratingThis && !isQueuedInAll && (
                    <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
                      <div className="w-10 h-10 rounded-xl bg-slate-800/60 flex items-center justify-center text-xl">
                        🎨
                      </div>
                      <p className="text-xs text-slate-400">Chưa sinh ảnh</p>
                      <button
                        onClick={() => onGenerateSingleImage(scene)}
                        disabled={isGeneratingAll}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-md shadow-indigo-600/20 active:scale-95"
                      >
                        Vẽ ảnh cảnh này
                      </button>
                    </div>
                  )}

                  {/* Quality Badge */}
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-md text-[10px] text-emerald-400 border border-emerald-500/20 font-mono z-10">
                    SKILL.md 1080p
                  </div>
                </div>

                {/* Dialogue Snippet */}
                <div className="p-3 bg-slate-950/30 border-b border-slate-800/60">
                  <div className="text-[10px] uppercase font-bold text-slate-500 mb-0.5">Lời thoại:</div>
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    &ldquo;{scene.text}&rdquo;
                  </p>
                </div>

                {/* Prompt & Quick Edit */}
                <div className="p-3 flex-1 flex flex-col justify-between space-y-2">
                  <div>
                    <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-500 mb-1">
                      <span>Prompt hình ảnh:</span>
                      <span className="text-slate-500 font-normal">Có thể sửa</span>
                    </div>
                    <textarea
                      rows={3}
                      value={scene.prompt}
                      onChange={(e) => onUpdateScenePrompt(idx, e.target.value)}
                      className="w-full p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-mono text-slate-300 focus:border-indigo-500 outline-none resize-none transition custom-scrollbar"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-400 flex items-center gap-1.5">
                      {isGeneratingThis ? (
                        <span className="text-indigo-400 font-semibold animate-pulse flex items-center gap-1">
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
                          Đang sinh ảnh mới...
                        </span>
                      ) : isQueuedInAll ? (
                        <span className="text-amber-400/90 font-medium flex items-center gap-1">
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" />
                          Đang trong hàng đợi...
                        </span>
                      ) : imageUrl ? (
                        <span className="text-emerald-400 font-medium flex items-center gap-1">
                          ✓ Đã có ảnh
                        </span>
                      ) : (
                        <span>Chờ sinh ảnh</span>
                      )}
                    </span>
                    <button
                      id={`btn-regen-scene-${idx + 1}`}
                      onClick={() => onGenerateSingleImage(scene)}
                      disabled={isGeneratingThis || isGeneratingAll}
                      className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                        isGeneratingThis
                          ? "bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 cursor-wait shadow-sm"
                          : isGeneratingAll
                          ? "bg-slate-800 text-slate-500 border border-slate-800 cursor-not-allowed"
                          : "text-indigo-400 hover:text-indigo-200 bg-slate-800/60 hover:bg-indigo-600/20 border border-slate-700/60 hover:border-indigo-500/50 active:scale-95"
                      }`}
                    >
                      {isGeneratingThis ? (
                        <>
                          <svg className="animate-spin w-3.5 h-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                          <span>Đang sinh lại...</span>
                        </>
                      ) : (
                        <>
                          <span className="text-xs">🔄</span>
                          <span>{imageUrl ? "Sinh lại ảnh" : "Tạo ảnh"}</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Navigation Footer */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
        <button
          onClick={onBackStep}
          className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold transition"
        >
          ← Quay lại Kịch bản
        </button>

        <div className="flex items-center gap-3">
          {!allImagesReady && (
            <span className="text-xs text-amber-400/90 hidden sm:inline">
              ⚠️ Cần có ảnh cho tất cả các cảnh để tiếp tục
            </span>
          )}
          <button
            id="btn-storyboard-next"
            onClick={onNextStep}
            disabled={!allImagesReady}
            className={`px-6 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition ${
              !allImagesReady
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30 active:scale-95"
            }`}
          >
            <span>Tiếp tục sang Giọng đọc (Bước 3)</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};
