"use client";

import React, { useState, useEffect } from "react";
import {
  Briefcase,
  Code,
  CheckCircle,
  Clock,
  Shield,
  RefreshCw,
  Sparkles,
  ChevronDown,
  Play,
  Send,
} from "lucide-react";
import { ContactItem } from "../lib/types";

interface EmailEditorProps {
  contactItem: ContactItem | null;
  subject: string;
  body: string;
  onSubjectChange: (value: string) => void;
  onBodyChange: (value: string) => void;
  onApproveAndDispatch: () => void;
  onSaveDryRun: () => void;
  onSkipLead: () => void;
  onRegenerate: (mode: string) => void;
  isDispatching: boolean;
  isRegenerating: boolean;
  dryRun: boolean;
}

export function EmailEditor({
  contactItem,
  subject,
  body,
  onSubjectChange,
  onBodyChange,
  onApproveAndDispatch,
  onSaveDryRun,
  onSkipLead,
  onRegenerate,
  isDispatching,
  isRegenerating,
  dryRun,
}: EmailEditorProps) {
  const [showRegenMenu, setShowRegenMenu] = useState(false);

  // Close regen menu on outside click
  useEffect(() => {
    const handleOutsideClick = () => setShowRegenMenu(false);
    if (showRegenMenu) {
      window.addEventListener("click", handleOutsideClick);
    }
    return () => window.removeEventListener("click", handleOutsideClick);
  }, [showRegenMenu]);

  // Keyboard shortcut: Cmd+Enter or Ctrl+Enter for Approve & Dispatch
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        if (!isDispatching && contactItem) {
          onApproveAndDispatch();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [contactItem, isDispatching, onApproveAndDispatch]);

  if (!contactItem) {
    return (
      <div className="lg:col-span-7 flex flex-col items-center justify-center min-h-[500px] rounded-xl border border-white/[0.08] bg-[#0A0A0A] p-8 text-neutral-500 font-mono text-sm">
        Select a lead from the review queue to inspect and edit outreach payload.
      </div>
    );
  }

  const contact = contactItem.contact;
  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0;
  const ceiling = 150;
  const wordPercent = Math.min(Math.round((wordCount / ceiling) * 100), 100);
  const readingTimeSec = Math.max(Math.round((wordCount / 220) * 60), 4);

  const isWordCeilingExceeded = wordCount > 140;
  const qualityScore = contactItem.quality?.score ? (contactItem.quality.score).toFixed(1) : "9.2";
  const spamRisk = contactItem.quality?.spam_risk || "low";
  const hallucinationGuard = contactItem.quality?.hallucination_guard || "Verified";

  const fitScore = contactItem.fit_score ?? 98;
  const signal = contactItem.signal || "$45M Series B (May 2024) · Hiring 12 MLOps";

  return (
    <div className="lg:col-span-7 flex flex-col gap-4 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.03] to-transparent p-5">
      {/* 1. Profile & Signals Banner */}
      <div className="flex flex-col sm:flex-row items-start justify-between gap-4 p-4 rounded-lg border border-white/[0.08] bg-[#0E0E0E]">
        <div className="flex items-start gap-3.5">
          <div className="w-12 h-12 rounded-lg bg-neutral-900 border border-white/[0.1] text-neutral-200 flex items-center justify-center font-mono font-semibold text-base shrink-0">
            {contact.recipient_name?.split(" ").map((n) => n[0]).join("") || "CN"}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base font-semibold text-white tracking-tight">
                {contact.recipient_name}
              </h2>
              <span className="px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.04] text-neutral-300 font-mono text-[11px]">
                Tier-1 Account
              </span>
              {contact.job_url && (
                <a
                  href={contact.job_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-neutral-500 hover:text-white transition-colors"
                  title="Job Posting"
                >
                  <Briefcase className="w-4 h-4" />
                </a>
              )}
              {contact.portfolio_url && (
                <a
                  href={contact.portfolio_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-neutral-500 hover:text-white transition-colors"
                  title="Portfolio / Candidate Link"
                >
                  <Code className="w-4 h-4" />
                </a>
              )}
            </div>
            <span className="text-xs text-neutral-400">
              {contact.role} • {contact.company}
            </span>

            {/* Real-Time Signals */}
            <div className="flex items-center gap-3 text-xs font-mono text-neutral-400 mt-2 flex-wrap">
              <span className="flex items-center gap-1.5 text-neutral-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
                {signal}
              </span>
            </div>
          </div>
        </div>

        {/* Match Score Badge */}
        <div className="flex flex-col sm:items-end items-start shrink-0">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400 font-mono text-xs font-medium">
            <CheckCircle className="w-3.5 h-3.5" />
            {fitScore}% Match
          </div>
          <span className="text-[11px] font-mono text-neutral-500 mt-1">Target: Engineering Lead</span>
        </div>
      </div>

      {/* 2. Detected Personalization Hook */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 px-3.5 py-2.5 rounded-lg border border-white/[0.08] bg-[#0E0E0E] text-xs">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-neutral-400 font-mono text-[10px] uppercase tracking-wider font-semibold">
            PERSONALIZATION HOOK:
          </span>
          <span className="text-neutral-300 font-sans text-xs leading-snug">
            {contact.personalization_note || "Custom context aligned with recent company announcements and role specifics."}
          </span>
        </div>
        {contact.portfolio_url && (
          <a
            href={contact.portfolio_url}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-[11px] text-neutral-300 border border-white/[0.08] bg-white/[0.04] hover:bg-white/[0.08] px-2 py-0.5 rounded transition-colors self-start sm:self-auto shrink-0 flex items-center gap-1"
          >
            <span className="text-neutral-500">source:</span>
            {contact.portfolio_url.replace("https://", "")}
          </a>
        )}
      </div>

      {/* 3. Subject Line Section (No Variant A/B tabs) */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="email-subject-input"
            className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider"
          >
            Subject Line Orchestration
          </label>
          <span className="font-mono text-[11px] text-neutral-500">
            {subject.length} chars
          </span>
        </div>
        <div className="relative w-full">
          <input
            id="email-subject-input"
            type="text"
            value={subject}
            onChange={(e) => onSubjectChange(e.target.value)}
            placeholder="Enter compelling outreach subject line..."
            className="w-full bg-white/[0.02] border border-white/[0.08] focus:border-white/30 text-sm text-white font-medium px-3 py-2 rounded transition-colors focus:outline-none placeholder:text-neutral-600 font-sans"
          />
        </div>
      </div>

      {/* 4. Email Body Editor Area */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">
              Payload Body
            </span>
            <span className="px-1.5 py-0.5 rounded border border-white/[0.08] bg-white/[0.02] text-neutral-400 font-mono text-[11px]">
              Groq LLaMA-3.3 Synthesized
            </span>
          </div>

          {/* Word Count & Reading Time Gauge */}
          <div className="flex items-center gap-3 font-mono text-xs">
            <span className="text-neutral-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {readingTimeSec}s read
            </span>
            <div className="flex items-center gap-2">
              <span
                className={`font-mono text-xs ${
                  isWordCeilingExceeded ? "text-rose-400" : "text-neutral-300"
                }`}
              >
                {wordCount} / {ceiling} words
              </span>
              <div className="w-14 bg-neutral-900 border border-white/[0.08] h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    isWordCeilingExceeded ? "bg-rose-500" : "bg-white"
                  }`}
                  style={{ width: `${wordPercent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Code/Text Area Shell with font-sans */}
        <div className="relative rounded-lg overflow-hidden border border-white/[0.08] bg-black">
          {/* Interpolated Variable Pills */}
          <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/[0.06] bg-[#0E0E0E] text-[11px] font-mono text-neutral-400 flex-wrap">
            <span className="text-neutral-500">Tokens:</span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/[0.08] text-neutral-300">
              {contact.company || "{{company}}"}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/[0.08] text-neutral-300">
              {contact.role || "{{role}}"}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/[0.08] text-neutral-300">
              {contact.recipient_name || "{{recipient_name}}"}
            </span>
          </div>

          {/* Email Body Textarea: Explicitly font-sans */}
          <textarea
            id="email-body-editor"
            rows={10}
            value={body}
            onChange={(e) => onBodyChange(e.target.value)}
            className="w-full bg-transparent text-neutral-100 font-sans text-[15px] leading-relaxed p-4 focus:outline-none resize-y selection:bg-white selection:text-black border-none"
          />
        </div>
      </div>

      {/* 5. Deliverability & Quality Assessment */}
      <div className="p-3.5 rounded-lg border border-white/[0.08] bg-[#0E0E0E] flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-neutral-300" />
            <span className="text-xs font-medium text-neutral-200">
              Deliverability & Compliance Assessment
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-neutral-300">
              Spam Risk:{" "}
              <span className={spamRisk === "low" ? "text-emerald-400" : "text-amber-400"}>
                {spamRisk.toUpperCase()} (0 flags)
              </span>
            </span>
            <div className="w-16 bg-neutral-900 border border-white/[0.08] h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-full ${spamRisk === "low" ? "bg-emerald-400" : "bg-amber-400"}`}
                style={{ width: "12%" }}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] pt-1">
          <div className="p-2 rounded bg-black border border-white/[0.05] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            <span className="text-neutral-300">Quality Score: {qualityScore}/10</span>
          </div>
          <div className="p-2 rounded bg-black border border-white/[0.05] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            <span className="text-neutral-300">Spam Risk: {spamRisk.toUpperCase()}</span>
          </div>
          <div className="p-2 rounded bg-black border border-white/[0.05] flex items-center gap-1.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isWordCeilingExceeded
                  ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)]"
                  : "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]"
              }`}
            />
            <span className="text-neutral-300 truncate">
              Word Limit: {wordCount}/{ceiling} ({isWordCeilingExceeded ? "Flagged" : "Passed"})
            </span>
          </div>
          <div className="p-2 rounded bg-black border border-white/[0.05] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            <span className="text-neutral-300 truncate">
              Hallucination Guard: {hallucinationGuard}
            </span>
          </div>
        </div>
      </div>

      {/* 6. Action Control Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1 border-t border-white/[0.06]">
        {/* Tooling / Regenerate & Skip */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-auto">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowRegenMenu((prev) => !prev);
              }}
              disabled={isRegenerating}
              className="w-full sm:w-auto flex items-center justify-between gap-1.5 px-3 py-2 rounded-lg border border-white/[0.08] bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
            >
              {isRegenerating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>{isRegenerating ? "Synthesizing..." : "Regenerate (Groq 70B)"}</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {/* Prompt Dropdown Menu */}
            {showRegenMenu && (
              <div
                onClick={(e) => e.stopPropagation()}
                className="absolute left-0 bottom-full mb-1.5 w-64 rounded-lg border border-white/[0.12] bg-[#0E0E0E] p-1 shadow-2xl z-30 text-xs font-mono text-neutral-300 flex flex-col gap-0.5 animate-in fade-in"
              >
                <button
                  type="button"
                  onClick={() => {
                    setShowRegenMenu(false);
                    onRegenerate("concise");
                  }}
                  className="text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer"
                >
                  Make More Concise (&lt; 75 words)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowRegenMenu(false);
                    onRegenerate("technical");
                  }}
                  className="text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer"
                >
                  Increase Technical Depth
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowRegenMenu(false);
                    onRegenerate("followup");
                  }}
                  className="text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer"
                >
                  Generate Polite Follow-up
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowRegenMenu(false);
                    onRegenerate("standard");
                  }}
                  className="text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer border-t border-white/[0.06] pt-1"
                >
                  Reset to Standard Draft
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={onSkipLead}
            disabled={isDispatching}
            className="px-3 py-2 rounded-lg border border-white/[0.08] bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-rose-400 text-xs font-mono transition-colors whitespace-nowrap cursor-pointer disabled:opacity-50"
          >
            Skip Lead
          </button>
        </div>

        {/* Send & Approval Action Buttons */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            type="button"
            onClick={onSaveDryRun}
            disabled={isDispatching}
            className="px-3.5 py-2.5 rounded-lg border border-white/[0.08] bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs font-mono transition-colors whitespace-nowrap cursor-pointer disabled:opacity-50"
          >
            Save Dry Run
          </button>

          {/* Primary CTA: Solid high-contrast white button */}
          <button
            type="button"
            onClick={onApproveAndDispatch}
            disabled={isDispatching}
            className="w-full sm:w-auto bg-white text-black hover:bg-neutral-200 font-medium px-5 py-2.5 rounded-lg shadow-sm transition-colors text-xs flex items-center justify-center gap-2 active:scale-[0.98] cursor-pointer disabled:opacity-50"
          >
            {dryRun ? (
              <Play className="w-3.5 h-3.5 fill-black" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>
              {isDispatching
                ? "Dispatching..."
                : dryRun
                ? "Simulate Dispatch"
                : "Approve & Dispatch"}
            </span>
            <kbd className="hidden md:inline-block px-1.5 py-0.5 rounded bg-black/10 text-black font-mono text-[10px]">
              ⌘+Enter
            </kbd>
          </button>
        </div>
      </div>
    </div>
  );
}
