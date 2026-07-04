# Videx — AI-Powered Video Reverse-Engineering Platform
### Principal Architect System Design Document

> **Platform Codename:** `VIDEX`  
> **Version:** 1.0 — Production-Ready Architecture  
> **AI Engine:** MiMo V2.5 (Xiaomi) — 310B MoE, Native Video Understanding  
> **Stack:** Next.js 15 · FastAPI · PostgreSQL · Redis · Cloudinary · Framer Motion

---

## Vision & Problem Statement

VIDEX is a reverse-engineering platform: users upload any video, and the platform outputs production-quality, physics-compliant **Text-to-Video prompts** by running the video through a structured AI pipeline. The output is precise enough to be dropped directly into any T2V generator (Sora, Kling, Wan2.1, etc.).

The UX is "antigravity" — floating cards, weightless transitions, levitating chips — built with Framer Motion and Tailwind CSS.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│  Next.js 15 (App Router) + Tailwind CSS + Framer Motion             │
│  Vercel Edge Network CDN                                            │
└────────────────────┬────────────────────────────────────────────────┘
                     │ HTTPS / REST / SSE
┌────────────────────▼────────────────────────────────────────────────┐
│                        API GATEWAY LAYER                            │
│  FastAPI (Python 3.12) — Async, Pydantic v2                         │
│  JWT Auth · Rate Limiting · CORS · OpenAPI Docs                     │
└────┬──────────────┬───────────────┬────────────────┬────────────────┘
     │              │               │                │
┌────▼───┐   ┌──────▼─────┐  ┌─────▼──────┐  ┌─────▼──────┐
│ Auth   │   │  Upload    │  │  Analysis  │  │  Prompt    │
│Service │   │  Service   │  │  Service   │  │  Engine    │
│(JWT)   │   │(Cloudinary)│  │ (MiMo V2.5)│  │(Detractor) │
└────┬───┘   └──────┬─────┘  └─────┬──────┘  └─────┬──────┘
     │              │               │                │
┌────▼──────────────▼───────────────▼────────────────▼───────────────┐
│                     DATA & INFRASTRUCTURE                           │
│  PostgreSQL (primary) · Redis (cache/jobs/SSE) · Celery Workers     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step System Design Flowchart

```mermaid
flowchart TD
    A([🎬 User Opens VIDEX]) --> B[Landing / Dashboard\nNext.js App Router]
    B --> C{Authenticated?}
    C -- No --> D[Auth Page\nEmail + Google OAuth]
    D --> B
    C -- Yes --> E[Upload Zone\nDrag-and-Drop or Browse]
    
    E --> F[/api/upload/signature\nFastAPI generates\nCloudinary signed URL/]
    F --> G[Direct Upload to Cloudinary\nClient → CDN\nNo backend bandwidth used]
    G --> H{Upload Success?}
    H -- Error --> E
    H -- Yes → secure_url --> I

    subgraph STEP1 ["⚡ STEP 1 — Analysis Engine"]
        I[POST /api/analyze\nbody: cloudinary_url, job_id] --> J[Celery Task Queued\nRedis Broker]
        J --> K[Worker: Call MiMo V2.5\nPOST api.xiaomimimo.com\nvideo_url + System Prompt]
        K --> L[MiMo Returns\nStructured JSON Analysis]
        L --> M[Parse & Validate\nPydantic Model]
        M --> N[(PostgreSQL\nSave job + analysis)]
        N --> O[SSE Push to Frontend\nevent: analysis_complete]
    end

    O --> P[Frontend Renders:\n• Scene Summary Card\n• 3 Style Option Pills\nAll animated with Framer Motion]

    subgraph STEP2 ["🎨 STEP 2 — Interactive Customization"]
        P --> Q[User Selects Options\nFloating Chip Selectors]
        Q --> R1[⏱ Duration: 8s / 10s / 15s]
        Q --> R2[📐 Aspect Ratio: 16:9 / 9:16 / 1:1]
        Q --> R3[🎭 Style: Original / Cinematic / Documentary]
        R1 & R2 & R3 --> S[User Clicks 'Generate Prompt']
    end

    subgraph STEP3 ["🔮 STEP 3 — Detractor Prompt Engine"]
        S --> T[POST /api/generate-prompt\nbody: analysis_id + user_choices]
        T --> U[Celery Task: Call MiMo V2.5\nDetractor System Prompt\n+ original analysis + user params]
        U --> V[MiMo Returns\nFinal Prompt JSON]
        V --> W[Parse, Validate & Score\nPydantic + Physics Compliance Check]
        W --> X[(PostgreSQL\nSave prompt + metadata)]
        X --> Y[SSE Push: prompt_ready]
    end

    Y --> Z[Frontend: Prompt Result Panel\n• Copy-to-Clipboard\n• Download JSON\n• Save to History\n• Share Link]
    Z --> ZA([✅ Done — User can start again])

    style STEP1 fill:#1a1a2e,stroke:#6c63ff,color:#fff
    style STEP2 fill:#16213e,stroke:#f72585,color:#fff
    style STEP3 fill:#0f3460,stroke:#4cc9f0,color:#fff
```

