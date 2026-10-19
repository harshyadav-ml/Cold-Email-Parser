"use client";

import React from "react";
import { Cpu, RefreshCw, Upload } from "lucide-react";
import { SystemStatus } from "../lib/types";
import { useSystem } from "./SystemContext";

interface SystemHeaderProps {
  status: SystemStatus | null;
  dryRun: boolean;
  onToggleDryRun: () => void;
  onRefresh: () => void;
  processedCount: number;
  totalCandidates: number;
}

export function SystemHeader({
  status,
  dryRun,
  onToggleDryRun,
  onRefresh,
  processedCount,
  totalCandidates,
}: SystemHeaderProps) {
  const { activeSourceFile, setIsUploadModalOpen } = useSystem();
  const progressPercent = totalCandidates > 0
    ? Math.min(Math.round((processedCount / totalCandidates) * 100), 100)
    : 0;

  const sessionLimit = status?.session_limit || "0 / 5 Live Sends";

  return (
    <div className="p-5 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.03] to-transparent flex flex-col xl:flex-row xl:items-center justify-between gap-4">
      {/* Sprint Title and Context */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 flex-wrap">
          <span className="hover:text-white transition-colors cursor-pointer">Runs</span>
          <span>/</span>
          <button
            type="button"
            onClick={() => setIsUploadModalOpen(true)}
            className="text-neutral-300 hover:text-white px-1.5 py-0.5 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] hover:border-white/30 transition-all flex items-center gap-1.5 cursor-pointer font-mono group"
            title="Click to upload or append contacts"
          >
            <Upload className="w-3 h-3 text-neutral-400 group-hover:text-white transition-colors" />
            <span>{activeSourceFile || status?.contacts_source || "data/contacts.json"}</span>
          </button>
          <span>/</span>
          <span className="text-neutral-200 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
            Human-in-the-Loop Review Queue
          </span>
        </div>


        <div className="flex items-center gap-3 mt-1 flex-wrap">
          <h1 className="text-lg font-semibold text-white tracking-tight">
            The Closer — Outreach Command
          </h1>
          <div className="h-4 w-px bg-white/[0.08] mx-1 hidden sm:block" />

          {/* Review Pipeline Gauge */}
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
              Pipeline:
            </span>
            <div className="w-32 bg-neutral-900 border border-white/[0.08] h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-white h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="text-xs font-mono text-neutral-300">
              {processedCount} / {totalCandidates}{" "}
              <span className="text-neutral-500 font-normal">({progressPercent}% cleared)</span>
            </span>
          </div>
        </div>
      </div>

      {/* Worker Telemetry Chips & Execution Switch */}
      <div className="flex items-center gap-2.5 flex-wrap self-start xl:self-auto">
        {/* Execution Mode Toggle */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg border border-white/[0.08] bg-[#0E0E0E]">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
              Mode
            </span>
            <span className="text-xs font-mono font-medium text-neutral-200">
              {dryRun ? "DRY_RUN ACTIVE" : "PRODUCTION"}
            </span>
          </div>
          <button
            aria-checked={dryRun}
            role="switch"
            type="button"
            onClick={onToggleDryRun}
            className="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full bg-neutral-800 border border-white/[0.1] p-0.5 transition-colors focus:outline-none"
          >
            <span
              className={`pointer-events-none inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200 ${
                dryRun ? "translate-x-4" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Live Sends Limit */}
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-white/[0.08] bg-[#0E0E0E]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
              Session Limit
            </span>
            <span className="text-xs font-mono text-neutral-300">{sessionLimit}</span>
          </div>
        </div>

        {/* LLM Core Spec */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/[0.08] bg-[#0E0E0E]">
          <Cpu className="w-4 h-4 text-neutral-400" />
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
              Core
            </span>
            <span className="text-xs font-mono text-neutral-300">
              {status?.llm_model || "Groq LLaMA-3.3-70B"}{" "}
              <span className="text-neutral-500">T:0.3</span>
            </span>
          </div>
        </div>

        {/* Refresh Telemetry Button */}
        <button
          onClick={onRefresh}
          className="p-2.5 rounded-lg border border-white/[0.08] bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors cursor-pointer"
          title="Refresh Agents & Queue"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
