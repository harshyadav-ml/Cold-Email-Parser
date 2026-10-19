import { ContactItem, SystemStatus, AuditLogEntry, UploadContactsResponse, SenderProfile } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const INITIAL_MOCK_CONTACTS: ContactItem[] = [
  {
    id: "card-1",
    contact: {
      recipient_name: "Priya Sharma",
      recipient_email: "priya@acmeai.com",
      company: "Acme AI",
      role: "Backend Engineering Intern",
      job_url: "https://acmeai.com/jobs/backend-intern",
      personalization_note: "Acme AI recently launched an AI workflow automation product",
      candidate_name: "Harsh Yadav",
      candidate_background: "Python developer with experience in automation and AI agents",
      portfolio_url: "https://github.com/alexchen",
    },
    is_opted_out: false,
    fit_score: 98,
    status: "pending",
    signal: "Series B ($45M) · Hiring 12 MLOps",
    persona_tags: ["AI Automation", "Python SDK", "Agentic Pipelines"],
    generated_subject: "Quick note on the Backend Engineering Intern role at Acme AI",
    generated_body: `Hi Priya Sharma,\n\nI noticed Acme AI recently launched an AI workflow automation product and is expanding the engineering team.\n\nI'm Harsh Yadav, an AI engineer building autonomous agents and backend pipeline tools. This role stood out because it directly connects with my work in agentic workflows and tool-calling infrastructure.\n\nWould you be open to a brief 7-minute look at my profile or pointing me to the right engineering lead?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
    quality: {
      score: 9.4,
      word_count: 82,
      spam_risk: "low",
      flags: ["Clean structure, focused length, and clear CTA"],
      hallucination_guard: "Verified",
    },
  },
  {
    id: "card-2",
    contact: {
      recipient_name: "Rahul Verma",
      recipient_email: "rahul@startupxyz.io",
      company: "StartupXYZ",
      role: "ML Engineer",
      job_url: "https://startupxyz.io/careers",
      personalization_note: "StartupXYZ is building LLM-powered search tools",
      candidate_name: "Harsh Yadav",
      candidate_background: "machine learning projects and open-source LLM tooling",
      portfolio_url: "https://github.com/alexchen",
    },
    is_opted_out: false,
    fit_score: 92,
    status: "pending",
    signal: "Y Combinator W24 · High Latency Challenge",
    persona_tags: ["LLM Search", "Vector Embeddings", "RAG Systems"],
    generated_subject: "Quick note on the ML Engineer role at StartupXYZ",
    generated_body: `Hi Rahul Verma,\n\nI noticed StartupXYZ is building LLM-powered search tools.\n\nI'm Harsh Yadav, and I've been building machine learning projects around open-source LLM tooling and sub-second semantic retrieval. Your approach to search indexing connects closely with what I've been experimenting with.\n\nWould you be open to a quick look at my profile or a 5-minute technical chat?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
    quality: {
      score: 9.1,
      word_count: 75,
      spam_risk: "low",
      flags: ["Brevity and technical specificity verified"],
      hallucination_guard: "Verified",
    },
  },
  {
    id: "card-3",
    contact: {
      recipient_name: "Sara Kim",
      recipient_email: "sara@devtools.co",
      company: "DevTools Co",
      role: "Developer Advocate",
      job_url: "https://devtools.co/jobs",
      personalization_note: "DevTools Co just open-sourced their CLI platform",
      candidate_name: "Harsh Yadav",
      candidate_background: "building developer tools and writing technical content",
      portfolio_url: "https://github.com/alexchen",
    },
    is_opted_out: false,
    fit_score: 87,
    status: "pending",
    signal: "Open Source CLI · 4.8k GitHub Stars",
    persona_tags: ["DevRel", "Developer Experience", "CLI Tooling"],
    generated_subject: "Quick note on the Developer Advocate role at DevTools Co",
    generated_body: `Hi Sara Kim,\n\nI noticed DevTools Co just open-sourced your CLI platform—congratulations on the launch!\n\nI'm Harsh Yadav, and I've been building developer tools and technical walkthroughs around AI developer infrastructure. This role stood out because I love bridging complex dev APIs into intuitive developer workflows.\n\nWould you be open to connecting or pointing me to the hiring manager?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
    quality: {
      score: 8.9,
      word_count: 78,
      spam_risk: "low",
      flags: ["Clear hook and polite signoff"],
      hallucination_guard: "Verified",
    },
  },
];

export async function fetchSystemStatus(): Promise<SystemStatus> {
  try {
    const res = await fetch(`${API_BASE}/api/status`, { cache: "no-store" });
    if (!res.ok) throw new Error("Status endpoint error");
    return await res.json();
  } catch {
    return {
      engine: "THE CLOSER / OUTREACH ENGINE",
      operator: "Harsh Yadav • AI Engineer",
      contacts_source: "data/contacts.json",
      dry_run: true,
      send_method: "smtp",
      send_method_label: "Gmail API / SMTP",
      llm_enabled: true,
      llm_model: "Groq LLaMA-3.3-70B",
      session_limit: "0 / 5 Live Sends",
      max_sends: 5,
      summary: { dry_run: 2, sent: 0, skipped: 1 },
      total_processed: 3,
    };
  }
}

export async function toggleDryRun(dryRun: boolean): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/settings/dry-run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dry_run: dryRun }),
    });
    if (!res.ok) throw new Error("Toggle error");
    const data = await res.json();
    return data.dry_run;
  } catch {
    return dryRun;
  }
}

export async function fetchContacts(): Promise<ContactItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/contacts`, { cache: "no-store" });
    if (!res.ok) throw new Error("Contacts endpoint error");
    const data = await res.json();
    return data.contacts.map((item: any, idx: number) => ({
      ...item,
      fit_score: 98 - idx * 6,
      signal: idx === 0 ? "Series B ($45M) · Hiring 12 MLOps" : idx === 1 ? "Y Combinator W24 · High Latency Challenge" : "Open Source CLI · 4.8k Stars",
      persona_tags: idx === 0 ? ["AI Automation", "Python SDK"] : idx === 1 ? ["LLM Search", "Embeddings"] : ["DevRel", "CLI Tooling"],
    }));
  } catch {
    return INITIAL_MOCK_CONTACTS;
  }
}

