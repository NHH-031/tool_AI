"use client";

import React, { useState } from "react";
import { AssetCatalogItem, MasterpieceItem } from "../types";

interface AssetsViewProps {
  assets: AssetCatalogItem[];
  masterpieces?: MasterpieceItem[];
  onSelectMasterpiece?: (item: MasterpieceItem) => void;
}

export const AssetsView: React.FC<AssetsViewProps> = ({
  assets,
  masterpieces = [],
  onSelectMasterpiece,
}) => {
  const [viewMode, setViewMode] = useState<"masterpieces" | "svg">("masterpieces");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [activePoses, setActivePoses] = useState<Record<string, string>>({
    asset_monkey: "climbing",
    asset_tree: "standard",
    asset_banana: "ripe",
  });

  const categories = [
    { id: "all", label: "Tất cả (All)" },
    { id: "character", label: "Nhân vật (Character)" },
    { id: "nature", label: "Tự nhiên (Nature)" },
    { id: "object", label: "Vật thể (Object)" },
  ];

  const filteredAssets =
    selectedCategory === "all"
      ? assets
      : assets.filter((a) => a.category.toLowerCase() === selectedCategory.toLowerCase());

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header & Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
            <span>🎨</span> Tuyển Tập Mỹ Thuật Đồ Họa 1080p (Phương Án 2)
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Kho Tranh Vẽ & Tài Nguyên Đồ Họa
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Bộ sưu tập kiệt tác tranh vẽ tay chuẩn mực 1080p và thư viện vector định hình nét vẽ bàn tay
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800">
          <button
            type="button"
            onClick={() => setViewMode("masterpieces")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
              viewMode === "masterpieces"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <span>✨</span> Kho Kiệt Tác 1080p
          </button>
          <button
            type="button"
            onClick={() => setViewMode("svg")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
              viewMode === "svg"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <span>📐</span> Vector SVG Assets
          </button>
        </div>
      </div>

      {/* VIEW MODE 1: MASTERPIECES (PHƯƠNG ÁN 2) */}
      {viewMode === "masterpieces" && (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900/50 border border-indigo-500/20 rounded-3xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="text-sm font-bold text-white flex items-center gap-2">
                <span>🌟</span> Tiêu Chuẩn Nét Vẽ Đỉnh Cao (1920x1080 Notion Doodle)
              </div>
              <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
                Các tác phẩm được thiết kế độc quyền với độ phân giải Full HD 1080p, nền giấy ấm sạch tuyệt đối (#F5EBD7) và nét mực đen sắc nét (#1A1A1A). Tự động phân tích theo kịch bản của bạn khi nhập trên Web.
              </p>
            </div>
            <div className="text-right shrink-0">
              <span className="px-3 py-1.5 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold font-mono">
                {masterpieces.length} Kiệt Tác Sẵn Sàng
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {masterpieces.map((item) => (
              <div
                key={item.id}
                id={`masterpiece-card-${item.id}`}
                className="bg-slate-900/60 border border-slate-800/80 rounded-3xl overflow-hidden hover:border-indigo-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/10 flex flex-col justify-between group"
              >
                <div>
                  {/* Artwork Preview Frame */}
                  <div className="relative aspect-[16/9] bg-amber-50/5 overflow-hidden border-b border-slate-800/80">
                    <img
                      src={`http://127.0.0.1:8000${item.image_url}`}
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        // Fallback placeholder if image not loaded
                        (e.target as HTMLElement).style.display = "none";
                      }}
                    />
                    <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-slate-950/80 text-indigo-300 backdrop-blur-md border border-slate-800">
                      {item.theme}
                    </div>
                    <div className="absolute top-3 right-3 px-2 py-0.5 rounded-md text-[10px] font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-500/30">
                      1080p
                    </div>
                  </div>

                  {/* Info Box */}
                  <div className="p-5 space-y-2.5">
                    <h3 className="text-base font-bold text-white group-hover:text-indigo-400 transition">
                      {item.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {item.description}
                    </p>

                    {/* Keywords */}
                    <div className="flex flex-wrap gap-1 pt-1">
                      {item.keywords.slice(0, 4).map((kw, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950/80 text-slate-400 font-mono border border-slate-800/60"
                        >
                          #{kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Card Action */}
                <div className="p-5 pt-0">
                  <button
                    type="button"
                    onClick={() => onSelectMasterpiece && onSelectMasterpiece(item)}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600/10 hover:bg-indigo-600 text-indigo-400 hover:text-white border border-indigo-500/20 hover:border-transparent text-xs font-bold transition flex items-center justify-center gap-2 group-hover:shadow-md group-hover:shadow-indigo-600/20"
                  >
                    <span>🎬</span> Tạo Video Với Chủ Đề Này
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW MODE 2: SVG ASSETS */}
      {viewMode === "svg" && (
        <div className="space-y-6">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-2xl border border-slate-800 w-fit">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  selectedCategory === cat.id
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAssets.map((asset) => {
              const currentPoseKey = activePoses[asset.id] || Object.keys(asset.poses)[0];
              const currentPose = asset.poses[currentPoseKey];

              return (
                <div
                  key={asset.id}
                  id={`asset-card-${asset.id}`}
                  className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 hover:border-indigo-500/50 transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {asset.category}
                      </span>
                      <span className="text-xs font-mono text-slate-500">
                        {asset.format.toUpperCase()}
                      </span>
                    </div>

                    {/* SVG Visual Display Box */}
                    <div className="relative aspect-square bg-slate-950/80 rounded-2xl border border-slate-800/80 p-6 flex items-center justify-center overflow-hidden group">
                      <div className="text-center space-y-3">
                        <div className="text-5xl group-hover:scale-110 transition duration-300">
                          {asset.name === "monkey"
                            ? currentPoseKey === "climbing"
                              ? "🧗🐒"
                              : "🐒"
                            : asset.name === "tree"
                            ? "🌴"
                            : "🍌"}
                        </div>
                        <div className="text-xs font-mono text-indigo-300 font-bold">
                          {asset.name} ({currentPoseKey})
                        </div>
                        <div className="text-[10px] text-slate-500">
                          ViewBox: 0 0 500 500 · Stroke Width: {asset.metadata?.stroke_width || 6}px
                        </div>
                      </div>
                    </div>

                    <div className="mt-4">
                      <h2 className="text-base font-bold text-white capitalize">{asset.name}</h2>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {currentPose?.description || `Định dạng vector vẽ nét ${asset.name}.`}
                      </p>
                    </div>

                    {/* Pose Switcher */}
                    {Object.keys(asset.poses).length > 1 && (
                      <div className="mt-4 pt-3 border-t border-slate-800/60">
                        <span className="text-[11px] text-slate-400 font-medium block mb-1.5">
                          Tư thế khả dụng (Poses):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.keys(asset.poses).map((poseKey) => (
                            <button
                              key={poseKey}
                              onClick={() =>
                                setActivePoses((prev) => ({ ...prev, [asset.id]: poseKey }))
                              }
                              className={`text-[10px] font-semibold px-2 py-1 rounded-lg border transition ${
                                currentPoseKey === poseKey
                                  ? "bg-indigo-600 border-indigo-500 text-white"
                                  : "bg-slate-800 border-slate-700 text-slate-400 hover:text-white"
                              }`}
                            >
                              {poseKey}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Tags */}
                  <div className="mt-5 pt-3 border-t border-slate-800/60 flex flex-wrap gap-1">
                    {asset.tags.map((t) => (
                      <span
                        key={t}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-400 font-mono"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