---

## Boilerplate Folder Structure

### Frontend — `videx-frontend/`
```
videx-frontend/
├── app/                                 # Next.js App Router
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx                # Auth page (Clerk or NextAuth)
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx                  # Dashboard shell with nav
│   │   ├── page.tsx                    # Main upload + analysis view
│   │   └── history/
│   │       └── page.tsx                # Saved prompts history
│   ├── api/
│   │   └── auth/[...nextauth]/
│   │       └── route.ts                # NextAuth API handler
│   ├── globals.css                     # Tailwind base + custom tokens
│   ├── layout.tsx                      # Root layout (fonts, providers)
│   └── page.tsx                        # Landing / marketing page
│
├── components/
│   ├── ui/                             # Primitive UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   └── Spinner.tsx
│   ├── antigravity/                    # Framer Motion physics components
│   │   ├── FloatingCard.tsx            # Levitating card wrapper
│   │   ├── FloatingChip.tsx            # Interactive selection pill
│   │   ├── WeightlessTransition.tsx    # Page/section transitions
│   │   ├── ParticleField.tsx           # Background particle system
│   │   └── GravityText.tsx             # Text with drift animations
│   ├── upload/
│   │   ├── DropZone.tsx                # Drag-and-drop video uploader
│   │   ├── UploadProgress.tsx          # Animated upload progress
│   │   └── VideoPreview.tsx            # Thumbnail preview
│   ├── analysis/
│   │   ├── AnalysisLoader.tsx          # SSE loading state UI
│   │   ├── SceneSummaryCard.tsx        # Step 1 result display
│   │   └── StyleOptionPills.tsx        # 3 floating style selectors
│   ├── customization/
│   │   ├── DurationSelector.tsx        # 8s / 10s / 15s chip group
│   │   ├── AspectRatioSelector.tsx     # Ratio selector chips
│   │   └── CustomizationPanel.tsx     # Combined Step 2 panel
│   ├── prompt/
│   │   ├── PromptResultCard.tsx        # Final prompt display
│   │   ├── PromptCopyButton.tsx        # Copy to clipboard
│   │   ├── PromptDownload.tsx          # Export as JSON
│   │   └── PromptShareLink.tsx         # Shareable link gen
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── providers/
│       ├── QueryProvider.tsx           # TanStack Query
│       ├── MotionProvider.tsx          # Framer Motion config
│       └── ThemeProvider.tsx           # Dark/light theme
│
├── hooks/
│   ├── useUpload.ts                    # Cloudinary upload logic
│   ├── useSSE.ts                       # Server-Sent Events listener
│   ├── useAnalysis.ts                  # Analysis polling/SSE state
│   └── usePromptGeneration.ts          # Final prompt generation state
│
├── lib/
│   ├── api.ts                          # Typed API client (axios/fetch)
│   ├── cloudinary.ts                   # Cloudinary client helpers
│   ├── constants.ts                    # App-wide constants
│   └── utils.ts                        # Utility functions
│
├── store/
│   └── videx.store.ts                  # Zustand global state
│
├── types/
│   ├── api.types.ts                    # Auto-generated from FastAPI OpenAPI
│   ├── analysis.types.ts
│   └── prompt.types.ts
│
├── public/
│   ├── fonts/
│   └── images/
│
├── tailwind.config.ts                  # Extended Tailwind config
├── next.config.ts                      # Next.js config (env, rewrites)
├── tsconfig.json
└── package.json
```

