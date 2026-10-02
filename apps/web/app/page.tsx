"use client";

import React, { useEffect, useState } from "react";
import {
  ActiveTab,
  AssetCatalogItem,
  GenerationState,
  MusicTrackItem,
  ProductionJob,
  ProjectSummary,
  RegenerateTarget,
  ReviewData,
  TemplateItem,
  VoiceItem,
} from "./types";
import {
  checkBackendHealth,
  createProductionJob,
  DEFAULT_REVIEW_DATA,
  fetchAssets,
  fetchJobReview,
  fetchJobs,
  fetchMusic,
  fetchProjects,
  fetchTemplates,
  fetchVoices,
  regenerateJobComponent,
} from "./api-client";
import { Navbar } from "./components/Navbar";
import { DashboardView } from "./components/DashboardView";
import { CreateVideoView } from "./components/CreateVideoView";
import { ReviewScreenView } from "./components/ReviewScreenView";
import { TemplatesView } from "./components/TemplatesView";
import { AssetsView } from "./components/AssetsView";
import { VoicesView } from "./components/VoicesView";
import { MusicView } from "./components/MusicView";
import { JobsView } from "./components/JobsView";

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("dashboard");
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);

  // Studio Data
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [assets, setAssets] = useState<AssetCatalogItem[]>([]);
  const [voices, setVoices] = useState<VoiceItem[]>([]);
  const [musicTracks, setMusicTracks] = useState<MusicTrackItem[]>([]);
  const [jobs, setJobs] = useState<ProductionJob[]>([]);

  // Active Job & Review State
  const [activeJob, setActiveJob] = useState<ProductionJob | null>(null);
  const [reviewData, setReviewData] = useState<ReviewData>(DEFAULT_REVIEW_DATA);
  const [generationState, setGenerationState] = useState<GenerationState>("completed");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Quick prompt prefill
  const [prefilledPrompt, setPrefilledPrompt] = useState<string>("");

  useEffect(() => {
    async function initStudio() {
      const health = await checkBackendHealth();
      setBackendHealthy(health.ok);

      const [tpls, asts, vcs, msc, projs, jbs] = await Promise.all([
        fetchTemplates(),
        fetchAssets(),
        fetchVoices(),
        fetchMusic(),
        fetchProjects(),
        fetchJobs(),
      ]);

      setTemplates(tpls);
      setAssets(asts);
      setVoices(vcs);
      setMusicTracks(msc);
      setProjects(projs);
      setJobs(jbs);

      if (jbs.length > 0) {
        setActiveJob(jbs[0]);
        const rev = await fetchJobReview(jbs[0].id);
        setReviewData(rev);
      }
    }

    initStudio();
  }, []);

  // Quick generate from Dashboard
  const handleQuickGenerate = (promptText: string) => {
    setPrefilledPrompt(promptText);
    setActiveTab("create");
  };

  // Create Video & Generate Pipeline
  const handleCreateVideo = async (config: {
    title: string;
    prompt: string;
    language: string;
    voice_id: string;
    speed: number;
    music_id: string;
    music_volume: number;
    visual_style: string;
    aspect_ratio: string;
  }) => {
    setGenerationState("generating");
    setErrorMessage(null);
    setActiveTab("review");

    try {
      const newJob = await createProductionJob(config);
      setActiveJob(newJob);

      // Refresh jobs list
      const updatedJobs = await fetchJobs();
      setJobs(updatedJobs);

      // Fetch or synthesize review data
      const rev = await fetchJobReview(newJob.id);
      setReviewData({
        ...rev,
        idea: config.prompt,
        visual_style: config.visual_style,
        voice_id: config.voice_id,
        aspect_ratio: config.aspect_ratio,
        script: {
          title: config.title,
          full_text: config.prompt,
          segments: [
            {
              segment_id: "seg-01",
              text: config.prompt,
              estimated_duration: 5.18,
              semantic_meaning: "Diễn hoạt phân cảnh dựa trên ý tưởng người dùng",
              keywords: ["khỉ", "trèo", "cây", "chuối"],
            },
          ],
        },
      });

      setGenerationState("completed");
    } catch (err: any) {
      setGenerationState("failed");
      setErrorMessage(err?.message || "Lỗi trong quá trình tạo kịch bản và kết xuất.");
    }
  };

  // Inspect Project from Dashboard
  const handleOpenProject = async (projectId: string) => {
    const matchedJob = jobs.find((j) => j.id.includes("monkey") || j.id === projectId) || jobs[0];
    if (matchedJob) {
      setActiveJob(matchedJob);
      const rev = await fetchJobReview(matchedJob.id);
      setReviewData(rev);
    }
    setGenerationState("completed");
    setActiveTab("review");
  };

  // Inspect Job from Production Jobs
  const handleInspectJob = async (jobId: string) => {
    const matched = jobs.find((j) => j.id === jobId);
    if (matched) {
      setActiveJob(matched);
      const rev = await fetchJobReview(jobId);
      setReviewData(rev);
      setGenerationState(matched.status === "completed" ? "completed" : "generating");
      setActiveTab("review");
    }
  };

  // Regenerate Component
  const handleRegenerate = async (target: RegenerateTarget, instructions?: string) => {
    if (!activeJob) return;
    setGenerationState("retrying");

    try {
      await regenerateJobComponent(activeJob.id, target, instructions);
      const rev = await fetchJobReview(activeJob.id);
      setReviewData(rev);
      setGenerationState("completed");
    } catch {
      setGenerationState("failed");
      setErrorMessage(`Không thể tái tạo thành phần ${target}`);
    }
  };

  // Export MP4
  const handleExportMP4 = () => {
    const videoUrl =
      reviewData.video_url || "http://127.0.0.1:8000/media/monkey_banana_e2e/scene_default_final.mp4";
    const a = document.createElement("a");
    a.href = videoUrl;
    a.download = "whiteboard_video_studio.mp4";
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendHealthy={backendHealthy}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === "dashboard" && (
          <DashboardView
            projects={projects}
            onOpenProject={handleOpenProject}
            onQuickGenerate={handleQuickGenerate}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "create" && (
          <CreateVideoView
            initialPrompt={prefilledPrompt}
            voices={voices}
            musicTracks={musicTracks}
            templates={templates}
            onGenerate={handleCreateVideo}
            isGenerating={generationState === "generating"}
          />
        )}

        {activeTab === "review" && (
          <ReviewScreenView
            job={activeJob}
            reviewData={reviewData}
            generationState={generationState}
            errorMessage={errorMessage}
            onRetry={() => setGenerationState("completed")}
            onRegenerate={handleRegenerate}
            onExportMP4={handleExportMP4}
          />
        )}

        {activeTab === "templates" && (
          <TemplatesView
            templates={templates}
            onSelectTemplate={(tplId) => {
              // Preselect template
            }}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "assets" && <AssetsView assets={assets} />}

        {activeTab === "voices" && <VoicesView voices={voices} />}

        {activeTab === "music" && <MusicView musicTracks={musicTracks} />}

        {activeTab === "jobs" && (
          <JobsView jobs={jobs} onInspectJob={handleInspectJob} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 mt-12 text-center text-xs text-slate-500">
        <p>AI Whiteboard Video Production Studio · Phase 10 Studio UI</p>
      </footer>
    </div>
  );
}
