"use client";

import React, { useState, useMemo } from "react";
import { Search, X } from "lucide-react";
import { ContactItem } from "../lib/types";

interface ContactQueueProps {
  contacts: ContactItem[];
  selectedContactId: string | null;
  onSelectContact: (id: string) => void;
  onBatchApprove?: (ids: string[]) => void;
  onBatchSkip?: (ids: string[]) => void;
}

export function ContactQueue({
  contacts,
  selectedContactId,
  onSelectContact,
  onBatchApprove,
  onBatchSkip,
}: ContactQueueProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "pending" | "draft" | "risk">("all");
  const [sortOption, setSortOption] = useState<"intent_desc" | "recent" | "urgency">("intent_desc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Filter & Search Logic
  const filteredContacts = useMemo(() => {
    return contacts.filter((c) => {
      // Filter tab
      if (activeFilter === "pending" && c.status && c.status !== "pending") return false;
      if (activeFilter === "draft" && c.status !== "dry_run" && c.status !== "drafted") return false;
      if (activeFilter === "risk" && !c.is_opted_out && c.quality?.spam_risk !== "high" && (c.quality?.flags?.length || 0) === 0) return false;

      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const name = (c.contact?.recipient_name || "").toLowerCase();
        const comp = (c.contact?.company || "").toLowerCase();
        const role = (c.contact?.role || "").toLowerCase();
        const email = (c.contact?.recipient_email || "").toLowerCase();
        const notes = (c.contact?.personalization_note || "").toLowerCase();
        return (
          name.includes(query) ||
          comp.includes(query) ||
          role.includes(query) ||
          email.includes(query) ||
          notes.includes(query)
        );
      }
      return true;
    }).sort((a, b) => {
      if (sortOption === "intent_desc") {
        return (b.fit_score || 90) - (a.fit_score || 90);
      }
      if (sortOption === "urgency") {
        return (b.is_opted_out ? 1 : 0) - (a.is_opted_out ? 1 : 0);
      }
      return 0;
    });
  }, [contacts, activeFilter, searchTerm, sortOption]);

  const allVisibleSelected =
    filteredContacts.length > 0 && filteredContacts.every((c) => selectedIds.has(c.id));

  const handleToggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(filteredContacts.map((c) => c.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleToggleItem = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  // Counts for pills
  const counts = useMemo(() => {
    let pending = 0;
    let draft = 0;
    let risk = 0;
    contacts.forEach((c) => {
      if (c.status === "pending" || !c.status) pending++;
      if (c.status === "dry_run" || c.status === "drafted") draft++;
      if (c.is_opted_out || c.quality?.spam_risk === "high" || (c.quality?.flags && c.quality.flags.length > 1)) risk++;
    });
    return { all: contacts.length, pending, draft, risk };
  }, [contacts]);

  return (
    <div className="lg:col-span-5 flex flex-col gap-3 rounded-xl border border-white/[0.08] bg-[#0A0A0A] bg-gradient-to-b from-white/[0.03] to-transparent p-4">
      {/* Queue Header with Search & Filter Controls */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white text-sm">Review Stream</span>
            <span className="px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.02] text-neutral-400 font-mono text-xs">
              {filteredContacts.length} Candidates
            </span>
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-neutral-500">
            <span>Sort:</span>
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value as any)}
              className="bg-[#0E0E0E] border border-white/[0.08] text-neutral-200 rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-white/20 cursor-pointer"
            >
              <option value="intent_desc">Intent Score (High-Low)</option>
              <option value="recent">Generated (Newest)</option>
              <option value="urgency">Compliance Urgency</option>
            </select>
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="relative w-full">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter by name, company, intent keyword..."
            className="w-full bg-[#0E0E0E] border border-white/[0.08] text-neutral-200 placeholder:text-neutral-600 text-xs pl-8 pr-8 py-2 rounded-lg focus:outline-none focus:border-white/25 transition-colors font-sans"
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

        {/* Queue Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 text-xs font-mono">
          <button
            onClick={() => setActiveFilter("all")}
            className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
              activeFilter === "all"
                ? "bg-white text-black font-medium"
                : "border border-white/[0.08] bg-white/[0.02] text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            All ({counts.all})
          </button>
          <button
            onClick={() => setActiveFilter("pending")}
            className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
              activeFilter === "pending"
                ? "bg-white text-black font-medium"
                : "border border-white/[0.08] bg-white/[0.02] text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            Pending ({counts.pending})
          </button>
          <button
            onClick={() => setActiveFilter("draft")}
            className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
              activeFilter === "draft"
                ? "bg-white text-black font-medium"
                : "border border-white/[0.08] bg-white/[0.02] text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            Dry Run ({counts.draft})
          </button>
          <button
            onClick={() => setActiveFilter("risk")}
            className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
              activeFilter === "risk"
                ? "bg-white text-black font-medium"
                : "border border-white/[0.08] bg-white/[0.02] text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            Risk Flag ({counts.risk})
          </button>
        </div>
      </div>

      {/* Batch Action Quick Bar */}
      <div className="flex items-center justify-between px-3 py-2 rounded-lg border border-white/[0.08] bg-[#0E0E0E] text-xs font-mono">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="select-all-checkbox"
            checked={allVisibleSelected}
            onChange={(e) => handleToggleSelectAll(e.target.checked)}
            className="w-3.5 h-3.5 rounded bg-black border-neutral-700 text-white cursor-pointer accent-white focus:ring-0 focus:ring-offset-0"
          />
          <label htmlFor="select-all-checkbox" className="text-neutral-400 cursor-pointer text-xs">
            Select All ({filteredContacts.length} visible)
          </label>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onBatchApprove && onBatchApprove(Array.from(selectedIds))}
            disabled={selectedIds.size === 0}
            className="px-2.5 py-1 rounded border border-white/[0.08] bg-neutral-900 text-neutral-300 hover:text-white hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs cursor-pointer"
          >
            Quick Approve
          </button>
          <button
            onClick={() => onBatchSkip && onBatchSkip(Array.from(selectedIds))}
            disabled={selectedIds.size === 0}
            className="px-2 py-1 rounded text-neutral-500 hover:text-rose-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs cursor-pointer"
          >
            Skip
          </button>
        </div>
      </div>

      {/* Scrollable Candidate Cards Stream */}
      <div className="flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-0.5">
        {filteredContacts.length === 0 ? (
          <div className="p-8 text-center text-neutral-500 font-mono text-xs">
            No contacts found matching filter criteria.
          </div>
        ) : (
          filteredContacts.map((item) => {
            const isSelected = item.id === selectedContactId;
            const fitScore = item.fit_score ?? 90;
            const domain = item.contact.recipient_email?.split("@")[1] || "domain.io";
            const isOpted = item.is_opted_out;
            const statusLabel = isOpted
              ? "Opted Out"
              : item.status === "sent"
              ? "Sent (200)"
              : item.status === "dry_run"
              ? "Dry Run"
              : item.status === "skipped"
              ? "Skipped"
              : "Pending";

            return (
              <div
                key={item.id}
                onClick={() => onSelectContact(item.id)}
                className={`p-3 rounded-lg border transition-all duration-150 cursor-pointer relative group ${
                  isSelected
                    ? "border-white/20 bg-white/[0.04] shadow-sm"
                    : "border-white/[0.06] bg-[#0E0E0E] hover:border-white/[0.12] hover:bg-white/[0.02]"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(item.id)}
                      onClick={(e) => handleToggleItem(item.id, e)}
                      onChange={() => {}}
                      className="candidate-checkbox mt-0.5 w-3.5 h-3.5 rounded bg-black border-neutral-700 text-white cursor-pointer accent-white focus:ring-0"
                    />
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm leading-snug">
                          {item.contact.recipient_name}
                        </span>
                        <span
                          className={`font-mono text-[11px] ${
                            fitScore >= 90
                              ? "text-emerald-400"
                              : fitScore >= 80
                              ? "text-amber-400"
                              : "text-neutral-400"
                          }`}
                        >
                          {fitScore}% Fit
                        </span>
                      </div>
                      <span className="text-xs text-neutral-400">
                        {item.contact.role} @ {item.contact.company}
                      </span>
                      <span className="font-mono text-[11px] text-neutral-600">{domain}</span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded-full font-mono text-[11px] whitespace-nowrap ${
                      isOpted
                        ? "border border-rose-500/30 bg-rose-500/[0.08] text-rose-400"
                        : item.status === "sent"
                        ? "border border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-400"
                        : "border border-white/[0.08] bg-white/[0.02] text-neutral-300"
                    }`}
                  >
                    {statusLabel}
                  </span>
                </div>

                {/* Persona Tags */}
                {item.persona_tags && item.persona_tags.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap mt-2 pl-6">
                    {item.persona_tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 rounded bg-neutral-900 border border-white/[0.06] text-neutral-400 font-mono text-[10px]"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Card Sub-bar */}
                <div className="flex items-center justify-between pt-2 mt-2 font-mono text-[11px] text-neutral-500 pl-6 border-t border-white/[0.04]">
                  <span className="flex items-center gap-1 text-neutral-400">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isOpted
                          ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.4)]"
                          : "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]"
                      }`}
                    />
                    {isOpted ? "Policy Flagged" : "Agent synthesized"}
                  </span>
                  <span className="text-neutral-500 group-hover:text-neutral-300 transition-colors">
                    {isSelected ? "Active payload →" : "Preview payload →"}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between text-xs font-mono text-neutral-500 pt-2 px-1 border-t border-white/[0.05]">
        <span>
          Showing {filteredContacts.length} of {contacts.length}
        </span>
        <div className="flex items-center gap-1">
          <button className="px-2 py-0.5 rounded border border-white/[0.08] bg-[#0E0E0E] text-neutral-500 cursor-not-allowed">
            ←
          </button>
          <span className="px-1 text-neutral-400">Page 1 of 1</span>
          <button className="px-2 py-0.5 rounded border border-white/[0.08] bg-[#0E0E0E] text-neutral-500 cursor-not-allowed">
            →
          </button>
        </div>
      </div>
    </div>
  );
}
