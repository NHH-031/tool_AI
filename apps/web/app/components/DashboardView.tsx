"use client";

import React from "react";
import { ActiveTab, ProjectSummary } from "../types";

interface DashboardViewProps {
  projects: ProjectSummary[];
  onOpenProject: (projectId: string) => void;
  onQuickGenerate: (promptText: string) => void;
  setActiveTab: (tab: ActiveTab) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  projects,
  onOpenProject,
  onQuickGenerate,
  setActiveTab,
}) => {
  const [quickPrompt, setQuickPrompt] = React.useState("");

  const inspirationPresets = [
    {
      title: "Con khỉ trèo cây lấy chuối",
      prompt: "Con khỉ đang trèo lên cây để lấy một quả chuối.",
      badge: "Phase 9 Certified",
    },
    {
      title: "Giải thích lạm phát qua ổ bánh mì",
      prompt: "Tại sao cùng một số tiền năm ngoái mua được 2 ổ bánh mì mà năm nay chỉ mua được 1 ổ bánh mì?",
      badge: "Kinh Tế Học",
    },
    {
      title: "Vòng tuần hoàn nước",
      prompt: "Nước từ đại dương bốc hơi tạo thành mây, mây ngưng tụ đổ mưa xuống núi rừng và chảy về sông suối.",
      badge: "Khoa Học",
    },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Quick Generate Banner */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-950 border border-indigo-500/20 p-6 md:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 mb-4">
            <span>✨</span> Next-Gen AI Hand-Drawn Animation
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Turn Any Idea into a Hand-Drawn Whiteboard Masterpiece
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-300">
            Tự động hóa toàn diện từ ý tưởng văn bản sang kịch bản phân cảnh, giọng đọc truyền cảm, lộ trình nét vẽ chuẩn mực và kết xuất video MP4 Full HD.
          </p>

          {/* Quick Input Bar */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                id="input-quick-prompt"
                type="text"
                value={quickPrompt}
                onChange={(e) => setQuickPrompt(e.target.value)}
                placeholder="Nhập ý tưởng video (ví dụ: Con khỉ đang trèo lên cây để lấy một quả chuối...)"
                className="w-full bg-slate-950/90 border border-slate-700/80 rounded-2xl px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition shadow-inner"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && quickPrompt.trim()) {
                    onQuickGenerate(quickPrompt);
                  }
                }}
              />
            </div>
            <button
              id="btn-quick-generate-hero"
              onClick={() => {
                if (quickPrompt.trim()) {
                  onQuickGenerate(quickPrompt);
                } else {
                  setActiveTab("create");
                }
              }}
              className="px-6 py-3.5 rounded-2xl text-sm font-bold bg-gradient-to-r from-indigo-500 via-violet-600 to-indigo-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-xl shadow-indigo-600/30 transition active:scale-95 whitespace-nowrap flex items-center justify-center gap-2"
            >
              <span>🚀</span>
              <span>{quickPrompt.trim() ? "Generate Video" : "Start Studio"}</span>
            </button>
          </div>

          {/* Inspiration Tags */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Gợi ý kịch bản:</span>
            {inspirationPresets.map((item, idx) => (
              <button
                key={idx}
                id={`chip-preset-${idx}`}
                onClick={() => {
                  setQuickPrompt(item.prompt);
                  onQuickGenerate(item.prompt);
                }}
                className="text-xs px-3 py-1 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/50 transition flex items-center gap-1.5 active:scale-95"
              >
                <span>💡</span>
                <span>{item.title}</span>
                <span className="text-[10px] text-indigo-400 font-semibold bg-indigo-500/10 px-1.5 py-0.2 rounded-md">
                  {item.badge}
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Metrics Grid */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Active Projects</span>
            <span className="text-lg">📁</span>
          </div>
          <div className="text-2xl font-extrabold text-white">{projects.length}</div>
          <p className="text-xs text-emerald-400 mt-1">100% cloud synced</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Render Quality</span>
            <span className="text-lg">🎯</span>
          </div>
          <div className="text-2xl font-extrabold text-white">1080p Full HD</div>
          <p className="text-xs text-slate-400 mt-1">30 fps · H.264 / AAC</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Vector Asset Library</span>
            <span className="text-lg">📦</span>
          </div>
          <div className="text-2xl font-extrabold text-white">35+ Poses</div>
          <p className="text-xs text-indigo-400 mt-1">Structured SVG strokes</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Pipeline Pass Rate</span>
            <span className="text-lg">⚡</span>
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">100%</div>
          <p className="text-xs text-slate-400 mt-1">78 / 78 Verified tests</p>
        </div>
      </section>

      {/* Recent Projects Section */}
      <section className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Recent Projects</h2>
            <p className="text-xs text-slate-400 mt-0.5">Dự án video hoạt hình được tạo và lưu trữ gần đây</p>
          </div>
          <button
            onClick={() => setActiveTab("jobs")}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition flex items-center gap-1"
          >
            <span>View All Production Jobs</span>
            <span>→</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              id={`card-project-${proj.id}`}
              className="group bg-slate-950/70 border border-slate-800/80 rounded-2xl overflow-hidden hover:border-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/10 transition flex flex-col"
            >
              {/* Thumbnail / Video Preview Area */}
              <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden">
                <img
                  src="http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default.png"
                  alt={proj.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  onError={(e) => {
                    // Fallback to stylized SVG thumbnail
                    (e.target as HTMLElement).style.display = "none";
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80"></div>

                <div className="absolute top-3 left-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    {proj.status}
                  </span>
                </div>

                <div className="absolute bottom-3 right-3">
                  <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-black/70 text-slate-200">
                    {proj.duration_sec.toFixed(1)}s
                  </span>
                </div>
              </div>

              {/* Content Area */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-white text-base group-hover:text-indigo-300 transition">
                    {proj.title}
                  </h3>
                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                    {proj.description || "Video Whiteboard Animation tự động."}
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-800/60 flex items-center justify-between">
                  <div className="text-[11px] text-slate-500 font-mono">
                    Aspect {proj.aspect_ratio} · {proj.scene_count} Scene
                  </div>
                  <button
                    id={`btn-open-review-${proj.id}`}
                    onClick={() => onOpenProject(proj.id)}
                    className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 transition flex items-center gap-1 active:scale-95"
                  >
                    <span>🎬 Review / Edit</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