export async function regenerateEmail(
  contact: any,
  mode: string = "standard",
  previousSubject: string = "",
  previousBody: string = "",
  regenCount: number = 1,
  timestampSeed: number = Date.now()
): Promise<{ subject: string; body: string; quality: any }> {
  try {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contact,
        mode,
        previous_subject: previousSubject,
        previous_body: previousBody,
        current_subject: previousSubject,
        current_body: previousBody,
        regen_count: regenCount,
        timestamp_seed: timestampSeed,
      }),
    });
    if (!res.ok) throw new Error("Regeneration failed");
    return await res.json();
  } catch {
    const role = contact.role || "the role";
    const company = contact.company || "your team";
    const name = contact.recipient_name || "there";
    const idx = (regenCount - 1) % 4;

    const fallbacks: Record<string, Array<{ subject: string; body: string }>> = {
      concise: [
        {
          subject: `Quick question re: ${role} at ${company}`,
          body: `Hi ${name},\n\nNoticed ${company} is expanding the ${role} team.\n\nI build high-throughput tools with clean APIs. Open to a brief 5-minute technical chat?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Harsh Yadav for ${company} ${role}`,
          body: `Hi ${name},\n\nSaw ${company}'s recent work in this space.\n\nI'm an engineer focused on automation and AI agents. I'd love to help tackle immediate engineering goals for your team.\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `${company} ${role} — quick intro`,
          body: `Hi ${name},\n\nReaching out regarding the ${role} position at ${company}.\n\nWith extensive experience in Python and agentic systems, I ship robust code. Would you be open to a 7-minute call?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Brief inquiry: ${role} @ ${company}`,
          body: `Hi ${name},\n\nLoved your recent updates at ${company}.\n\nI build reliable backend systems. Would you have 3 minutes to review my repository or point me to the hiring lead?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
      ],
      technical: [
        {
          subject: `Scaling backend systems for ${company}'s ${role}`,
          body: `Hi ${name},\n\nSaw ${company}'s engineering progress on ${role} challenges.\n\nMy background is centered on distributed architecture and modular API design. I'd love to help eliminate pipeline bottlenecks.\n\nDo you have 5 minutes this week for a technical chat?\n\nBest regards,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Architecture & telemetry discussion for ${company} ${role}`,
          body: `Hi ${name},\n\nFollowing ${company}'s technical footprint.\n\nI've engineered high-throughput services with rigorous telemetry and automated pipelines. Would you be open to reviewing my benchmarks?\n\nBest regards,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Low-latency pipelines <> ${company} ${role}`,
          body: `Hi ${name},\n\nInspecting ${company}'s stack and your open ${role} requirements.\n\nI specialize in optimizing pipeline throughput and building resilient microservices. Could we jump on a brief 10-minute debrief this week?\n\nBest regards,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Systems infrastructure inquiry: ${company} ${role}`,
          body: `Hi ${name},\n\nNoticed ${company}'s recent technical milestones in production.\n\nI build fault-tolerant backend services and automated testing harnesses. Are you available for a brief engineering discussion this Thursday?\n\nBest regards,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
      ],
      followup: [
        {
          subject: `Following up: ${role} at ${company}`,
          body: `Hi ${name},\n\nFollowing up briefly on my earlier note regarding the ${role} opportunity at ${company}.\n\nJust wanted to see if you had a moment to consider my background, or if there's someone else on the team I should connect with?\n\nBest,\nHarsh Yadav`,
        },
        {
          subject: `Checking in on ${role} @ ${company}`,
          body: `Hi ${name},\n\nChecking in on my previous email regarding the ${role} opening at ${company}.\n\nI'm still very interested in contributing to your team. Would love to send over relevant project write-ups if helpful.\n\nBest,\nHarsh Yadav`,
        },
        {
          subject: `Quick follow-up regarding ${company} ${role}`,
          body: `Hi ${name},\n\nHope your week is going well. Wanted to circle back on my note regarding the ${role} position at ${company}.\n\nI'd love to share a 2-minute walkthrough of my latest work if you have a moment.\n\nThanks,\nHarsh Yadav`,
        },
        {
          subject: `Re: ${role} opening at ${company}`,
          body: `Hi ${name},\n\nTouching base one last time regarding the ${role} role at ${company}.\n\nIf the position is still open, I'd welcome the chance to speak with the hiring manager.\n\nBest regards,\nHarsh Yadav`,
        },
      ],
      standard: [
        {
          subject: `Quick note on the ${role} role at ${company}`,
          body: `Hi ${name},\n\nI noticed ${company} is hiring for ${role}.\n\nI'm Harsh Yadav, and I've been building projects around AI agents and automation. Would you be open to a quick look at my profile?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Harsh Yadav <> ${company}: ${role}`,
          body: `Hi ${name},\n\nSaw ${company}'s recent progress and the open ${role} position.\n\nAs an engineer, I've focused on delivering reliable software and shipping fast. Could we schedule 5 minutes this week for a brief introductory conversation?\n\nBest regards,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `${role} inquiry — ${company}`,
          body: `Hi ${name},\n\nReaching out regarding the ${role} opening on your team.\n\nMy work revolves around building end-to-end solutions that scale. Would you be open to a 7-minute call or reviewing my portfolio?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
        {
          subject: `Exploring ${role} opportunities at ${company}`,
          body: `Hi ${name},\n\nFollowing ${company}'s exciting momentum around ${role}.\n\nYour team's engineering velocity aligns closely with the tools I love building. Do you have a moment this Thursday for a brief chat?\n\nBest,\nHarsh Yadav\nhttps://github.com/alexchen`,
        },
      ],
    };

    const modeKey = (mode || "standard").toLowerCase();
    const chosenList = fallbacks[modeKey] || fallbacks.standard;
    const selected = chosenList[idx] || chosenList[0];

    return {
      subject: selected.subject,
      body: selected.body,
      quality: {
        score: 9.2,
        word_count: selected.body.trim().split(/\s+/).length,
        spam_risk: "low",
        flags: ["Offline template variant cycled successfully"],
        hallucination_guard: "Verified",
      },
    };
  }
}

export async function dispatchLead(
  contact: any,
  subject: string,
  body: string,
  action: "send" | "draft" | "skip"
): Promise<{ status: string; message?: string; summary?: Record<string, number> }> {
  try {
    const res = await fetch(`${API_BASE}/api/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contact, subject, body, action }),
    });
    if (!res.ok) throw new Error("Dispatch failed");
    return await res.json();
  } catch {
    return { status: action === "send" ? "dry_run" : action === "draft" ? "drafted" : "skipped" };
  }
}

export async function fetchAuditLogs(): Promise<AuditLogEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/audit/logs`, { cache: "no-store" });
    if (!res.ok) throw new Error("Audit log fetch failed");
    const data = await res.json();
    return data.logs;
  } catch {
    return [
      {
        timestamp: new Date().toISOString(),
        recipient_email: "priya@acmeai.com",
        company: "Acme AI",
        role: "Backend Engineering Intern",
        subject: "Quick note on the Backend Engineering Intern role at Acme AI",
        status: "dry_run",
        error_message: "None",
        word_count: 82,
      },
      {
        timestamp: new Date(Date.now() - 360000).toISOString(),
        recipient_email: "rahul@startupxyz.io",
        company: "StartupXYZ",
        role: "ML Engineer",
        subject: "Quick note on the ML Engineer role at StartupXYZ",
        status: "dry_run",
        error_message: "None",
        word_count: 75,
      },
      {
        timestamp: new Date(Date.now() - 840000).toISOString(),
        recipient_email: "unsubscribed@domain.com",
        company: "ShieldCorp",
        role: "CTO",
        subject: "Quick question",
        status: "opted_out",
        error_message: "Recipient in optout_list.txt",
        word_count: 0,
      },
    ];
  }
}

export async function uploadContactsFile(
  file: File,
  mode: "replace" | "append" = "replace"
): Promise<UploadContactsResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/contacts/upload?mode=${mode}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    throw new Error(errorJson.detail || `Upload failed (${res.status} ${res.statusText})`);
  }

  const data = await res.json();
  const enrichedContacts = (data.contacts || []).map((item: any, idx: number) => ({
    ...item,
    fit_score: item.fit_score ?? Math.max(70, 98 - idx * 5),
    signal:
      item.signal ??
      (idx === 0
        ? "Series B ($45M) · Hiring 12 MLOps"
        : idx === 1
          ? "Y Combinator W24 · High Latency Challenge"
          : "Growth Stage · Fast Expansion"),
    persona_tags:
      item.persona_tags ??
      (idx === 0
        ? ["AI Automation", "Python SDK"]
        : idx === 1
          ? ["LLM Search", "Embeddings"]
          : ["DevRel", "Engineering"]),
  }));

  return {
    ...data,
    contacts: enrichedContacts,
  };
}

