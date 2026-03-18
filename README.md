# ChronoCanvasAI — AI Portrait Studio

> Portraits of History's Finest in Any Style.

Describe a historical figure, pick an art style, and watch AI render them in seconds. Powered by GPT-4o-mini for prompt enhancement and DALL·E 3 for image generation.

---

## Project Structure

```
aistyle-historical-figures/
├── backend/       # Python FastAPI — LangGraph pipeline, OpenAI integration, SQLite gallery
├── frontend/      # Next.js 14 — animated portrait generation UI
└── README.md      # README.md file
```

- [Backend README](backend/README.md) — setup, API reference, generation pipeline
- [Frontend README](frontend/README.md) — setup, pages, components, customization

---

## Tech Stack

| Layer         | Technology                            | Purpose                                                 |
|---------------|---------------------------------------|---------------------------------------------------------|
| Frontend      | Next.js 14, TypeScript, Tailwind CSS  | Routing, image optimization, great DX                   |
| Animations    | Framer Motion                         | Smooth loading states and image reveal                  |
| Backend       | Python FastAPI                        | Async REST API                                          |
| Orchestration | LangChain + LangGraph                 | Multi-step prompt enhancement and generation pipeline   |
| Image Gen     | DALL·E 3                              | High-quality portrait generation                        |
| Prompt AI     | GPT-4o-mini                           | Enriches prompts with historical context before DALL·E  |
| Database      | SQLite + SQLAlchemy                   | Portrait gallery persistence                            |
| Fonts         | Playfair Display + Inter              | Historical elegance + clean body text                   |

---

## How It Works

```
User types prompt + selects style
            ↓
  FastAPI receives the request
            ↓
  GPT-4o-mini enhances the prompt
  (adds historical context, artistic detail)
            ↓
  DALL·E 3 generates the portrait
            ↓    (content policy hit → sanitize description → retry once)
  Image bytes downloaded from CDN and stored in SQLite
            ↓
  Portrait metadata + image saved to gallery.db
            ↓
  Portrait served from DB via /api/gallery/{id}/image
            ↓
  Framer Motion reveals the portrait
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (Client)                             │
│                                                                     │
│  Next.js 14 App Router (port 3000)                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐    │
│  │  /          │  │  /generate   │  │  /gallery  │  │ /figures │    │
│  │  Home Page  │  │  Composer    │  │  Grid      │  │ Catalog  │    │
│  └─────────────┘  └──────────────┘  └────────────┘  └──────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP (REST JSON)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (port 3001)                     │
│                                                                     │
│  Routers (/api/*)                                                   │
│  ┌──────────┐  ┌────────────────┐  ┌─────────┐  ┌──────────────┐    │
│  │ /generate│  │ /enhance-prompt│  │/gallery │  │ /styles      │    │
│  └────┬─────┘  └───────┬────────┘  └────┬────┘  └──────────────┘    │
│       │                │               │                            │
│       ▼                ▼               ▼                            │
│  ┌──────────────────────────┐   ┌───────────────────┐               │
│  │   image_generator.py     │   │    gallery.py     │               │
│  │   (LangGraph Pipeline)   │   │    (CRUD service) │               │
│  └──────────┬───────────────┘   └────────┬──────────┘               │
│             │                            │                          │
│             ▼                            ▼                          │
│  ┌──────────────────────────┐   ┌───────────────────┐               │
│  │   prompt_builder.py      │   │    SQLAlchemy     │               │
│  │   (LangChain chains)     │   │    (async ORM)    │               │
│  └──────────┬───────────────┘   └────────┬──────────┘               │
└─────────────┼────────────────────────────┼──────────────────────────┘
              │                            │
              ▼                            ▼
┌─────────────────────────┐      ┌───────────────────────┐
│   OpenAI API            │      │   SQLite (gallery.db) │
│  ┌───────────────────┐  │      │                       │
│  │ GPT-4o-mini       │  │      │  portraits table      │
│  │ (prompt enhance)  │  │      │  - id, figure, style  │
│  └───────────────────┘  │      │  - prompt, image_url  │
│  ┌───────────────────┐  │      │  - image_data (BLOB)  │
│  │ DALL·E 3          │  │      │  - created_at         │
│  │ (image generation)│  │      └───────────────────────┘
│  └───────────────────┘  │
└─────────────────────────┘
```

---

### Backend Architecture

#### Directory Structure