### Backend — `videx-backend/`
```
videx-backend/
├── app/
│   ├── main.py                         # FastAPI app factory, CORS, startup
│   ├── config.py                       # Settings via pydantic-settings
│   ├── dependencies.py                 # DI: db sessions, auth, rate limiter
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py               # APIRouter aggregator
│   │       ├── endpoints/
│   │       │   ├── auth.py             # POST /auth/login, /auth/refresh
│   │       │   ├── upload.py           # POST /upload/signature
│   │       │   ├── analyze.py          # POST /analyze, GET /analyze/{job_id}
│   │       │   ├── prompts.py          # POST /generate-prompt, GET /prompts
│   │       │   ├── stream.py           # GET /stream/{job_id} (SSE)
│   │       │   └── health.py           # GET /health
│   │       └── middleware/
│   │           ├── auth_middleware.py  # JWT verification
│   │           └── rate_limit.py       # Sliding window rate limiter
│   │
│   ├── services/
│   │   ├── cloudinary_service.py       # Signature generation, URL validation
│   │   ├── mimo_service.py             # MiMo V2.5 API client
│   │   ├── analysis_service.py         # Step 1 orchestration
│   │   ├── prompt_service.py           # Step 3 Detractor Engine
│   │   └── sse_service.py              # Redis pub/sub → SSE bridge
│   │
│   ├── tasks/
│   │   ├── celery_app.py               # Celery + Redis config
│   │   ├── analyze_task.py             # Async video analysis job
│   │   └── prompt_task.py              # Async prompt generation job
│   │
│   ├── models/                         # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── job.py
│   │   └── prompt.py
│   │
│   ├── schemas/                        # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   └── prompt.py
│   │
│   ├── db/
│   │   ├── session.py                  # Async SQLAlchemy engine
│   │   └── migrations/                 # Alembic migrations
│   │       ├── env.py
│   │       └── versions/
│   │
│   └── core/
│       ├── security.py                 # JWT, password hashing
│       ├── prompts/                    # MiMo system prompt templates
│       │   ├── analysis_system.txt     # Step 1 analysis prompt
│       │   └── detractor_system.txt    # Step 3 detractor prompt
│       └── exceptions.py
│
├── tests/
│   ├── unit/
│   │   ├── test_mimo_service.py
│   │   ├── test_cloudinary_service.py
│   │   └── test_prompt_service.py
│   └── integration/
│       ├── test_analyze_endpoint.py
│       └── test_prompt_endpoint.py
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── alembic.ini
├── pyproject.toml
└── .env.example
```

---

