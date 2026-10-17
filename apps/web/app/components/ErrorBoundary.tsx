"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary caught an error]", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[400px] w-full flex items-center justify-center p-6 bg-slate-950/80 rounded-2xl border border-red-500/20 backdrop-blur-md">
          <div className="max-w-md w-full text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 text-red-400 border border-red-500/30">
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
              <h3 className="text-xl font-bold text-white tracking-wide">
                Đã xảy ra sự cố không mong muốn
              </h3>
              <p className="text-sm text-slate-400">
                Giao diện gặp lỗi trong quá trình xử lý. Bạn có thể thử khôi phục lại hoặc tải lại trang.
              </p>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/20 transition-all cursor-pointer"
              >
                Thử lại
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-all cursor-pointer"
              >
                Tải lại trang
              </button>
            </div>

            {this.state.error && (
              <div className="pt-4 text-left border-t border-slate-800">
                <button
                  onClick={() =>
                    this.setState((prev) => ({ showDetails: !prev.showDetails }))
                  }
                  className="text-xs text-slate-500 hover:text-slate-400 underline cursor-pointer"
                >
                  {this.state.showDetails ? "Ẩn chi tiết kỹ thuật" : "Xem chi tiết lỗi"}
                </button>

                {this.state.showDetails && (
                  <div className="mt-2 p-3 bg-slate-900 rounded-lg text-xs font-mono text-red-300 overflow-x-auto max-h-48 border border-red-950">
                    <p className="font-bold">{this.state.error.name}: {this.state.error.message}</p>
                    {this.state.errorInfo?.componentStack && (
                      <pre className="mt-2 text-slate-500 whitespace-pre-wrap text-[11px]">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
