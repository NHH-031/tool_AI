"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { fetchDoodleVault, saveCanvasEdit } from "../../api-client";
import { DoodleItem, Scene, StoryboardImage } from "../../types";

interface SceneCanvasEditorProps {
  scene: Scene;
  imageUrl: string;
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSaveSuccess: (updatedImage: StoryboardImage) => void;
}

type ToolMode = "pen" | "highlighter" | "eraser" | "arrow" | "circle" | "box" | "text" | "doodle";

const PALETTE = [
  { name: "Mực đen", hex: "#1A1A1A" },
  { name: "Vàng dạ quang", hex: "#FFE600" },
  { name: "Đỏ nhấn", hex: "#E53935" },
  { name: "Xanh biển", hex: "#1E88E5" },
  { name: "Xanh ngọc", hex: "#10B981" },
  { name: "Cam rực", hex: "#FF5500" },
  { name: "Giấy kem", hex: "#F5EBD7" },
];

export const SceneCanvasEditor: React.FC<SceneCanvasEditorProps> = ({
  scene,
  imageUrl,
  projectId,
  isOpen,
  onClose,
  onSaveSuccess,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [tool, setTool] = useState<ToolMode>("pen");
  const [color, setColor] = useState<string>("#1A1A1A");
  const [strokeWidth, setStrokeWidth] = useState<number>(4);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Doodle Vault state
  const [doodles, setDoodles] = useState<DoodleItem[]>([]);
  const [selectedDoodle, setSelectedDoodle] = useState<DoodleItem | null>(null);
  const [isDoodleDrawerOpen, setIsDoodleDrawerOpen] = useState<boolean>(false);

  // Text input state
  const [textInput, setTextInput] = useState<string>("");
  const [isAddingText, setIsAddingText] = useState<boolean>(false);

  // Starting coordinate for shape drawing
  const startPos = useRef<{ x: number; y: number } | null>(null);
  const snapshotBeforeShape = useRef<ImageData | null>(null);

  // Nạp danh mục Doodle
  useEffect(() => {
    if (isOpen) {
      fetchDoodleVault().then((items) => {
        setDoodles(items);
        if (items.length > 0 && !selectedDoodle) {
          setSelectedDoodle(items[0]);
        }
      });
    }
  }, [isOpen, selectedDoodle]);

  // Khởi tạo Canvas với hình ảnh phân cảnh gốc
  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = imageUrl;
    img.onload = () => {
      canvas.width = img.naturalWidth || 1920;
      canvas.height = img.naturalHeight || 1080;

      // Tô màu nền giấy kem ấm cổ #F5EBD7 trước
      ctx.fillStyle = "#F5EBD7";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Vẽ hình ảnh lên
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Lưu khung hình ban đầu vào history stack
      const initialData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      setHistory([initialData]);
      setHistoryIndex(0);
    };
  }, [imageUrl]);

  useEffect(() => {
    if (isOpen) {
      initCanvas();
    }
  }, [isOpen, initCanvas]);

  const pushHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const currentData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(currentData);
    if (newHistory.length > 25) newHistory.shift(); // Giữ tối đa 25 bước hoàn tác
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const targetIndex = historyIndex - 1;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.putImageData(history[targetIndex], 0, 0);
      setHistoryIndex(targetIndex);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const targetIndex = historyIndex + 1;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.putImageData(history[targetIndex], 0, 0);
      setHistoryIndex(targetIndex);
    }
  };

  const handleReset = () => {
    if (history.length > 0) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.putImageData(history[0], 0, 0);
      setHistory([history[0]]);
      setHistoryIndex(0);
    }
  };

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCanvasCoords(e);
    setIsDrawing(true);
    startPos.current = { x, y };

    if (tool === "doodle" && selectedDoodle) {
      // Đóng dấu doodle trực tiếp tại vị trí click
      const img = new Image();
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(selectedDoodle.svg_content);
      img.onload = () => {
        const size = Math.max(120, canvas.width * 0.12);
        ctx.drawImage(img, x - size / 2, y - size / 2, size, size);
        pushHistory();
      };
      setIsDrawing(false);
      return;
    }

    if (tool === "text") {
      setIsAddingText(true);
      return;
    }

    if (["arrow", "circle", "box"].includes(tool)) {
      snapshotBeforeShape.current = ctx.getImageData(0, 0, canvas.width, canvas.height);
      return;
    }

    ctx.beginPath();
    ctx.moveTo(x, y);

    if (tool === "eraser") {
      ctx.strokeStyle = "#F5EBD7";
      ctx.lineWidth = strokeWidth * 3.5;
      ctx.globalAlpha = 1.0;
    } else if (tool === "highlighter") {
      ctx.strokeStyle = color === "#1A1A1A" ? "#FFE600" : color;
      ctx.lineWidth = strokeWidth * 2.5;
      ctx.globalAlpha = 0.45;
    } else {
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;
      ctx.globalAlpha = 1.0;
    }

    ctx.lineCap = "round";
    ctx.lineJoin = "round";
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCanvasCoords(e);

    if (["arrow", "circle", "box"].includes(tool) && snapshotBeforeShape.current && startPos.current) {
      // Phục hồi lại canvas trước khi vẽ tạm preview hình học
      ctx.putImageData(snapshotBeforeShape.current, 0, 0);
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.globalAlpha = 1.0;

      const sx = startPos.current.x;
      const sy = startPos.current.y;

      if (tool === "arrow") {
        // Vẽ mũi tên chỉ dẫn
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(x, y);
        ctx.stroke();

        // Vẽ đầu mũi tên
        const angle = Math.atan2(y - sy, x - sx);
        const headLen = Math.max(16, strokeWidth * 3.2);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(
          x - headLen * Math.cos(angle - Math.PI / 6),
          y - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.moveTo(x, y);
        ctx.lineTo(
          x - headLen * Math.cos(angle + Math.PI / 6),
          y - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.stroke();
      } else if (tool === "circle") {
        const radiusX = Math.abs(x - sx) / 2;
        const radiusY = Math.abs(y - sy) / 2;
        const centerX = sx + (x - sx) / 2;
        const centerY = sy + (y - sy) / 2;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
        ctx.stroke();
      } else if (tool === "box") {
        ctx.strokeRect(sx, sy, x - sx, y - sy);
      }
      return;
    }

    if (["pen", "highlighter", "eraser"].includes(tool)) {
      ctx.lineTo(x, y);
      ctx.stroke();
    }
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    startPos.current = null;
    snapshotBeforeShape.current = null;
    pushHistory();
  };

  const handleApplyText = () => {
    if (!textInput.trim() || !startPos.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.font = `bold ${Math.max(28, strokeWidth * 7)}px Inter, system-ui, sans-serif`;
    ctx.fillStyle = color;
    ctx.fillText(textInput, startPos.current.x, startPos.current.y);

    setTextInput("");
    setIsAddingText(false);
    pushHistory();
  };

  const handleSaveAndSync = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      setIsSaving(true);
      setErrorMsg(null);
      const dataUrl = canvas.toDataURL("image/png");

      const savedImg = await saveCanvasEdit({
        projectId,
        sceneId: scene.id,
        sceneIndex: scene.scene_index,
        imageDataBase64: dataUrl,
      });

      onSaveSuccess(savedImg);
      onClose();
    } catch (err: any) {
      console.error("[SceneCanvasEditor] Lỗi lưu canvas:", err);
      setErrorMsg(err?.message || "Không thể lưu hình ảnh đã chỉnh sửa");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[95vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Top Header */}
        <div className="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-indigo-600/30 text-indigo-400 border border-indigo-500/40 flex items-center justify-center font-bold text-sm">
              🎨
            </span>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Canvas Studio: Chỉnh sửa nét vẽ phân cảnh {scene.scene_index}
              </h3>
              <p className="text-xs text-slate-400">
                Thêm mũi tên chỉ dẫn, khoanh vùng điểm nhấn, đóng dấu doodle hoặc tẩy xóa nét thừa
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleUndo}
              disabled={historyIndex <= 0}
              className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 disabled:opacity-40 transition"
              title="Hoàn tác (Undo)"
            >
              ↩️
            </button>
            <button
              onClick={handleRedo}
              disabled={historyIndex >= history.length - 1}
              className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 disabled:opacity-40 transition"
              title="Làm lại (Redo)"
            >
              ↪️
            </button>
            <button
              onClick={handleReset}
              className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-amber-400 hover:bg-slate-700 transition text-xs font-medium"
              title="Khôi phục ảnh gốc"
            >
              🔄 Gốc
            </button>
            <div className="h-5 w-px bg-slate-700 mx-1" />
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
              title="Đóng"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Toolbar Bar */}
        <div className="px-6 py-2.5 bg-slate-950/40 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Tool Modes */}
          <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setTool("pen")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "pen" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>✏️</span>
              <span>Bút vẽ</span>
            </button>

            <button
              onClick={() => setTool("highlighter")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "highlighter" ? "bg-amber-500 text-slate-950 font-bold shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>🖍️</span>
              <span>Dạ quang</span>
            </button>

            <button
              onClick={() => setTool("eraser")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "eraser" ? "bg-rose-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>🧹</span>
              <span>Giẻ tẩy</span>
            </button>

            <button
              onClick={() => setTool("arrow")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "arrow" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>➡️</span>
              <span>Mũi tên</span>
            </button>

            <button
              onClick={() => setTool("circle")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "circle" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>⭕</span>
              <span>Khoanh tròn</span>
            </button>

            <button
              onClick={() => setTool("box")}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "box" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>🔲</span>
              <span>Khung</span>
            </button>

            <button
              onClick={() => {
                setTool("doodle");
                setIsDoodleDrawerOpen(true);
              }}
              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition ${
                tool === "doodle" ? "bg-amber-500 text-slate-950 font-bold shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <span>⭐</span>
              <span>Doodle Vault</span>
            </button>
          </div>

          {/* Color Palette */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 mr-1 text-[11px]">Màu:</span>
            {PALETTE.map((p) => (
              <button
                key={p.hex}
                onClick={() => setColor(p.hex)}
                style={{ backgroundColor: p.hex }}
                className={`w-6 h-6 rounded-full border transition transform ${
                  color === p.hex ? "scale-115 ring-2 ring-indigo-400 border-white" : "border-slate-700 hover:scale-105"
                }`}
                title={p.name}
              />
            ))}
          </div>

          {/* Stroke Width */}
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-[11px]">Nét:</span>
            <input
              type="range"
              min="2"
              max="24"
              value={strokeWidth}
              onChange={(e) => setStrokeWidth(Number(e.target.value))}
              className="w-24 accent-indigo-500 cursor-pointer"
            />
            <span className="text-slate-300 font-mono text-[11px] w-6">{strokeWidth}px</span>
          </div>
        </div>

        {/* Main Canvas Viewport */}
        <div className="relative flex-1 bg-slate-950 overflow-auto flex items-center justify-center p-4">
          <canvas
            ref={canvasRef}
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            className="max-h-[62vh] max-w-full object-contain rounded-xl shadow-2xl border border-slate-800 cursor-crosshair bg-[#F5EBD7]"
          />

          {/* Doodle Vault Drawer */}
          {isDoodleDrawerOpen && (
            <div className="absolute right-4 top-4 bottom-4 w-72 bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl backdrop-blur-md p-4 flex flex-col z-30">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="font-bold text-white text-xs flex items-center gap-1.5">
                  <span>⭐</span> Kho biểu tượng Doodle
                </span>
                <button
                  onClick={() => setIsDoodleDrawerOpen(false)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  ✕
                </button>
              </div>

              <div className="flex-1 overflow-y-auto py-2 grid grid-cols-2 gap-2 custom-scrollbar">
                {doodles.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      setSelectedDoodle(d);
                      setTool("doodle");
                    }}
                    className={`p-2 rounded-xl border flex flex-col items-center gap-1.5 transition ${
                      selectedDoodle?.id === d.id
                        ? "bg-indigo-600/20 border-indigo-500 text-indigo-300"
                        : "bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white"
                    }`}
                  >
                    <div
                      className="w-12 h-12 flex items-center justify-center"
                      dangerouslySetInnerHTML={{ __html: d.svg_content }}
                    />
                    <span className="text-[10px] text-center truncate w-full font-medium">{d.name}</span>
                  </button>
                ))}
              </div>

              <p className="text-[10px] text-slate-400 pt-2 border-t border-slate-800 text-center">
                Click chọn icon, sau đó click chuột lên bảng vẽ để đóng dấu.
              </p>
            </div>
          )}
        </div>

        {/* Text Input Popup */}
        {isAddingText && (
          <div className="px-6 py-2 bg-indigo-950/60 border-t border-indigo-800/80 flex items-center gap-3">
            <span className="text-xs text-indigo-300 font-medium">Nhập chữ viết lên canvas:</span>
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Gõ tiêu đề hoặc ghi chú..."
              className="flex-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-indigo-500/50 text-white text-xs outline-none"
            />
            <button
              onClick={handleApplyText}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500"
            >
              Áp dụng
            </button>
            <button
              onClick={() => setIsAddingText(false)}
              className="px-2 py-1.5 text-xs text-slate-400 hover:text-white"
            >
              Hủy
            </button>
          </div>
        )}

        {/* Error Bar */}
        {errorMsg && (
          <div className="px-6 py-2 bg-rose-950/80 border-t border-rose-800/80 text-xs text-rose-300 flex items-center justify-between">
            <span>⚠️ {errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Footer Actions */}
        <div className="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Nền giấy kem chuẩn <strong className="text-amber-300 font-mono">#F5EBD7</strong> • Tỷ lệ 1080p
          </span>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition"
            >
              Hủy bỏ
            </button>

            <button
              id="btn-save-canvas-studio"
              onClick={handleSaveAndSync}
              disabled={isSaving}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 transition shadow-lg shadow-emerald-600/25 flex items-center gap-2 active:scale-95 disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Đang lưu phân cảnh...</span>
                </>
              ) : (
                <>
                  <span>💾</span>
                  <span>Lưu & Đồng bộ phân cảnh</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
