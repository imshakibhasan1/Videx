# VIDEX Frontend

> Antigravity UI — AI-Powered Video Reverse-Engineering Platform

The Next.js 15 frontend for VIDEX, featuring a kinetic "zero-gravity" design system built with Tailwind CSS and Framer Motion.

## 🎨 Design System — Antigravity Theme

All Antigravity UI primitives live in `components/antigravity/`:

| Component | Description |
|---|---|
| `FloatingCard` | Glassmorphic card with continuous y-axis oscillation and magnetic hover lift |
| `FloatingChip` | Interactive selection pill with glow box-shadow and spring-based tap feedback |
| `WeightlessTransition` | Layout transition wrapper with float-up entry and gravity-pull exit |
| `ParticleField` | Ambient background particle system for depth |
| `StaggerContainer` | Cascading entrance animation for lists |

## 🧱 Tech Stack

- **Framework**: Next.js 15 (App Router, Turbopack)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 3.4 with custom design tokens
- **Animation**: Framer Motion 11
- **State**: Zustand 5 (single store, devtools)
- **HTTP**: Axios with typed wrappers
- **Toast**: Sonner
- **Icons**: Lucide React

## 🚀 Getting Started

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start development server (with Turbopack)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## 📁 Project Structure

```
videx-frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (fonts, providers)
│   ├── page.tsx            # Landing page
│   ├── dashboard/          # Main upload pipeline
│   ├── login/              # Auth page
│   └── history/            # Past prompts
├── components/
│   ├── antigravity/        # Design system primitives
│   ├── layout/             # Navbar, Footer
│   ├── providers/          # React context providers
│   └── upload/             # DropZone component
├── hooks/
│   ├── useUpload.ts        # Cloudinary signed upload flow
│   └── useSSE.ts           # Server-Sent Events consumer
├── lib/
│   ├── api.ts              # Typed API client (Axios)
│   ├── constants.ts        # App-wide constants
│   └── utils.ts            # Utility functions (cn, formatters)
├── store/
│   └── videx.store.ts      # Zustand global state
└── types/
    └── api.types.ts        # TypeScript type definitions
```

## 🔌 Backend Connection

The frontend proxies all `/api/v1/*` requests to the FastAPI backend via Next.js rewrites (configured in `next.config.ts`). Set `NEXT_PUBLIC_API_URL` in `.env.local` to your backend URL.