```
backend/
├── main.py                 # FastAPI app — CORS, rate limiter, lifespan, router registration
├── config.py               # Environment variable loader with typed getters
├── database.py             # SQLAlchemy async engine, SessionLocal, get_db() dependency
├── llm.py                  # Shared ChatOpenAI instance with in-memory response cache
├── rate_limit.py           # slowapi Limiter instance
├── logger.py               # Logging configuration
├── requirements.txt
│
├── models/
│   ├── portrait.py         # SQLAlchemy ORM model — "portraits" table
│   └── schemas.py          # Pydantic v2 request/response schemas
│
├── routers/
│   ├── generate.py         # POST /api/generate — rate-limited portrait creation
│   ├── enhance_prompt.py   # POST /api/enhance-prompt — prompt preview only
│   ├── gallery.py          # GET|DELETE /api/gallery/** — CRUD + image serving
│   ├── styles.py           # GET /api/styles
│   └── health.py           # GET /api/health
│
└── services/
    ├── image_generator.py  # LangGraph state machine orchestrating the full pipeline
    ├── prompt_builder.py   # LangChain chains: extract, enhance, format, sanitize
    └── gallery.py          # Database CRUD operations (save, list, get, delete)
```

#### Startup Lifecycle (`main.py`)

The FastAPI app uses an async lifespan context manager to:
1. Verify OpenAI connectivity before accepting traffic
2. Create all SQLAlchemy tables (`CREATE TABLE IF NOT EXISTS`)
3. Run schema migrations (e.g., add `image_data` column if upgrading from an older schema)
4. Register slowapi exception handlers for rate limit responses

#### Database Layer

**ORM Model** — `models/portrait.py`

| Column            | Type        | Notes                                   |
|-------------------|-------------|-----------------------------------------|
| `id`              | Integer PK  | Auto-increment                          |
| `figure`          | String(255) | Clean display title, indexed            |
| `style`           | String(100) | Art style, indexed                      |
| `prompt`          | Text        | Raw user input                          |
| `enhanced_prompt` | Text        | GPT-4o-mini output                      |
| `image_url`       | Text        | Original DALL·E CDN URL                 |
| `image_data`      | LargeBinary | Downloaded PNG bytes (CDN-independent)  |
| `created_at`      | DateTime    | UTC, auto-set on insert                 |

Images are downloaded from the CDN immediately after generation and stored as binary blobs so the gallery never depends on expiring DALL·E URLs.

#### LangGraph Generation Pipeline (`services/image_generator.py`)

The generation pipeline is a directed state machine built with LangGraph. Each node is a pure async function that receives and returns the shared state dict.

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  extract                                                        │
│  GPT-4o-mini with structured output                             │
│  • Parses figure_title (clean display name)                     │
│  • Resolves art style (user hint > explicit style > AI choice)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  build_prompt (enhance_node)                                    │
│  Routes to one of three LangChain chains:                       │
│  • enhance_prompt()              — stateless creative           │
│  • enhance_prompt_with_history() — session-aware (RunnableWith  │
│                                    MessageHistory)              │
│  • format_prompt()               — format-only (enhance=False)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  generate                                                       │
│  DallEAPIWrapper → DALL·E 3 (1024×1024)                         │
│  Retries on: rate limit, timeout, connection errors             │
│  Sets content_policy_hit=True on content policy rejection       │
└──────────────┬──────────────────────────────┬───────────────────┘
               │ policy hit & attempt < 2     │ success / max retries
               ▼                              ▼
┌──────────────────────────┐                 END
│  soften                  │
│  sanitize_figure_        │
│  description() chain     │
│  Replaces combat/violence│
│  language with peaceful  │
│  alternatives, re-frames │
│  as mythological/        │
│  allegorical composition │
└──────────┬───────────────┘
           │
           └──────► generate (retry once)
```

**State dictionary** flowing through the graph:

```python
class _State(TypedDict):
    figure: str                    # Raw user input
    style: str                     # Raw style input
    user_prompt: str               # Optional extra context
    session_id: Optional[str]      # For history-aware generation
    enhance: bool                  # True = creative / False = format-only
    figure_title: Optional[str]    # Extracted clean display name
    resolved_style: Optional[str]  # Extracted or LLM-decided style
    enhanced_prompt: Optional[str] # Final prompt sent to DALL·E
    image_url: Optional[str]       # Generated image CDN URL
    content_policy_hit: bool       # Flag for policy violation retry
    attempt: int                   # Retry counter