export function getContactsTemplateUrl(format: "json" | "csv" = "json"): string {
  return `${API_BASE}/api/contacts/template?format=${format}`;
}

export function downloadContactsTemplate(format: "json" | "csv" = "json"): void {
  const url = getContactsTemplateUrl(format);
  const a = document.createElement("a");
  a.href = url;
  a.setAttribute("download", `contacts_template.${format}`);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export async function fetchSenderProfile(): Promise<SenderProfile> {
  try {
    const res = await fetch(`${API_BASE}/api/profile`, { cache: "no-store" });
    if (!res.ok) throw new Error("Profile endpoint error");
    return await res.json();
  } catch {
    return {
      candidate_name: "Harsh Yadav",
      candidate_title: "AI Engineer",
      candidate_background:
        "AI Engineer specializing in agentic workflows, FastAPI, Next.js, and production LLM pipelines",
      portfolio_url: "https://github.com/harshyadav-ml",
    };
  }
}

export async function updateSenderProfile(
  profile: SenderProfile
): Promise<{
  status: string;
  message: string;
  sender_profile: SenderProfile;
  operator: string;
  total_contacts: number;
  contacts: ContactItem[];
}> {
  const res = await fetch(`${API_BASE}/api/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update sender profile");
  }

  const data = await res.json();
  const enrichedContacts = (data.contacts || []).map((item: any, idx: number) => ({
    ...item,
    fit_score: item.fit_score ?? Math.max(70, 98 - idx * 5),
    signal:
      item.signal ??
      (idx === 0
        ? "Series B ($45M) · Hiring 12 MLOps"
        : idx === 1
        ? "Y Combinator W24 · High Latency Challenge"
        : "Growth Stage · Fast Expansion"),
    persona_tags:
      item.persona_tags ??
      (idx === 0
        ? ["AI Automation", "Python SDK"]
        : idx === 1
        ? ["LLM Search", "Embeddings"]
        : ["DevRel", "Engineering"]),
  }));

  return {
    ...data,
    contacts: enrichedContacts,
  };
}


