"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSystem } from "./SystemContext";

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/contacts", label: "Contacts" },
  { href: "/compose", label: "Review & Compose" },
  { href: "/logs", label: "Audit Logs" },
];

export function Navbar() {
  const pathname = usePathname();
  const { status, dryRun, toggleDryRun, senderProfile, setIsProfileModalOpen } = useSystem();

  const candidateName = senderProfile?.candidate_name || "Harsh Yadav";
  const candidateTitle = senderProfile?.candidate_title || "AI Engineer";
  const initials =
    candidateName
      .split(" ")
      .filter(Boolean)
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "HY";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-black/80 backdrop-blur-xl">
      <div className="max-w-[1500px] mx-auto px-6 h-14 flex items-center justify-between">
        {/* Left: Brand Monolith */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            {/* Geometric vector mark */}
            <div className="w-7 h-7 rounded-md bg-white text-black flex items-center justify-center font-bold tracking-tighter text-xs group-hover:bg-neutral-200 transition-colors">
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 2L2 22h20L12 2zm0 4.5l6.5 13.5h-13L12 6.5z" />
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium tracking-tight text-white text-sm">THE CLOSER</span>
              <span className="text-neutral-600">/</span>
              <span className="text-neutral-400 text-xs font-mono uppercase tracking-wider hidden sm:inline">
                Outreach Engine
              </span>
            </div>
          </Link>

          {/* Navigation Links with Active Indicator */}
          <nav className="flex items-center gap-1 pl-4 border-l border-white/10">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname === link.href || pathname?.startsWith(link.href + "/");

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3 py-1.5 text-xs font-medium transition-colors ${
                    isActive ? "text-white" : "text-neutral-400 hover:text-neutral-200"
                  }`}
                >
                  <span>{link.label}</span>
                  {isActive && (
                    <span className="absolute bottom-[-11px] left-3 right-3 h-[2px] bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.6)]" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right: Telemetry & Live DRY_RUN Switch */}
        <div className="flex items-center gap-4">
          {/* Live Telemetry Pills */}
          <div className="hidden lg:flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-[11px] font-mono text-neutral-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
              Agents Online
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-[11px] font-mono text-neutral-400">
              {status?.send_method_label || "Gmail API / SMTP"}
            </span>
          </div>

          <div className="h-4 w-px bg-white/10 hidden sm:block" />

          {/* DRY_RUN Toggle Switch */}
          <div className="flex items-center gap-2.5 px-2.5 py-1 rounded-lg border border-white/10 bg-[#0E0E0E]">
            <div className="flex items-center gap-1.5 text-xs font-mono">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  dryRun
                    ? "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]"
                    : "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]"
                }`}
              />
              <span className="text-[11px] font-medium text-neutral-300 hidden sm:inline">
                {dryRun ? "DRY_RUN" : "PRODUCTION"}
              </span>
            </div>
            <button
              role="switch"
              type="button"
              aria-checked={dryRun}
              onClick={toggleDryRun}
              className="relative inline-flex h-4 w-8 shrink-0 cursor-pointer rounded-full bg-neutral-800 border border-white/10 p-0.5 transition-colors focus:outline-none"
            >
              <span
                className={`pointer-events-none inline-block h-2.5 w-2.5 transform rounded-full bg-white shadow transition-transform duration-200 ${
                  dryRun ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          {/* Interactive Sender Profile Badge */}
          <button
            type="button"
            onClick={() => setIsProfileModalOpen(true)}
            title="Configure Sender / Paste Resume"
            className="flex items-center gap-2.5 pl-2.5 pr-1.5 py-1 -mr-1 rounded-lg border border-white/10 hover:border-white/30 bg-white/[0.02] hover:bg-white/[0.06] transition-all group cursor-pointer focus:outline-none hidden md:flex"
          >
            <div className="flex flex-col text-right">
              <span className="text-xs font-medium text-white leading-tight group-hover:text-neutral-200 transition-colors">
                {candidateName}
              </span>
              <span className="text-[10px] font-mono text-neutral-500 group-hover:text-neutral-400 transition-colors">
                {candidateTitle}
              </span>
            </div>
            <div className="w-7 h-7 rounded-full bg-neutral-900 border border-white/10 group-hover:border-white/30 text-neutral-300 group-hover:text-white flex items-center justify-center text-xs font-mono font-medium transition-colors">
              {initials}
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}
