"use client";

import React from "react";
import { WizardStep } from "../types";

export interface StepInfo {
  number: WizardStep;
  title: string;
  subtitle: string;
  statusText: string;
}

interface StepProgressBarProps {
  currentStep: WizardStep;
  completedSteps: WizardStep[];
  onStepClick: (step: WizardStep) => void;
  stepSubtitles?: { [key in WizardStep]?: string };
}

export const StepProgressBar: React.FC<StepProgressBarProps> = ({
  currentStep,
  completedSteps,
  onStepClick,
  stepSubtitles = {},
}) => {
  const steps: StepInfo[] = [
    {
      number: 1,
      title: "Kịch bản",
      subtitle: stepSubtitles[1] || (completedSteps.includes(1) ? "Đã lưu" : "Nhập & phân cảnh"),
      statusText: completedSteps.includes(1) ? "Đã lưu" : currentStep === 1 ? "Đang soạn" : "Chờ nhập",
    },
    {
      number: 2,
      title: "Storyboard",
      subtitle: stepSubtitles[2] || (completedSteps.includes(2) ? "Đã sinh ảnh" : "Vẽ tay AI"),
      statusText: completedSteps.includes(2) ? "Hoàn thành" : currentStep === 2 ? "Đang xử lý" : "Chưa tạo",
    },
    {
      number: 3,
      title: "Giọng đọc",
      subtitle: stepSubtitles[3] || (completedSteps.includes(3) ? "Đã có audio" : "Thu âm & nhạc"),
      statusText: completedSteps.includes(3) ? "Hoàn thành" : currentStep === 3 ? "Đang chọn" : "Chưa tạo",
    },
    {
      number: 4,
      title: "Xuất video",
      subtitle: stepSubtitles[4] || (completedSteps.includes(4) ? "Đã kết xuất" : "Render & QA"),
      statusText: completedSteps.includes(4) ? "Đã xuất" : currentStep === 4 ? "Sẵn sàng" : "Chờ render",
    },
  ];

  return (
    <div className="w-full bg-slate-900/60 border-b border-slate-800/80 backdrop-blur-md py-4 px-4 sm:px-8">
      <div className="max-w-4xl mx-auto flex items-center justify-between relative">
        {/* Connecting line behind step circles */}
        <div className="absolute top-1/2 left-8 right-8 -translate-y-4 h-[2px] bg-slate-800 z-0">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-indigo-500 to-indigo-600 transition-all duration-300"
            style={{
              width: `${
                completedSteps.length === 0
                  ? 0
                  : Math.min(100, ((Math.max(...completedSteps, currentStep) - 1) / 3) * 100)
              }%`,
            }}
          />
        </div>

        {/* 4 Step Items */}
        {steps.map((step) => {
          const isCompleted = completedSteps.includes(step.number);
          const isCurrent = currentStep === step.number;
          const isAccessible = isCompleted || step.number <= currentStep || isCompleted;

          return (
            <button
              key={step.number}
              id={`step-btn-${step.number}`}
              onClick={() => {
                if (isAccessible) {
                  onStepClick(step.number);
                }
              }}
              disabled={!isAccessible}
              className={`relative z-10 flex flex-col items-center group transition focus:outline-none ${
                isAccessible ? "cursor-pointer" : "cursor-not-allowed opacity-50"
              }`}
            >
              {/* Circle Badge */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-200 border-2 ${
                  isCurrent
                    ? "bg-emerald-500 border-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/30 scale-110 ring-4 ring-emerald-500/20"
                    : isCompleted
                    ? "bg-slate-900 border-emerald-500 text-emerald-400 group-hover:border-emerald-400"
                    : "bg-slate-900 border-slate-700 text-slate-400 group-hover:border-slate-600"
                }`}
              >
                {isCompleted && !isCurrent ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span>{step.number}</span>
                )}
              </div>

              {/* Step Title & Subtitle */}
              <div className="mt-2 text-center">
                <span
                  className={`block text-xs sm:text-sm font-semibold transition ${
                    isCurrent
                      ? "text-emerald-400 font-bold"
                      : isCompleted
                      ? "text-slate-200 group-hover:text-white"
                      : "text-slate-400"
                  }`}
                >
                  {step.title}
                </span>
                <span
                  className={`block text-[10px] sm:text-[11px] transition ${
                    isCurrent
                      ? "text-emerald-300/80"
                      : isCompleted
                      ? "text-slate-400"
                      : "text-slate-500"
                  }`}
                >
                  ({step.subtitle})
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
