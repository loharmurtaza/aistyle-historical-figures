# ChronoCanvasAI — AI Portrait Studio

> Portraits of History's Finest in Any Style.

Describe a historical figure, pick an art style, and watch AI render them in seconds. Powered by GPT-4o-mini for prompt enhancement, DALL·E 3 for image generation, and a RAG chatbot that answers questions about the figures in your catalog.

---

## Project Structure

```
aistyle-historical-figures/
├── backend/       # Python FastAPI — LangGraph pipeline, RAG chatbot, SQLite DB
├── frontend/      # Next.js 14 — portrait generation UI + floating chat widget
└── README.md
```

- [Backend README](backend/README.md) — setup, API reference, generation pipeline, chatbot
- [Frontend README](frontend/README.md) — setup, pages, components, customization

---

## Tech Stack

| Layer          | Technology                            | Purpose                                                  |
|----------------|---------------------------------------|----------------------------------------------------------|
| Frontend       | Next.js 14, TypeScript, Tailwind CSS  | Routing, image optimization, great DX                    |
| Animations     | Framer Motion                         | Smooth loading states and image reveal                   |
| Markdown       | react-markdown                        | Renders chatbot responses with bold, lists, etc.         |
| Backend        | Python FastAPI                        | Async REST API + SSE streaming                           |
| Orchestration  | LangChain + LangGraph                 | Multi-step prompt enhancement and generation pipeline    |
| RAG / Chat     | LangChain + FAISS                     | Vector similarity search over figures for chatbot        |
| Image Gen      | DALL·E 3                              | High-quality portrait generation                         |
| Prompt AI      | GPT-4o-mini                           | Enriches prompts with historical context before DALL·E   |
| Embeddings     | text-embedding-3-small                | Encodes figures into FAISS index for semantic retrieval  |
| Database       | SQLite + SQLAlchemy                   | Portrait gallery + chat session/message persistence      |
| Fonts          | Playfair Display + Inter              | Historical elegance + clean body text                    |

---

## How It Works

### Portrait Generation

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

### RAG Chatbot

```
User types a question in the floating chat widget
            ↓
  Session history loaded from chat_messages table
            ↓
  User message embedded via text-embedding-3-small
            ↓
  FAISS similarity search → top-k matching figures
            ↓
  System prompt assembled:
    (a) catalog summary  — global context (all eras, origins, tags)
    (b) RAG context      — top-k figure details for this query
            ↓
  GPT-4o-mini streams response tokens via SSE
            ↓
  User + assistant messages persisted to DB with
  token usage and timing metrics
```

---

## Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          Browser (Client)                                  │
│                                                                            │
│  Next.js 14 App Router (port 3000)                                         │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐             │
│  │    /     │  │  /generate   │  │  /gallery  │  │ /figures │             │
│  │  Home    │  │  Composer    │  │  Grid      │  │ Catalog  │             │
│  └──────────┘  └──────────────┘  └────────────┘  └──────────┘             │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ChatWidget (global — mounted in layout, visible on every page)    │    │
│  │  • Floating toggle button                                          │    │
│  │  • Streaming SSE message list with react-markdown rendering        │    │
│  │  • Reset button — closes session, starts fresh, retains DB data    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ HTTP (REST JSON + SSE)
                               ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (port 3001)                           │
