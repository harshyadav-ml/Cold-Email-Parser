"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Upload,
  FileJson,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  X,
  Download,
  Loader2,
  Sparkles,
} from "lucide-react";
import { useSystem } from "./SystemContext";
import { downloadContactsTemplate } from "../lib/api";

function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

export function UploadContactsModal() {
  const { isUploadModalOpen, setIsUploadModalOpen, uploadContacts } = useSystem();

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"replace" | "append">("replace");
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [parsedPreview, setParsedPreview] = useState<{
    count: number;
    sampleNames: string[];
  } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state whenever modal is opened
  useEffect(() => {
    if (isUploadModalOpen) {
      setFile(null);
      setParsedPreview(null);
      setErrorMsg(null);
      setIsUploading(false);
      setIsDragging(false);
    }
  }, [isUploadModalOpen]);

  // Handle client-side parsing for instant feedback on file drop/selection
  const handleSelectFile = useCallback((selectedFile: File) => {
    setErrorMsg(null);
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "json" && ext !== "csv") {
      setErrorMsg("Unsupported format. Please select a valid .json or .csv file.");
      setFile(null);
      setParsedPreview(null);
      return;
    }

    setFile(selectedFile);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        if (ext === "json") {
          const parsed = JSON.parse(text);
          const records = Array.isArray(parsed)
            ? parsed
            : parsed?.contacts || parsed?.data || [parsed];
          const names = records
            .slice(0, 3)
            .map(
              (r: any) =>
                r.recipient_name || r.name || r.recipient_email || "Unknown Lead"
            );
          setParsedPreview({ count: records.length, sampleNames: names });
        } else {
          // Quick CSV lines preview
          const lines = text
            .split(/\r?\n/)
            .map((l) => l.trim())
            .filter((l) => l.length > 0);
          const count = Math.max(0, lines.length - 1);
          const sample = lines
            .slice(1, 4)
            .map((l) => l.split(",")[0].replace(/^["']|["']$/g, ""));
          setParsedPreview({ count, sampleNames: sample });
        }
      } catch {
        setParsedPreview(null);
      }
    };
    reader.readAsText(selectedFile);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile) {
        handleSelectFile(droppedFile);
      }
    },
    [handleSelectFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || isUploading) return;

    setIsUploading(true);
    setErrorMsg(null);

    try {
      await uploadContacts(file, mode);
      setIsUploadModalOpen(false);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to ingest contacts. Please check your file schema.");
    } finally {
      setIsUploading(false);
    }
  };

  if (!isUploadModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div
        className="bg-zinc-950 border border-white/10 rounded-xl shadow-2xl backdrop-blur-xl w-full max-w-xl flex flex-col overflow-hidden text-neutral-200 relative animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-modal-title"
      >
        {/* Modal Header */}
        <div className="p-6 pb-4 border-b border-white/10 flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-white text-black flex items-center justify-center">
                <Upload className="w-4 h-4 text-black" />
              </div>
              <h2 id="upload-modal-title" className="text-lg font-semibold text-white tracking-tight">
                Ingest Outreach Contacts
              </h2>
            </div>
            <p className="text-xs text-neutral-400 mt-1">
              Upload target leads via JSON or CSV to update the queue and pre-synthesize initial drafts.
            </p>
          </div>

          <button
            onClick={() => setIsUploadModalOpen(false)}
            className="p-1.5 rounded-lg border border-white/10 text-neutral-400 hover:text-white hover:bg-neutral-900 transition-colors cursor-pointer"
            aria-label="Close upload modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-5">
          {/* Ingestion Mode Toggle */}
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold">
              Ingestion Mode
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 rounded-lg border border-white/10 bg-black">
              <button
                type="button"
                onClick={() => setMode("replace")}
                className={`px-3 py-2.5 rounded-md text-xs font-mono text-left transition-all cursor-pointer flex flex-col gap-0.5 ${
                  mode === "replace"
                    ? "bg-white text-black font-semibold shadow-sm"
                    : "text-neutral-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      mode === "replace" ? "bg-black" : "bg-neutral-500"
                    }`}
                  />
                  Replace Queue
                </span>
                <span
                  className={`text-[10px] leading-tight font-sans ${
                    mode === "replace" ? "text-neutral-700 font-normal" : "text-neutral-500"
                  }`}
                >
                  Overwrites active contacts with new file
                </span>
              </button>

              <button
                type="button"
                onClick={() => setMode("append")}
                className={`px-3 py-2.5 rounded-md text-xs font-mono text-left transition-all cursor-pointer flex flex-col gap-0.5 ${
                  mode === "append"
                    ? "bg-white text-black font-semibold shadow-sm"
                    : "text-neutral-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      mode === "append" ? "bg-black" : "bg-neutral-500"
                    }`}
                  />
                  Append & Dedupe
                </span>
                <span
                  className={`text-[10px] leading-tight font-sans ${
                    mode === "append" ? "text-neutral-700 font-normal" : "text-neutral-500"
                  }`}
                >
                  Merges leads, skipping existing emails
                </span>
              </button>
            </div>
          </div>

          {/* Drag & Drop File Zone */}
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 font-semibold">
              Contact File (.JSON / .CSV)
            </label>

            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.csv"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  handleSelectFile(e.target.files[0]);
                }
              }}
            />

            {!file ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer flex flex-col items-center justify-center gap-2.5 ${
                  isDragging
                    ? "border-white/60 bg-white/[0.06] scale-[1.01]"
                    : "border-white/15 bg-white/[0.02] hover:border-white/40 hover:bg-white/[0.04]"
                }`}
              >
                <div className="w-11 h-11 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-neutral-300">
                  <Upload className="w-5 h-5 text-neutral-300" />
                </div>
                <div className="flex flex-col gap-1">
                  <p className="text-xs font-medium text-white">
                    Drag and drop your file here, or{" "}
                    <span className="underline underline-offset-2 text-neutral-300 hover:text-white">
                      browse
                    </span>
                  </p>
                  <p className="text-[11px] font-mono text-neutral-500">
                    Supports .JSON or .CSV (up to 5MB)
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-white/15 bg-white/[0.03] flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="w-10 h-10 rounded-lg bg-black border border-white/10 flex items-center justify-center shrink-0">
                    {file.name.endsWith(".csv") ? (
                      <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <FileJson className="w-5 h-5 text-sky-400" />
                    )}
                  </div>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-xs font-mono font-medium text-white truncate">
                      {file.name}
                    </span>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-neutral-400 mt-0.5">
                      <span>{formatBytes(file.size)}</span>
                      {parsedPreview && (
                        <>
                          <span>•</span>
                          <span className="text-emerald-400 flex items-center gap-1 font-medium">
                            <CheckCircle2 className="w-3 h-3" />
                            {parsedPreview.count} contacts detected
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setParsedPreview(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="p-1.5 rounded-lg border border-white/10 text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors cursor-pointer shrink-0"
                  title="Remove file"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          {/* Schema Requirements & Sample Downloads */}
          <div className="p-3.5 rounded-lg border border-white/10 bg-black/60 flex flex-col gap-2.5">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400 font-semibold flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-neutral-400" />
                Required Schema Keys
              </span>
              <div className="flex items-center gap-2 text-[11px] font-mono">
                <button
                  type="button"
                  onClick={() => downloadContactsTemplate("json")}
                  className="flex items-center gap-1 text-neutral-400 hover:text-white transition-colors cursor-pointer"
                  title="Download clean contacts.json template"
                >
                  <Download className="w-3 h-3" />
                  <span>Sample JSON</span>
                </button>
                <span className="text-neutral-700">|</span>
                <button
                  type="button"
                  onClick={() => downloadContactsTemplate("csv")}
                  className="flex items-center gap-1 text-neutral-400 hover:text-white transition-colors cursor-pointer"
                  title="Download clean contacts.csv template"
                >
                  <Download className="w-3 h-3" />
                  <span>Sample CSV</span>
                </button>
              </div>
            </div>

            <div className="font-mono text-[11px] text-zinc-400 flex flex-wrap gap-1.5">
              <span className="px-1.5 py-0.5 rounded bg-white/[0.08] border border-white/10 text-white font-medium">
                recipient_email *
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.08] border border-white/10 text-white font-medium">
                company *
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.08] border border-white/10 text-white font-medium">
                role *
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-300">
                recipient_name
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-300">
                personalization_note
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-300">
                candidate_name
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-300">
                candidate_background
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-500">
                job_url
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.03] text-neutral-500">
                portfolio_url
              </span>
            </div>
          </div>

          {/* Error Banner */}
          {errorMsg && (
            <div className="p-3 rounded-lg border border-rose-500/20 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Modal Actions */}
          <div className="pt-2 flex items-center justify-end gap-3 border-t border-white/10">
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(false)}
              disabled={isUploading}
              className="px-4 py-2 rounded-lg border border-white/10 text-neutral-400 hover:text-white hover:bg-neutral-900 text-xs font-mono transition-colors cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={!file || isUploading}
              className="bg-white text-black hover:bg-neutral-200 font-medium px-5 py-2.5 rounded-lg text-xs flex items-center gap-2 transition-all active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-lg"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-black" />
                  <span>Synthesizing Drafts...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5 text-black" />
                  <span>
                    {mode === "replace" ? "Replace & Ingest" : "Append & Ingest"}
                    {parsedPreview?.count ? ` (${parsedPreview.count})` : ""}
                  </span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
