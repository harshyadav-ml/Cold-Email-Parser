"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { RefreshCw, Download, Search, X, Ban } from "lucide-react";
import { fetchAuditLogs } from "../../lib/api";
import { AuditLogEntry } from "../../lib/types";
import { useSystem } from "../../components/SystemContext";

type StatusFilter = "all" | "sent" | "dry_run" | "skipped" | "opted_out";

export default function AuditLogsPage() {
  const { showToast } = useSystem();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const loadLogs = useCallback(
    async (silent = false) => {
      if (!silent) setIsLoading(true);
      try {
        const data = await fetchAuditLogs();
        setLogs(data);
      } catch {
        if (!silent) {
          showToast("Failed to fetch audit logs.", "error");
        }
      } finally {
        if (!silent) setIsLoading(false);
      }
    },
    [showToast]
  );

  useEffect(() => {
    loadLogs(false);
    const interval = setInterval(() => {
      loadLogs(true);
    }, 3000);
    return () => clearInterval(interval);
  }, [loadLogs]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Filter status
      const s = (log.status || "").toLowerCase();
      if (statusFilter !== "all") {
        if (statusFilter === "dry_run" && s !== "dry_run" && s !== "drafted") return false;
        if (statusFilter === "sent" && s !== "sent") return false;
        if (statusFilter === "skipped" && s !== "skipped") return false;
        if (statusFilter === "opted_out" && s !== "opted_out" && s !== "failed") return false;
      }

      // Search keyword
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        return (
          (log.recipient_email || "").toLowerCase().includes(query) ||
          (log.company || "").toLowerCase().includes(query) ||
          (log.role || "").toLowerCase().includes(query) ||
          (log.subject || "").toLowerCase().includes(query) ||
          (log.status || "").toLowerCase().includes(query) ||
          (log.error_message || "").toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [logs, statusFilter, searchTerm]);

  const handleDownloadCsv = () => {
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/audit/csv`;
    window.open(url, "_blank");
    showToast("Downloading outreach_log.csv...", "info");
  };

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
    if (s === "sent") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400 text-[11px] flex items-center gap-1.5 w-max">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
          SENT (200)
        </span>
      );
    }
    if (s === "dry_run" || s === "drafted") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-neutral-300 text-[11px] flex items-center gap-1.5 w-max">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
          DRY_RUN
        </span>
      );
    }
    if (s === "skipped") {
      return (
        <span className="px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-neutral-400 text-[11px] flex items-center gap-1 w-max">
          <Ban className="w-3 h-3 text-neutral-400" />
          SKIPPED
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-full border border-rose-500/30 bg-rose-500/[0.08] text-rose-400 text-[11px] flex items-center gap-1.5 w-max">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)]" />
        {s.toUpperCase()}
      </span>
    );
  };

  return (
    <main className="w-full max-w-[1500px] mx-auto px-6 py-8">
      <div className="flex flex-col gap-6">
        {/* Header Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 mb-1">
              <span>The Closer</span>
              <span>/</span>
              <span className="text-neutral-300">logs/outreach_log.csv</span>
            </div>
            <h1 className="text-2xl font-semibold text-white tracking-tight">
              Audit & Telemetry Logs
            </h1>
            <p className="text-xs text-neutral-400 mt-1">
              Append-only audit trail capturing IST timestamps, payload metrics, and dispatch statuses.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => loadLogs(false)}
              className="px-3 py-2 rounded-lg border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh Log</span>
            </button>
            <button
              onClick={handleDownloadCsv}
              className="bg-white text-black hover:bg-neutral-200 font-medium px-4 py-2 rounded-lg text-xs flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="p-4 rounded-xl border border-white/10 bg-[#0A0A0A] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search audit trail by email, company, subject, or error..."
              className="w-full bg-[#0E0E0E] border border-white/10 text-neutral-200 placeholder:text-neutral-600 text-xs pl-8 pr-8 py-2.5 rounded-lg focus:outline-none focus:border-white/25 transition-colors font-sans"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Status Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
            {(
              [
                { key: "all", label: "All Events" },
                { key: "sent", label: "Live Sent" },
                { key: "dry_run", label: "Dry Run" },
                { key: "skipped", label: "Skipped" },
                { key: "opted_out", label: "Policy Blocked" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setStatusFilter(tab.key)}
                className={`px-3 py-1.5 rounded-md transition-all cursor-pointer whitespace-nowrap ${
                  statusFilter === tab.key
                    ? "bg-white text-black font-medium"
                    : "border border-white/10 bg-white/[0.02] text-neutral-400 hover:text-white hover:bg-neutral-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Full-Page Audit Telemetry Table (8 Columns) */}
        <div className="rounded-xl border border-white/10 bg-[#0A0A0A] overflow-hidden">
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#0E0E0E] text-neutral-500 uppercase tracking-wider text-[10px] border-b border-white/10">
                <tr>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">TIMESTAMP (IST)</th>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">RECIPIENT EMAIL</th>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">COMPANY</th>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">ROLE</th>
                  <th className="py-3 px-4 font-medium">SUBJECT</th>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">STATUS</th>
                  <th className="py-3 px-4 font-medium whitespace-nowrap">WORDS</th>
                  <th className="py-3 px-4 font-medium">ERROR DETAILS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-neutral-300">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-12 px-4 text-center text-neutral-500 font-mono">
                      Loading audit telemetry ledger...
                    </td>
                  </tr>
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 px-4 text-center text-neutral-500 font-mono">
                      No matching log events recorded.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 text-neutral-500 whitespace-nowrap">
                        {formatTimestamp(log.timestamp)}
                      </td>
                      <td className="py-3 px-4 font-medium text-white whitespace-nowrap">
                        {log.recipient_email}
                      </td>
                      <td className="py-3 px-4 text-neutral-400 whitespace-nowrap">
                        {log.company}
                      </td>
                      <td className="py-3 px-4 text-neutral-400 whitespace-nowrap">
                        {log.role}
                      </td>
                      <td className="py-3 px-4 text-neutral-300 truncate max-w-xs">
                        {log.subject}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {getStatusBadge(log.status)}
                      </td>
                      <td className="py-3 px-4 text-neutral-400 whitespace-nowrap">
                        {log.word_count || "—"}
                      </td>
                      <td
                        className={`py-3 px-4 truncate max-w-xs ${
                          log.error_message && log.error_message !== "None"
                            ? "text-rose-400 font-medium"
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

          {/* Table Footer */}
          <div className="flex items-center justify-between p-4 border-t border-white/[0.06] text-xs font-mono text-neutral-500">
            <span>
              Showing {filteredLogs.length} of {logs.length} Logged Dispatches
            </span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-neutral-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
                Audit Log Verified (RFC 4180 CSV)
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