```

#### Prompt Engineering Layer (`services/prompt_builder.py`)

All chains are built with LangChain LCEL (`|` pipe operator):

| Chain                         | Model                                       | Purpose                                                                       |
|-------------------------------|---------------------------------------------|-------------------------------------------------------------------------------|
| `extract_figure_and_style`    | GPT-4o-mini (structured output)             | Parse input into figure title + style                                         |
| `enhance_prompt`              | GPT-4o-mini                                 | Creatively enrich with historical context and era-accurate visual details     |
| `enhance_prompt_with_history` | GPT-4o-mini + `RunnableWithMessageHistory`  | Same as above but references prior figures/styles within a session            |
| `format_prompt`               | GPT-4o-mini                                 | Reformat only — preserve user intent exactly                                  |
| `sanitize_figure_description` | GPT-4o-mini                                 | Rewrite violent/conflict scenes as peaceful alternatives on policy violation  |

Session history is stored in an in-memory dict (keyed by `session_id`) using `MessagesPlaceholder` injection. `chat_history.db` holds a SQLite-backed fallback for persistent history across restarts.

#### API Endpoints

| Method    | Path                      | Rate Limit    | Description |
|-----------|---------------------------|---------------|---------------------------------------------------------|
| `POST`    | `/api/generate`           | 10/min per IP | Run full pipeline; auto-save portrait to DB             |
| `POST`    | `/api/enhance-prompt`     | —             | Preview enhanced prompt without image generation        |
| `GET`     | `/api/gallery`            | —             | Paginated portrait list (`page`, `page_size`, `style`)  |
| `GET`     | `/api/gallery/featured`   | —             | Latest portrait ID per figure name                      |
| `GET`     | `/api/gallery/{id}`       | —             | Portrait metadata                                       |
| `GET`     | `/api/gallery/{id}/image` | —             | Serve stored PNG bytes from DB                          |
| `DELETE`  | `/api/gallery/{id}`       | —             | Remove portrait                                         |
| `GET`     | `/api/styles`             | —             | Available art styles                                    |
| `GET`     | `/api/health`             | —             | OpenAI connectivity check                               |

#### Key Configuration Variables (`backend/.env`)

| Variable                    | Default                 | Description                       |
|-----------------------------|-------------------------|-----------------------------------|
| `OPENAI_API_KEY`            | —                       | Required                          |
| `OPENAI_PROMPT_MODEL`       | `gpt-4o-mini`           | LLM for prompt enhancement        |
| `OPENAI_PROMPT_TEMPERATURE` | `0.8`                   | Creativity of prompt enhancement  |
| `OPENAI_IMAGE_MODEL`        | `dall-e-3`              | Image generation model            |
| `IMAGE_SIZE`                | `1024x1024`             | DALL·E output resolution          |
| `GENERATE_RATE_LIMIT`       | `10/minute`             | slowapi rule string               |
| `PORT`                      | `3001`                  | Uvicorn bind port                 |
| `FRONTEND_URL`              | `http://localhost:3000` | CORS allowed origin               |
| `LANGSMITH_TRACING_V2`      | `false`                 | Enable LangSmith tracing          |

---

### Frontend Architecture

#### Directory Structure

```
frontend/
├── app/                            # Next.js App Router
│   ├── layout.tsx                  # Root layout — fonts, Navbar, Footer, metadata
│   ├── page.tsx                    # / — Home (HeroSection + QuickStartTemplates)
│   ├── globals.css                 # Global styles, CSS custom properties
│   ├── generate/
│   │   └── page.tsx                # /generate — portrait generation interface
│   ├── gallery/
│   │   └── page.tsx                # /gallery — community gallery grid
│   └── figures/
│       └── page.tsx                # /figures — historical figures catalog
│
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx              # Top navigation bar
│   │   └── Footer.tsx              # Page footer
│   ├── home/
│   │   ├── HeroSection.tsx         # Landing hero wrapper
│   │   ├── HeroLeft.tsx            # Headline, CTA, quick templates
│   │   ├── HeroRight.tsx           # Live portrait card carousel
│   │   ├── PortraitCard.tsx        # Single portrait display card with icon badges
│   │   ├── PortraitComposer.tsx    # Core generation UI (textarea, styles, result)
│   │   ├── PortraitPageClient.tsx  # Client bridge: template → composer state
│   │   └── QuickStartTemplates.tsx # One-click template cards
│   └── ui/
│       ├── Button.tsx              # Generic button with variant props
│       ├── StyleButton.tsx         # Art style selector toggle button
│       └── LoadingSpinner.tsx      # Shimmer placeholder + spinner
│
├── lib/
│   └── constants.ts                # STYLES, QUICK_START_TEMPLATES, HERO_PORTRAIT_CARDS, STATS
│
├── types/
│   └── index.ts                    # TypeScript interfaces for all domain objects
│
├── tailwind.config.ts              # Custom theme (cream, dark, gold, parchment, cyan)
├── next.config.mjs                 # Image CDN allowlist + Next.js options
└── tsconfig.json                   # TypeScript config with @ path alias
```

