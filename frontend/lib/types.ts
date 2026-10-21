export interface ContactRecord {
  recipient_name: string;
  recipient_email: string;
  company: string;
  role: string;
  job_url?: string;
  personalization_note?: string;
  candidate_name?: string;
  candidate_background?: string;
  portfolio_url?: string;
  [key: string]: any;
}

export interface EmailQuality {
  score: number;
  word_count: number;
  spam_risk: "low" | "medium" | "high" | "unknown";
  flags: string[];
  hallucination_guard: string;
}

export interface ContactItem {
  id: string;
  contact: ContactRecord;
  is_opted_out: boolean;
  generated_subject: string;
  generated_body: string;
  quality: EmailQuality;
  status?: "pending" | "sent" | "drafted" | "skipped" | "dry_run" | "opted_out";
  fit_score?: number;
  persona_tags?: string[];
  signal?: string;
}

export interface SenderProfile {
  candidate_name: string;
  candidate_title: string;
  candidate_background: string;
  portfolio_url: string;
}

export interface SystemStatus {
  engine: string;
  operator: string;
  contacts_source: string;
  dry_run: boolean;
  send_method: string;
  send_method_label: string;
  llm_enabled: boolean;
  llm_model: string;
  session_limit: string;
  max_sends: number;
  summary: Record<string, number>;
  total_processed: number;
  sender_profile?: SenderProfile;
}


export interface AuditLogEntry {
  timestamp: string;
  recipient_email: string;
  company: string;
  role: string;
  subject: string;
  status: string;
  error_message: string;
  word_count: number;
}

export interface UploadContactsResponse {
  status: string;
  source_file: string;
  loaded_count: number;
  skipped_invalid: number;
  total_active: number;
  contacts: ContactItem[];
}

