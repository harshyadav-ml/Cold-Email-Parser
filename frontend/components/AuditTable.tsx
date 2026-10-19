"use client";

import React, { useState } from "react";
import { Ban, ChevronDown, ChevronRight, Download } from "lucide-react";
import { AuditLogEntry } from "../lib/types";

interface AuditTableProps {
  logs: AuditLogEntry[];
  onDownloadCsv: () => void;
}

export function AuditTable({ logs, onDownloadCsv }: AuditTableProps) {
  const [isOpen, setIsOpen] = useState(true);

  const formatTimestamp = (ts: string) => {
    if (!ts) return "—";
    if (ts.endsWith("IST")) return ts;
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return ts;
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }).formatToParts(d);
      const get = (type: string) => parts.find((p) => p.type === type)?.value || "";
      return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}:${get("second")} ${get("dayPeriod").toUpperCase()} IST`;
    } catch {
      return ts;
    }
  };

  const getStatusBadge = (status: string) => {
    const s = (status || "").toLowerCase();
    if (s === "sent" || s === "drafted") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400 text-[11px] flex items-center gap-1.5 w-max">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
          {s === "sent" ? "SENT (200)" : "DRAFTED"}
        </span>
      );
    }
    if (s === "dry_run") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-neutral-300 text-[11px] flex items-center gap-1.5 w-max">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
          DRY_RUN
        </span>
      );
    }
    if (s === "skipped") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-neutral-400 text-[11px] flex items-center gap-1 w-max">
          <Ban className="w-3 h-3 text-neutral-400" />
          SKIPPED
        </span>
      );
    }
    // opted_out or failed
    return (
      <span className="px-2 py-0.5 rounded-full border border-rose-500/30 bg-rose-500/[0.08] text-rose-400 text-[11px] flex items-center gap-1.5 w-max">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)]" />
        {s.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="flex flex-col rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden">
      {/* Table Header */}
      <div
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/[0.02] transition-colors border-b border-white/[0.06]"
      >
        <div className="flex items-center gap-2.5">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-neutral-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-neutral-400" />
          )}
          <div className="flex items-center gap-2.5">
            <span className="text-sm font-semibold text-white">
              Audit & Dispatch Telemetry
            </span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-[11px] font-mono text-neutral-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
              Live Pipeline Stream
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-neutral-500 hidden sm:inline-block">
            {logs.length > 0
              ? `Last event ${formatTimestamp(logs[0].timestamp)}`
              : "No dispatches yet"}
          </span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDownloadCsv();
            }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/[0.08] bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-300 text-xs font-mono transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Telemetry Table Content */}
      {isOpen && (
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#0E0E0E] text-neutral-500 uppercase tracking-wider text-[10px] border-b border-white/[0.06]">
              <tr>
                <th className="py-2.5 px-4 font-medium">TIMESTAMP (IST)</th>
                <th className="py-2.5 px-4 font-medium">RECIPIENT EMAIL</th>
                <th className="py-2.5 px-4 font-medium">COMPANY</th>
                <th className="py-2.5 px-4 font-medium">ROLE</th>
                <th className="py-2.5 px-4 font-medium">SUBJECT</th>
                <th className="py-2.5 px-4 font-medium">STATUS</th>
                <th className="py-2.5 px-4 font-medium">WORDS</th>
                <th className="py-2.5 px-4 font-medium">ERROR DETAILS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-neutral-300">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-6 px-4 text-center text-neutral-500">
                    No log events recorded in logs/outreach_log.csv yet.
                  </td>
                </tr>
              ) : (
                logs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-2.5 px-4 text-neutral-500 whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="py-2.5 px-4 font-medium text-white whitespace-nowrap">
                      {log.recipient_email}
                    </td>
                    <td className="py-2.5 px-4 text-neutral-400 whitespace-nowrap">
                      {log.company}
                    </td>
                    <td className="py-2.5 px-4 text-neutral-400 whitespace-nowrap">
                      {log.role}
                    </td>
                    <td className="py-2.5 px-4 text-neutral-400 truncate max-w-xs">
                      {log.subject}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      {getStatusBadge(log.status)}
                    </td>
                    <td className="py-2.5 px-4 text-neutral-500 whitespace-nowrap">
                      {log.word_count || "—"}
                    </td>
                    <td
                      className={`py-2.5 px-4 truncate max-w-xs ${
                        log.error_message && log.error_message !== "None"
                          ? "text-rose-400"
                          : "text-neutral-500"
                      }`}
                    >
                      {log.error_message || "None"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
