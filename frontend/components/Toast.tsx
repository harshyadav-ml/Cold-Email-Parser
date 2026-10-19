"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

export type ToastType = "info" | "success" | "warning" | "error";

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3800);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed top-20 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => {
          let dotColor = "bg-neutral-400";
          if (toast.type === "success") dotColor = "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]";
          if (toast.type === "warning") dotColor = "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]";
          if (toast.type === "error") dotColor = "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]";

          return (
            <div
              key={toast.id}
              className="p-3 rounded-lg border border-white/[0.12] bg-[#0E0E0E] shadow-2xl font-mono text-xs flex items-center gap-2.5 pointer-events-auto transform transition-all duration-300 text-white animate-in fade-in slide-in-from-top-2"
            >
              <span className={`w-2 h-2 rounded-full ${dotColor} shrink-0`} />
              <span>{toast.message}</span>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
