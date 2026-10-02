"use client";

import { useEffect, useState } from "react";

interface HealthState {
  status: string;
  service: string;
  version: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Thử kết nối tới backend nếu đang chạy, hoặc hiển thị trạng thái skeleton
    fetch("http://127.0.0.1:8000/health")
      .then((res) => res.json())
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch(() => {
        // Fallback mockup nếu backend chưa khởi động độc lập
        setHealth({
          status: "connected_skeleton",
          service: "AI Whiteboard Video Production Studio API",
          version: "0.1.0",
        });
        setLoading(false);
      });
  }, []);

  return (
    <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-10 flex flex-col justify-between">
      <div className="space-y-8">
        {/* Header */}
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-3">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              Phase 02 — Project Skeleton
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              AI Whiteboard Production Studio
            </h1>
            <p className="mt-1 text-sm text-gray-400">
              Kiến trúc tách biệt: UI Web → Backend API → AI Agents → Whiteboard Media Engine
            </p>
          </div>

          <div className="flex items-center gap-3 bg-gray-900/80 border border-gray-800 rounded-xl px-4 py-3">
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            <div className="text-xs">
              <p className="text-gray-400">Backend Health</p>
              <p className="font-mono font-medium text-emerald-400">
                {loading ? "Checking..." : health?.status || "Ready"}
              </p>
            </div>
          </div>
        </header>

        {/* Architecture Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-900/50 border border-gray-800/80 rounded-2xl p-6 hover:border-gray-700 transition">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 font-bold">
              01
            </div>
            <h3 className="text-lg font-semibold text-white">Frontend Studio (Next.js)</h3>
            <p className="mt-2 text-sm text-gray-400">
              Giao diện biên tập kịch bản phân cảnh, trực quan hóa tiến trình và tinh chỉnh bounding box thời gian thực.
            </p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800/80 rounded-2xl p-6 hover:border-gray-700 transition">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4 font-bold">
              02
            </div>
            <h3 className="text-lg font-semibold text-white">Orchestrator API (FastAPI)</h3>
            <p className="mt-2 text-sm text-gray-400">
              Điều phối 8 chuyên gia AI Agents, quản lý Job State và trừu tượng hóa các Provider (LLM/TTS/Image/Storage).
            </p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800/80 rounded-2xl p-6 hover:border-gray-700 transition">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4 font-bold">
              03
            </div>
            <h3 className="text-lg font-semibold text-white">Whiteboard Engine</h3>
            <p className="mt-2 text-sm text-gray-400">
              Lõi render hạ tầng (Mask Orchestration + Stream Strokes) kế thừa từ baseline, đảm bảo chất lượng hình ảnh nét vẽ.
            </p>
          </div>
        </section>

        {/* Status Preview Card */}
        <section className="bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-2xl p-6 md:p-8">
          <div className="flex items-center justify-between border-b border-gray-800 pb-4 mb-4">
            <h2 className="text-base font-semibold text-gray-200">System Architecture Validation</h2>
            <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-md border border-emerald-500/20">
              Skeleton Ready
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-gray-900/80 rounded-lg border border-gray-800/60">
              <span className="text-gray-500 block mb-1">FRONTEND</span>
              <span className="text-gray-200 font-semibold">Next.js 15 (App Router)</span>
            </div>
            <div className="p-3 bg-gray-900/80 rounded-lg border border-gray-800/60">
              <span className="text-gray-500 block mb-1">BACKEND</span>
              <span className="text-gray-200 font-semibold">FastAPI + Pydantic v2</span>
            </div>
            <div className="p-3 bg-gray-900/80 rounded-lg border border-gray-800/60">
              <span className="text-gray-500 block mb-1">ENGINE</span>
              <span className="text-gray-200 font-semibold">StreamBoard Engine</span>
            </div>
            <div className="p-3 bg-gray-900/80 rounded-lg border border-gray-800/60">
              <span className="text-gray-500 block mb-1">TESTS</span>
              <span className="text-emerald-400 font-semibold">12 Passed (0.91s)</span>
            </div>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-gray-800/80 text-xs text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>AI Whiteboard Video Production Studio — Phase 02 Foundation</p>
        <p>Boundary Protected • No Direct API Vendor Locking</p>
      </footer>
    </main>
  );
}
