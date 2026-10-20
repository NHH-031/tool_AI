"use client";

import React, { useEffect, useState } from "react";
import {
  AudioResult,
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
import { ErrorBoundary } from "./components/ErrorBoundary";

export default function Home() {
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);

  // Global Studio Data
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [voices, setVoices] = useState<VoiceItem[]>([]);
  const [musicTracks, setMusicTracks] = useState<MusicTrackItem[]>([]);

  // Video Archive Vault State
  const [isArchiveVaultOpen, setIsArchiveVaultOpen] = useState<boolean>(false);
  const [archiveVideosCount, setArchiveVideosCount] = useState<number>(0);

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

  // Initialize studio data
  useEffect(() => {
    async function initStudio() {
      const health = await checkBackendHealth();
      setBackendHealthy(health.ok);

      const [tpls, vcs, msc, projs] = await Promise.all([
        fetchTemplates(),
        fetchVoices(),
        fetchMusic(),
        fetchProjects(),
      ]);

      setTemplates(tpls);
      setVoices(vcs);
      setMusicTracks(msc);
      setProjects(projs);

      // Tải số lượng video trong kho lưu trữ ổ D
      fetchArchiveStats().then((st) => {
        if (st) setArchiveVideosCount(st.total_videos);
      });
    }

    initStudio();
  }, []);

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

  // Handler: Switch Step
  const handleStepClick = (step: WizardStep) => {
    setWorkflow((prev) => ({
      ...prev,
      currentStep: step,
    }));
  };

  // Handler: Switch Project
  const handleSelectProject = (projectId: string) => {
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
      setWorkflow((prev) => ({
        ...prev,
        projectName: prev.projectName === "Dự án kịch bản mới" || !prev.projectName ? res.title : prev.projectName,
        script: {
          ...prev.script,
          rawText: text,
          inputMode: mode,
          scenes: res.scenes,
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
      const img = await generateStoryboardImage(
        scene.id,
        scene.scene_index,
        scene.prompt,
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

  const handleGenerateAllImages = async () => {
    setIsGeneratingAllImages(true);
    try {
      for (const scene of workflow.script.scenes) {
        setGeneratingSceneId(scene.id);
        const img = await generateStoryboardImage(
          scene.id,
          scene.scene_index,
          scene.prompt,
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
      />

      {/* 2. Step Progress Bar (4 Linear Steps) */}
      <StepProgressBar
        currentStep={workflow.currentStep}
        completedSteps={workflow.completedSteps}
        onStepClick={handleStepClick}
      />

      {/* 3. Main Step Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
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
    </div>
  );
}