## Database Schema (PostgreSQL)

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid        id              PK
        varchar     email           UK
        varchar     name
        varchar     avatar_url
        varchar     provider        "google|email"
        varchar     provider_id
        timestamp   created_at
        timestamp   updated_at
    }

    JOBS {
        uuid        id              PK
        uuid        user_id         FK
        varchar     status          "queued|processing|analysis_done|prompt_done|failed"
        varchar     cloudinary_url
        varchar     cloudinary_public_id
        integer     video_duration_seconds
        jsonb       analysis_result
        timestamp   analysis_completed_at
        timestamp   created_at
        timestamp   updated_at
    }

    ANALYSIS_RESULTS {
        uuid        id              PK
        uuid        job_id          FK
        text        scene_summary
        jsonb       physical_properties
        jsonb       style_options
        text        raw_mimo_response
        float       confidence_score
        timestamp   created_at
    }

    PROMPT_CONFIGS {
        uuid        id              PK
        uuid        job_id          FK
        uuid        analysis_id     FK
        varchar     selected_style  "original|cinematic|documentary"
        varchar     duration        "8s|10s|15s"
        varchar     aspect_ratio    "16:9|9:16|1:1"
        integer     frame_rate
        jsonb       custom_overrides
        timestamp   created_at
    }

    GENERATED_PROMPTS {
        uuid        id              PK
        uuid        job_id          FK
        uuid        config_id       FK
        text        final_prompt
        jsonb       prompt_metadata
        float       physics_score
        float       quality_score
        varchar     share_token     UK
        boolean     is_public
        integer     copy_count
        timestamp   created_at
    }

    USERS        ||--o{ JOBS               : "owns"
    JOBS         ||--|| ANALYSIS_RESULTS   : "produces"
    JOBS         ||--o{ PROMPT_CONFIGS     : "has many"
    PROMPT_CONFIGS ||--|| GENERATED_PROMPTS : "generates"
```

### Raw SQL Schema
```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    name            VARCHAR(255),
    avatar_url      TEXT,
    provider        VARCHAR(50) NOT NULL DEFAULT 'email',
    provider_id     VARCHAR(255),
    hashed_password VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- JOBS
CREATE TABLE jobs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status                  VARCHAR(50) NOT NULL DEFAULT 'queued',
    cloudinary_url          TEXT NOT NULL,
    cloudinary_public_id    VARCHAR(255) NOT NULL,
    video_duration_seconds  INTEGER,
    analysis_result         JSONB,
    error_message           TEXT,
    analysis_completed_at   TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jobs_status_check CHECK (
        status IN ('queued', 'processing', 'analysis_done', 'generating_prompt', 'prompt_done', 'failed')
    )
);

-- ANALYSIS RESULTS
CREATE TABLE analysis_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    scene_summary       TEXT NOT NULL,
    physical_properties JSONB NOT NULL DEFAULT '{}',
    style_options       JSONB NOT NULL DEFAULT '[]',
    raw_mimo_response   TEXT,
    confidence_score    FLOAT DEFAULT 0.0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PROMPT CONFIGS
CREATE TABLE prompt_configs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id           UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    analysis_id      UUID NOT NULL REFERENCES analysis_results(id),
    selected_style   VARCHAR(50) NOT NULL DEFAULT 'original',
    duration         VARCHAR(10) NOT NULL DEFAULT '8s',
    aspect_ratio     VARCHAR(10) NOT NULL DEFAULT '16:9',
    frame_rate       INTEGER NOT NULL DEFAULT 24,
    custom_overrides JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT prompt_configs_style_check CHECK (
        selected_style IN ('original', 'cinematic', 'documentary')
    ),
    CONSTRAINT prompt_configs_duration_check CHECK (
        duration IN ('8s', '10s', '15s')
    ),
    CONSTRAINT prompt_configs_ratio_check CHECK (
        aspect_ratio IN ('16:9', '9:16', '1:1')
    )
);

-- GENERATED PROMPTS
CREATE TABLE generated_prompts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    config_id       UUID NOT NULL REFERENCES prompt_configs(id),
    final_prompt    TEXT NOT NULL,
    prompt_metadata JSONB NOT NULL DEFAULT '{}',
    physics_score   FLOAT DEFAULT 0.0,
    quality_score   FLOAT DEFAULT 0.0,
    share_token     VARCHAR(64) UNIQUE,
    is_public       BOOLEAN NOT NULL DEFAULT FALSE,
    copy_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_generated_prompts_share_token ON generated_prompts(share_token);
