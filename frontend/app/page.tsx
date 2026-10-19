"use client";

import React from "react";
import Link from "next/link";
import { Cpu, Gauge, RefreshCw, ArrowRight, Users, Mail, Terminal, Upload } from "lucide-react";
import { useSystem } from "../components/SystemContext";
import { MetricsRibbon } from "../components/MetricsRibbon";

export default function OverviewPage() {
  const {
    status,
    contacts,
    dryRun,
    refreshStatus,
    refreshContacts,
    activeSourceFile,
    setIsUploadModalOpen,
  } = useSystem();

  const pendingCount = contacts.filter((c) => !c.status || c.status === "pending").length;
  const processedCount = contacts.length - pendingCount;
  const clearanceRate =
    contacts.length > 0 ? Math.round((processedCount / contacts.length) * 100) : 0;

  const nextPendingLead = contacts.find((c) => !c.status || c.status === "pending") || contacts[0];

  const composeHref = nextPendingLead
    ? `/compose?email=${encodeURIComponent(nextPendingLead.contact.recipient_email)}`
    : "/compose";

  return (
    <main className="w-full max-w-[1500px] mx-auto px-6 py-8">
      <div className="flex flex-col gap-8">
        {/* 1. System Telemetry & Status Banner */}
        <div className="p-6 rounded-xl border border-white/10 bg-[#0A0A0A] bg-gradient-to-b from-white/[0.03] to-transparent flex flex-col xl:flex-row xl:items-center justify-between gap-6">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 flex-wrap">
              <span>Engine Status</span>
              <span>/</span>
              <button
                type="button"
                onClick={() => setIsUploadModalOpen(true)}
                className="text-neutral-300 hover:text-white px-2 py-0.5 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] hover:border-white/30 transition-all flex items-center gap-1.5 cursor-pointer font-mono group"
                title="Click to upload or append contacts"
              >
                <Upload className="w-3.5 h-3.5 text-neutral-400 group-hover:text-white transition-colors" />
                <span>{activeSourceFile || "data/contacts.json"}</span>
              </button>
              <span>/</span>
              <span className="text-neutral-200 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
                Human-in-the-Loop Orchestration
              </span>
            </div>


            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <h1 className="text-2xl font-semibold text-white tracking-tight">
                The Closer — Outreach Command
              </h1>
              <span
                className={`text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full border ${
                  dryRun
                    ? "border-amber-400/30 bg-amber-400/10 text-amber-300"
                    : "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                }`}
              >
                {dryRun ? "SIMULATION MODE" : "LIVE DISPATCH"}
              </span>
            </div>
          </div>

          {/* Telemetry Chips & Refresh */}
          <div className="flex items-center gap-3 flex-wrap self-start xl:self-auto">
            <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-white/10 bg-[#0E0E0E]">
              <Cpu className="w-4 h-4 text-neutral-400" />
              <div className="flex flex-col">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
                  Model
                </span>
                <span className="text-xs font-mono text-neutral-300">
                  {status?.llm_model || "Groq LLaMA-3.3-70B"}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-white/10 bg-[#0E0E0E]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
              <div className="flex flex-col">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
                  Transport
                </span>
                <span className="text-xs font-mono text-neutral-300">
                  {status?.send_method_label || "Gmail API / SMTP"}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-white/10 bg-[#0E0E0E]">
              <Gauge className="w-4 h-4 text-neutral-400" />
              <div className="flex flex-col">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
                  Session Limit
                </span>
                <span className="text-xs font-mono text-neutral-300">
                  {status?.session_limit || "0 / 5 Live Sends"}
                </span>
              </div>
            </div>

            <button
              onClick={() => {
                refreshStatus();
                refreshContacts();
              }}
              className="p-2.5 rounded-lg border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors cursor-pointer"
              title="Refresh Telemetry"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* 2. KPI Metric Cards */}
        <MetricsRibbon
          status={status}
          pendingCount={pendingCount}
          totalContacts={contacts.length}
        />

        {/* 3. Center Quick Start Card */}
        <div className="p-8 rounded-xl border border-white/10 bg-[#0A0A0A] bg-gradient-to-b from-white/[0.04] to-transparent flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
          <div className="flex flex-col gap-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
              <span className="text-xs font-mono text-amber-400 uppercase tracking-wider">
                Review Queue Priority
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white tracking-tight">
              {pendingCount > 0
                ? `${pendingCount} Candidate Leads Awaiting Review`
                : "All Leads in Queue Cleared!"}
            </h2>
            <p className="text-sm text-neutral-400 leading-relaxed font-sans">
              Each draft has been pre-synthesized with strict word count gates (&lt;150 words),
              hallucination defense checks, and personalized hook context. Step through candidates in
              the distraction-free studio.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <Link
              href={composeHref}
              className="bg-white text-black hover:bg-neutral-200 font-medium px-6 py-3 rounded-lg shadow-lg text-sm flex items-center gap-2 transition-all active:scale-[0.98] cursor-pointer"
            >
              <span>Start Reviewing Queue</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              className="px-4 py-3 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-white text-sm font-mono flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4 text-neutral-300" />
              <span>Upload Contacts (.JSON / .CSV)</span>
            </button>

            <Link
              href="/contacts"
              className="px-4 py-3 rounded-lg border border-white/10 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white text-sm font-mono transition-colors"
            >
              Directory ({contacts.length})
            </Link>
          </div>
        </div>

        {/* 4. Quick Architecture & Feature Split */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Link
            href="/contacts"
            className="p-5 rounded-xl border border-white/10 bg-[#0A0A0A] hover:border-white/20 transition-all flex flex-col justify-between group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                Module 01
              </span>
              <Users className="w-5 h-5 text-neutral-500 group-hover:text-white transition-colors" />
            </div>
            <div className="mt-4">
              <h3 className="text-base font-semibold text-white">Contacts Directory</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Filter and inspect candidates, fit scores, and verify automated opt-out list flags.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-white/[0.06] text-xs font-mono text-neutral-400 flex items-center justify-between">
              <span>{contacts.length} Records Loaded</span>
              <span className="group-hover:translate-x-0.5 transition-transform">Inspect →</span>
            </div>
          </Link>

          <Link
            href="/compose"
            className="p-5 rounded-xl border border-white/10 bg-[#0A0A0A] hover:border-white/20 transition-all flex flex-col justify-between group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                Module 02
              </span>
              <Mail className="w-5 h-5 text-neutral-500 group-hover:text-white transition-colors" />
            </div>
            <div className="mt-4">
              <h3 className="text-base font-semibold text-white">Distraction-Free Studio</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Single-lead compose view with multi-variant regeneration, dry-run simulation, and live dispatch.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-white/[0.06] text-xs font-mono text-neutral-400 flex items-center justify-between">
              <span>{pendingCount} Pending</span>
              <span className="group-hover:translate-x-0.5 transition-transform">Compose →</span>
            </div>
          </Link>

          <Link
            href="/logs"
            className="p-5 rounded-xl border border-white/10 bg-[#0A0A0A] hover:border-white/20 transition-all flex flex-col justify-between group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                Module 03
              </span>
              <Terminal className="w-5 h-5 text-neutral-500 group-hover:text-white transition-colors" />
            </div>
            <div className="mt-4">
              <h3 className="text-base font-semibold text-white">Audit & Telemetry Logs</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Full-page 8-column compliance ledger with real-time timestamps, error tracking, and CSV export.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-white/[0.06] text-xs font-mono text-neutral-400 flex items-center justify-between">
              <span>outreach_log.csv</span>
              <span className="group-hover:translate-x-0.5 transition-transform">View Logs →</span>
            </div>
          </Link>
        </div>
      </div>
    </main>
  );
}
