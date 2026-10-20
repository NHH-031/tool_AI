"use client";

import React, { useEffect, useState } from "react";
import {
  AudioResult,
  DrawingToolItem,
  MusicTrackItem,
  ProjectSummary,
  ProjectWorkflow,
  Scene,
  StoryboardImage,
  TemplateItem,
  VoiceItem,
  WizardStep,
} from "./types";
import {
  analyzeScript,
  checkBackendHealth,
  fetchMusic,
  fetchProjects,
  fetchStoryboard,
  fetchTemplates,
  fetchVoices,
  fetchDrawingTools,
  generateStoryboardImage,
  getExportStatus,
  subscribeExportProgress,
  renderExport,
  synthesizeVoice,
  fetchArchiveStats,
  getSubtitleDownloadUrl,
} from "./api-client";
import { StudioHeader } from "./components/StudioHeader";
import { StepProgressBar } from "./components/StepProgressBar";
import { ScriptStep } from "./components/steps/ScriptStep";
import { StoryboardStep } from "./components/steps/StoryboardStep";
import { VoiceStep } from "./components/steps/VoiceStep";
import { ExportStep } from "./components/steps/ExportStep";
import { ArchiveVaultModal } from "./components/ArchiveVaultModal";
import { SettingsModal, SETTINGS_STORAGE_KEY } from "./components/SettingsModal";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useAutoSave } from "./hooks/useAutoSave";

