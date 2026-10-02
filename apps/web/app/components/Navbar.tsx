"use client";

import React from "react";
import { ActiveTab } from "../types";

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  backendHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  backendHealthy,
}) => {
  const navItems: { id: ActiveTab; label: string; icon: string }[] = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "create", label: "Create Video", icon: "✨" },
    { id: "review", label: "Review & Editor", icon: "🎬" },
    { id: "templates", label: "Templates", icon: "🎨" },
    { id: "assets", label: "Assets", icon: "📦" },
    { id: "voices", label: "Voices", icon: "🎙️" },
    { id: "music", label: "Music", icon: "🎵" },
    { id: "jobs", label: "Production Jobs", icon: "⚙️" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div
          onClick={() => setActiveTab("dashboard")}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-amber-500 p-[1px] shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center font-bold text-lg text-white">
              ✍️
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-white text-base tracking-tight group-hover:text-indigo-300 transition">
                AI Whiteboard Studio
              </span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Phase 10
              </span>
            </div>
            <p className="text-[11px] text-slate-400">End-to-End Hand-Drawn Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800/60">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                onClick={() => setActiveTab(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Actions & Health Badge */}
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs border ${
              backendHealthy
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
            title={backendHealthy ? "FastAPI Backend is online" : "Running in standalone mode with mock fallback"}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendHealthy ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            ></span>
            <span className="font-mono text-[11px]">
              {backendHealthy ? "API Online" : "Local Engine"}
            </span>
          </div>

          <button
            id="btn-quick-create"
            onClick={() => setActiveTab("create")}
            className="hidden sm:inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white shadow-lg shadow-indigo-500/25 transition active:scale-95"
          >
            <span>+</span>
            <span>New Video</span>
          </button>
        </div>
      </div>
    </header>
  );
};
