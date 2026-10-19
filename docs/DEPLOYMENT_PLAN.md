# 🚀 THE CLOSER — Production Deployment Plan

> **Document Version:** 1.0
> **Generated:** 2026-10-19
> **Repository:** `Cold Email Parser` (Next.js 16 App Router + FastAPI 0.x)
> **Scope:** Complete Vercel production deployment blueprint — zero hand-waving, every file copy-pasteable.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Feasibility Analysis — Can We Deploy Everything on Vercel?](#2-feasibility-analysis)
3. [Architecture Comparison & Final Verdict](#3-architecture-comparison--final-verdict)
4. [Dry-Run Frontend Build Verification](#4-dry-run-frontend-build-verification)
5. [Exact Configuration Files](#5-exact-configuration-files)
6. [Step-by-Step Zero-Error Rollout Checklist](#6-step-by-step-zero-error-rollout-checklist)
7. [Post-Deployment Verification](#7-post-deployment-verification)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        THE CLOSER                                    │
├──────────────────────┬───────────────────────────────────────────────┤
│   FRONTEND           │   BACKEND                                     │
│   Next.js 16.4.2     │   FastAPI (Python 3.11+)                      │
│   App Router         │                                               │
│   React 19.3.0       │   src/closer/api.py         → REST API       │
│   Tailwind CSS v4    │   src/closer/input/loader.py → File I/O      │
│   TypeScript 5.x     │   src/closer/generation/    → LLM + Template │
│                      │   src/closer/delivery/      → SMTP + Gmail   │
│   Pages:             │   src/closer/audit/logger.py → CSV Logging   │
│   - / (Overview)     │   src/closer/config/        → Settings       │
│   - /compose         │                                               │
│   - /contacts        │   External Services:                          │
│   - /logs            │   - Groq API (LLM)                            │
│                      │   - Gmail SMTP / Gmail API                    │
├──────────────────────┴───────────────────────────────────────────────┤
│  DATA / STATE (Filesystem-Dependent)                                 │
│  - data/contacts.json      (read + write on every upload/profile)    │
│  - logs/outreach_log.csv   (append on every dispatch action)         │
│  - optout_list.txt         (read on every contact load + dispatch)   │
│  - outreach_log.csv        (root symlink → logs/outreach_log.csv)    │
│  - token.json              (Gmail OAuth credentials, read + refresh) │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Feasibility Analysis

### 2.1 Filesystem Write Audit

Every file the backend reads from or writes to on the local filesystem:

| File | Operation | Code Location | Vercel Impact |
|------|-----------|---------------|---------------|
| `data/contacts.json` | **READ + WRITE** | `loader.py` L169-183 (`save_contacts`), L186-223 (`load_contacts`) | 🔴 **FATAL** — Vercel's filesystem is read-only except `/tmp`. Writes to `data/contacts.json` will crash with `OSError: Read-only file system`. |
| `logs/outreach_log.csv` | **APPEND (every dispatch)** | `audit/logger.py` L134 (`log_entry`), L64-84 (`_ensure_header`) | 🔴 **FATAL** — Same read-only constraint. Every "Approve & Dispatch", "Save Dry Run", or "Skip Lead" action will fail. |
| `optout_list.txt` | **READ only** | `loader.py` L226-254 (`load_optout_list`) | 🟡 **OK if bundled** — Read-only is fine, but the file must be included in the deployment bundle. |
| `outreach_log.csv` (root) | **SYMLINK creation** | `audit/logger.py` L43-60 (`_sync_root_symlink`) | 🔴 **FATAL** — Symlink creation on read-only FS will fail (gracefully caught, but still broken). |
| `token.json` | **READ + WRITE** (OAuth token refresh) | `delivery/gmail.py` L77 | 🔴 **FATAL** — Token refresh writes back to disk. Gmail API OAuth flow is incompatible with serverless. |
| `credentials.json` | **READ only** | `delivery/gmail.py` L19 | 🟡 **OK if bundled** — But OAuth interactive flow cannot run in serverless. |

### 2.2 Serverless Timeout Risk Analysis

| Operation | Code Path | Estimated Duration | Vercel Limit (Hobby: 10s / Pro: 60s) | Risk |
|-----------|-----------|-------------------|---------------------------------------|------|
| **Groq LLM Generation** | `generation/llm.py` L200-206 | 2-8s per call (network bound) | Hobby: ⚠️ TIGHT / Pro: ✅ OK | Medium — LLM timeout is set to 30s (`LLM_TIMEOUT`). A slow Groq response + retry to `qwen/qwen3.8-27b` could exceed 10s on Hobby. |
| **SMTP Email Send** | `delivery/smtp.py` L55-64 | 1-5s per email (TLS handshake + send) | Hobby: ⚠️ / Pro: ✅ | Medium — SMTP connection establishment involves DNS + TLS + auth on every cold call (no connection pooling in serverless). |
| **Gmail API Send** | `delivery/gmail.py` L208-217 | 1-3s | ✅ OK | Low |
| **Contact Upload + Pre-generation** | `api.py` L296-438 | 2-15s (depends on contact count × LLM calls) | Hobby: 🔴 / Pro: ⚠️ | High — Uploading 10 contacts triggers 10 × `generate_email()` calls sequentially. With LLM enabled, this is 10 × 5s = 50s. |
| **Profile Update + Re-synthesis** | `api.py` L169-234 | Same as above | Same risk | High — Re-generates drafts for ALL contacts on profile change. |

### 2.3 In-Memory State Risk

| State | Location | Impact |
|-------|----------|--------|
| `sender_profile` (global dict) | `api.py` L64-69 | 🔴 Lost between invocations — Vercel serverless functions are stateless. Each request may hit a fresh cold-start. Profile updates won't persist. |
| `active_source_file` (global str) | `api.py` L62 | 🔴 Same — resets to `"data/contacts.json"` on every cold start. |
| `_generation_counters` (global dict) | `api.py` L480 | 🔴 Lost — regeneration counter resets on cold start, causing duplicate generations. |
| `settings.DRY_RUN` (toggled at runtime) | `api.py` L238-242 | 🔴 Lost — dry-run toggle resets to env var default on cold start. |
| `settings.LLM_SESSION_DISABLED` | `generation/llm.py` L144-151 | 🔴 Lost — rate-limit cooldown resets on cold start. |

---

## 3. Architecture Comparison & Final Verdict

### Architecture A: 100% Vercel Monorepo

Deploy Next.js frontend + FastAPI as Vercel Python Serverless Functions.

| Aspect | Assessment | Workaround Required |
|--------|------------|---------------------|
| **File Storage** | 🔴 Broken | Replace all `Path(...).write` / `open(..., "w")` calls with an external store. Options: **Vercel KV (Redis)**, **Vercel Postgres**, **Upstash Redis**, or **Supabase**. Every `save_contacts()`, `log_entry()`, `_ensure_header()` must be rewritten. |
| **In-Memory State** | 🔴 Broken | Move `sender_profile`, `_generation_counters`, `active_source_file`, `DRY_RUN` toggle to Vercel KV or Postgres. Every global variable must become a DB read/write. |
| **Timeouts** | ⚠️ Risky | Hobby tier (10s) is insufficient for LLM + contact upload. Pro tier (60s) works for most cases. Must add background processing for bulk uploads (Vercel Cron or async patterns). |
| **Gmail OAuth** | 🔴 Broken | Cannot run interactive OAuth flow. Must use SMTP App Password exclusively, or store refresh tokens in Vercel KV and handle refresh in-code (without writing `token.json`). |
| **SMTP** | ✅ Works | SMTP connections work in serverless (fire-and-forget per request). |
| **Groq LLM** | ✅ Works | HTTP API call — fully compatible with serverless. |
| **ASGI Bridge** | ⚠️ Complex | Requires `mangum` or Vercel's `@vercel/python` ASGI adapter to bridge FastAPI into a serverless handler. |

**Estimated Effort:** 15-25 hours of refactoring to make the backend fully stateless.

#### Required Code Changes for Architecture A (Summary)

1. Replace `save_contacts()` → Write to Vercel Postgres / KV
2. Replace `load_contacts()` → Read from Vercel Postgres / KV
3. Replace `log_entry()` → Append to Vercel Postgres / KV list
4. Replace `get_log_summary()` → Aggregate from Vercel Postgres / KV
5. Replace `load_optout_list()` → Read from Vercel KV or bundle as static asset
6. Remove `_sync_root_symlink()` entirely
7. Move all global state (`sender_profile`, `_generation_counters`, etc.) to Vercel KV
8. Remove `token.json` write-back; use SMTP-only or store OAuth tokens in KV
9. Add `mangum` ASGI adapter for Vercel Python runtime

---

### Architecture B: Hybrid (Recommended ✅)

Deploy Next.js on Vercel + FastAPI on Render/Railway (persistent server).

| Aspect | Assessment | Notes |
|--------|------------|-------|
| **File Storage** | ✅ Works out-of-the-box | Render/Railway provide persistent disk. `data/contacts.json`, `logs/outreach_log.csv`, `optout_list.txt` all work as-is. |
| **In-Memory State** | ✅ Works | Long-running server process keeps globals alive. `sender_profile`, `_generation_counters` persist for the session lifetime. |
| **Timeouts** | ✅ No limit | No serverless timeout — requests run as long as needed. |
| **Gmail OAuth** | ✅ Works | `token.json` can be refreshed and written back to persistent disk. |
| **SMTP** | ✅ Works | Can maintain connection pools for efficiency. |
| **Groq LLM** | ✅ Works | No change needed. |
| **CORS** | ⚠️ Config needed | Must update `CORSMiddleware` to include the Vercel production domain. |
| **Cost** | 💰 Free tier available | Render free tier: 750 hours/month. Railway: $5/month hobby plan with generous limits. |

**Estimated Effort:** 1-2 hours. Zero code refactoring needed for the backend.

---

### 🏆 FINAL VERDICT

> **Architecture B (Hybrid) is the clear winner.**
>
> The backend is fundamentally stateful — it writes to `data/contacts.json` on every upload and profile update, appends to `logs/outreach_log.csv` on every dispatch action, stores mutable global state in memory, and refreshes Gmail OAuth tokens on disk. Forcing this into Vercel's stateless serverless model would require rewriting ~40% of the backend and introducing a database dependency that doesn't exist today.
>
> **Go with: Next.js on Vercel + FastAPI on Render (free tier).**

However, both configuration sets are provided below so you have complete flexibility.

---

## 4. Dry-Run Frontend Build Verification

### 4.1 `package.json` Analysis

```json
// frontend/package.json — Current State
{
  "dependencies": {
    "lucide-react": "^1.59.0",
    "next": "16.4.2",
    "react": "19.3.0",
    "react-dom": "19.3.0"
  },
  "devDependencies": {
    "@tailwindcss/turbopack": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
```

**Status:** ✅ All dependencies are compatible and up-to-date. No missing peer dependencies.

### 4.2 `next.config.ts` Analysis

```typescript
// frontend/next.config.ts — Current State
const nextConfig: NextConfig = {
  cacheComponents: true,        // ⚠️ POTENTIAL ISSUE — see below
  partialPrefetching: true,     // ⚠️ POTENTIAL ISSUE — see below
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};
```

**Issues Found:**

| Issue | Severity | Details | Fix |
|-------|----------|---------|-----|
| `cacheComponents: true` | ⚠️ Medium | This is an **experimental** Next.js 16 flag. If Vercel's build environment uses a slightly different Next.js resolution, it could cause a warning or error. | Wrap in `experimental: { cacheComponents: true }` if build fails, or remove entirely for safety. |
| `partialPrefetching: true` | ⚠️ Medium | Same — experimental flag. May not be recognized in all build contexts. | Same as above. |
| `turbopack` rules | ✅ OK | Turbopack is used for `next dev` only. Production `next build` uses Webpack by default. This block is safely ignored during production builds. | No change needed. |
| **Missing `output: 'standalone'`** | ℹ️ Info | Not required for Vercel (Vercel handles output natively), but recommended if you ever want to self-host. | Optional addition. |

**Recommended `next.config.ts` for production (changes to make in source when ready):**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep experimental features wrapped properly
  experimental: {
    // cacheComponents: true,       // Uncomment if supported by your Next.js version
    // partialPrefetching: true,    // Uncomment if supported by your Next.js version
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
```

### 4.3 `tsconfig.json` Analysis

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "jsx": "react-jsx",
    "module": "esnext",
    "moduleResolution": "bundler",
    "paths": { "@/*": ["./*"] }
  }
}
```

**Issues Found:**

| Issue | Severity | Details | Fix |
|-------|----------|---------|-----|
| `"jsx": "react-jsx"` | ⚠️ Low | Next.js typically expects `"jsx": "preserve"` and handles JSX transformation itself. `"react-jsx"` may cause conflicts with Next.js's internal SWC compiler. However, if the project builds locally without errors, this is fine. | Change to `"preserve"` only if `next build` fails with JSX-related errors. |

### 4.4 `frontend/lib/api.ts` — API URL Analysis

```typescript
// Line 3 — Current State
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

**Status:** ✅ **Correctly implemented.** The frontend already reads from `NEXT_PUBLIC_API_URL` with a localhost fallback. This is the exact pattern needed for Vercel deployment.

**What to set in Vercel Dashboard:**

| Architecture | `NEXT_PUBLIC_API_URL` Value |
|-------------|---------------------------|
| **A (100% Vercel)** | Leave **unset** or set to `""` (empty string). API routes will be same-origin via `vercel.json` rewrites. Alternatively, set to the Vercel deployment URL (e.g., `https://the-closer.vercel.app`). |
| **B (Hybrid)** | Set to your Render/Railway backend URL, e.g., `https://the-closer-api.onrender.com` |

### 4.5 Potential `next build` Failure Points

| Check | Status | Notes |
|-------|--------|-------|
| ESLint config present? | ⚠️ No `.eslintrc` found | Next.js will use default ESLint during build. `next build` may emit warnings but should not fail. If it does, add `eslint: { ignoreDuringBuilds: true }` to `next.config.ts`. |
| TypeScript strict mode | ✅ Enabled | `strict: true` in tsconfig. If any type errors exist, `next build` will fail. Test locally with `cd frontend && npx next build` before deploying. |
| Missing env vars at build time | ⚠️ Low risk | `NEXT_PUBLIC_API_URL` is used at build time (it's a `NEXT_PUBLIC_*` var). If not set in Vercel, the fallback `http://localhost:8000` is baked in. For Architecture B, you **must** set this env var in Vercel **before** building. |
| `next lint` script missing | ℹ️ Info | The root `package.json` has `"lint": "npm --prefix frontend run lint"` but `frontend/package.json` has no `lint` script. This will cause `npm run lint` to fail if Vercel runs it, but Vercel doesn't run lint by default. |

---

## 5. Exact Configuration Files

### 5.1 `vercel.json` — Architecture A (100% Vercel Monorepo)

> Place this file at the **repository root** (`/vercel.json`).

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "version": 2,
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/index.py"
    }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "@vercel/python@4.3.1",
      "maxDuration": 60
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET, POST, PUT, DELETE, OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type, Authorization" }
      ]
    }
  ]
}
```

### 5.2 `vercel.json` — Architecture B (Hybrid — Recommended ✅)

> Place this file at the **repository root** (`/vercel.json`).
> Set **Root Directory** to `frontend` in Vercel Dashboard, OR use this config at the repo root.

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "version": 2,
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs"
}
```

**Alternative (simpler):** Instead of using `vercel.json`, set the **Root Directory** to `frontend` in the Vercel Dashboard → Project Settings → General → Root Directory. Then Vercel will auto-detect Next.js and use `npm run build` automatically. No `vercel.json` needed.

### 5.3 `api/index.py` — Vercel ASGI Bridge (Architecture A Only)

> Create this file at `<repo_root>/api/index.py`. This bridges FastAPI into Vercel's Python serverless runtime.

```python
"""api/index.py — Vercel Python Serverless ASGI bridge for FastAPI.

This file is the entrypoint for Vercel's @vercel/python runtime.
It imports the FastAPI app and wraps it with Mangum for AWS Lambda / Vercel compatibility.
"""
import sys
from pathlib import Path

# Ensure the project root is in sys.path so `from src.closer...` imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now import the FastAPI app
from src.closer.api import app

# Option 1: Use Mangum (recommended — handles ASGI → Lambda/Vercel translation)
# pip install mangum  (add to requirements.txt)
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Option 2: Direct ASGI export for Vercel's native Python runtime
    # Vercel's @vercel/python can handle ASGI apps directly if exported as `app`
    handler = app

# Vercel looks for a callable named `handler` or `app`
```

**Add to `requirements.txt` if using Mangum:**

```
python-dotenv
groq
google-api-python-client
google-auth-oauthlib
python-multipart
fastapi
uvicorn
mangum
pydantic
```

> ⚠️ **WARNING:** Architecture A requires `mangum` in `requirements.txt` AND significant refactoring of all filesystem operations. **Do not deploy Architecture A without completing the refactoring outlined in Section 3.**

### 5.4 `requirements.txt` — Production-Ready (Both Architectures)

> The current `requirements.txt` is missing critical packages. Here is the corrected version:

```
python-dotenv
groq
google-api-python-client
google-auth-oauthlib
python-multipart
fastapi
uvicorn[standard]
pydantic
```

**Add `mangum` only for Architecture A:**

```
mangum
```

**Remove `streamlit`** — it's not used by the FastAPI backend and adds 100+ MB of unnecessary dependencies.

### 5.5 Root `package.json` vs. Vercel Root Directory Setting

**Current root `package.json`:**

```json
{
  "name": "the-closer",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "npm --prefix frontend run dev",
    "build": "npm --prefix frontend run build",
    "start": "npm --prefix frontend run start",
    "lint": "npm --prefix frontend run lint"
  }
}
```

**Two valid approaches for Vercel:**

| Approach | Configuration | Pros | Cons |
|----------|--------------|------|------|
| **A) Root Directory = `frontend`** | Set in Vercel Dashboard → Settings → General → Root Directory = `frontend` | Simplest setup. Vercel auto-detects Next.js. No `vercel.json` needed for Arch B. | Cannot reference backend files in Vercel functions (Arch A incompatible). |
| **B) Root Directory = `.` (default)** | Keep root directory as `.`. Use `vercel.json` with custom `buildCommand`. | Required for Architecture A. Gives access to `src/`, `api/`, and `requirements.txt`. | Requires explicit `vercel.json` configuration. |

**Recommendation:**
- **Architecture A:** Root Directory = `.` (repo root) + `vercel.json` from Section 5.1
- **Architecture B:** Root Directory = `frontend` (no `vercel.json` needed, OR use Section 5.2)

### 5.6 FastAPI `CORSMiddleware` — Production Configuration

**Current state** (`src/closer/api.py` lines 79-85):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue:** The wildcard `"*"` is present but combined with `allow_credentials=True`. Per the CORS specification, **`allow_origins=["*"]` with `allow_credentials=True` is invalid** — browsers will reject credentials. FastAPI/Starlette silently allows this but it's technically non-conformant.

**Production fix (apply when deploying):**

```python
import os

# Read allowed origins from environment, with sensible defaults
_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]

if not _allowed_origins:
    _allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Add Vercel production domains
_vercel_url = os.getenv("VERCEL_URL")  # Auto-set by Vercel
_vercel_project_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")  # Auto-set by Vercel
if _vercel_url:
    _allowed_origins.append(f"https://{_vercel_url}")
if _vercel_project_url:
    _allowed_origins.append(f"https://{_vercel_project_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
```

**Quick-and-dirty alternative** (if you just want it to work immediately):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # <-- Changed to False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> **IMPORTANT:** For Architecture B, you **must** add your Vercel production URL to the `allow_origins` list on Render/Railway, otherwise all frontend API calls will fail with CORS errors in the browser.

---

## 6. Step-by-Step Zero-Error Rollout Checklist

### Architecture B Deployment (Recommended)

#### Phase 1: Deploy FastAPI Backend on Render

**Step 1.** Create a Render account at [render.com](https://render.com).

**Step 2.** Create a **New Web Service** → Connect your GitHub repo.

**Step 3.** Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `the-closer-api` |
| **Region** | Oregon (US West) or closest to your users |
| **Branch** | `main` |
| **Root Directory** | `.` (repo root) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn src.closer.api:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (or Starter $7/mo for always-on) |

**Step 4.** Add **Environment Variables** in Render Dashboard:

| Variable | Value | Required? |
|----------|-------|-----------|
| `SMTP_HOST` | `smtp.gmail.com` | ✅ Yes |
| `SMTP_PORT` | `587` | ✅ Yes |
| `SMTP_USER` | `your_email@gmail.com` | ✅ Yes (for live sends) |
| `SMTP_PASSWORD` | `your_16_char_app_password` | ✅ Yes (for live sends) |
| `SENDER_NAME` | `Harsh Yadav` | ✅ Yes |
| `DRY_RUN` | `true` | ✅ Yes (set to `false` for live sends) |
| `SEND_METHOD` | `smtp` | ✅ Yes |
| `LLM_ENABLED` | `true` | Optional |
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxx` | Optional (for LLM generation) |
| `MAX_SENDS_PER_SESSION` | `5` | Optional |
| `CORS_ALLOWED_ORIGINS` | `https://the-closer.vercel.app,https://the-closer-*.vercel.app` | ✅ Yes (after you know your Vercel URL) |

**Step 5.** Deploy. Wait for "Live" status. Note the URL (e.g., `https://the-closer-api.onrender.com`).

**Step 6.** Verify backend is live:

```bash
curl https://the-closer-api.onrender.com/api/status
```

Expected response: JSON with `"engine": "THE CLOSER / OUTREACH ENGINE"`.

---

#### Phase 2: Deploy Next.js Frontend on Vercel

**Step 7.** Create a Vercel account at [vercel.com](https://vercel.com).

**Step 8.** Import your GitHub repository → **New Project**.

**Step 9.** Configure the project:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (auto-detected) |
| **Output Directory** | `.next` (auto-detected) |
| **Install Command** | `npm install` (auto-detected) |
| **Node.js Version** | 20.x (or 22.x) |

**Step 10.** Add **Environment Variables** in Vercel Dashboard:

| Variable | Value | Required? |
|----------|-------|-----------|
| `NEXT_PUBLIC_API_URL` | `https://the-closer-api.onrender.com` | ✅ **CRITICAL** — This is the only env var the frontend needs. Without it, all API calls go to `http://localhost:8000` which doesn't exist in production. |

> ⚠️ **CAUTION:** `NEXT_PUBLIC_API_URL` is a **build-time** variable (it's prefixed with `NEXT_PUBLIC_`). It gets baked into the JavaScript bundle during `next build`. If you add or change this variable, you **must redeploy** the frontend for the change to take effect.

**Step 11.** Click **Deploy**. Wait for build to succeed.

**Step 12.** Once deployed, copy your Vercel production URL (e.g., `https://the-closer.vercel.app`).

**Step 13.** Go back to Render Dashboard → Add your Vercel URL to `CORS_ALLOWED_ORIGINS`:

```
https://the-closer.vercel.app,https://the-closer-git-main-*.vercel.app
```

Redeploy Render service to pick up the new CORS origins (or use the production CORS fix from Section 5.6 which reads from env vars dynamically).

---

#### Phase 3: Update Backend CORS (If Not Using Env-Based CORS)

If you choose not to implement the env-based CORS from Section 5.6, you need to hardcode your Vercel URL. **Changes to make in `src/closer/api.py`:**

```python
# Line 79-85 — Replace with:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://the-closer.vercel.app",           # <-- Your production domain
        "https://the-closer-git-main-*.vercel.app", # <-- Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### Phase 4: Update `requirements.txt`

The current `requirements.txt` is missing `fastapi`, `uvicorn`, and `pydantic`. Render's build will fail without them.

**Replace contents of `requirements.txt` with:**

```
python-dotenv
groq
google-api-python-client
google-auth-oauthlib
python-multipart
fastapi
uvicorn[standard]
pydantic
```

> **NOTE:** Remove `streamlit` — it's a 100+ MB dependency used only by the legacy `streamlit_app.py` and is not needed for the production FastAPI backend.

---

## 7. Post-Deployment Verification

### 7.1 Smoke Test Checklist

Run these tests **in order** after both services are live:

| # | Test | Command / Action | Expected Result |
|---|------|-----------------|-----------------|
| 1 | **Backend Health** | `curl https://YOUR-RENDER-URL/api/status` | JSON response with `engine`, `operator`, `dry_run: true` |
| 2 | **Frontend Loads** | Visit `https://YOUR-VERCEL-URL/` in browser | Dashboard renders with metrics ribbon, contact cards |
| 3 | **Frontend → Backend CORS** | Open browser DevTools → Network tab → Check `/api/status` call | ✅ 200 response, no CORS errors |
| 4 | **Contact Upload** | Click Upload button → Upload `contacts_template.json` | Contacts appear in the queue, drafts pre-generated |
| 5 | **Email Generation** | Navigate to `/compose` → Click "Regenerate" | New subject/body appear with quality score |
| 6 | **LLM Generation** (if `GROQ_API_KEY` set) | Same as above | Check Render logs for `[GROQ] Calling Groq API...` |
| 7 | **Dry Run Dispatch** | Click "Approve & Dispatch" with DRY_RUN=true | Status changes to `dry_run`, appears in `/logs` audit table |
| 8 | **Audit Logs** | Navigate to `/logs` | Table shows the dry_run entry with IST timestamp |
| 9 | **CSV Download** | Click "Export CSV" on `/logs` page | Browser downloads `outreach_log.csv` |
| 10 | **Sender Profile Update** | Click profile icon → Update name → Save | All contact drafts re-generate with new sender name |

### 7.2 Live SMTP Send Test (When Ready)

> ⚠️ **WARNING:** Only do this after confirming all dry-run tests pass.

1. Set `DRY_RUN=false` in Render environment variables
2. Redeploy Render service
3. Toggle "DRY RUN" to OFF in the frontend UI
4. Compose an email to **your own email address** (e.g., `harsh@gmail.com`)
5. Click "Approve & Dispatch"
6. Check your inbox for the email
7. Check `/logs` for status `sent` (not `dry_run`)
8. **Immediately set `DRY_RUN=true` again** after testing

### 7.3 Common Failure Modes & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Frontend shows mock data, not live contacts | `NEXT_PUBLIC_API_URL` not set or set incorrectly | Set in Vercel Dashboard → Redeploy |
| CORS error in browser console | Backend doesn't include Vercel domain in `allow_origins` | Update CORS config on Render → Redeploy |
| `500 Internal Server Error` on contact upload | `requirements.txt` missing `fastapi` or `python-multipart` | Update `requirements.txt` → Redeploy Render |
| LLM generation returns template fallback | `GROQ_API_KEY` not set on Render | Add env var → Redeploy Render |
| SMTP send fails with `EnvironmentError` | `SMTP_USER` / `SMTP_PASSWORD` not set | Add env vars → Redeploy Render |
| SMTP send fails with `SMTPAuthenticationError` | Gmail App Password wrong or 2FA not enabled | Generate new App Password in Google Account → Security → App Passwords |
| `ModuleNotFoundError: No module named 'src'` | Render start command running from wrong directory | Ensure Root Directory = `.` and start command uses `src.closer.api:app` |
| Build fails: `cacheComponents is not a valid config` | Next.js version doesn't support this experimental flag | Remove `cacheComponents` and `partialPrefetching` from `next.config.ts` |
| Render free tier "spinning down" (cold starts) | Free tier spins down after 15min of inactivity | Upgrade to Starter ($7/mo) or set up a health-check ping with UptimeRobot |

---

## Appendix A: Full Environment Variables Reference

### Backend (Render/Railway)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | ✅ | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | ✅ | `587` | SMTP server port (TLS) |
| `SMTP_USER` | ✅ | `""` | Gmail address for sending |
| `SMTP_PASSWORD` | ✅ | `""` | Gmail App Password (16-char) |
| `SENDER_NAME` | ✅ | `""` | Display name in From header |
| `DRY_RUN` | ✅ | `true` | Safety flag — `true` prevents real sends |
| `SEND_METHOD` | ✅ | `smtp` | `smtp` or `gmail_api` |
| `MAX_SENDS_PER_SESSION` | Optional | `5` | Max live sends per session |
| `LLM_ENABLED` | Optional | `false` | Enable Groq LLM generation |
| `GROQ_API_KEY` | Optional | `""` | Groq API key (auto-enables LLM) |
| `LLM_MODEL` | Optional | `openai/gpt-oss-120b` | Groq model name |
| `LLM_TIMEOUT` | Optional | `30.0` | LLM API timeout in seconds |
| `CORS_ALLOWED_ORIGINS` | ✅ (Hybrid) | localhost only | Comma-separated list of allowed origins |

### Frontend (Vercel)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost:8000` | Backend API base URL (build-time) |

---

## Appendix B: Architecture A — Vercel Python Function File Layout

> Only relevant if you choose to refactor for 100% Vercel. Provided for reference.

```
/                          ← Vercel Root Directory = "."
├── api/
│   └── index.py           ← Vercel Python serverless entrypoint (Section 5.3)
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── next.config.ts
├── src/
│   └── closer/
│       ├── api.py          ← FastAPI app (imported by api/index.py)
│       ├── ...
├── requirements.txt        ← Python deps (must include mangum)
├── vercel.json             ← Unified config (Section 5.1)
└── package.json            ← Root scripts (delegates to frontend/)
```

---

## Appendix C: Gmail App Password Setup

To send real emails via SMTP, you need a Gmail App Password (not your regular password):

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Navigate to **Security** → **2-Step Verification** (must be enabled)
3. At the bottom, click **App passwords**
4. Select **Mail** → **Other (Custom name)** → Enter "The Closer"
5. Click **Generate** → Copy the 16-character password
6. Set this as `SMTP_PASSWORD` in your Render environment variables

---

> **End of Deployment Plan.**
> Zero existing files were modified. This document is your complete, self-contained deployment blueprint.