│                                                                            │
│  Routers (/api/*)                                                          │
│  ┌──────────┐  ┌────────────────┐  ┌─────────┐  ┌──────────┐  ┌───────┐   │
│  │/generate │  │/enhance-prompt │  │/gallery │  │/figures  │  │/chat  │   │
│  └────┬─────┘  └───────┬────────┘  └────┬────┘  └────┬─────┘  └───┬───┘   │
│       │                │               │             │            │       │
│       ▼                ▼               ▼             ▼            ▼       │
│  ┌──────────────────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │   image_generator.py     │  │  gallery.py │  │    chatbot.py        │  │
│  │   (LangGraph Pipeline)   │  │  (CRUD svc) │  │  (RAG + streaming)   │  │
│  └──────────┬───────────────┘  └──────┬──────┘  └──────────┬───────────┘  │
│             │                        │                     │              │
│             ▼                        ▼                     ▼              │
│  ┌──────────────────┐      ┌──────────────────┐  ┌─────────────────────┐  │
│  │  prompt_builder  │      │   SQLAlchemy ORM │  │  figures_index.py   │  │
│  │  (LCEL chains)   │      │                  │  │  (FAISS in-memory)  │  │
│  └──────────┬───────┘      └──────────────────┘  └─────────────────────┘  │
└─────────────┼──────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────┐      ┌─────────────────────────────────────────┐
│   OpenAI API            │      │   SQLite (gallery.db)                   │
│  ┌───────────────────┐  │      │                                         │
│  │ GPT-4o-mini       │  │      │  portraits      — image blobs           │
│  │ (prompt + chat)   │  │      │  figures        — catalog data          │
│  └───────────────────┘  │      │  styles         — available styles      │
│  ┌───────────────────┐  │      │  chat_sessions  — session tracking      │
│  │ text-embedding-   │  │      │  chat_messages  — full history +        │
│  │ 3-small (FAISS)   │  │      │                   token/timing metrics  │
│  └───────────────────┘  │      └─────────────────────────────────────────┘
│  ┌───────────────────┐  │
│  │ DALL·E 3          │  │
│  │ (image gen)       │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

---

### Backend Architecture

#### Directory Structure

```
backend/
├── main.py                     # FastAPI app — CORS, rate limiter, lifespan, router registration
├── config.py                   # Typed env var loader (str/int/float/bool getters)
├── database.py                 # SQLAlchemy engine, SessionLocal, get_db() dependency
├── llm.py                      # Shared ChatOpenAI instance
├── rate_limit.py               # slowapi Limiter instance
├── logger.py                   # Logging configuration
├── requirements.txt
├── .env.example
│
├── models/
│   ├── portrait.py             # ORM — portraits table (image BLOB storage)
│   ├── figure.py               # ORM — figures table (catalog data)
│   ├── style.py                # ORM — styles table
│   ├── chat.py                 # ORM — chat_sessions + chat_messages tables
│   └── schemas.py              # Pydantic v2 request/response schemas
│
├── routers/
│   ├── generate.py             # POST /api/generate — rate-limited portrait creation
│   ├── enhance_prompt.py       # POST /api/enhance-prompt — prompt preview only
│   ├── gallery.py              # GET|DELETE /api/gallery/** — CRUD + image serving
│   ├── styles.py               # GET /api/styles
│   ├── figures.py              # GET|POST /api/figures — catalog CRUD + filters
│   ├── stats.py                # GET /api/stats — live counts
│   ├── chatbot.py              # POST /api/chat (SSE) + POST /api/chat/{id}/reset
│   └── health.py               # GET /api/health
│
├── services/
│   ├── image_generator.py      # LangGraph state machine — full generation pipeline
│   ├── prompt_builder.py       # LangChain LCEL chains: enhance, format, sanitize
│   ├── gallery.py              # DB CRUD for portraits
│   ├── figures_index.py        # FAISS vector index over figures; TTL refresh + invalidation
│   └── chatbot.py              # RAG chat: retrieve → prompt → stream → persist
│
└── scripts/
    ├── seed_figures.py         # CLI: bulk-import figures from JSON
    ├── seed_styles.py          # CLI: seed styles table
    └── figures_data.json       # Source data for figures seed
```

#### Startup Lifecycle (`main.py`)

The FastAPI lifespan context manager runs at startup:

1. Set LangSmith environment variables (if tracing is enabled)
2. `Base.metadata.create_all` — create all ORM tables that don't exist yet (`portraits`, `figures`, `styles`, `chat_sessions`, `chat_messages`)
3. Run inline SQLite `ALTER TABLE` migrations for columns added after initial deploy (e.g. `image_data` on portraits)
4. `figures_index.build_sync()` — embed all figures via `text-embedding-3-small` and load into FAISS; blocks until ready so the chatbot is available on the first request
5. Verify OpenAI connectivity

#### Database Layer

**`portraits`**

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

**`figures`**

| Column       | Type        | Notes                            |
|--------------|-------------|----------------------------------|
| `id`         | Integer PK  |                                  |
| `name`       | String(255) | Unique, indexed                  |
| `slug`       | String(255) | URL-safe unique key, indexed     |
| `description`| Text        |                                  |
| `born_year`  | Integer     |                                  |
| `died_year`  | Integer     |                                  |
| `era`        | String(100) | Indexed                          |
| `origin`     | String(100) | Indexed                          |
| `tags`       | String(500) | Comma-separated                  |
| `featured`   | Boolean     |                                  |
| `created_at` | DateTime    | Server default                   |

**`chat_sessions`**

| Column       | Type        | Notes                              |
|--------------|-------------|------------------------------------|
| `id`         | Integer PK  |                                    |
| `session_id` | String(255) | UUID, unique, indexed              |
| `created_at` | DateTime    |                                    |
| `last_active`| DateTime    | Bumped on every exchange or reset  |

**`chat_messages`**

| Column             | Type     | Notes                                              |
|--------------------|----------|----------------------------------------------------|
| `id`               | Int PK   |                                                    |
| `session_id`       | String   | Indexed; references `chat_sessions.session_id`     |
| `role`             | String   | `'user'` or `'assistant'`                          |
| `content`          | Text     |                                                    |
| `created_at`       | DateTime |                                                    |
| `prompt_tokens`    | Integer  | Assistant rows only (NULL on user rows)            |
| `completion_tokens`| Integer  | Assistant rows only                                |
| `total_tokens`     | Integer  | Assistant rows only                                |
| `retrieval_ms`     | Float    | FAISS search duration                              |
| `first_token_ms`   | Float    | Time to first streamed token                       |
| `total_ms`         | Float    | Full round-trip duration                           |
| `docs_retrieved`   | Integer  | Number of FAISS hits used as context               |

#### LangGraph Generation Pipeline (`services/image_generator.py`)

```
START
  │
  ▼
┌───────────────────────────────────────────────────────────────────┐
│  extract                                                          │
│  GPT-4o-mini (structured output)                                  │
│  • Parses figure_title (clean display name)                       │
│  • Resolves art style (user hint > explicit > AI choice)          │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│  build_prompt (enhance_node)                                      │
│  Routes to one of three LangChain chains:                         │
│  • enhance_prompt()              — stateless creative             │
│  • enhance_prompt_with_history() — session-aware                  │
│  • format_prompt()               — format-only (enhance=False)    │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│  generate                                                         │
│  DallEAPIWrapper → DALL·E 3 (1024×1024)                           │
│  Sets content_policy_hit=True on policy rejection                 │
└──────────────┬────────────────────────────────┬───────────────────┘
               │ policy hit & attempt < 2       │ success / max retries
               ▼                                ▼
┌──────────────────────────┐                   END
│  soften                  │
│  sanitize_figure_        │
│  description() chain     │
│  Rewrites violent scenes │
│  as peaceful alternatives│
└──────────┬───────────────┘
           └──────► generate (retry once)
```

#### RAG Chatbot (`services/chatbot.py` + `services/figures_index.py`)

**FAISS Index (`figures_index.py`)**

- Built synchronously at startup via `build_sync()` — all figures are embedded in one batch
- Stored in RAM; no disk persistence needed
- TTL-based background refresh (configurable via `CHATBOT_INDEX_TTL`)
- `invalidate()` is called by the figures router after any new figure is created, so the next query always reflects the latest catalog

**Per-request flow:**

1. Load session history from `chat_messages` (ordered by `created_at`)
2. Embed the user message and run FAISS `similarity_search_with_score`
3. Build system prompt: catalog summary + top-k RAG context
4. Stream GPT-4o-mini response tokens over SSE
5. Write user + assistant rows to DB with full metrics

#### API Endpoints

| Method   | Path                            | Rate Limit    | Description                                          |
|----------|---------------------------------|---------------|------------------------------------------------------|
| `POST`   | `/api/generate`                 | 10/min per IP | Full pipeline; auto-saves portrait to DB             |
| `POST`   | `/api/enhance-prompt`           | —             | Preview enhanced prompt without generating           |
| `GET`    | `/api/gallery`                  | —             | Paginated portrait list (`page`, `page_size`, `style`)|
| `GET`    | `/api/gallery/featured`         | —             | Latest portrait ID per figure name                   |
| `GET`    | `/api/gallery/{id}`             | —             | Portrait metadata                                    |
| `GET`    | `/api/gallery/{id}/image`       | —             | Serve stored PNG bytes from DB                       |
| `DELETE` | `/api/gallery/{id}`             | —             | Remove portrait                                      |
| `GET`    | `/api/styles`                   | —             | Available art styles                                 |
| `GET`    | `/api/figures`                  | —             | Paginated + filtered figures catalog                 |
| `GET`    | `/api/figures/meta`             | —             | Distinct eras, origins, tags for filter dropdowns    |
| `GET`    | `/api/figures/{slug}`           | —             | Single figure by slug                                |
| `POST`   | `/api/figures`                  | —             | Create a figure (also invalidates FAISS index)       |
| `GET`    | `/api/stats`                    | —             | Live counts (portraits, figures, styles)             |
| `POST`   | `/api/chat`                     | —             | SSE stream — one `{"token": "..."}` event per chunk  |
| `POST`   | `/api/chat/{session_id}/reset`  | —             | Close session, return `{"new_session_id": "..."}`    |
| `GET`    | `/api/health`                   | —             | OpenAI connectivity check                            |

#### Key Configuration Variables (`backend/.env`)

| Variable                    | Default                 | Description                        |
|-----------------------------|-------------------------|------------------------------------|
| `OPENAI_API_KEY`            | —                       | Required                           |
| `OPENAI_PROMPT_MODEL`       | `gpt-4o-mini`           | LLM for prompt enhancement + chat  |
| `OPENAI_PROMPT_TEMPERATURE` | `0.8`                   | Creativity of prompt enhancement   |
| `OPENAI_IMAGE_MODEL`        | `dall-e-3`              | Image generation model             |
| `IMAGE_SIZE`                | `1024x1024`             | DALL·E output resolution           |
| `OPENAI_EMBEDDING_MODEL`    | `text-embedding-3-small`| Embedding model for FAISS index    |
| `CHATBOT_RETRIEVAL_K`       | `5`                     | Top-k figures returned per query   |
| `CHATBOT_INDEX_TTL`         | `300`                   | Seconds before FAISS auto-refresh  |
| `GENERATE_RATE_LIMIT`       | `10/minute`             | slowapi rule string                |
| `PORT`                      | `3001`                  | Uvicorn bind port                  |
| `FRONTEND_URL`              | `http://localhost:3000` | CORS allowed origin                |
| `LANGCHAIN_TRACING_V2`      | `false`                 | Enable LangSmith tracing           |

---

### Frontend Architecture

#### Directory Structure

```
frontend/
├── app/                            # Next.js App Router
│   ├── layout.tsx                  # Root layout — fonts, Navbar, Footer, ChatWidget
│   ├── page.tsx                    # / — Home (HeroSection + QuickStartTemplates)
│   ├── globals.css
│   ├── generate/
│   │   └── page.tsx                # /generate — portrait generation interface
│   ├── gallery/
│   │   └── page.tsx                # /gallery — community gallery grid
│   └── figures/
│       └── page.tsx                # /figures — historical figures catalog
│
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   └── Footer.tsx
│   ├── home/
│   │   ├── HeroSection.tsx
│   │   ├── HeroLeft.tsx            # Headline, CTA, stats, quick templates
│   │   ├── HeroRight.tsx           # Live portrait card carousel
│   │   ├── PortraitCard.tsx
│   │   ├── PortraitComposer.tsx    # Core generation UI
│   │   ├── PortraitPageClient.tsx
│   │   └── QuickStartTemplates.tsx
│   ├── figures/
│   │   ├── FiguresGrid.tsx         # Searchable, filterable figures catalog grid
│   │   └── FigureInfoPanel.tsx     # Side panel with selected figure details
│   ├── chat/
│   │   └── ChatWidget.tsx          # Floating RAG chatbot (SSE streaming + session reset)
│   └── ui/
│       ├── Button.tsx
│       ├── StyleButton.tsx
│       └── LoadingSpinner.tsx
│
├── lib/
│   └── constants.ts                # STYLES, QUICK_START_TEMPLATES, HERO_PORTRAIT_CARDS
│
├── types/
│   └── index.ts                    # TypeScript interfaces for all domain objects
│
├── tailwind.config.ts
├── next.config.mjs
└── tsconfig.json
```

#### Page & Component Hierarchy

```
RootLayout (layout.tsx)
├── Navbar
│
├── / (page.tsx)
│   └── HeroSection
│       ├── HeroLeft
│       │   ├── Headline + CTA + live stats
│       │   └── QuickStartTemplates
│       │       └── PortraitPageClient ──► passes selected template to PortraitComposer
│       └── HeroRight
│           └── PortraitCard × N       (live images from /api/gallery/featured)
│
├── /generate (page.tsx)
│   └── PortraitComposer              (receives ?figure= query param as initial state)
│       ├── Textarea (figure input)
│       ├── StyleButton × N
│       ├── AI enhance toggle
│       ├── Generate button
│       ├── LoadingSpinner
│       └── Result panel
│           ├── Portrait image
│           └── Collapsible enhanced prompt
│
├── /gallery (page.tsx)
│   └── GalleryClient
│       ├── Style filter buttons
│       ├── Portrait grid (image from /api/gallery/{id}/image)
│       └── Pagination controls
│
├── /figures (page.tsx)
│   └── FiguresGrid
│       ├── Search + era/origin/tags/year filters
│       ├── FigureCard × N (links to /generate?figure=...)
│       └── FigureInfoPanel (slide-in details for selected figure)
│
├── ChatWidget (global — always present)
│   ├── Toggle button (bottom-right)
│   ├── Header (title + reset ↺ + close ✕)
│   ├── Message list (user + assistant, react-markdown, streaming cursor)
│   └── Input bar + send button
│
└── Footer
```

#### State Management

The frontend uses local React `useState` — no global state library.

| Component          | State                                   | Description                                  |
|--------------------|-----------------------------------------|----------------------------------------------|
| `PortraitComposer` | `figure`, `selectedStyle`, `aiEnhance`  | Form inputs                                  |
| `PortraitComposer` | `loading`, `error`, `result`            | API call lifecycle                           |
| `GalleryClient`    | `portraits`, `page`, `selectedStyle`    | Paginated gallery data                       |
| `FiguresGrid`      | `query`, `era`, `origin`, `tags`, etc.  | Filter state                                 |
| `ChatWidget`       | `messages`, `input`, `loading`, `open`  | Chat UI state                                |
| `ChatWidget`       | `sessionIdRef`                          | Stable UUID per session (rotated on reset)   |

#### Data Fetching

All API calls go directly from the browser to the FastAPI backend.

```
PortraitComposer
  POST /api/generate → { image_url, figure_title, enhanced_prompt, ... }

GalleryClient
  GET /api/gallery?page=N&style=X → { items, total, page, page_size }

FiguresGrid
  GET /api/figures?era=X&origin=Y&search=Z → { items, total, page, page_size }
  GET /api/figures/meta → { eras, origins, tags }

ChatWidget
  POST /api/chat → SSE stream of { token } events
  POST /api/chat/{session_id}/reset → { new_session_id }
```

#### Styling System

Tailwind CSS custom palette:

| Token       | Usage                     |
|-------------|---------------------------|
| `cream`     | Light backgrounds, cards  |
| `dark`      | Primary dark background   |
| `gold`      | Accent, CTAs, pulse dot   |
| `parchment` | Secondary backgrounds     |

Typography: **Playfair Display** (headings) + **Inter** (body).

#### Environment Variables (`frontend/.env.local`)

| Variable                  | Default                 | Description             |
|---------------------------|-------------------------|-------------------------|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:3001` | FastAPI backend origin  |

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- OpenAI API key with access to GPT-4o-mini, DALL·E 3, and text-embedding-3-small

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
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

- **AI Portrait Generation** — Describe any historical figure, get a portrait in seconds
- **Prompt Enhancement** — GPT-4o-mini enriches your input with historically accurate detail before DALL·E 3 runs
- **5 Art Styles** — Renaissance, Anime, Sketch, Watercolor, Baroque
- **Persistent Image Storage** — Generated images stored as binary blobs in SQLite; served from DB so they never expire
- **Content Policy Handling** — Auto scene sanitisation (removes combat language) and prompt retry on DALL·E rejection
- **Historical Figures Catalog** — Browse and filter hundreds of figures by era, origin, and tags; one click generates a portrait
- **RAG Chatbot** — Ask anything about figures in the catalog; answers grounded strictly in catalog data via FAISS + GPT-4o-mini
- **Chat Session Persistence** — Full conversation history stored in DB with per-turn token usage and timing metrics
- **Session Reset** — Reset button starts a fresh conversation; old messages retained in DB for analytics
- **Community Gallery** — Paginated, style-filtered gallery of all generated portraits
- **Live Stats** — Home page shows real-time portrait count, unique figures, and styles
- **Session-Aware Portrait Generation** — Reference previous prompts within a session for iterative generation
- **Rate Limiting** — 10 portrait generation requests per minute per IP

---

## API

The backend exposes a REST + SSE API at `http://localhost:3001`.

| Method   | Path                           | Description                                         |
|----------|--------------------------------|-----------------------------------------------------|
| `POST`   | `/api/generate`                | Generate a portrait                                 |
| `POST`   | `/api/enhance-prompt`          | Preview enhanced prompt only                        |
| `GET`    | `/api/gallery`                 | List saved portraits (paginated)                    |
| `GET`    | `/api/gallery/featured`        | Latest portrait ID for each given figure name       |
| `GET`    | `/api/gallery/{id}`            | Portrait metadata by ID                             |
| `GET`    | `/api/gallery/{id}/image`      | Serve stored image bytes (PNG) from DB              |
| `DELETE` | `/api/gallery/{id}`            | Delete portrait by ID                               |
| `GET`    | `/api/styles`                  | List available art styles                           |
| `GET`    | `/api/figures`                 | Paginated + filtered figures catalog                |
| `GET`    | `/api/figures/meta`            | Distinct eras, origins, tags for filters            |
| `GET`    | `/api/figures/{slug}`          | Single figure by slug                               |
| `POST`   | `/api/figures`                 | Create a figure                                     |
| `GET`    | `/api/stats`                   | Live counts (portraits, figures, styles)            |
| `POST`   | `/api/chat`                    | Streaming SSE chatbot (RAG-grounded)                |
| `POST`   | `/api/chat/{session_id}/reset` | Close session, get new session_id                   |
| `GET`    | `/api/health`                  | Health check                                        |

Full API reference in the [Backend README](backend/README.md#api-reference).

---

## Customization

| Goal                        | Where                                                          |
|-----------------------------|----------------------------------------------------------------|
| Add art styles              | `frontend/lib/constants.ts` — `STYLES` array                  |
| Add quick-start templates   | `frontend/lib/constants.ts` — `QUICK_START_TEMPLATES` array   |
| Add historical figures      | `backend/scripts/figures_data.json` + run `seed_figures.py`   |
| Tune portrait prompt chains | `backend/services/prompt_builder.py`                          |
| Tune chatbot system prompt  | `backend/services/chatbot.py` — `_SYSTEM_TEMPLATE`            |
| Adjust RAG retrieval depth  | `CHATBOT_RETRIEVAL_K` in `backend/.env`                       |
| Change FAISS refresh rate   | `CHATBOT_INDEX_TTL` in `backend/.env`                         |
| Change enhancement model    | `OPENAI_PROMPT_MODEL` in `backend/.env`                       |
| Adjust rate limits          | `backend/routers/generate.py`                                 |

---

## Project Status

**Current state: Feature-complete MVP.** Core generation pipeline, gallery, figures catalog, stats, and RAG chatbot are all operational.

### Known Limitations

| ID      | Area           | Description |
|---------|----------------|-------------|
| TD-001  | Infrastructure | SQLite + BLOB image storage will not survive concurrent load. Needs PostgreSQL + object storage (S3/R2). |
| TD-002  | Infrastructure | FAISS index is in-process RAM only — not shared across multiple workers. |
| TD-005  | Infrastructure | No Docker/Compose setup. Full stack requires manual environment setup. |
| TD-006  | Infrastructure | No CI/CD pipeline. |
| BUG-001 | Frontend       | Hero section shows broken cards if the DB has no portraits for the featured figures. |
| BUG-003 | Frontend       | No navigation guard — mid-generation navigation silently discards the result. |
| FEAT-001| Feature        | No user accounts or auth. All usage is anonymous. |
| FEAT-002| Feature        | No portrait download button. |
| FEAT-003| UX             | Generation takes 15–20 seconds with no progress feedback. |