CREATE INDEX idx_generated_prompts_job_id ON generated_prompts(job_id);
```

---

## API Contract (FastAPI Pydantic Schemas)

### Step 1 — Analysis Response Schema
```python
# schemas/analysis.py

class StyleOption(BaseModel):
    id: str                     # "original" | "cinematic" | "documentary"
    label: str                  # "Original Style"
    description: str            # "Faithful to source material..."
    mood_tags: list[str]        # ["naturalistic", "raw", "authentic"]
    color_grading: str          # "Log-flat, true-to-life"
    camera_movement: str        # "Static, handheld"

class PhysicalProperties(BaseModel):
    lighting: str
    camera_angle: str
    depth_of_field: str
    motion_blur: str
    color_temperature: str
    environment: str
    time_of_day: str
    weather_conditions: str | None

class AnalysisResult(BaseModel):
    job_id: UUID
    scene_summary: str
    physical_properties: PhysicalProperties
    style_options: list[StyleOption]   # Always exactly 3 options
    confidence_score: float            # 0.0 - 1.0
```

### Step 3 — Final Prompt Output Schema
```python
# schemas/prompt.py

class GeneratedPromptResponse(BaseModel):
    prompt_id: UUID
    job_id: UUID
    final_prompt: str              # The actual T2V prompt text
    metadata: PromptMetadata
    physics_score: float           # How physics-compliant (0-1)
    quality_score: float           # Overall quality estimate (0-1)
    share_token: str               # For sharing

class PromptMetadata(BaseModel):
    duration: str                  # "8s"
    aspect_ratio: str              # "16:9"
    selected_style: str            # "cinematic"
    frame_rate: int                # 24
    camera_specs: str              # "Sony FX6, 85mm f/1.4"
    lighting_setup: str            # "Golden hour, backlit"
    motion_description: str        # "Slow push in, 2°/s"
    physics_notes: list[str]       # ["Gravity confirmed", "Fluid dynamics plausible"]
    recommended_models: list[str]  # ["Sora", "Kling 2.0", "Wan2.1"]
    tags: list[str]
```

---

## MiMo V2.5 System Prompt Architecture

### Step 1 — Analysis System Prompt (Stored in `core/prompts/analysis_system.txt`)
```
You are an expert cinematography analyst and physics-compliance engine.

Analyze the provided video and return a STRICT JSON object with the following structure.
Do NOT include any text outside the JSON block.

{
  "scene_summary": "<detailed paragraph describing the complete scene>",
  "physical_properties": {
    "lighting": "<describe lighting setup>",
    "camera_angle": "<angle and position>",
    "depth_of_field": "<bokeh, focus plane>",
    "motion_blur": "<amount and direction>",
    "color_temperature": "<Kelvin estimate>",
    "environment": "<indoor/outdoor, setting>",
    "time_of_day": "<dawn/midday/dusk/night>",
    "weather_conditions": "<if applicable>"
  },
  "style_options": [
    {
      "id": "original",
      "label": "Original Style",
      "description": "<faithful reconstruction>",
      "mood_tags": ["<tag1>", "<tag2>"],
      "color_grading": "<describe>",
      "camera_movement": "<describe>"
    },
    {
      "id": "cinematic",
      "label": "Cinematic Alternate",
      "description": "<elevated, film-like variant>",
      "mood_tags": ["<tag1>", "<tag2>"],
      "color_grading": "<describe>",
      "camera_movement": "<describe>"
    },
    {
      "id": "documentary",
      "label": "Documentary Style",
      "description": "<raw, observational variant>",
      "mood_tags": ["<tag1>", "<tag2>"],
      "color_grading": "<describe>",
      "camera_movement": "<describe>"
    }
  ],
  "confidence_score": <float between 0 and 1>
}
```

### Step 3 — Detractor Engine System Prompt (Stored in `core/prompts/detractor_system.txt`)
```
You are the VIDEX Detractor Prompt Engine — an expert Text-to-Video prompt architect.