#### Page & Component Hierarchy

```
RootLayout (layout.tsx)
├── Navbar
│
├── / (page.tsx)
│   └── HeroSection
│       ├── HeroLeft
│       │   ├── Headline + CTA button
│       │   └── QuickStartTemplates
│       │       └── PortraitPageClient  ──► passes selected template to PortraitComposer
│       └── HeroRight
│           └── PortraitCard × N        (live images from /api/gallery/featured)
│
├── /generate (page.tsx)
│   └── PortraitComposer              (receives ?figure= query param as initial state)
│       ├── Textarea (figure input)
│       ├── StyleButton × N           (style selector)
│       ├── AI enhance toggle
│       ├── Generate button
│       ├── LoadingSpinner            (shimmer during fetch)
│       └── Result panel
│           ├── <img> / Next Image    (portrait)
│           └── Collapsible prompt    (enhanced_prompt disclosure)
│
├── /gallery (page.tsx)
│   └── GalleryClient
│       ├── Style filter buttons
│       ├── Portrait grid
│       │   └── GalleryCard × N       (image from /api/gallery/{id}/image)
│       └── Pagination controls
│
├── /figures (page.tsx)
│   └── FigureCard × 12              (links to /generate?figure=...)
│
└── Footer
```

#### State Management

The frontend uses local React `useState` — there is no global state library. State is co-located with the component that needs it:

| Component             | State                                   | Description                               |
|-----------------------|-----------------------------------------|-------------------------------------------|
| `PortraitComposer`    | `figure`, `selectedStyle`, `aiEnhance`  | Form inputs                               | 
| `PortraitComposer`    | `loading`, `error`, `result`            | API call lifecycle                        |
| `GalleryClient`       | `portraits`, `page`, `selectedStyle`    | Paginated gallery data                    |
| `PortraitPageClient`  | `selectedTemplate`                      | Bridge from quick-start click to composer |

#### Data Fetching

All API calls go directly from the browser to the FastAPI backend. There are no Next.js API routes or server actions — the frontend is a pure client-side consumer of the REST API.

```
PortraitComposer
  POST /api/generate → { image_url, figure_title, enhanced_prompt, ... }

GalleryClient
  GET /api/gallery?page=N&style=X → { items, total, page, page_size }

HeroRight / PortraitCard
  GET /api/gallery/featured?figures=Cleopatra,...
  GET /api/gallery/{id}/image → PNG bytes
```

The backend URL is injected via the `NEXT_PUBLIC_BACKEND_URL` environment variable (defaults to `http://localhost:3001`).

#### Styling System

Tailwind CSS is configured with a historical/vintage custom palette:

| Token       | Hex       | Usage                     | 
|-------------|-----------|---------------------------|
| `cream`     | `#f2ece0` | Light backgrounds, cards  |
| `dark`      | `#1c1710` | Primary dark background   |
| `gold`      | `#c9963a` | Accent, CTAs, badges      |
| `parchment` | `#e8d9bc` | Secondary backgrounds     |
| `dark-card` | —         | Dark card surfaces        |
| `cyan`      | —         | Hover accents             |

Typography is driven by two Google Fonts loaded in `layout.tsx`:
- **Playfair Display** — Serif headings, figure names, historical aesthetic
- **Inter** — Sans-serif body text, UI labels

#### Animation

