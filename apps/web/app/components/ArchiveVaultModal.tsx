"use client";

import React, { useState, useEffect } from "react";
import { ArchivedVideo, ArchiveStats } from "../types";
import {
  fetchArchivedVideos,
  fetchArchiveStats,
  scanArchiveVideos,
  openArchiveFolder,
  deleteArchivedVideo,
} from "../api-client";

interface ArchiveVaultModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectVideoForPreview?: (videoUrl: string) => void;
}

export const ArchiveVaultModal: React.FC<ArchiveVaultModalProps> = ({
  isOpen,
  onClose,
  onSelectVideoForPreview,
}) => {
  const [videos, setVideos] = useState<ArchivedVideo[]>([]);
  const [stats, setStats] = useState<ArchiveStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activePreviewVideo, setActivePreviewVideo] = useState<ArchivedVideo | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [vList, sInfo] = await Promise.all([
        fetchArchivedVideos(),
        fetchArchiveStats(),
      ]);
      setVideos(vList);
      setStats(sInfo);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const vList = await scanArchiveVideos();
      const sInfo = await fetchArchiveStats();
      setVideos(vList);
      setStats(sInfo);
      showToast(`Đã quét xong: tìm thấy ${vList.length} video trên ổ D!`);
    } finally {
      setScanning(false);
    }
  };

  const handleOpenFolder = async (path?: string) => {
    const ok = await openArchiveFolder(path);
    if (ok) {
      showToast("Đã mở File Explorer tại thư mục video trên ổ D!");
    } else {
      showToast("Không thể mở File Explorer tự động.");
    }
  };

  const handleCopyPath = (path: string, id: string) => {
    navigator.clipboard.writeText(path);
    setCopiedId(id);
    showToast("Đã sao chép đường dẫn file ổ D!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDelete = async (vid: ArchivedVideo) => {
    if (!confirm(`Bạn có chắc muốn xóa video "${vid.title}" khỏi kho và ổ D?`)) {
      return;
    }
    const ok = await deleteArchivedVideo(vid.id);
    if (ok) {
      setVideos((prev) => prev.filter((v) => v.id !== vid.id));
      if (activePreviewVideo?.id === vid.id) {
        setActivePreviewVideo(null);
      }
      showToast("Đã xóa video và giải phóng dung lượng ổ D!");
      const sInfo = await fetchArchiveStats();
      setStats(sInfo);
    } else {
      showToast("Lỗi khi xóa video.");
    }
  };

  const handleDownload = (vid: ArchivedVideo) => {
    const a = document.createElement("a");
    a.href = vid.video_url;
    a.download = vid.file_name || `${vid.title}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast(`Đang tải file ${vid.file_name}...`);
  };

  if (!isOpen) return null;

  const filteredVideos = videos.filter((v) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      v.title.toLowerCase().includes(q) ||
      v.file_name.toLowerCase().includes(q) ||
      v.project_id.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-[60] px-4 py-2.5 rounded-xl bg-slate-900 border border-indigo-500/50 shadow-2xl text-xs sm:text-sm text-indigo-200 flex items-center gap-2 animate-in slide-in-from-top-4 duration-200">
          <span>✨</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Modal Container */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Top Header */}
        <div className="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl text-indigo-400">
              📂
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-white">
                  Kho Lưu Trữ Video Bền Vững (Ổ D)
                </h2>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  {stats?.drive_letter || "D:"} Storage
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Toàn bộ video đã xuất đều được lưu an toàn tại máy của bạn, không bị mất khi tải về.
              </p>
            </div>
          </div>

          {/* Quick Actions in Header */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleOpenFolder()}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition border border-slate-700 shadow"
              title="Mở thư mục lưu trữ trên máy tính của bạn (Windows Explorer)"
            >
              <span>📁</span>
              <span>Mở thư mục ổ D</span>
            </button>

            <button
              onClick={handleScan}
              disabled={scanning}
              className="px-3.5 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
              title="Quét lại toàn bộ các video có trong thư mục output"
            >
              <span className={scanning ? "animate-spin" : ""}>🔄</span>
              <span>{scanning ? "Đang quét..." : "Quét lại ổ D"}</span>
            </button>

            <button
              onClick={onClose}
              className="w-9 h-9 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-base transition ml-1"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Storage Path & Stats Bar */}
        <div className="px-6 py-2.5 bg-slate-950/40 border-b border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-3 flex-shrink-0">
          <div className="flex items-center gap-2 truncate">
            <span className="text-slate-500">Đường dẫn lưu trữ:</span>
            <code className="text-indigo-300 font-mono text-[11px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800 truncate">
              {stats?.storage_path || "D:\\Tool\\output\\export"}
            </code>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium">
            <span>
              Tổng số: <strong className="text-white">{stats?.total_videos || videos.length}</strong> video
            </span>
            <span>
              Đã dùng: <strong className="text-amber-400">{stats?.used_storage_formatted || "0 MB"}</strong>
            </span>
            <span>
              Ổ D còn trống: <strong className="text-emerald-400">{stats?.disk_free_formatted || "0 GB"}</strong>
            </span>
          </div>
        </div>

        {/* Filter / Search Bar */}
        <div className="p-4 bg-slate-900/60 border-b border-slate-800/60 flex items-center justify-between gap-4 flex-shrink-0">
          <div className="relative flex-1 max-w-md">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500 text-sm">
              🔍
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm theo tiêu đề video hoặc tên file..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500 transition"
            />
          </div>

          <div className="text-xs text-slate-400">
            Hiển thị <strong className="text-white">{filteredVideos.length}</strong> / {videos.length} video
          </div>
        </div>

        {/* Videos Grid Body */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-950/20">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 space-y-3">
              <svg className="animate-spin w-10 h-10 text-indigo-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-sm text-slate-300 font-medium">Đang kiểm tra kho lưu trữ ổ D...</p>
            </div>
          ) : filteredVideos.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 flex items-center justify-center text-3xl">
                🎬
              </div>
              <div>
                <p className="text-base font-semibold text-white">Chưa có video nào trong kho lưu trữ</p>
                <p className="text-xs text-slate-400 max-w-md mt-1">
                  Khi bạn render video ở Bước 4, video sẽ tự động được lưu kiên cố vào thư mục <span className="font-mono text-indigo-300">D:\Tool\output\export</span> và hiển thị ở đây.
                </p>
              </div>
              <button
                onClick={handleScan}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
              >
                🔄 Thử quét lại ổ đĩa
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredVideos.map((vid) => (
                <div
                  key={vid.id}
                  className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition flex flex-col shadow-lg group hover:shadow-indigo-500/5"
                >
                  {/* Thumbnail / Video Preview */}
                  <div className="relative aspect-video w-full bg-slate-950 flex items-center justify-center overflow-hidden border-b border-slate-800/80">
                    <video
                      src={vid.video_url}
                      className="w-full h-full object-cover transition duration-300 group-hover:scale-105"
                      preload="metadata"
                      muted
                      onMouseEnter={(e) => (e.target as HTMLVideoElement).play().catch(() => {})}
                      onMouseLeave={(e) => {
                        const v = e.target as HTMLVideoElement;
                        v.pause();
                        v.currentTime = 0;
                      }}
                    />

                    {/* Overlay Badges */}
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-md text-[10px] text-indigo-300 border border-indigo-500/20 font-mono">
                      {vid.resolution || "720p HD"}
                    </div>

                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-md text-[10px] text-emerald-400 border border-emerald-500/20 font-mono">
                      ~{vid.duration_sec.toFixed(1)}s
                    </div>

                    {/* Quick Play Button in Center */}
                    <button
                      onClick={() => setActivePreviewVideo(vid)}
                      className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center backdrop-blur-xs"
                      title="Xem video toàn màn hình"
                    >
                      <span className="w-12 h-12 rounded-full bg-indigo-600/90 text-white flex items-center justify-center text-xl shadow-xl hover:scale-110 transition active:scale-95">
                        ▶
                      </span>
                    </button>
                  </div>

                  {/* Card Body */}
                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                    <div>
                      <h3 className="text-sm font-bold text-white line-clamp-1 group-hover:text-indigo-300 transition">
                        {vid.title}
                      </h3>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-1">
                        <span>{vid.file_size_formatted}</span>
                        <span>·</span>
                        <span>{new Date(vid.created_at).toLocaleString("vi-VN")}</span>
                      </div>
                      <p className="text-[10px] font-mono text-slate-500 truncate mt-1" title={vid.absolute_path}>
                        {vid.file_name}
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-1">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleDownload(vid)}
                          className="px-2.5 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition flex items-center gap-1 active:scale-95"
                          title="Tải video về máy tính"
                        >
                          <span>⬇️</span>
                          <span className="hidden sm:inline">Tải về</span>
                        </button>

                        <button
                          onClick={() => handleOpenFolder(vid.absolute_path)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition flex items-center gap-1 active:scale-95 border border-slate-700"
                          title="Mở vị trí file trên Windows Explorer ổ D"
                        >
                          <span>📁</span>
                          <span className="hidden sm:inline">Vị trí</span>
                        </button>

                        <button
                          onClick={() => handleCopyPath(vid.absolute_path, vid.id)}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xs transition"
                          title="Sao chép đường dẫn file trên ổ D"
                        >
                          {copiedId === vid.id ? "✓" : "📋"}
                        </button>
                      </div>

                      <button
                        onClick={() => handleDelete(vid)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Xóa video khỏi kho"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 flex-shrink-0">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Kho lưu trữ hoạt động offline trên ổ D: <strong className="text-slate-200">D:\Tool\output\export</strong></span>
          </span>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
          >
            Đóng
          </button>
        </div>
      </div>

      {/* Fullscreen Video Player Lightbox */}
      {activePreviewVideo && (
        <div className="fixed inset-0 z-[70] bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
            <div className="p-4 bg-slate-950 flex items-center justify-between border-b border-slate-800">
              <div className="truncate pr-4">
                <h3 className="text-sm sm:text-base font-bold text-white truncate">
                  {activePreviewVideo.title}
                </h3>
                <p className="text-xs text-slate-400 font-mono truncate">
                  {activePreviewVideo.absolute_path}
                </p>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => handleDownload(activePreviewVideo)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow"
                >
                  <span>⬇️ Tải xuống</span>
                </button>
                <button
                  onClick={() => handleOpenFolder(activePreviewVideo.absolute_path)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <span>📁 Mở ổ D</span>
                </button>
                <button
                  onClick={() => setActivePreviewVideo(null)}
                  className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="aspect-video w-full bg-black flex items-center justify-center">
              <video
                src={activePreviewVideo.video_url}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
