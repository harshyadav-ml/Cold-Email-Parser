"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { SystemStatus, ContactItem, SenderProfile } from "../lib/types";
import {
  fetchSystemStatus,
  fetchContacts,
  toggleDryRun as apiToggleDryRun,
  uploadContactsFile,
  fetchSenderProfile,
  updateSenderProfile,
  INITIAL_MOCK_CONTACTS,
} from "../lib/api";
import { UploadContactsModal } from "./UploadContactsModal";
import { SenderProfileModal } from "./SenderProfileModal";

export type ToastType = "info" | "success" | "warning" | "error";

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface SystemContextType {
  status: SystemStatus | null;
  dryRun: boolean;
  toggleDryRun: () => Promise<void>;
  refreshStatus: () => Promise<void>;
  contacts: ContactItem[];
  setContacts: React.Dispatch<React.SetStateAction<ContactItem[]>>;
  refreshContacts: () => Promise<void>;
  updateContactStatus: (
    id: string,
    newStatus: NonNullable<ContactItem["status"]>,
    newSubject?: string,
    newBody?: string,
    newQuality?: any
  ) => void;
  showToast: (message: string, type?: ToastType) => void;
  isLoading: boolean;
  activeSourceFile: string;
  setActiveSourceFile: React.Dispatch<React.SetStateAction<string>>;
  isUploadModalOpen: boolean;
  setIsUploadModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
  uploadContacts: (file: File, mode: "replace" | "append") => Promise<any>;
  senderProfile: SenderProfile;
  setSenderProfile: React.Dispatch<React.SetStateAction<SenderProfile>>;
  isProfileModalOpen: boolean;
  setIsProfileModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
  updateProfile: (profile: SenderProfile) => Promise<any>;
}


const SystemContext = createContext<SystemContextType | undefined>(undefined);

export function SystemProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [dryRun, setDryRun] = useState<boolean>(true);
  const [contacts, setContacts] = useState<ContactItem[]>(INITIAL_MOCK_CONTACTS);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeSourceFile, setActiveSourceFile] = useState<string>("data/contacts.json");
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [senderProfile, setSenderProfile] = useState<SenderProfile>({
    candidate_name: "Harsh Yadav",
    candidate_title: "AI Engineer",
    candidate_background:
      "AI Engineer specializing in agentic workflows, FastAPI, Next.js, and production LLM pipelines",
    portfolio_url: "https://github.com/harshyadav-ml",
  });
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3800);
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await fetchSystemStatus();
      setStatus(data);
      setDryRun(data.dry_run);
      if (data.contacts_source) {
        setActiveSourceFile(data.contacts_source);
      }
      if (data.sender_profile) {
        setSenderProfile(data.sender_profile);
      }
    } catch {
      // Keep existing state
    }
  }, []);

  const refreshContacts = useCallback(async () => {
    try {
      const list = await fetchContacts();
      if (list && list.length > 0) {
        setContacts(list);
      }
    } catch {
      // Keep existing contacts
    }
  }, []);

  useEffect(() => {
    async function init() {
      setIsLoading(true);
      await Promise.all([
        refreshStatus(),
        refreshContacts(),
        fetchSenderProfile().then((sp) => setSenderProfile(sp)).catch(() => {}),
      ]);
      setIsLoading(false);
    }
    init();
  }, [refreshStatus, refreshContacts]);

  const handleToggleDryRun = useCallback(async () => {
    const nextVal = !dryRun;
    setDryRun(nextVal);
    try {
      const updated = await apiToggleDryRun(nextVal);
      setDryRun(updated);
      if (updated) {
        showToast("DRY_RUN Active: Outreach simulations only (no live mail dispatched).", "info");
      } else {
        showToast("PRODUCTION ACTIVE! Real emails will dispatch via Gmail API / SMTP.", "warning");
      }
      await refreshStatus();
    } catch {
      showToast("Failed to toggle mode.", "error");
    }
  }, [dryRun, refreshStatus, showToast]);

  const uploadContacts = useCallback(
    async (file: File, mode: "replace" | "append") => {
      try {
        const result = await uploadContactsFile(file, mode);
        if (result.contacts && result.contacts.length > 0) {
          setContacts(result.contacts);
        }
        if (result.source_file) {
          setActiveSourceFile(result.source_file);
        }
        await refreshStatus();
        const malformedNotice =
          result.skipped_invalid > 0
            ? ` (${result.skipped_invalid} malformed skipped)`
            : "";
        showToast(
          `Loaded ${result.loaded_count} contacts from ${result.source_file}${malformedNotice}`,
          "success"
        );
        return result;
      } catch (err: any) {
        showToast(err.message || "Failed to upload contacts file.", "error");
        throw err;
      }
    },
    [refreshStatus, showToast]
  );

  const updateProfile = useCallback(
    async (newProfile: SenderProfile) => {
      try {
        const result = await updateSenderProfile(newProfile);
        if (result.sender_profile) {
          setSenderProfile(result.sender_profile);
        }
        if (result.contacts && result.contacts.length > 0) {
          setContacts(result.contacts);
        }
        await refreshStatus();
        showToast("Sender profile updated — drafts re-synthesized", "success");
        return result;
      } catch (err: any) {
        showToast(err.message || "Failed to update sender profile.", "error");
        throw err;
      }
    },
    [refreshStatus, showToast]
  );

  const updateContactStatus = useCallback(
    (
      id: string,
      newStatus: NonNullable<ContactItem["status"]>,
      newSubject?: string,
      newBody?: string,
      newQuality?: any
    ) => {
      setContacts((prev) =>
        prev.map((c) => {
          if (c.id === id) {
            return {
              ...c,
              status: newStatus,
              generated_subject: newSubject ?? c.generated_subject,
              generated_body: newBody ?? c.generated_body,
              quality: newQuality ?? c.quality,
            };
          }
          return c;
        })
      );
    },
    []
  );

  return (
    <SystemContext.Provider
      value={{
        status,
        dryRun,
        toggleDryRun: handleToggleDryRun,
        refreshStatus,
        contacts,
        setContacts,
        refreshContacts,
        updateContactStatus,
        showToast,
        isLoading,
        activeSourceFile,
        setActiveSourceFile,
        isUploadModalOpen,
        setIsUploadModalOpen,
        uploadContacts,
        senderProfile,
        setSenderProfile,
        isProfileModalOpen,
        setIsProfileModalOpen,
        updateProfile,
      }}
    >
      {children}
      <UploadContactsModal />
      <SenderProfileModal />



      {/* Global Toast Container */}
      <div className="fixed top-20 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => {
          let dotColor = "bg-neutral-400";
          if (toast.type === "success")
            dotColor = "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]";
          if (toast.type === "warning")
            dotColor = "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]";
          if (toast.type === "error")
            dotColor = "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]";

          return (
            <div
              key={toast.id}
              className="p-3 rounded-lg border border-white/[0.12] bg-[#0E0E0E] shadow-2xl font-mono text-xs flex items-center gap-2.5 pointer-events-auto transform transition-all duration-300 text-white animate-in fade-in slide-in-from-top-2"
            >
              <span className={`w-2 h-2 rounded-full ${dotColor} shrink-0`} />
              <span>{toast.message}</span>
            </div>
          );
        })}
      </div>
    </SystemContext.Provider>
  );
}

export function useSystem() {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error("useSystem must be used within a SystemProvider");
  }
  return context;
}
