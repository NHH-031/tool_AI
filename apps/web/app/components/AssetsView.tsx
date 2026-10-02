"use client";

import React, { useState } from "react";
import { AssetCatalogItem } from "../types";

interface AssetsViewProps {
  assets: AssetCatalogItem[];
}

export const AssetsView: React.FC<AssetsViewProps> = ({ assets }) => {
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Vector SVG Asset Library
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Kho tài nguyên vector SVG phân cấp, định hình thứ tự nét vẽ và lộ trình đầu bút
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-2xl border border-slate-800">
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
  );
};