[Framer Motion](https://www.framer.com/motion/) handles all transitions:
- **Image reveal** — `opacity: 0 → 1` + `scale: 0.95 → 1` when portrait loads
- **Loading shimmer** — Pulse animation on placeholder while fetching
- **Prompt disclosure** — Height collapse/expand for the enhanced prompt panel

#### Key Constants (`lib/constants.ts`)

**`STYLES`** — 5 selectable art styles:
```
renaissance | anime | sketch | watercolor | baroque
```

**`QUICK_START_TEMPLATES`** — Pre-configured figure + style pairs for one-click generation:
```
Napoleon Bonaparte (Cyberpunk)  | Cleopatra (Marvel superhero)
Einstein (Studio Ghibli)        | Genghis Khan (Watercolor)     | Marie Curie (Art Deco)
```

**`HERO_PORTRAIT_CARDS`** — Figures displayed on the home page hero, pulled live from the gallery DB: Cleopatra, Nikola Tesla, Leonardo da Vinci, Raja Dahir.

#### TypeScript Types (`types/index.ts`)

```typescript
Style            { id, label }
Template         { figure, style, displayLabel }
GenerateRequest  { figure, style, user_prompt?, session_id?, enhance }
GenerateResponse { image_url, revised_prompt, enhanced_prompt, figure, figure_title, style }
GalleryItem      { id, figure, style, prompt, enhanced_prompt, image_url, created_at }
GalleryResponse  { items, total, page, page_size }
```

#### Environment Variables (`frontend/.env.local`)

| Variable                  | Default                 | Description             |
|---------------------------|-------------------------|-------------------------|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:3001` | FastAPI backend origin  |

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- OpenAI API key with access to GPT-4o-mini and DALL·E 3

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENAI_API_KEY
uvicorn main:app --reload --port 3001
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local if backend runs on a different port
npm run dev
```

Open `http://localhost:3000`.

---

## Features

- **AI Portrait Generation** — Describe any historical figure and scene, get a portrait in seconds
- **Prompt Enhancement** — GPT-4o-mini enriches your input with historically accurate detail before DALL·E 3 runs
- **5 Art Styles** — Renaissance, Anime, Sketch, Watercolor, Baroque
- **Persistent Image Storage** — Generated images are downloaded and stored as binary blobs in SQLite; served from the DB so they never expire
- **Content Policy Handling** — Automatic scene description sanitisation (removes combat/conflict language) and prompt retry if DALL·E rejects a request
- **Hero Gallery** — Home page shows the latest generated portraits for Cleopatra, Nikola Tesla, Da Vinci, and Raja Dahir pulled live from the DB
- **Animated Image Reveal** — Framer Motion entrance animation when the portrait loads
- **Quick-Start Templates** — One-click generation for Napoleon, Cleopatra, Einstein, Genghis Khan, Marie Curie
- **Historical Figures Catalog** — Browse pre-configured figures and generate with one click
- **Community Gallery** — Paginated, filterable gallery of all generated portraits served from DB
- **Session-Aware History** — Reference previous prompts within a session for iterative generation
- **Rate Limiting** — 10 requests per minute per IP

---

## API

The backend exposes a REST API at `http://localhost:3001`. Key endpoints:

| Method    | Path                         | Description                                        |
|-----------|------------------------------|----------------------------------------------------|
| `POST`    | `/api/generate`              | Generate a portrait                                |
| `POST`    | `/api/enhance-prompt`        | Preview enhanced prompt only                       |
| `GET`     | `/api/gallery`               | List saved portraits (paginated)                   |
| `GET`     | `/api/gallery/featured`      | Latest portrait ID for each given figure name      |
| `GET`     | `/api/gallery/{id}`          | Get portrait metadata by ID                        |
| `GET`     | `/api/gallery/{id}/image`    | Serve stored image bytes (PNG) from DB             |
| `DELETE`  | `/api/gallery/{id}`          | Delete portrait by ID                              |
| `GET`     | `/api/styles`                | List available art styles                          |
| `GET`     | `/api/health`                | Health check                                       |

Full API reference in the [Backend README](backend/README.md#api-reference).

---

## Customization

| Goal                      | Where                                                       |
|---------------------------|-------------------------------------------------------------|
| Add art styles            | `frontend/lib/constants.ts` — `STYLES` array                |
| Add quick-start templates | `frontend/lib/constants.ts` — `QUICK_START_TEMPLATES` array |
| Add historical figures    | `backend/scripts/figures_data.json` + run `seed_figures.py` |
| Tune prompt engineering   | `backend/services/prompt_builder.py`                        |
| Change enhancement model  | `OPENAI_PROMPT_MODEL` in `backend/.env`                     |
| Adjust rate limits        | `backend/routers/generate.py`                               |

---

## Project Status

**Current state: Feature-complete MVP.** Core generation pipeline, gallery, figures catalog, and stats are all operational. The following areas are known to need work before a production deployment.

### Known Limitations

| ID | Area | Description |
|----|------|-------------|
| TD-001 | Infrastructure | SQLite + BLOB image storage will not survive concurrent load. Needs PostgreSQL + object storage (S3/R2). |
| TD-005 | Infrastructure | No Docker/Compose setup. Full stack requires manual environment setup. |
| TD-006 | Infrastructure | No CI/CD pipeline. Tests exist but run manually only. |
| BUG-001 | Frontend | Hero section shows broken cards if the DB has no portraits for the featured figures. |
| BUG-003 | Frontend | No navigation guard — mid-generation navigation silently discards the result. |
| FEAT-001 | Feature | No user accounts or auth. All usage is anonymous. |
| FEAT-002 | Feature | No portrait download button. |
| FEAT-003 | UX | Generation takes 15–20 seconds with a static spinner and zero progress feedback. |

> Full issue list with priorities and proposed fixes: see `ISSUES.md` (local, not committed).