export default function Home() {
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);

  // Global Studio Data
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [voices, setVoices] = useState<VoiceItem[]>([]);
  const [musicTracks, setMusicTracks] = useState<MusicTrackItem[]>([]);
  const [drawingTools, setDrawingTools] = useState<DrawingToolItem[]>([]);

  // Video Archive Vault State
  const [isArchiveVaultOpen, setIsArchiveVaultOpen] = useState<boolean>(false);
  const [archiveVideosCount, setArchiveVideosCount] = useState<number>(0);

  // Settings Modal State
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Current Active Project Workflow State
  const [workflow, setWorkflow] = useState<ProjectWorkflow>({
    projectId: "proj-solar-panels-01",
    projectName: "Pin năng lượng mặt trời hoạt động thế nào?",
    aspectRatio: "16:9",
    currentStep: 1,
    completedSteps: [],
    script: {
      rawText:
        "Pin năng lượng mặt trời hấp thụ photon từ ánh sáng mặt trời. Các photon này giải phóng electron bên trong tinh thể silic, tạo ra dòng điện một chiều. Bộ biến tần inverter sau đó chuyển đổi thành dòng điện xoay chiều để thắp sáng ngôi nhà bạn.",
      inputMode: "text",
      scenes: [],
      status: "idle",
    },
    storyboard: {
      images: [],
      status: "idle",
    },
    voice: {
      voiceId: "vi-VN-Standard-B",
      speed: 1.0,
      musicId: "whimsical_play",
      musicVolume: 0.15,
      audios: [],
      status: "idle",
    },
    export: {
      videoUrl: null,
      srtUrl: null,
      vttUrl: null,
      subtitleStyle: "classic",
      handToolId: "hand-pen-modern",
      jobId: null,
      status: "idle",
      progress: 0,
    },
    updatedAt: new Date().toISOString(),
  });

  // Step 1: Script state
  const [isAnalyzingScript, setIsAnalyzingScript] = useState<boolean>(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("notion_minimal");

  // Step 2: Storyboard state
  const [isGeneratingAllImages, setIsGeneratingAllImages] = useState<boolean>(false);
  const [generatingSceneId, setGeneratingSceneId] = useState<string | null>(null);

  // Step 3: Voice state
  const [isSynthesizingAllVoices, setIsSynthesizingAllVoices] = useState<boolean>(false);
  const [synthesizingSceneId, setSynthesizingSceneId] = useState<string | null>(null);

  // Step 4: Export state
  const [isRenderingVideo, setIsRenderingVideo] = useState<boolean>(false);
  const [renderProgress, setRenderProgress] = useState<number>(0);
  const [renderStage, setRenderStage] = useState<string>("");
  const [renderErrorMessage, setRenderErrorMessage] = useState<string | null>(null);

  // =========================================================================
  // GLOBAL LOADING STATE — prevents step-switch from hiding loading indicators
  // =========================================================================
  const isAnyLoading = isAnalyzingScript || isGeneratingAllImages || !!generatingSceneId || isSynthesizingAllVoices || !!synthesizingSceneId || isRenderingVideo;

  const getGlobalLoadingMessage = (): { emoji: string; label: string; detail: string; step: WizardStep } | null => {
    if (isAnalyzingScript) return { emoji: "🤖", label: "Đang phân tích kịch bản...", detail: "AI đang chia cảnh và tạo prompt vẽ tay", step: 1 };
    if (isGeneratingAllImages || generatingSceneId) return { emoji: "🎨", label: "Đang tạo ảnh storyboard...", detail: generatingSceneId ? `Sinh ảnh cho cảnh đang xử lý` : "Sinh ảnh toàn bộ phân cảnh", step: 2 };
    if (isSynthesizingAllVoices || synthesizingSceneId) return { emoji: "🎙️", label: "Đang thu âm giọng đọc...", detail: synthesizingSceneId ? `Thu âm cảnh đang xử lý` : "Thu âm toàn bộ phân cảnh", step: 3 };
    if (isRenderingVideo) return { emoji: "🎬", label: "Đang kết xuất video...", detail: renderStage || `Tiến độ: ${renderProgress}%`, step: 4 };
    return null;
  };

  // Initialize studio data
  useEffect(() => {
    async function initStudio() {
      const health = await checkBackendHealth();
      setBackendHealthy(health.ok);

      const [tpls, vcs, msc, projs, dTools] = await Promise.all([
        fetchTemplates(),
        fetchVoices(),
        fetchMusic(),
        fetchProjects(),
        fetchDrawingTools(),
      ]);

      setTemplates(tpls);
      setVoices(vcs);
      setMusicTracks(msc);
      setProjects(projs);
      setDrawingTools(dTools);

      // Tải số lượng video trong kho lưu trữ ổ D
      fetchArchiveStats().then((st) => {
        if (st) setArchiveVideosCount(st.total_videos);
      });

      // Tải cài đặt mặc định từ localStorage nếu có
      try {
        const rawSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (rawSettings) {
          const s = JSON.parse(rawSettings);
          setWorkflow((prev) => ({
            ...prev,
            aspectRatio: s.defaultAspectRatio || prev.aspectRatio,
            voice: {
              ...prev.voice,
              voiceId: s.defaultVoiceId || prev.voice.voiceId,
              speed: s.defaultSpeed || prev.voice.speed,
            },
            export: {
              ...prev.export,
              handToolId: s.defaultHandToolId || prev.export.handToolId,
              subtitleStyle: s.defaultSubtitleStyle || prev.export.subtitleStyle,
            },
          }));
        }
      } catch {}
    }

    initStudio();
  }, []);

  // Auto-Save dự án tự động vào localStorage & Khôi phục phiên làm việc
  const { hasDraft, draftMeta, restoreDraft, discardDraft } = useAutoSave(
    workflow,
    setWorkflow
  );

  // Auto-sync existing storyboard images when arriving at Step 2
  useEffect(() => {
    if (workflow.currentStep === 2 && workflow.script.scenes.length > 0) {
      fetchStoryboard(workflow.projectId).then((existingImgs) => {
        if (existingImgs && existingImgs.length > 0) {
          setWorkflow((prev) => {
            const nextScenes = prev.script.scenes.map((sc) => {
              const match = existingImgs.find(
                (img) => img.scene_index === sc.scene_index || img.scene_id === sc.id
              );
              if (match) {
                return { ...sc, image_url: match.image_url, image_status: "completed" as const };
              }
              return sc;
            });
            return {
              ...prev,
              script: { ...prev.script, scenes: nextScenes },
              storyboard: { ...prev.storyboard, images: existingImgs },
            };
          });
        }
      });
    }
  }, [workflow.currentStep, workflow.projectId, workflow.script.scenes.length]);

  // Handler: Switch Step — blocked while any async operation is running
  const handleStepClick = (step: WizardStep) => {
    if (isAnyLoading) return; // Block navigation while loading
    setWorkflow((prev) => ({
      ...prev,
      currentStep: step,
    }));
  };

  // Handler: Switch Project
  const handleSelectProject = (projectId: string) => {
    if (isAnyLoading) return;
    const proj = projects.find((p) => p.id === projectId);
    if (!proj) return;

    setWorkflow({
      projectId: proj.id,
      projectName: proj.title,
      aspectRatio: (proj.aspect_ratio as any) === "9:16" ? "9:16" : "16:9",
      currentStep: proj.status === "completed" ? 4 : 1,
      completedSteps: proj.status === "completed" ? [1, 2, 3, 4] : [],
      script: {
        rawText: proj.description || proj.title,
        inputMode: "text",
        scenes: [],
        status: proj.status === "completed" ? "completed" : "idle",
      },
      storyboard: {
        images: [],
        status: proj.status === "completed" ? "completed" : "idle",
      },
      voice: {
        voiceId: "vi-VN-Standard-B",
        speed: 1.0,
        musicId: "whimsical_play",
        musicVolume: 0.15,
        audios: [],
        status: proj.status === "completed" ? "completed" : "idle",
      },
      export: {
        videoUrl: proj.video_url,
        status: proj.status === "completed" ? "completed" : "idle",
        progress: proj.status === "completed" ? 100 : 0,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  // Handler: New Project
  const handleNewProject = () => {
    if (isAnyLoading) return;
    const newId = `proj-${Date.now()}`;
    const newTitle = "Dự án kịch bản mới";
    setWorkflow({
      projectId: newId,
      projectName: newTitle,
      aspectRatio: "16:9",
      currentStep: 1,
      completedSteps: [],
      script: {
        rawText: "",
        inputMode: "text",
        scenes: [],
        status: "idle",
      },
      storyboard: {
        images: [],
        status: "idle",
      },
      voice: {
        voiceId: "vi-VN-Standard-B",
        speed: 1.0,
        musicId: "whimsical_play",
        musicVolume: 0.15,
        audios: [],
        status: "idle",
      },
      export: {
        videoUrl: null,
        status: "idle",
        progress: 0,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  // =========================================================================
  // STEP 1: SCRIPT LOGIC
  // =========================================================================
  const handleAnalyzeScript = async (
    text: string,
    mode: "text" | "srt",
    targetScenes?: number
  ) => {
    setIsAnalyzingScript(true);
    try {
      const res = await analyzeScript(text, mode, targetScenes);
      let processedScenes = res.scenes;
      if (workflow.script.characterAnchor) {
        const anchor = workflow.script.characterAnchor;
        const anchorClause = `[Character Identity]: Main character ${anchor.name}, ${anchor.gender}, ${anchor.hair_style}, ${anchor.clothing}.`;
        processedScenes = res.scenes.map((s) => ({
          ...s,
          prompt: `${anchorClause}\n${s.prompt}`,
        }));
      }

      setWorkflow((prev) => ({
        ...prev,
        projectName: prev.projectName === "Dự án kịch bản mới" || !prev.projectName ? res.title : prev.projectName,
        script: {
          ...prev.script,
          rawText: text,
          inputMode: mode,
          scenes: processedScenes,
          status: "completed",
        },
      }));
    } catch (e) {
      console.error("Lỗi phân tích kịch bản:", e);
    } finally {
      setIsAnalyzingScript(false);
    }
  };

  const handleNextFromScript = () => {
    if (isAnyLoading) return;
    setWorkflow((prev) => ({
      ...prev,
      currentStep: 2,
      completedSteps: Array.from(new Set([...prev.completedSteps, 1 as WizardStep])),
    }));
  };

  // =========================================================================
  // STEP 2: STORYBOARD LOGIC
  // =========================================================================
  const handleUpdateScenePrompt = (index: number, newPrompt: string) => {
    setWorkflow((prev) => {
      const updatedScenes = [...prev.script.scenes];
      if (updatedScenes[index]) {
        updatedScenes[index] = { ...updatedScenes[index], prompt: newPrompt };
      }
      return {
        ...prev,
        script: { ...prev.script, scenes: updatedScenes },
      };
    });
  };

  const handleGenerateSingleImage = async (scene: Scene) => {
    setGeneratingSceneId(scene.id);
    try {
      let promptToSend = scene.prompt;
      if (workflow.script.characterAnchor && !promptToSend.includes("[Character Identity]")) {
        const anchor = workflow.script.characterAnchor;
        promptToSend = `[Character Identity]: Main character ${anchor.name}, ${anchor.gender}, ${anchor.hair_style}, ${anchor.clothing}.\n${promptToSend}`;
      }

      const img = await generateStoryboardImage(
        scene.id,
        scene.scene_index,
        promptToSend,
        workflow.projectId,
        true,
        workflow.aspectRatio || "16:9"
      );
      setWorkflow((prev) => {
        const nextImages = prev.storyboard.images.filter((i) => i.scene_id !== scene.id);
        nextImages.push(img);
        const updatedScenes = prev.script.scenes.map((sc) =>
          sc.id === scene.id ? { ...sc, image_url: img.image_url, image_status: "completed" as const } : sc
        );
        return {
          ...prev,
          script: { ...prev.script, scenes: updatedScenes },
          storyboard: { ...prev.storyboard, images: nextImages },
        };
      });
    } catch (e) {
      console.error("Lỗi sinh ảnh:", e);
    } finally {
      setGeneratingSceneId(null);
    }
  };

  const handleUpdateSceneImage = (img: StoryboardImage) => {
    setWorkflow((prev) => {
      const nextImages = prev.storyboard.images.filter(
        (i) => i.scene_id !== img.scene_id && i.scene_index !== img.scene_index
      );
      nextImages.push(img);
      const updatedScenes = prev.script.scenes.map((sc) =>
        sc.id === img.scene_id || sc.scene_index === img.scene_index
          ? { ...sc, image_url: img.image_url, image_status: "completed" as const }
          : sc
      );
      return {
        ...prev,
        script: { ...prev.script, scenes: updatedScenes },
        storyboard: { ...prev.storyboard, images: nextImages },
      };
    });
  };

  const handleGenerateAllImages = async () => {
    setIsGeneratingAllImages(true);
    try {
      for (const scene of workflow.script.scenes) {
        setGeneratingSceneId(scene.id);
        let promptToSend = scene.prompt;
        if (workflow.script.characterAnchor && !promptToSend.includes("[Character Identity]")) {
          const anchor = workflow.script.characterAnchor;
          promptToSend = `[Character Identity]: Main character ${anchor.name}, ${anchor.gender}, ${anchor.hair_style}, ${anchor.clothing}.\n${promptToSend}`;
        }

        const img = await generateStoryboardImage(
          scene.id,
          scene.scene_index,
          promptToSend,
          workflow.projectId,
          false,
          workflow.aspectRatio || "16:9"
        );
        setWorkflow((prev) => {
          const nextImages = prev.storyboard.images.filter((i) => i.scene_id !== scene.id);
          nextImages.push(img);
          const updatedScenes = prev.script.scenes.map((sc) =>
            sc.id === scene.id ? { ...sc, image_url: img.image_url, image_status: "completed" as const } : sc
          );
          return {
            ...prev,
            script: { ...prev.script, scenes: updatedScenes },
            storyboard: { ...prev.storyboard, images: nextImages },
          };
        });
      }
    } finally {
      setGeneratingSceneId(null);
      setIsGeneratingAllImages(false);
    }
  };

  const handleNextFromStoryboard = () => {
    if (isAnyLoading) return;
    setWorkflow((prev) => ({
      ...prev,
      currentStep: 3,
      completedSteps: Array.from(new Set([...prev.completedSteps, 2 as WizardStep])),
    }));
  };

  // =========================================================================
  // STEP 3: VOICE LOGIC
  // =========================================================================
  const handleSynthesizeSingleVoice = async (scene: Scene) => {
    setSynthesizingSceneId(scene.id);
    try {
      const audio = await synthesizeVoice(
        scene.id,
        scene.scene_index,
        scene.text,
        workflow.voice.voiceId,
        workflow.voice.speed,
        workflow.projectId
      );
      setWorkflow((prev) => {
        const nextAudios = prev.voice.audios.filter((a) => a.scene_id !== scene.id);
        nextAudios.push(audio);
        const updatedScenes = prev.script.scenes.map((sc) =>
          sc.id === scene.id ? { ...sc, audio_url: audio.audio_url, audio_status: "completed" as const } : sc
        );
        return {
          ...prev,
          script: { ...prev.script, scenes: updatedScenes },
          voice: { ...prev.voice, audios: nextAudios },
        };
      });
    } catch (e) {
      console.error("Lỗi thu âm cảnh:", e);
    } finally {
      setSynthesizingSceneId(null);
    }
  };

  const handleSynthesizeAllVoices = async () => {
    setIsSynthesizingAllVoices(true);
    try {
      for (const scene of workflow.script.scenes) {
        setSynthesizingSceneId(scene.id);
        const audio = await synthesizeVoice(
          scene.id,
          scene.scene_index,
          scene.text,
          workflow.voice.voiceId,
          workflow.voice.speed,
          workflow.projectId
        );
        setWorkflow((prev) => {
          const nextAudios = prev.voice.audios.filter((a) => a.scene_id !== scene.id);
          nextAudios.push(audio);
          const updatedScenes = prev.script.scenes.map((sc) =>
            sc.id === scene.id ? { ...sc, audio_url: audio.audio_url, audio_status: "completed" as const } : sc
          );
          return {
            ...prev,
            script: { ...prev.script, scenes: updatedScenes },
            voice: { ...prev.voice, audios: nextAudios },
          };
        });
      }
    } finally {
      setSynthesizingSceneId(null);
      setIsSynthesizingAllVoices(false);
    }
  };

  const handleNextFromVoice = () => {
    if (isAnyLoading) return;
    setWorkflow((prev) => ({
      ...prev,
      currentStep: 4,
      completedSteps: Array.from(new Set([...prev.completedSteps, 3 as WizardStep])),
    }));
  };

  // =========================================================================
  // STEP 4: EXPORT LOGIC
  // =========================================================================
  const handleStartRender = async () => {
    setIsRenderingVideo(true);
    setRenderProgress(10);
    setRenderStage("Bắt đầu xử lý nét vẽ và overlay bàn tay marker...");
    setRenderErrorMessage(null);

    try {
      const res = await renderExport({
        projectId: workflow.projectId,
        title: workflow.projectName,
        scenes: workflow.script.scenes,
        voiceId: workflow.voice.voiceId,
        speed: workflow.voice.speed,
        musicId: workflow.voice.musicId,
        musicVolume: workflow.voice.musicVolume,
        hasColor: true,
        subtitleStyle: workflow.export.subtitleStyle || "classic",
        aspectRatio: workflow.aspectRatio || "16:9",
        handToolId: workflow.export.handToolId || "hand-pen-modern",
        multiPen: workflow.export.multiPen !== undefined ? workflow.export.multiPen : true,
        transitionType: workflow.export.transitionType || "eraser",
      });

      if (res.videoUrl) {
        setWorkflow((prev) => ({
          ...prev,
          export: {
            ...prev.export,
            videoUrl: res.videoUrl,
            srtUrl: res.srtUrl,
            vttUrl: res.vttUrl,
            jobId: res.jobId,
            status: "completed",
            progress: 100,
          },
          completedSteps: Array.from(new Set([...prev.completedSteps, 4 as WizardStep])),
        }));
        setRenderProgress(100);
        setRenderStage("Hoàn thành kết xuất video!");
        setIsRenderingVideo(false);
      } else {
        // Cập nhật tiến độ thời gian thực qua Server-Sent Events (SSE) kèm polling fallback
        let isDone = false;
        const handleStatusUpdate = (statusData: {
          status: string;
          progressPercent: number;
          stage: string;
          videoUrl: string | null;
          srtUrl?: string | null;
          vttUrl?: string | null;
          errorMessage?: string;
          qaReport?: any;
        }) => {
          if (statusData.progressPercent >= 0) {
            setRenderProgress(statusData.progressPercent);
            setRenderStage(statusData.stage);
          }
          if (statusData.status === "completed" && statusData.videoUrl) {
            isDone = true;
            setWorkflow((prev) => ({
              ...prev,
              export: {
                ...prev.export,
                videoUrl: statusData.videoUrl,
                srtUrl: statusData.srtUrl || prev.export.srtUrl,
                vttUrl: statusData.vttUrl || prev.export.vttUrl,
                jobId: res.jobId,
                status: "completed",
                progress: 100,
                qaReport: statusData.qaReport,
              },
              completedSteps: Array.from(new Set([...prev.completedSteps, 4 as WizardStep])),
            }));
            setIsRenderingVideo(false);
          } else if (statusData.status === "failed") {
            isDone = true;
            setRenderErrorMessage(statusData.errorMessage || "Kết xuất video thất bại");
            setIsRenderingVideo(false);
          }
        };

        const startPollingFallback = () => {
          const pollInterval = setInterval(async () => {
            if (isDone) {
              clearInterval(pollInterval);
              return;
            }
            try {
              const statusData = await getExportStatus(res.jobId);
              handleStatusUpdate(statusData);
              if (isDone) {
                clearInterval(pollInterval);
              }
            } catch (pollErr) {
              console.warn("[Export Polling] Lỗi thăm dò tiến trình:", pollErr);
            }
          }, 3000);
        };

        // Đăng ký SSE Stream
        try {
          subscribeExportProgress(
            res.jobId,
            (eventData) => {
              handleStatusUpdate(eventData);
            },
            () => {
              if (!isDone) {
                startPollingFallback();
              }
            }
          );
        } catch {
          startPollingFallback();
        }
      }
    } catch (e: any) {
      setRenderErrorMessage(e.message || "Lỗi trong quá trình render video");
      setIsRenderingVideo(false);
    }
  };

  const handleDownloadMP4 = () => {
    const url = workflow.export.videoUrl;
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `${workflow.projectName || "whiteboard_video"}.mp4`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadSubtitle = (format: "srt" | "vtt" = "srt") => {
    const jobId = workflow.export.jobId;
    let url = format === "vtt" ? workflow.export.vttUrl : workflow.export.srtUrl;
    if (!url && jobId) {
      url = getSubtitleDownloadUrl(jobId, format);
    }
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = `${workflow.projectName || "whiteboard_video"}.${format}`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* 1. Header with Project Selector & New Script */}
      <StudioHeader
        currentProjectTitle={workflow.projectName}
        projects={projects}
        onSelectProject={handleSelectProject}
        onNewProject={handleNewProject}
        backendHealthy={backendHealthy}
        archiveCount={archiveVideosCount}
        onOpenArchiveVault={() => setIsArchiveVaultOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isLocked={isAnyLoading}
      />

      {/* 2. Step Progress Bar (4 Linear Steps) */}
      <StepProgressBar
        currentStep={workflow.currentStep}
        completedSteps={workflow.completedSteps}
        onStepClick={handleStepClick}
        isLocked={isAnyLoading}
      />

      {/* 2b. Global Loading Banner — persists regardless of active step */}
      {isAnyLoading && (() => {
        const info = getGlobalLoadingMessage();
        if (!info) return null;
        return (
          <div className="w-full bg-indigo-950/60 border-b border-indigo-500/30 backdrop-blur-md">
            <div className="max-w-4xl mx-auto flex items-center justify-between px-4 sm:px-8 py-3">
              <div className="flex items-center gap-3">
                <div className="relative flex items-center justify-center">
                  <div className="w-9 h-9 rounded-full bg-indigo-500/20 border-2 border-indigo-400/50 flex items-center justify-center text-lg animate-pulse">
                    {info.emoji}
                  </div>
                  <svg className="absolute -inset-0.5 w-10 h-10 animate-spin" viewBox="0 0 36 36" fill="none">
                    <circle cx="18" cy="18" r="16" stroke="currentColor" strokeWidth="2" className="text-slate-800" />
                    <path d="M18 2 a16 16 0 0 1 16 16" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" className="text-indigo-400" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-semibold text-white leading-tight">{info.label}</p>
                  <p className="text-[10px] sm:text-[11px] text-indigo-300/70">{info.detail}</p>
                </div>
              </div>
              {info.step !== workflow.currentStep && (
                <button
                  onClick={() => setWorkflow((prev) => ({ ...prev, currentStep: info.step }))}
                  className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600/40 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-500/30 font-medium transition"
                >
                  Quay về Bước {info.step}
                </button>
              )}
              {isRenderingVideo && (
                <div className="hidden sm:flex items-center gap-2">
                  <div className="w-24 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500 rounded-full"
                      style={{ width: `${renderProgress}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-indigo-300">{renderProgress}%</span>
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* 3. Main Step Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* Autosave Draft Notification Banner */}
        {hasDraft && draftMeta && (
          <div className="mb-6 p-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 backdrop-blur-md animate-in fade-in">
            <div className="flex items-center gap-3">
              <span className="text-2xl">💾</span>
              <div>
                <p className="text-xs sm:text-sm font-semibold text-white">
                  Phát hiện bản nháp đã lưu: &ldquo;{draftMeta.projectName}&rdquo; ({draftMeta.sceneCount} phân cảnh)
                </p>
                <p className="text-[11px] text-slate-400">
                  Lưu lúc {new Date(draftMeta.savedAt).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" })}. Bạn có muốn tiếp tục làm việc không?
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-auto">
              <button
                onClick={discardDraft}
                className="px-3 py-1.5 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                Bỏ qua
              </button>
              <button
                onClick={restoreDraft}
                className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition shadow-md shadow-indigo-600/20 active:scale-95"
              >
                Khôi phục bản nháp
              </button>
            </div>
          </div>
        )}

        <ErrorBoundary>
        {workflow.currentStep === 1 && (
          <ScriptStep
            projectTitle={workflow.projectName}
            onUpdateTitle={(title) =>
              setWorkflow((prev) => ({ ...prev, projectName: title }))
            }
            rawText={workflow.script.rawText}
            onUpdateRawText={(text) =>
              setWorkflow((prev) => ({
                ...prev,
                script: { ...prev.script, rawText: text },
              }))
            }
            inputMode={workflow.script.inputMode}
            onUpdateInputMode={(mode) =>
              setWorkflow((prev) => ({
                ...prev,
                script: { ...prev.script, inputMode: mode },
              }))
            }
            aspectRatio={workflow.aspectRatio || "16:9"}
            onUpdateAspectRatio={(ratio) =>
              setWorkflow((prev) => ({ ...prev, aspectRatio: ratio }))
            }
            scenes={workflow.script.scenes}
            onUpdateScenes={(scenes) =>
              setWorkflow((prev) => ({
                ...prev,
                script: { ...prev.script, scenes },
              }))
            }
            templates={templates}
            selectedTemplateId={selectedTemplateId}
            onSelectTemplate={setSelectedTemplateId}
            onAnalyze={handleAnalyzeScript}
            isAnalyzing={isAnalyzingScript}
            onNextStep={handleNextFromScript}
            characterAnchor={workflow.script.characterAnchor}
            onUpdateCharacterAnchor={(anchor) =>
              setWorkflow((prev) => ({
                ...prev,
                script: { ...prev.script, characterAnchor: anchor },
              }))
            }
          />
        )}

        {workflow.currentStep === 2 && (
          <StoryboardStep
            scenes={workflow.script.scenes}
            images={workflow.storyboard.images}
            onUpdateScenePrompt={handleUpdateScenePrompt}
            onGenerateSingleImage={handleGenerateSingleImage}
            onGenerateAllImages={handleGenerateAllImages}
            isGeneratingAll={isGeneratingAllImages}
            generatingSceneId={generatingSceneId}
            onBackStep={() => handleStepClick(1)}
            onNextStep={handleNextFromStoryboard}
            projectId={workflow.projectId}
            aspectRatio={workflow.aspectRatio || "16:9"}
            handToolId={workflow.export.handToolId || "hand-pen-modern"}
            onUpdateSceneImage={handleUpdateSceneImage}
          />
        )}

        {workflow.currentStep === 3 && (
          <VoiceStep
            scenes={workflow.script.scenes}
            audios={workflow.voice.audios}
            voices={voices}
            selectedVoiceId={workflow.voice.voiceId}
            onSelectVoice={(id) =>
              setWorkflow((prev) => ({
                ...prev,
                voice: { ...prev.voice, voiceId: id },
              }))
            }
            speed={workflow.voice.speed}
            onUpdateSpeed={(s) =>
              setWorkflow((prev) => ({
                ...prev,
                voice: { ...prev.voice, speed: s },
              }))
            }
            musicTracks={musicTracks}
            selectedMusicId={workflow.voice.musicId}
            onSelectMusic={(id) =>
              setWorkflow((prev) => ({
                ...prev,
                voice: { ...prev.voice, musicId: id },
              }))
            }
            musicVolume={workflow.voice.musicVolume}
            onUpdateMusicVolume={(v) =>
              setWorkflow((prev) => ({
                ...prev,
                voice: { ...prev.voice, musicVolume: v },
              }))
            }
            onSynthesizeSingle={handleSynthesizeSingleVoice}
            onSynthesizeAll={handleSynthesizeAllVoices}
            isSynthesizing={isSynthesizingAllVoices}
            synthesizingSceneId={synthesizingSceneId}
            onBackStep={() => handleStepClick(2)}
            onNextStep={handleNextFromVoice}
          />
        )}

        {workflow.currentStep === 4 && (
          <ExportStep
            workflow={workflow}
            scenes={workflow.script.scenes}
            videoUrl={workflow.export.videoUrl}
            srtUrl={workflow.export.srtUrl}
            vttUrl={workflow.export.vttUrl}
            jobId={workflow.export.jobId}
            subtitleStyle={workflow.export.subtitleStyle || "classic"}
            onUpdateSubtitleStyle={(style) =>
              setWorkflow((prev) => ({
                ...prev,
                export: { ...prev.export, subtitleStyle: style },
              }))
            }
            drawingTools={drawingTools}
            selectedHandToolId={workflow.export.handToolId || "hand-pen-modern"}
            onSelectHandTool={(toolId) =>
              setWorkflow((prev) => ({
                ...prev,
                export: { ...prev.export, handToolId: toolId },
              }))
            }
            multiPen={workflow.export.multiPen !== undefined ? workflow.export.multiPen : true}
            onUpdateMultiPen={(m) =>
              setWorkflow((prev) => ({
                ...prev,
                export: { ...prev.export, multiPen: m },
              }))
            }
            transitionType={workflow.export.transitionType || "eraser"}
            onUpdateTransitionType={(t) =>
              setWorkflow((prev) => ({
                ...prev,
                export: { ...prev.export, transitionType: t },
              }))
            }
            isRendering={isRenderingVideo}
            renderProgress={renderProgress}
            renderStage={renderStage}
            errorMessage={renderErrorMessage}
            qaReport={workflow.export.qaReport}
            onStartRender={handleStartRender}
            onDownloadMP4={handleDownloadMP4}
            onDownloadSubtitle={handleDownloadSubtitle}
            onBackStep={() => handleStepClick(3)}
            onOpenArchiveVault={() => setIsArchiveVaultOpen(true)}
          />
        )}
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 mt-12 text-center text-xs text-slate-500">
        <p>Whiteboard Studio · 4-Step Production Pipeline · SKILL.md High Fidelity</p>
      </footer>

      {/* Video Archive Vault Modal (Kho Lưu Trữ Ổ D) */}
      <ArchiveVaultModal
        isOpen={isArchiveVaultOpen}
        onClose={() => {
          setIsArchiveVaultOpen(false);
          fetchArchiveStats().then((st) => st && setArchiveVideosCount(st.total_videos));
        }}
      />

      {/* Settings Modal (Cài Đặt Studio & API Key) */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        voices={voices}
        drawingTools={drawingTools}
        onClearDrafts={discardDraft}
      />
    </div>
  );
}
