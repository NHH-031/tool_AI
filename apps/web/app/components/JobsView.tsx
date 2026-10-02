"use client";

import React, { useState } from "react";
import { ProductionJob } from "../types";

interface JobsViewProps {
  jobs: ProductionJob[];
  onInspectJob: (jobId: string) => void;
}

export const JobsView: React.FC<JobsViewProps> = ({ jobs, onInspectJob }) => {
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const filtered =
    filterStatus === "all" ? jobs : jobs.filter((j) => j.status === filterStatus);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Production Jobs Monitor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Theo dõi tiến trình thực thi 8 bước của Orchestrator API và Whiteboard Media Engine
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-2xl border border-slate-800">
          {["all", "completed", "running", "pending", "failed"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase transition ${
                filterStatus === st
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filtered.map((job) => (
          <div
            key={job.id}
            id={`job-row-${job.id}`}
            className="bg-slate-900/50 border border-slate-800/80 rounded-3xl p-6 hover:border-slate-700 transition space-y-4 shadow-lg"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/60 pb-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="font-extrabold text-white text-base">{job.title}</h2>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      job.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : job.status === "running"
                        ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse"
                        : job.status === "failed"
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {job.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">Prompt: "{job.prompt}"</p>
              </div>

              <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-slate-400">
                  Stage: <strong className="text-white">{job.current_stage}</strong>
                </span>
                <button
                  id={`btn-inspect-job-${job.id}`}
                  onClick={() => onInspectJob(job.id)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition active:scale-95"
                >
                  Inspect Review →
                </button>
              </div>
            </div>

            {/* Stage Progress Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
              {job.stages.map((stage, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-center"
                >
                  <div className="text-[10px] font-medium text-slate-400 truncate">
                    {stage.stage.replace(/_/g, " ")}
                  </div>
                  <div
                    className={`text-[11px] font-bold mt-1 ${
                      stage.status === "completed"
                        ? "text-emerald-400"
                        : stage.status === "running"
                        ? "text-indigo-400 animate-pulse"
                        : stage.status === "failed"
                        ? "text-rose-400"
                        : "text-slate-600"
                    }`}
                  >
                    {stage.status === "completed"
                      ? "✓ Done"
                      : stage.status === "running"
                      ? "● Running"
                      : stage.status === "failed"
                      ? "✕ Failed"
                      : "○ Pending"}
                  </div>
                </div>
              ))}
            </div>

            {/* Artifacts List */}
            {job.artifacts && Object.keys(job.artifacts).length > 0 && (
              <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-400 font-medium">Output Artifacts:</span>
                {Object.entries(job.artifacts).map(([key, path]) => (
                  <span
                    key={key}
                    className="font-mono text-[11px] px-2.5 py-1 rounded-lg bg-slate-950 text-indigo-300 border border-slate-800"
                  >
                    {key}: {path}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
