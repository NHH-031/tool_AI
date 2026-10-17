"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Next.js App Error]", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-slate-900/80 border border-red-500/30 rounded-2xl p-8 text-center space-y-6 shadow-2xl backdrop-blur-xl">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
          <svg
            className="w-8 h-8"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Đã xảy ra lỗi hệ thống
          </h2>
          <p className="text-sm text-slate-400">
            Ứng dụng gặp sự cố ngoài dự tính. Đừng lo lắng, dữ liệu của bạn có thể vẫn còn nguyên.
          </p>
        </div>

        {error?.message && (
          <div className="p-3 bg-slate-950/80 rounded-xl text-left border border-slate-800 text-xs font-mono text-red-300 max-h-32 overflow-y-auto">
            {error.message}
          </div>
        )}

        <div className="flex items-center justify-center gap-4 pt-2">
          <button
            onClick={() => reset()}
            className="px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
          >
            Thử tải lại (Retry)
          </button>
          <button
            onClick={() => {
              window.location.href = "/";
            }}
            className="px-5 py-2.5 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all cursor-pointer"
          >
            Trang chủ
          </button>
        </div>
      </div>
    </div>
  );
}