You will receive:
1. A structured video analysis JSON (scene_summary, physical_properties, chosen_style)
2. User preferences: duration, aspect_ratio, selected_style

Your mission: Output a SINGLE unified, production-quality Text-to-Video prompt that is:
- Physics-compliant (respect gravity, motion blur, lighting physics)
- Ultra-descriptive (camera lens, f-stop, ISO, movement speed)
- Temporally structured (describe action over the specified duration)
- Style-consistent with the selected aesthetic option

Return STRICT JSON only:
{
  "final_prompt": "<the complete T2V prompt, 150-300 words>",
  "metadata": {
    "duration": "<Xs>",
    "aspect_ratio": "<ratio>",
    "frame_rate": <int>,
    "camera_specs": "<camera body + lens>",
    "lighting_setup": "<lighting description>",
    "motion_description": "<camera movement>",
    "physics_notes": ["<note1>", "<note2>"],
    "recommended_models": ["<model1>", "<model2>"]
  },
  "physics_score": <float 0-1>,
  "quality_score": <float 0-1>,
  "tags": ["<tag1>", "<tag2>"]
}
```

---

## Key Service Implementations

### MiMo Service (`services/mimo_service.py`)
```python
import httpx
from app.config import settings

MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"

class MiMoService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {
            "api-key": settings.MIMO_API_KEY,
            "Content-Type": "application/json"
        }

    async def analyze_video(self, video_url: str, system_prompt: str) -> dict:
        payload = {
            "model": "mimo-v2.5",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {"url": video_url},
                            "fps": 2,
                            "media_resolution": "default"
                        },
                        {
                            "type": "text",
                            "text": "Analyze this video and return the structured JSON as instructed."
                        }
                    ]
                }
            ],
            "max_completion_tokens": 2048,
            "response_format": {"type": "json_object"}
        }
        response = await self.client.post(
            MIMO_API_URL, 
            json=payload, 
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

### SSE Streaming (`api/v1/endpoints/stream.py`)
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.sse_service import SSEService
import asyncio, json

router = APIRouter()

@router.get("/stream/{job_id}")
async def stream_job_events(job_id: str):
    async def event_generator():
        pubsub = await SSEService.subscribe(f"job:{job_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        finally:
            await pubsub.unsubscribe(f"job:{job_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

---

## Antigravity UI — Key Framer Motion Patterns

### FloatingCard Component
```tsx
// components/antigravity/FloatingCard.tsx
'use client'
import { motion } from 'framer-motion'

export function FloatingCard({ children, delay = 0 }: FloatingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.95 }}
      animate={{
        opacity: 1,
        y: [0, -8, 0],          // Continuous float
        scale: 1,
      }}
      transition={{
        opacity: { duration: 0.4, delay },
        scale:   { duration: 0.4, delay },
        y: {
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
          delay: delay + 0.4
        }
      }}
      whileHover={{ y: -16, scale: 1.02, transition: { duration: 0.2 } }}
      className="backdrop-blur-xl bg-white/5 border border-white/10 
                 rounded-2xl shadow-2xl shadow-black/40 p-6"
    >
      {children}
    </motion.div>
  )
}
```

### FloatingChip Selector
```tsx
// components/antigravity/FloatingChip.tsx
'use client'
import { motion } from 'framer-motion'

export function FloatingChip({ label, selected, onClick }: ChipProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ y: -4, scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      animate={selected ? {
        boxShadow: "0 0 20px rgba(99, 102, 241, 0.6)",
        backgroundColor: "rgba(99, 102, 241, 0.3)"
      } : {
        boxShadow: "0 0 0px rgba(99, 102, 241, 0)",
        backgroundColor: "rgba(255, 255, 255, 0.05)"
      }}
      className="px-5 py-2.5 rounded-full border border-white/10 
                 text-sm font-medium text-white cursor-pointer
                 transition-colors duration-200"
    >
      {label}
    </motion.button>
  )
}
```

---

## Environment Variables

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=your_cloud_name
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Backend (`.env`)
```env
# App
APP_NAME=VIDEX
DEBUG=false
SECRET_KEY=your_super_secret_jwt_key
ALLOWED_ORIGINS=http://localhost:3000,https://videx.app

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/videx_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# MiMo AI
MIMO_API_KEY=your_mimo_api_key
MIMO_API_URL=https://api.xiaomimimo.com/v1/chat/completions
MIMO_MODEL=mimo-v2.5
MIMO_MAX_TOKENS=2048

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## Infrastructure & Deployment

### Docker Compose (`docker/docker-compose.yml`)
```yaml
version: '3.9'
services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    env_file: .env
    depends_on: [db, redis]
    volumes:
      - ./app:/app/app

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    env_file: .env
    depends_on: [db, redis]
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: videx_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Production Deployment Targets

| Service | Platform | Notes |
|:---|:---|:---|
| **Frontend** | Vercel | Auto CI/CD from `main` branch |
| **FastAPI** | Railway / Render | Dockerized, auto-scale |
| **Celery Workers** | Railway / Render | Separate worker service |
| **PostgreSQL** | Railway / Supabase | Managed, daily backups |
| **Redis** | Railway / Upstash | Serverless Redis |
| **Video CDN** | Cloudinary | Auto-expiring temp storage |
| **Monitoring** | Sentry + Datadog | Error tracking + APM |

---

## Security Architecture

| Layer | Mechanism |
|:---|:---|
| **Auth** | JWT Access (15min) + Refresh Tokens (7 days) |
| **API Security** | HTTPS only, CORS whitelist, Helmet headers |
| **Rate Limiting** | 10 uploads/hr, 50 prompts/day per user |
| **File Validation** | Cloudinary webhook validates MIME type server-side |
| **Secret Management** | Env vars via Railway/Render Secrets, never in code |
| **DB** | Parameterized queries via SQLAlchemy, no raw SQL |
| **Cloudinary** | Signed uploads only, API secret stays on backend |
| **MiMo URLs** | Cloudinary URLs auto-expire after 24 hours |

---

## Open Questions

> [!IMPORTANT]
> **Q1 — Authentication Strategy:** Should VIDEX support anonymous/guest users with limited free credits (e.g., 3 prompts before sign-up), or require full registration before upload?

> [!IMPORTANT]  
> **Q2 — Credit System:** Should there be a credit/quota system (e.g., pay-per-prompt via Stripe), or is this MVP free-tier first?

> [!IMPORTANT]
> **Q3 — Video Size Limits:** What is the max video file size/duration for uploads? (Cloudinary free tier: 100MB max, 10s video limit without paid plan)

> [!NOTE]
> **Q4 — Auth Provider:** Clerk vs. NextAuth vs. Supabase Auth — any preference, or should the plan default to Clerk for ease of integration?

> [!NOTE]
> **Q5 — Monorepo vs. Two Repos:** Should `videx-frontend` and `videx-backend` live in a single Turborepo monorepo, or separate repositories?

---

## Verification Plan

### Automated Tests
```bash
# Backend unit + integration tests
cd videx-backend && pytest tests/ -v --cov=app

# Frontend type-check + lint
cd videx-frontend && npx tsc --noEmit && npx eslint .

# E2E with Playwright
npx playwright test --project=chromium
```

### Manual Verification Steps
1. Upload a 10s video → confirm Cloudinary URL is returned
2. Confirm SSE stream fires `analysis_complete` within 30s
3. Verify 3 style options render as floating chips
4. Select all customization options → click Generate
5. Confirm final prompt renders in < 20s
6. Test Copy, Download JSON, Share Link functionality
7. Test history page shows all past prompts
8. Verify rate limiting kicks in after 10 uploads
