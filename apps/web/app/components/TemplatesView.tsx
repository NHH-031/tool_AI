"use client";

import React from "react";
import { ActiveTab, TemplateItem } from "../types";

interface TemplatesViewProps {
  templates: TemplateItem[];
  onSelectTemplate: (tplId: string) => void;
  setActiveTab: (tab: ActiveTab) => void;
}

export const TemplatesView: React.FC<TemplatesViewProps> = ({
  templates,
  onSelectTemplate,
  setActiveTab,
}) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Video Templates Library</h1>
        <p className="text-xs text-slate-400 mt-1">
          Các mẫu định dạng thiết lập mỹ thuật, nền bảng vẽ và quy chuẩn kỹ thuật cho video whiteboard
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((tpl) => (
          <div
            key={tpl.id}
            id={`template-card-${tpl.id}`}
            className="group bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 hover:border-indigo-500/50 hover:shadow-xl transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl">🎨</span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-slate-800 text-slate-300">
                  {tpl.aspect_ratio} · {tpl.default_fps} FPS
                </span>
              </div>

              <h2 className="text-base font-bold text-white group-hover:text-indigo-300 transition">
                {tpl.name}
              </h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                {tpl.description}
              </p>

              <div className="mt-4 pt-4 border-t border-slate-800/60 flex items-center gap-2">
                <span className="text-xs text-slate-500">Màu nền giấy:</span>
                <div
                  className="w-4 h-4 rounded-full border border-slate-700 shadow-sm"
                  style={{ backgroundColor: tpl.bg_color_hex }}
                ></div>
                <span className="text-xs font-mono text-slate-400">{tpl.bg_color_hex}</span>
              </div>

              <div className="flex flex-wrap gap-1.5 mt-3">
                {tpl.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 font-mono"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/60">
              <button
                id={`btn-apply-template-${tpl.id}`}
                onClick={() => {
                  onSelectTemplate(tpl.id);
                  setActiveTab("create");
                }}
                className="w-full py-2.5 rounded-xl text-xs font-bold bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 transition flex items-center justify-center gap-2 active:scale-95"
              >
                <span>Sử dụng mẫu này</span>
                <span>→</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
