"use client";

import React, { useState, useEffect } from "react";
import {
  User,
  Briefcase,
  FileText,
  Globe,
  RotateCcw,
  X,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { useSystem } from "./SystemContext";
import { SenderProfile } from "../lib/types";

const DEFAULT_PROFILE: SenderProfile = {
  candidate_name: "Harsh Yadav",
  candidate_title: "AI Engineer",
  candidate_background:
    "AI Engineer specializing in agentic workflows, FastAPI, Next.js, and production LLM pipelines",
  portfolio_url: "https://github.com/harshyadav-ml",
};

export function SenderProfileModal() {
  const {
    isProfileModalOpen,
    setIsProfileModalOpen,
    senderProfile,
    updateProfile,
  } = useSystem();

  const [formData, setFormData] = useState<SenderProfile>(senderProfile || DEFAULT_PROFILE);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync form data with current sender profile when modal opens
  useEffect(() => {
    if (isProfileModalOpen) {
      setFormData(senderProfile || DEFAULT_PROFILE);
      setErrorMsg(null);
      setIsSaving(false);
    }
  }, [isProfileModalOpen, senderProfile]);

  if (!isProfileModalOpen) return null;

  const handleResetDefaults = () => {
    setFormData(DEFAULT_PROFILE);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSaving) return;

    if (!formData.candidate_name.trim()) {
      setErrorMsg("Candidate name cannot be empty.");
      return;
    }

    setIsSaving(true);
    setErrorMsg(null);

    try {
      await updateProfile(formData);
      setIsProfileModalOpen(false);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update profile and re-synthesize queue.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div
        className="bg-zinc-950 border border-white/10 rounded-xl shadow-2xl backdrop-blur-xl w-full max-w-xl flex flex-col overflow-hidden text-neutral-200 relative animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-modal-title"
      >
        {/* Modal Header */}
        <div className="p-6 pb-4 border-b border-white/10 flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-white text-black flex items-center justify-center">
                <User className="w-4 h-4 text-black" />
              </div>
              <h2 id="profile-modal-title" className="text-lg font-semibold text-white tracking-tight">
                Sender Profile & Resume Context
              </h2>
            </div>
            <p className="text-xs text-neutral-400 mt-1">
              Configure your sender identity or paste raw resume context to dynamically personalize all outreach drafts.
            </p>
          </div>

          <button
            onClick={() => setIsProfileModalOpen(false)}
            className="p-1.5 rounded-lg border border-white/10 text-neutral-400 hover:text-white hover:bg-neutral-900 transition-colors cursor-pointer"
            aria-label="Close profile modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
          {/* Identity Grid: Name & Title */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-neutral-400" />
                Full Name
              </label>
              <input
                type="text"
                required
                value={formData.candidate_name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, candidate_name: e.target.value }))
                }
                placeholder="e.g. Harsh Yadav"
                className="w-full bg-[#0E0E0E] border border-white/10 text-neutral-200 placeholder:text-neutral-600 text-xs px-3.5 py-2.5 rounded-lg focus:outline-none focus:border-white/30 transition-colors font-sans"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-neutral-400" />
                Role / Headline
              </label>
              <input
                type="text"
                required
                value={formData.candidate_title}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, candidate_title: e.target.value }))
                }
                placeholder="e.g. AI Engineer"
                className="w-full bg-[#0E0E0E] border border-white/10 text-neutral-200 placeholder:text-neutral-600 text-xs px-3.5 py-2.5 rounded-lg focus:outline-none focus:border-white/30 transition-colors font-sans"
              />
            </div>
          </div>

          {/* Portfolio / GitHub URL */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-neutral-400" />
              Portfolio / GitHub URL
            </label>
            <input
              type="url"
              value={formData.portfolio_url}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, portfolio_url: e.target.value }))
              }
              placeholder="e.g. https://github.com/harshyadav-ml"
              className="w-full bg-[#0E0E0E] border border-white/10 text-neutral-200 placeholder:text-neutral-600 text-xs px-3.5 py-2.5 rounded-lg focus:outline-none focus:border-white/30 transition-colors font-mono"
            />
          </div>

          {/* Resume & Background Summary Textarea */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-neutral-400" />
                Resume / Background Context
              </label>
              <span className="text-[10px] font-mono text-neutral-500">
                Injected into Groq LLM & templates
              </span>
            </div>
            <textarea
              rows={5}
              required
              value={formData.candidate_background}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, candidate_background: e.target.value }))
              }
              placeholder="Paste raw resume bullet points, key technical achievements, frameworks, or your bio summary here. The engine will weave this exact context into each personalized pitch..."
              className="w-full bg-[#0E0E0E] border border-white/10 text-neutral-200 placeholder:text-neutral-600 text-xs p-3.5 rounded-lg focus:outline-none focus:border-white/30 transition-colors font-sans leading-relaxed resize-y"
            />
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="p-3 rounded-lg border border-rose-500/20 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Footer Controls */}
          <div className="pt-2 flex items-center justify-between gap-3 border-t border-white/10">
            <button
              type="button"
              onClick={handleResetDefaults}
              className="text-xs font-mono text-neutral-400 hover:text-white transition-colors flex items-center gap-1.5 cursor-pointer"
              title="Reset form fields to Harsh Yadav defaults"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset to Default (Harsh Yadav)</span>
            </button>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setIsProfileModalOpen(false)}
                disabled={isSaving}
                className="px-4 py-2 rounded-lg border border-white/10 text-neutral-400 hover:text-white hover:bg-neutral-900 text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={isSaving}
                className="bg-white text-black hover:bg-neutral-200 font-medium px-5 py-2.5 rounded-lg text-xs flex items-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-lg"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-black" />
                    <span>Re-Synthesizing Queue...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 text-black" />
                    <span>Save & Re-Synthesize Queue</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
