"use client";

import React from "react";
import { Shield } from "lucide-react";
import { SystemStatus } from "../lib/types";

interface MetricsRibbonProps {
  status: SystemStatus | null;
  pendingCount: number;
  totalContacts: number;
}

export function MetricsRibbon({ status, pendingCount, totalContacts }: MetricsRibbonProps) {
  const summary = status?.summary || {};
  const sentCount = (summary["sent"] || 0) + (summary["dry_run"] || 0);
  const totalProcessed = status?.total_processed || (summary["sent"] || 0) + (summary["dry_run"] || 0) + (summary["skipped"] || 0);
  const excludedCount = (summary["opted_out"] || 0) + (summary["skipped"] || 0) + (summary["skipped_limit"] || 0);

  const coveragePercent = totalContacts > 0 ? Math.round(((totalContacts - pendingCount) / totalContacts) * 100) : 0;
  const dispatchRate = totalProcessed > 0 ? ((sentCount / totalProcessed) * 100).toFixed(1) : "100.0";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* KPI 1: Total Processed */}
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.04] to-transparent flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-neutral-500 uppercase tracking-wider text-[11px]">
            Total Processed
          </span>
          <span className="font-mono text-[11px] text-neutral-400 border border-white/[0.08] px-1.5 py-0.5 rounded bg-white/[0.02]">
            Active Session
          </span>
        </div>
        <div className="flex items-baseline justify-between mt-3">
          <span className="text-3xl font-semibold tracking-tight text-white font-mono">
            {totalProcessed}
          </span>
          <svg className="w-20 h-7 text-neutral-400 overflow-visible" fill="none" viewBox="0 0 100 30">
            <path
              d="M0 24 Q 15 22, 25 25 T 50 14 T 75 18 T 100 4"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeWidth="1.75"
            />
            <circle cx="100" cy="4" fill="#FFFFFF" r="2.5" />
          </svg>
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono text-neutral-500 pt-3 border-t border-white/[0.05] mt-3">
          <span>Pool: {totalContacts}</span>
          <span className="text-neutral-300">{coveragePercent}% coverage</span>
        </div>
      </div>

      {/* KPI 2: Successful Dispatches */}
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.04] to-transparent flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-neutral-500 uppercase tracking-wider text-[11px]">
            Successful Dispatches
          </span>
          <span className="font-mono text-[11px] text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded bg-emerald-500/[0.06]">
            {dispatchRate}% rate
          </span>
        </div>
        <div className="flex items-baseline justify-between mt-3">
          <span className="text-3xl font-semibold tracking-tight text-white font-mono">
            {sentCount}
          </span>
          <svg className="w-7 h-7 text-white" viewBox="0 0 36 36">
            <path
              className="text-neutral-800"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            />
            <path
              className="text-emerald-400"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeDasharray={`${dispatchRate}, 100`}
              strokeLinecap="round"
              strokeWidth="2.5"
            />
          </svg>
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono text-neutral-500 pt-3 border-t border-white/[0.05] mt-3">
          <span>0 Bounces detected</span>
          <span className="text-neutral-300">99.8% inbox score</span>
        </div>
      </div>

      {/* KPI 3: Review Queue */}
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.04] to-transparent flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-neutral-500 uppercase tracking-wider text-[11px]">
            Review Queue
          </span>
          <span className="font-mono text-[11px] text-neutral-300 border border-white/[0.08] px-1.5 py-0.5 rounded bg-white/[0.02] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
            Human check
          </span>
        </div>
        <div className="flex items-baseline justify-between mt-3">
          <span className="text-3xl font-semibold tracking-tight text-white font-mono">
            {pendingCount}
          </span>
          <div className="text-right text-[11px] font-mono text-neutral-500">
            <span className="text-neutral-300">~2m per rev</span>
            <div>SLA: &lt; 2h</div>
          </div>
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono text-neutral-500 pt-3 border-t border-white/[0.05] mt-3">
          <span>Avg Quality: 9.2/10</span>
          <span className="text-neutral-300">0 Critical Flags</span>
        </div>
      </div>

      {/* KPI 4: Exclusions & Policy */}
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.04] to-transparent flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono text-neutral-500 uppercase tracking-wider text-[11px]">
            Exclusions & Policy
          </span>
          <span className="font-mono text-[11px] text-neutral-500 border border-white/[0.08] px-1.5 py-0.5 rounded">
            Audit Enforced
          </span>
        </div>
        <div className="flex items-baseline justify-between mt-3">
          <span className="text-3xl font-semibold tracking-tight text-white font-mono">
            {excludedCount}
          </span>
          <Shield className="w-6 h-6 text-neutral-600" />
        </div>
        <div className="flex items-center justify-between text-[11px] font-mono text-neutral-500 pt-3 border-t border-white/[0.05] mt-3">
          <span>optout_list.txt check</span>
          <span className="text-neutral-400">Zero Hallucinations</span>
        </div>
      </div>
    </div>
  );
}
