import { useEffect, useState, useCallback, useRef } from "react";
import { ProjectWorkflow } from "../types";

export const AUTOSAVE_STORAGE_KEY = "whiteboard_studio_autosave_v1";

export interface AutoSaveMetadata {
  savedAt: string;
  projectName: string;
  sceneCount: number;
  currentStep: number;
}

export function useAutoSave(
  workflow: ProjectWorkflow,
  setWorkflow: React.Dispatch<React.SetStateAction<ProjectWorkflow>>
) {
  const [hasDraft, setHasDraft] = useState<boolean>(false);
  const [draftMeta, setDraftMeta] = useState<AutoSaveMetadata | null>(null);
  const isInitialMount = useRef<boolean>(true);

  // Kiểm tra lúc tải trang xem có bản nháp tự lưu trong localStorage không
  useEffect(() => {
    try {
      const raw = localStorage.getItem(AUTOSAVE_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.workflow && parsed.savedAt) {
          // Chỉ hiện nếu bản nháp có kịch bản hoặc phân cảnh
          const hasContent =
            (parsed.workflow.script?.scenes && parsed.workflow.script.scenes.length > 0) ||
            (parsed.workflow.script?.rawText && parsed.workflow.script.rawText.length > 50);

          if (hasContent) {
            setHasDraft(true);
            setDraftMeta({
              savedAt: parsed.savedAt,
              projectName: parsed.workflow.projectName || "Dự án chưa đặt tên",
              sceneCount: parsed.workflow.script?.scenes?.length || 0,
              currentStep: parsed.workflow.currentStep || 1,
            });
          }
        }
      }
    } catch (e) {
      console.warn("[useAutoSave] Lỗi đọc bản nháp:", e);
    }
  }, []);

  // Tự động lưu nháp sau 2.5s khi workflow thay đổi (Debounced auto-save)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    const timer = setTimeout(() => {
      try {
        const payload = {
          savedAt: new Date().toISOString(),
          workflow,
        };
        localStorage.setItem(AUTOSAVE_STORAGE_KEY, JSON.stringify(payload));
      } catch (e) {
        console.warn("[useAutoSave] Lỗi lưu tự động:", e);
      }
    }, 2500);

    return () => clearTimeout(timer);
  }, [workflow]);

  // Khôi phục bản nháp
  const restoreDraft = useCallback(() => {
    try {
      const raw = localStorage.getItem(AUTOSAVE_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed?.workflow) {
          setWorkflow(parsed.workflow);
          setHasDraft(false);
          return true;
        }
      }
    } catch (e) {
      console.error("[useAutoSave] Lỗi khôi phục bản nháp:", e);
    }
    return false;
  }, [setWorkflow]);

  // Xóa / Bỏ qua bản nháp
  const discardDraft = useCallback(() => {
    try {
      localStorage.removeItem(AUTOSAVE_STORAGE_KEY);
      setHasDraft(false);
      setDraftMeta(null);
    } catch (e) {
      console.warn("[useAutoSave] Lỗi xóa bản nháp:", e);
    }
  }, []);

  return {
    hasDraft,
    draftMeta,
    restoreDraft,
    discardDraft,
  };
}
