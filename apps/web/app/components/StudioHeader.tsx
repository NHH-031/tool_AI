"use client";

import React, { useState, useRef, useEffect } from "react";
import { ProjectSummary } from "../types";

interface StudioHeaderProps {
  currentProjectTitle: string;
  projects: ProjectSummary[];
  onSelectProject: (projectId: string) => void;
  onNewProject: () => void;
  backendHealthy: boolean;
  archiveCount?: number;
  onOpenArchiveVault?: () => void;
}

export const StudioHeader: React.FC<StudioHeaderProps> = ({
  currentProjectTitle,
  projects,
  onSelectProject,
  onNewProject,
  backendHealthy,
  archiveCount,
  onOpenArchiveVault,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-xl border-b border-slate-800/80 shadow-md shadow-black/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-3 select-none">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-amber-500 p-[1px] shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center font-bold text-lg text-white">
              ✍️
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-white text-base tracking-tight">
                Whiteboard Studio
              </span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Local AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Tạo video vẽ tay AI hoàn chỉnh</p>
          </div>
        </div>

        {/* Project Selector Dropdown in Middle */}
        <div className="relative flex-1 max-w-md mx-auto" ref={dropdownRef}>
          <button
            id="btn-project-dropdown"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full flex items-center justify-between gap-2 px-4 py-2 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-850 text-slate-200 text-xs sm:text-sm font-medium transition shadow-inner"
          >
            <div className="flex items-center gap-2 truncate">
              <span className="text-slate-400 text-xs font-normal">Dự án:</span>
              <span className="font-semibold text-white truncate max-w-[240px] sm:max-w-[300px]">
                {currentProjectTitle || "Chưa đặt tên"}
              </span>
            </div>
            <svg
              className={`w-4 h-4 text-slate-400 transition-transform flex-shrink-0 ${
                dropdownOpen ? "rotate-180 text-indigo-400" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 border border-slate-800 rounded-xl shadow-2xl backdrop-blur-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="p-2 border-b border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold uppercase tracking-wider text-[10px] text-slate-400">
                  Dự án đã lưu ({projects.length})
                </span>
                <span className="text-[10px] text-slate-500">Click để chuyển đổi</span>
              </div>
              <div className="max-h-60 overflow-y-auto divide-y divide-slate-800/40 custom-scrollbar">
                {projects.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">
                    Chưa có dự án nào được lưu
                  </div>
                ) : (
                  projects.map((proj) => (
                    <button
                      key={proj.id}
                      onClick={() => {
                        onSelectProject(proj.id);
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-3.5 py-2.5 hover:bg-slate-800/60 transition flex items-center justify-between group"
                    >
                      <div className="truncate pr-2">
                        <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-300 truncate">
                          {proj.title}
                        </div>
                        <div className="text-[11px] text-slate-500 truncate">
                          {proj.scene_count} cảnh · {proj.duration_sec}s · {new Date(proj.updated_at || proj.created_at).toLocaleDateString("vi-VN")}
                        </div>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50 flex-shrink-0">
                        {proj.status}
                      </span>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Actions: Health + "+ Kịch bản mới" */}
        <div className="flex items-center gap-3">
          <div
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] border ${
              backendHealthy
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
            title={backendHealthy ? "Backend API & Local models online" : "Backend offline - sử dụng chế độ demo"}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendHealthy ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span className="font-mono text-[11px]">
              {backendHealthy ? "AI Online" : "Demo Mode"}
            </span>
          </div>

          {onOpenArchiveVault && (
            <button
              id="btn-open-archive-vault"
              onClick={onOpenArchiveVault}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/80 transition shadow active:scale-95 group"
              title="Xem Kho Lưu Trữ Video đã xuất trên ổ D"
            >
              <span className="text-base leading-none">📂</span>
              <span>Kho Video</span>
              {archiveCount !== undefined && archiveCount > 0 && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {archiveCount}
                </span>
              )}
            </button>
          )}

          <button
            id="btn-new-script"
            onClick={onNewProject}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-600/30 transition active:scale-95"
          >
            <span className="text-base leading-none font-bold">+</span>
            <span>Kịch bản mới</span>
          </button>
        </div>
      </div>
    </header>
  );
};
