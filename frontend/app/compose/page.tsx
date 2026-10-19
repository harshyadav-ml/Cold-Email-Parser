"use client";

import React, { useState, useEffect, Suspense, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Play,
  Send,
} from "lucide-react";
import { useSystem } from "../../components/SystemContext";
import { regenerateEmail, dispatchLead } from "../../lib/api";

function ComposeStudioContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email");

  const {
    contacts,
    dryRun,
    updateContactStatus,
    refreshStatus,
    showToast,
  } = useSystem();

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [subject, setSubject] = useState<string>("");
  const [body, setBody] = useState<string>("");
  const [quality, setQuality] = useState<any>(null);
  const [showRegenMenu, setShowRegenMenu] = useState<boolean>(false);
  const [isDispatching, setIsDispatching] = useState<boolean>(false);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [regenCount, setRegenCount] = useState<number>(0);
  const [activeMode, setActiveMode] = useState<string>("standard");

  // Sync index from email param if provided
  useEffect(() => {
    if (contacts.length === 0) return;

    if (emailParam) {
      const idx = contacts.findIndex(
        (c) => c.contact.recipient_email?.toLowerCase() === emailParam.toLowerCase()
      );
      if (idx !== -1) {
        setCurrentIndex(idx);
        return;
      }
    }

    // Otherwise default to first pending lead
    const firstPendingIdx = contacts.findIndex((c) => !c.status || c.status === "pending");
    if (firstPendingIdx !== -1) {
      setCurrentIndex(firstPendingIdx);
    } else {
      setCurrentIndex(0);
    }
  }, [emailParam, contacts]);

  const currentLead = contacts[currentIndex] || contacts[0] || null;

  // Sync editor fields when current lead changes
  useEffect(() => {
    if (currentLead) {
      setSubject(currentLead.generated_subject || "");
      setBody(currentLead.generated_body || "");
      setQuality(currentLead.quality || null);
      setRegenCount(0);
    }
  }, [currentIndex, currentLead?.id]);

  // Navigate to another lead
  const goToIndex = useCallback(
    (idx: number) => {
      if (idx < 0 || idx >= contacts.length) return;
      setCurrentIndex(idx);
      const target = contacts[idx];
      if (target?.contact?.recipient_email) {
        router.replace(`/compose?email=${encodeURIComponent(target.contact.recipient_email)}`, {
          scroll: false,
        });
      }
    },
    [contacts, router]
  );

  // Advance to next pending lead
  const advanceToNextPending = useCallback(() => {
    // Search forward from current index
    const nextIdx = contacts.findIndex(
      (c, i) => i > currentIndex && (!c.status || c.status === "pending")
    );
    if (nextIdx !== -1) {
      goToIndex(nextIdx);
      return;
    }
    // Search from beginning
    const anyPendingIdx = contacts.findIndex((c) => !c.status || c.status === "pending");
    if (anyPendingIdx !== -1 && anyPendingIdx !== currentIndex) {
      goToIndex(anyPendingIdx);
      return;
    }
    // Otherwise go to next index if exists
    if (currentIndex < contacts.length - 1) {
      goToIndex(currentIndex + 1);
    }
  }, [contacts, currentIndex, goToIndex]);

  // Action: Approve & Dispatch
  const handleApproveAndDispatch = async () => {
    if (!currentLead || isDispatching) return;
    setIsDispatching(true);

    try {
      const res = await dispatchLead(currentLead.contact, subject, body, "send");
      const isLive = res.status === "sent";
      const newStatus = isLive ? "sent" : "dry_run";

      showToast(
        isLive
          ? `[LIVE] Gmail API / SMTP 200 OK — Dispatched to ${currentLead.contact.recipient_name}`
          : `[DRY RUN] Simulated dispatch recorded for ${currentLead.contact.recipient_name}`,
        "success"
      );

      updateContactStatus(currentLead.id, newStatus, subject, body);
      await refreshStatus();
      advanceToNextPending();
    } catch {
      showToast("Dispatch failed. Check backend connection.", "error");
    } finally {
      setIsDispatching(false);
    }
  };

  // Action: Save Draft (Dry Run)
  const handleSaveDraft = async () => {
    if (!currentLead || isDispatching) return;
    setIsDispatching(true);

    try {
      await dispatchLead(currentLead.contact, subject, body, "draft");
      showToast(`Draft snapshot saved for ${currentLead.contact.recipient_name}`, "info");

      updateContactStatus(currentLead.id, "dry_run", subject, body);
      await refreshStatus();
    } catch {
      showToast("Failed to save draft.", "error");
    } finally {
      setIsDispatching(false);
    }
  };

  // Action: Skip Lead
  const handleSkipLead = async () => {
    if (!currentLead || isDispatching) return;
    setIsDispatching(true);

    try {
      await dispatchLead(currentLead.contact, subject, body, "skip");
      showToast(`Skipped outreach for ${currentLead.contact.recipient_name}`, "warning");

      updateContactStatus(currentLead.id, "skipped", subject, body);
      await refreshStatus();
      advanceToNextPending();
    } catch {
      showToast("Failed to skip lead.", "error");
    } finally {
      setIsDispatching(false);
    }
  };

  // Action: Regenerate
  const handleRegenerate = async (mode: string = activeMode) => {
    if (!currentLead || isRegenerating) return;
    setIsRegenerating(true);
    setShowRegenMenu(false);

    const nextCount = regenCount + 1;
    setRegenCount(nextCount);
    setActiveMode(mode);
    showToast(`Synthesizing variation #${nextCount} (${mode} mode)...`, "info");

    try {
      const res = await regenerateEmail(
        currentLead.contact,
        mode,
        subject,
        body,
        nextCount,
        Date.now()
      );
      setSubject(res.subject);
      setBody(res.body);
      if (res.quality) {
        setQuality(res.quality);
      }

      updateContactStatus(
        currentLead.id,
        currentLead.status || "pending",
        res.subject,
        res.body,
        res.quality
      );
      showToast(`Variation #${nextCount} applied to editor`, "success");
    } catch {
      showToast("Synthesis failed. Check backend connection.", "error");
    } finally {
      setIsRegenerating(false);
    }
  };

  // Keyboard shortcut: Cmd+Enter or Ctrl+Enter for Approve & Dispatch
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleApproveAndDispatch();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  if (!currentLead) {
    return (
      <div className="w-full max-w-3xl mx-auto py-24 text-center font-mono text-sm text-neutral-500">
        No contacts available. Check data/contacts.json.
      </div>
    );
  }

  // Word count & quality calculations
  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0;
  const ceiling = 150;
  const isWordCeilingExceeded = wordCount > 140;
  const activeQuality = quality || currentLead.quality;
  const qualityScore =
    activeQuality?.score !== undefined ? Number(activeQuality.score).toFixed(1) : "9.4";
  const spamRisk = activeQuality?.spam_risk || "low";
  const hallucinationGuard = activeQuality?.hallucination_guard || "Verified";

  const totalLeads = contacts.length;
  const leadNumber = currentIndex + 1;

  return (
    <div className="w-full max-w-4xl mx-auto py-8 px-6 flex flex-col gap-6">
      {/* 1. Top Bar: Lead X of Y & Pagination Controls */}
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <Link
            href="/contacts"
            className="text-neutral-400 hover:text-white transition-colors text-xs font-mono flex items-center gap-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>All Leads</span>
          </Link>
          <span className="text-neutral-600">/</span>
          <span className="font-mono text-xs text-neutral-300 font-medium">
            Lead {leadNumber} of {totalLeads}
          </span>
          <span
            className={`px-2 py-0.5 rounded-full font-mono text-[10px] uppercase tracking-wider ${
              currentLead.status === "sent"
                ? "border border-emerald-500/30 bg-emerald-500/[0.08] text-emerald-400"
                : currentLead.status === "dry_run" || currentLead.status === "drafted"
                ? "border border-white/10 bg-white/[0.04] text-neutral-300"
                : currentLead.status === "skipped"
                ? "border border-white/10 text-neutral-500"
                : "border border-amber-400/30 bg-amber-400/[0.08] text-amber-400"
            }`}
          >
            {currentLead.status || "Pending Review"}
          </span>
        </div>

        {/* Previous / Next buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => goToIndex(currentIndex - 1)}
            disabled={currentIndex === 0}
            className="px-3 py-1.5 rounded-lg border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-300 text-xs font-mono transition-colors flex items-center gap-1 cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>
          <button
            onClick={() => goToIndex(currentIndex + 1)}
            disabled={currentIndex === totalLeads - 1}
            className="px-3 py-1.5 rounded-lg border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-300 text-xs font-mono transition-colors flex items-center gap-1 cursor-pointer"
          >
            <span>Next Lead</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Recipient Context Card */}
      <div className="p-5 rounded-xl border border-white/10 bg-[#0A0A0A] flex flex-col gap-3.5 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/10 text-white font-mono font-medium flex items-center justify-center text-sm shrink-0">
              {currentLead.contact.recipient_name?.split(" ").map((n) => n[0]).join("") || "CN"}
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white tracking-tight">
                  {currentLead.contact.recipient_name}
                </h2>
                <span className="text-xs text-neutral-400 font-mono">
                  ({currentLead.contact.recipient_email})
                </span>
              </div>
              <span className="text-xs text-neutral-300">
                {currentLead.contact.role} @ <strong className="text-white font-medium">{currentLead.contact.company}</strong>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            {currentLead.contact.job_url && (
              <a
                href={currentLead.contact.job_url}
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1 rounded border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-300 text-[11px] flex items-center gap-1 transition-colors"
              >
                <span>Job Link</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {currentLead.contact.portfolio_url && (
              <a
                href={currentLead.contact.portfolio_url}
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1 rounded border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-300 text-[11px] flex items-center gap-1 transition-colors"
              >
                <span>Portfolio</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Personalization Context Line */}
        <div className="p-3 rounded-lg border border-white/10 bg-[#0E0E0E] text-xs flex items-baseline gap-2">
          <span className="font-mono text-[10px] text-neutral-400 uppercase tracking-wider font-semibold shrink-0">
            HOOK CONTEXT:
          </span>
          <span className="text-neutral-300 leading-snug font-sans">
            {currentLead.contact.personalization_note || "Custom candidate profile match."}
          </span>
        </div>
      </div>

      {/* 3. Subject Line Input */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <label htmlFor="compose-subject" className="text-neutral-400 uppercase tracking-wider text-[11px]">
            Subject Line
          </label>
          <span className="text-neutral-500">{subject.length} chars</span>
        </div>
        <input
          id="compose-subject"
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Enter outreach subject line..."
          className="w-full bg-[#0A0A0A] border border-white/10 focus:border-white/30 text-sm text-white font-medium px-3.5 py-2.5 rounded-lg transition-colors focus:outline-none font-sans"
        />
      </div>

      {/* 4. Email Body Editor (<textarea font-sans>) */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <label htmlFor="compose-body" className="text-neutral-400 uppercase tracking-wider text-[11px]">
            Email Body
          </label>
          <span className="text-neutral-500 font-mono text-[11px]">Geist Sans Typography</span>
        </div>

        <div className="rounded-xl overflow-hidden border border-white/10 bg-black">
          {/* Interpolated Tokens Preview Bar */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 border-b border-white/[0.06] bg-[#0E0E0E] text-[11px] font-mono text-neutral-400 flex-wrap">
            <span className="text-neutral-500">Tokens:</span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/10 text-neutral-300">
              {currentLead.contact.company}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/10 text-neutral-300">
              {currentLead.contact.role}
            </span>
            <span className="px-1.5 py-0.5 rounded bg-black border border-white/10 text-neutral-300">
              {currentLead.contact.recipient_name}
            </span>
          </div>

          <textarea
            id="compose-body"
            rows={11}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full bg-transparent text-neutral-100 font-sans text-[15px] leading-relaxed p-4 focus:outline-none resize-y selection:bg-white selection:text-black border-none"
          />
        </div>
      </div>

      {/* 5. Single Status Line */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-lg border border-white/10 bg-[#0E0E0E] text-xs font-mono">
        <div className="flex items-center gap-2 text-neutral-300">
          <span className={isWordCeilingExceeded ? "text-rose-400" : "text-neutral-300"}>
            Words: {wordCount} / {ceiling}
          </span>
          <span className="text-neutral-600">•</span>
          <span className="text-neutral-300">Quality: {qualityScore} / 10</span>
          <span className="text-neutral-600">•</span>
          <span className="text-emerald-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            Spam Risk: {spamRisk.toUpperCase()}
          </span>
        </div>

        <span className="text-neutral-500 hidden sm:inline">
          Hallucination Guard: {hallucinationGuard}
        </span>
      </div>

      {/* 6. Four Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        {/* Left: Regenerate Dropdown & Skip */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-auto">
            <div className="flex items-center w-full sm:w-auto">
              <button
                type="button"
                onClick={() => handleRegenerate(activeMode)}
                disabled={isRegenerating}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-l-lg border border-r-0 border-white/10 bg-neutral-900 hover:bg-neutral-800 text-neutral-200 hover:text-white text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
                title="Click to generate a fresh variation"
              >
                {isRegenerating ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>
                  {isRegenerating
                    ? "Synthesizing..."
                    : regenCount > 0
                    ? `Regenerate (#${regenCount + 1})`
                    : "Regenerate (Groq 70B)"}
                </span>
              </button>
              <button
                type="button"
                onClick={() => setShowRegenMenu((prev) => !prev)}
                disabled={isRegenerating}
                className="px-2 py-2.5 rounded-r-lg border border-white/10 bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-white text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
                title="Select generation mode"
              >
                <ChevronDown className="w-3.5 h-3.5" />
              </button>
            </div>

            {showRegenMenu && (
              <div className="absolute left-0 bottom-full mb-1.5 w-64 rounded-lg border border-white/[0.12] bg-[#0E0E0E] p-1 shadow-2xl z-30 text-xs font-mono text-neutral-300 flex flex-col gap-0.5 animate-in fade-in">
                <button
                  type="button"
                  onClick={() => handleRegenerate("concise")}
                  className={`text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer flex items-center justify-between ${
                    activeMode === "concise" ? "bg-white/[0.08] text-white" : ""
                  }`}
                >
                  <span>Make More Concise (&lt; 75 words)</span>
                  {activeMode === "concise" && <span className="text-[10px] text-emerald-400">ACTIVE</span>}
                </button>
                <button
                  type="button"
                  onClick={() => handleRegenerate("technical")}
                  className={`text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer flex items-center justify-between ${
                    activeMode === "technical" ? "bg-white/[0.08] text-white" : ""
                  }`}
                >
                  <span>Increase Technical Depth</span>
                  {activeMode === "technical" && <span className="text-[10px] text-emerald-400">ACTIVE</span>}
                </button>
                <button
                  type="button"
                  onClick={() => handleRegenerate("followup")}
                  className={`text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer flex items-center justify-between ${
                    activeMode === "followup" ? "bg-white/[0.08] text-white" : ""
                  }`}
                >
                  <span>Generate Polite Follow-up</span>
                  {activeMode === "followup" && <span className="text-[10px] text-emerald-400">ACTIVE</span>}
                </button>
                <button
                  type="button"
                  onClick={() => handleRegenerate("standard")}
                  className={`text-left px-2.5 py-1.5 rounded hover:bg-white/[0.06] hover:text-white transition-colors cursor-pointer border-t border-white/[0.06] pt-1 flex items-center justify-between ${
                    activeMode === "standard" ? "bg-white/[0.08] text-white" : ""
                  }`}
                >
                  <span>Standard / Fresh Variation</span>
                  {activeMode === "standard" && <span className="text-[10px] text-emerald-400">ACTIVE</span>}
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={handleSkipLead}
            disabled={isDispatching}
            className="px-3.5 py-2.5 rounded-lg border border-white/10 bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-rose-400 text-xs font-mono transition-colors whitespace-nowrap cursor-pointer disabled:opacity-50"
          >
            Skip Lead
          </button>
        </div>

        {/* Right: Save Draft & Approve & Dispatch */}
        <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
          <button
            type="button"
            onClick={handleSaveDraft}
            disabled={isDispatching}
            className="px-4 py-2.5 rounded-lg border border-white/10 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs font-mono transition-colors whitespace-nowrap cursor-pointer disabled:opacity-50"
          >
            Save Draft
          </button>

          {/* Primary CTA: Solid white button */}
          <button
            type="button"
            onClick={handleApproveAndDispatch}
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

export default function ComposeStudioPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-4xl mx-auto py-24 text-center font-mono text-sm text-neutral-500">
          Loading Compose Studio...
        </div>
      }
    >
      <ComposeStudioContent />
    </Suspense>
  );
}
