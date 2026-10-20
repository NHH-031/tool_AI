"use client";

import React, { useState, useRef } from "react";
import { uploadCustomImage } from "../../api-client";
import { Scene, StoryboardImage } from "../../types";

interface CustomImageUploadModalProps {
  scene: Scene;
  projectId: string;
  aspectRatio?: "16:9" | "9:16";
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (updatedImage: StoryboardImage) => void;
}

export const CustomImageUploadModal: React.FC<CustomImageUploadModalProps> = ({
  scene,
  projectId,
  aspectRatio = "16:9",
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileB64, setSelectedFileB64] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [applyFilter, setApplyFilter] = useState<boolean>(true);
  const [sketchStyle, setSketchStyle] = useState<"watercolor_comic" | "pure_ink">("watercolor_comic");
  const [contrast, setContrast] = useState<number>(1.2);
  const [lineStrength, setLineStrength] = useState<number>(1.3);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setErrorMsg("Vui lòng chọn file hình ảnh hợp lệ (PNG, JPG, WEBP, SVG)");
      return;
    }

    setFileName(file.name);
    setErrorMsg(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      setSelectedFileB64(event.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUploadAndConvert = async () => {
    if (!selectedFileB64) {
      setErrorMsg("Vui lòng chọn 1 ảnh từ thiết bị của bạn trước");
      return;
    }

    try {
      setIsProcessing(true);
      setErrorMsg(null);

      const savedImg = await uploadCustomImage({
        projectId,
        sceneId: scene.id,
        sceneIndex: scene.scene_index,
        imageDataBase64: selectedFileB64,
        applySketchFilter: applyFilter,
        sketchStyle,
        contrast,
        lineStrength,
        aspectRatio,
      });

      onUploadSuccess(savedImg);
      onClose();
    } catch (err: any) {
      console.error("[CustomImageUploadModal] Lỗi tải và chuyển đổi ảnh:", err);
      setErrorMsg(err?.message || "Không thể tải lên và áp dụng bộ lọc cho hình ảnh");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center justify-center font-bold text-sm">
              📤
            </span>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Tải ảnh riêng / Logo & Chuyển thành nét vẽ (Cảnh {scene.scene_index})
              </h3>
              <p className="text-xs text-slate-400">
                Tự động đưa ảnh về nền giấy kem cổ điển <span className="text-amber-300 font-mono">#F5EBD7</span> và viền nét mực đen
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[75vh]">
          {/* File Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Chọn ảnh logo, ảnh chụp sản phẩm hoặc sơ đồ từ máy tính:
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-6 text-center cursor-pointer transition bg-slate-950/40 hover:bg-slate-950/60"
            >
              {selectedFileB64 ? (
                <div className="flex flex-col items-center gap-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={selectedFileB64}
                    alt="Preview"
                    className="max-h-44 max-w-full rounded-lg object-contain border border-slate-700 shadow"
                  />
                  <div className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
                    <span>✓ Đã chọn:</span>
                    <span className="font-mono text-slate-200">{fileName}</span>
                    <span className="text-slate-400 underline ml-2">(Bấm để đổi ảnh)</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 py-4">
                  <div className="text-3xl">📁</div>
                  <p className="text-xs font-semibold text-indigo-400">
                    Bấm để tải ảnh lên (PNG, JPG, WEBP, SVG)
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Hỗ trợ ảnh trong suốt (transparent logo), ảnh chụp sản phẩm hoặc sơ đồ
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Filter Options */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>🎨</span> Bộ lọc nét vẽ tay (Comic Sketch Filter)
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Khử chất liệu 3D thực tế, biến hình ảnh thành tranh vẽ tay trên nền kem cổ điển #F5EBD7
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={applyFilter}
                  onChange={(e) => setApplyFilter(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>

            {applyFilter && (
              <div className="space-y-3 pt-3 border-t border-slate-800/80">
                {/* Style Mode */}
                <div>
                  <span className="text-[11px] font-medium text-slate-400 block mb-1.5">Phong cách nét vẽ:</span>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setSketchStyle("watercolor_comic")}
                      className={`p-2.5 rounded-xl border text-xs font-medium flex items-center gap-2 transition ${
                        sketchStyle === "watercolor_comic"
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      <span>🖌️</span>
                      <div className="text-left">
                        <div className="font-bold text-slate-200">Màu nước Comic</div>
                        <div className="text-[10px] text-slate-400">Giữ màu dịu + viền mực đen</div>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setSketchStyle("pure_ink")}
                      className={`p-2.5 rounded-xl border text-xs font-medium flex items-center gap-2 transition ${
                        sketchStyle === "pure_ink"
                          ? "bg-indigo-600/20 border-indigo-500 text-indigo-300"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      <span>✒️</span>
                      <div className="text-left">
                        <div className="font-bold text-slate-200">Nét mực đen thuần</div>
                        <div className="text-[10px] text-slate-400">Bút sắt + bóng chì graphite</div>
                      </div>
                    </button>
                  </div>
                </div>

                {/* Sliders */}
                <div className="grid grid-cols-2 gap-4 pt-1">
                  <div>
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                      <span>Độ tương phản:</span>
                      <span className="font-mono text-slate-300">{contrast.toFixed(1)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.8"
                      max="1.8"
                      step="0.1"
                      value={contrast}
                      onChange={(e) => setContrast(Number(e.target.value))}
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                      <span>Độ đanh nét mực:</span>
                      <span className="font-mono text-slate-300">{lineStrength.toFixed(1)}x</span>
                    </div>
                    <input
                      type="range"
                      min="0.8"
                      max="2.0"
                      step="0.1"
                      value={lineStrength}
                      onChange={(e) => setLineStrength(Number(e.target.value))}
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Error display */}
          {errorMsg && (
            <div className="p-3 bg-rose-950/70 border border-rose-800/80 rounded-xl text-xs text-rose-300 flex items-center gap-2">
              <span>⚠️</span>
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
          >
            Hủy bỏ
          </button>

          <button
            id="btn-upload-sketch-convert"
            onClick={handleUploadAndConvert}
            disabled={isProcessing || !selectedFileB64}
            className={`px-5 py-2.5 rounded-xl text-xs font-bold text-white flex items-center gap-2 transition shadow-lg ${
              isProcessing || !selectedFileB64
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/25 active:scale-95"
            }`}
          >
            {isProcessing ? (
              <>
                <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Đang xử lý nét vẽ...</span>
              </>
            ) : (
              <>
                <span>✨</span>
                <span>Chuyển thành tranh vẽ & Áp dụng</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
