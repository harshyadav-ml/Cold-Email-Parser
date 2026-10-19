"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { RefreshCw, Send, Search, X, ArrowRight, Upload } from "lucide-react";
import { useSystem } from "../../components/SystemContext";

type FilterStatus = "all" | "pending" | "drafted" | "sent" | "skipped";

export default function ContactsDirectoryPage() {
  const {
    contacts,
    refreshContacts,
    isLoading,
    activeSourceFile,
    setIsUploadModalOpen,
  } = useSystem();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("all");

  const filteredContacts = useMemo(() => {
    return contacts.filter((c) => {
      // Filter status
      if (statusFilter === "pending") {
        if (c.status && c.status !== "pending") return false;
      } else if (statusFilter === "drafted") {
        if (c.status !== "dry_run" && c.status !== "drafted") return false;
      } else if (statusFilter === "sent") {
        if (c.status !== "sent") return false;
      } else if (statusFilter === "skipped") {
        if (c.status !== "skipped" && !c.is_opted_out) return false;
      }

      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const name = (c.contact.recipient_name || "").toLowerCase();
        const comp = (c.contact.company || "").toLowerCase();
        const role = (c.contact.role || "").toLowerCase();
        const email = (c.contact.recipient_email || "").toLowerCase();
        const note = (c.contact.personalization_note || "").toLowerCase();
        return (
          name.includes(query) ||
          comp.includes(query) ||
          role.includes(query) ||
          email.includes(query) ||
          note.includes(query)
        );
      }
      return true;
    });
  }, [contacts, statusFilter, searchTerm]);

  // Status counts
  const counts = useMemo(() => {
    let pending = 0;
    let drafted = 0;
    let sent = 0;
    let skipped = 0;

    contacts.forEach((c) => {
      if (!c.status || c.status === "pending") pending++;
      else if (c.status === "dry_run" || c.status === "drafted") drafted++;
      else if (c.status === "sent") sent++;
      else if (c.status === "skipped" || c.is_opted_out) skipped++;
    });

    return { all: contacts.length, pending, drafted, sent, skipped };
  }, [contacts]);

  return (
    <main className="w-full max-w-[1500px] mx-auto px-6 py-8">
      <div className="flex flex-col gap-6">
        {/* Header Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-neutral-500 mb-1">
              <span>The Closer</span>
              <span>/</span>
              <button
                type="button"
                onClick={() => setIsUploadModalOpen(true)}
                className="text-neutral-300 hover:text-white px-1.5 py-0.5 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] hover:border-white/30 transition-all flex items-center gap-1.5 cursor-pointer font-mono group"
                title="Click to upload or append contacts"
              >
                <Upload className="w-3 h-3 text-neutral-400 group-hover:text-white transition-colors" />
                <span>{activeSourceFile || "data/contacts.json"}</span>
              </button>
            </div>
            <h1 className="text-2xl font-semibold text-white tracking-tight">
              Contacts Directory
            </h1>
            <p className="text-xs text-neutral-400 mt-1">
              Review target companies, candidate roles, and individualized personalization hooks.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              className="px-3.5 py-2 rounded-lg border border-white/15 bg-white/5 hover:bg-white/10 text-white text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
            >
              <Upload className="w-4 h-4 text-neutral-300" />
              <span>Upload JSON / CSV</span>
            </button>
            <button
              onClick={() => refreshContacts()}
              className="px-3 py-2 rounded-lg border border-white/10 bg-[#0E0E0E] hover:bg-neutral-800 text-neutral-300 hover:text-white text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reload Leads</span>
            </button>
            <Link
              href="/compose"
              className="bg-white text-black hover:bg-neutral-200 font-medium px-4 py-2 rounded-lg text-xs flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Open Compose Studio</span>
            </Link>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="p-4 rounded-xl border border-white/10 bg-[#0A0A0A] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by recipient name, company, role, or keywords..."
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

          {/* Filter Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
            {(
              [
                { key: "all", label: "All", count: counts.all },
                { key: "pending", label: "Pending", count: counts.pending },
                { key: "drafted", label: "Drafted", count: counts.drafted },
                { key: "sent", label: "Sent", count: counts.sent },
                { key: "skipped", label: "Skipped", count: counts.skipped },
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
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>

        {/* Full-Width Contacts Table */}
        <div className="rounded-xl border border-white/10 bg-[#0A0A0A] overflow-hidden">
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#0E0E0E] text-neutral-500 uppercase tracking-wider text-[10px] border-b border-white/10">
                <tr>
                  <th className="py-3 px-4 font-medium">RECIPIENT & COMPANY</th>
                  <th className="py-3 px-4 font-medium">ROLE</th>
                  <th className="py-3 px-4 font-medium">MATCH SCORE</th>
                  <th className="py-3 px-4 font-medium">STATUS</th>
                  <th className="py-3 px-4 font-medium">PERSONALIZATION HOOK</th>
                  <th className="py-3 px-4 font-medium text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-neutral-300 font-sans">
                {filteredContacts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 px-4 text-center text-neutral-500 font-mono">
                      No contacts found matching criteria.
                    </td>
                  </tr>
                ) : (
                  filteredContacts.map((c) => {
                    const email = c.contact.recipient_email;
                    const fitScore = c.fit_score ?? 94;
                    const isOpted = c.is_opted_out;

                    let statusBadge;
                    if (isOpted) {
                      statusBadge = (
                        <span className="px-2 py-0.5 rounded-full border border-rose-500/30 bg-rose-500/[0.08] text-rose-400 font-mono text-[11px] whitespace-nowrap">
                          Opted Out
                        </span>
                      );
                    } else if (c.status === "sent") {
                      statusBadge = (
                        <span className="px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400 font-mono text-[11px] whitespace-nowrap flex items-center gap-1 w-max">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
                          Sent
                        </span>
                      );
                    } else if (c.status === "dry_run" || c.status === "drafted") {
                      statusBadge = (
                        <span className="px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-neutral-300 font-mono text-[11px] whitespace-nowrap flex items-center gap-1 w-max">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
                          Drafted
                        </span>
                      );
                    } else if (c.status === "skipped") {
                      statusBadge = (
                        <span className="px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-neutral-500 font-mono text-[11px] whitespace-nowrap">
                          Skipped
                        </span>
                      );
                    } else {
                      statusBadge = (
                        <span className="px-2 py-0.5 rounded-full border border-white/10 bg-white/[0.02] text-neutral-300 font-mono text-[11px] whitespace-nowrap">
                          Pending
                        </span>
                      );
                    }

                    return (
                      <tr
                        key={c.id}
                        className="hover:bg-white/[0.02] transition-colors group cursor-pointer"
                      >
                        {/* Recipient & Company */}
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-md bg-neutral-900 border border-white/10 text-neutral-300 flex items-center justify-center font-mono text-xs shrink-0">
                              {c.contact.recipient_name?.split(" ").map((n) => n[0]).join("") || "CN"}
                            </div>
                            <div className="flex flex-col">
                              <span className="font-medium text-white text-sm">
                                {c.contact.recipient_name}
                              </span>
                              <div className="flex items-center gap-1.5 font-mono text-xs text-neutral-400">
                                <span>{c.contact.company}</span>
                                <span className="text-neutral-600">•</span>
                                <span className="text-neutral-500">{email}</span>
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Role */}
                        <td className="py-3 px-4 text-neutral-300 text-xs font-mono">
                          {c.contact.role}
                        </td>

                        {/* Match Score */}
                        <td className="py-3 px-4 font-mono text-xs">
                          <span
                            className={
                              fitScore >= 90
                                ? "text-emerald-400"
                                : fitScore >= 80
                                ? "text-amber-400"
                                : "text-neutral-400"
                            }
                          >
                            {fitScore}% Fit
                          </span>
                        </td>

                        {/* Status */}
                        <td className="py-3 px-4">{statusBadge}</td>

                        {/* Personalization Hook */}
                        <td className="py-3 px-4 max-w-sm">
                          <p className="text-xs text-neutral-400 truncate leading-relaxed">
                            {c.contact.personalization_note || "Standard company background alignment."}
                          </p>
                        </td>

                        {/* Action Link */}
                        <td className="py-3 px-4 text-right">
                          <Link
                            href={`/compose?email=${encodeURIComponent(email)}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-white/10 bg-neutral-900 hover:bg-white hover:text-black text-neutral-300 text-xs font-mono transition-all cursor-pointer whitespace-nowrap"
                          >
                            <span>Review Email</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="flex items-center justify-between p-4 border-t border-white/[0.06] text-xs font-mono text-neutral-500">
            <span>
              Showing {filteredContacts.length} of {contacts.length} Directory Records
            </span>
            <div className="flex items-center gap-2 text-neutral-400">
              <span>Synced with data/contacts.json</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
