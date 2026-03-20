# ChronoCanvasAI — Backend

FastAPI backend for AI-powered historical portrait generation and a RAG chatbot grounded in the figures catalog. Orchestrates prompt enhancement with GPT-4o-mini, image generation with DALL·E 3 through a LangGraph pipeline, and streaming chat responses via FAISS retrieval.

---

## Tech Stack

| Technology           | Version | Purpose                                        |
|----------------------|---------|------------------------------------------------|
| FastAPI              | 0.111.0 | Async REST API + SSE streaming                 |
| LangChain            | 0.2.6   | LLM chain orchestration + RAG chat             |
| LangGraph            | 0.1.19  | Multi-step generation workflow                 |
| langchain-openai     | 0.1.13  | GPT-4o-mini, DALL·E 3, embeddings wrappers     |
| langchain-core       | 0.2.22  | Base chain primitives                          |
| faiss-cpu            | 1.8.0   | In-memory vector similarity search             |
| SQLAlchemy           | 2.0.31  | ORM for portrait, figures, and chat tables     |
| SQLite + aiosqlite   | —       | Local database                                 |
| slowapi              | 0.1.9   | Rate limiting (10 req/min per IP)              |
| Uvicorn              | 0.30.1  | ASGI server                                    |
| Pydantic             | v2      | Request/response validation                    |

---

## Project Structure

```
backend/
├── main.py                     # FastAPI app, CORS, rate limiting, lifespan
├── config.py                   # Typed env var loader (str/int/float/bool getters)
├── database.py                 # SQLAlchemy engine, SessionLocal, get_db() dependency
├── llm.py                      # Shared ChatOpenAI instance
├── logger.py                   # Logging setup
├── rate_limit.py               # slowapi limiter instance
├── requirements.txt
├── .env.example
├── pytest.ini
│
├── models/
│   ├── portrait.py             # ORM — portraits table (stores image bytes as BLOB)
│   ├── figure.py               # ORM — figures table (catalog data)
│   ├── style.py                # ORM — styles table
│   ├── chat.py                 # ORM — chat_sessions + chat_messages tables
│   └── schemas.py              # Pydantic v2 schemas (requests + responses)
│
├── routers/
│   ├── health.py               # GET /api/health
│   ├── generate.py             # POST /api/generate
│   ├── enhance_prompt.py       # POST /api/enhance-prompt
│   ├── gallery.py              # GET|DELETE /api/gallery/**
│   ├── styles.py               # GET /api/styles
│   ├── figures.py              # GET|POST /api/figures + /meta + /{slug}
│   ├── stats.py                # GET /api/stats
│   └── chatbot.py              # POST /api/chat (SSE) + POST /api/chat/{id}/reset
│
├── services/
│   ├── image_generator.py      # LangGraph pipeline: enhance → generate → sanitize/retry
│   ├── prompt_builder.py       # GPT-4o-mini LCEL chains
│   ├── gallery.py              # DB CRUD for portraits
│   ├── figures_index.py        # FAISS vector index — build, TTL refresh, invalidation
│   └── chatbot.py              # RAG chat: retrieve → stream → persist to DB
│
└── scripts/
    ├── seed_figures.py         # CLI: bulk-import figures from JSON
    ├── seed_styles.py          # CLI: seed styles table
    └── figures_data.json       # Source data for figure seeding
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- An OpenAI API key with access to GPT-4o-mini, DALL·E 3, and text-embedding-3-small

### Setup

```bash
cd backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — OPENAI_API_KEY is required; all other vars have sensible defaults

uvicorn main:app --reload --port 3001
```

Server runs at `http://localhost:3001`.

On first startup the app will:
1. Create all database tables
2. Build the FAISS index by embedding all figures (requires OpenAI call)
3. Verify OpenAI connectivity

---

## Environment Variables

| Variable                    | Required | Default                   | Description                        |
|-----------------------------|----------|---------------------------|------------------------------------|
| `OPENAI_API_KEY`            | Yes      | —                         | OpenAI API key                     |
| `PORT`                      | No       | `3001`                    | Server port                        |
| `FRONTEND_URL`              | No       | `http://localhost:3000`   | Allowed CORS origin                |
| `LOG_LEVEL`                 | No       | `INFO`                    | Logging level                      |
| `OPENAI_PROMPT_MODEL`       | No       | `gpt-4o-mini`             | Model for prompt enhancement + chat|
| `OPENAI_PROMPT_TEMPERATURE` | No       | `0.8`                     | Temperature for prompt chains      |
| `OPENAI_PROMPT_MAX_RETRIES` | No       | `2`                       | LLM retry attempts                 |
| `OPENAI_IMAGE_MODEL`        | No       | `dall-e-3`                | Image generation model             |
| `IMAGE_SIZE`                | No       | `1024x1024`               | DALL·E output resolution           |
| `OPENAI_EMBEDDING_MODEL`    | No       | `text-embedding-3-small`  | Embedding model for FAISS index    |
| `CHATBOT_RETRIEVAL_K`       | No       | `5`                       | Top-k figures returned per query   |
| `CHATBOT_INDEX_TTL`         | No       | `300`                     | Seconds before FAISS auto-refresh  |
| `GENERATE_RATE_LIMIT`       | No       | `10/minute`               | slowapi rule for /api/generate     |
| `LANGCHAIN_TRACING_V2`      | No       | `false`                   | Enable LangSmith tracing           |
| `LANGCHAIN_API_KEY`         | No       | —                         | LangSmith API key                  |
| `LANGCHAIN_PROJECT`         | No       | `chronocanvasai`          | LangSmith project name             |

---

## API Reference

### Portrait Generation

#### `POST /api/generate`

Generate a portrait for a historical figure. Rate limited to **10 requests per minute per IP**.

**Request**
```json
{
  "figure": "Napoleon Bonaparte standing on a misty battlefield",
  "style": "renaissance",
  "user_prompt": "make the lighting dramatic",
  "session_id": "optional-uuid",
  "enhance": true
}
```

**Response**
```json
{
  "image_url": "/api/gallery/42/image",
  "revised_prompt": "...",
  "enhanced_prompt": "A detailed oil painting...",
  "figure": "Napoleon Bonaparte",
  "figure_title": "Napoleon Bonaparte",
  "style": "renaissance"
}
```

---

#### `POST /api/enhance-prompt`

Preview the enhanced prompt without generating an image.

**Request**
```json
{ "figure": "Cleopatra", "style": "watercolor", "user_prompt": "optional" }
```

**Response**
```json
{ "enhanced_prompt": "Cleopatra VII...", "figure": "Cleopatra", "style": "watercolor" }
```

---

### Gallery

#### `GET /api/gallery`

Paginated portrait list.

| Param       | Type   | Default | Description              |
|-------------|--------|---------|--------------------------|
| `page`      | int    | `1`     | Page number              |
| `page_size` | int    | `12`    | Items per page (max 50)  |
| `style`     | string | —       | Filter by art style      |

#### `GET /api/gallery/featured`

Latest portrait ID per figure name.

| Param     | Type   | Description                                 |
|-----------|--------|---------------------------------------------|
| `figures` | string | Comma-separated names, e.g. `Cleopatra,Tesla`|

#### `GET /api/gallery/{id}/image`

Serves PNG bytes from the database (not from expiring DALL·E CDN URLs).

#### `DELETE /api/gallery/{id}`

Delete a portrait by ID.

---

### Figures Catalog

#### `GET /api/figures`

Paginated figures list with filters.

| Param       | Type   | Description                        |
|-------------|--------|------------------------------------|
| `page`      | int    | Page number (default 1)            |
| `page_size` | int    | Per page (default 20, max 100)     |
| `era`       | string | Filter by era                      |
| `origin`    | string | Filter by origin                   |
| `tags`      | string | Filter by tag (partial match)      |
| `search`    | string | Full-text search on name           |
| `featured`  | bool   | Show featured figures only         |
| `born_min`  | int    | Min birth year                     |
| `born_max`  | int    | Max birth year                     |

#### `GET /api/figures/meta`

Returns distinct values for filter dropdowns.

```json
{ "eras": ["Ancient", "Medieval", ...], "origins": ["Egypt", ...], "tags": ["philosopher", ...] }
```

#### `GET /api/figures/{slug}`

Single figure by URL slug.

#### `POST /api/figures`

Create a new figure. Also invalidates the FAISS index so the chatbot reflects the new figure immediately.

---

### Stats

#### `GET /api/stats`

```json
{ "portraits_created": 142, "unique_figures": 58, "styles_available": 5 }
```

---

### Chatbot

#### `POST /api/chat`

Streaming SSE endpoint. Loads session history from DB, runs FAISS retrieval, streams GPT-4o-mini response, persists the exchange.

**Request**
```json
{ "message": "Who was Cleopatra?", "session_id": "optional-uuid" }
```

**SSE event stream**
```
data: {"token": "Cleo"}
data: {"token": "patra"}
...
data: [DONE]
```

#### `POST /api/chat/{session_id}/reset`

Stamps the current session's `last_active` and creates a fresh `ChatSession` row. Existing messages are **retained** in the DB for analytics.

**Response**
```json
{ "new_session_id": "550e8400-e29b-41d4-a716-446655440000" }
```

---

### Health

#### `GET /api/health`

Returns OpenAI connectivity status.

---

## Generation Pipeline

The core logic in `services/image_generator.py` is a LangGraph state machine:

```
extract_figure_and_style
      ↓
enhance_prompt  (or format_prompt when enhance=False)
      ↓
generate_image  (DALL·E 3)
      ↓ (on content policy violation, attempt < 2)
sanitize_figure_description → enhance_prompt → generate_image (retry)
      ↓ (success)
download image bytes from CDN
      ↓
save portrait + image_data to gallery.db
```

1. **extract** — GPT-4o-mini parses raw input into `figure_title` + `resolved_style` using structured output.
2. **enhance_prompt** — Builds a vivid DALL·E prompt. Uses `enhance_prompt_with_history` (session-aware via `RunnableWithMessageHistory`) when a `session_id` is provided; `format_prompt` when `enhance=false`.
3. **generate_image** — Sends the prompt to DALL·E 3.
4. **sanitize** — If DALL·E rejects on content policy, rewrites conflict/violence language as peaceful alternatives, then retries once.
5. **download** — Stores image bytes in the `image_data` column so the gallery never depends on expiring CDN URLs.

---

## RAG Chatbot

### FAISS Index (`services/figures_index.py`)

- Embeds all figures at startup using `text-embedding-3-small` in one batched call
- Stored in RAM; rebuilt on TTL expiry (background task) or immediately on `invalidate()` after a figure is created
- Also computes a catalog summary string (total figures, list of eras, origins, top tags) used as global context

### Chat flow (`services/chatbot.py`)

1. Open DB session → ensure `ChatSession` exists → load `ChatMessage` history → close session
2. Embed user message → FAISS `similarity_search` → top-k figure documents
3. Build system prompt: catalog summary block + RAG context block + strict rules
4. Stream response from GPT-4o-mini; yield each token
5. After stream: open DB session → write user row + assistant row (with all metrics) → bump `last_active` → close session

### DB schema

**`chat_sessions`** — one row per session

| Column       | Type     |
|--------------|----------|
| `session_id` | String   |
| `created_at` | DateTime |
| `last_active`| DateTime |

**`chat_messages`** — one row per turn

| Column              | Type     | Notes                          |
|---------------------|----------|--------------------------------|
| `session_id`        | String   | Indexed                        |
| `role`              | String   | `'user'` or `'assistant'`      |
| `content`           | Text     |                                |
| `prompt_tokens`     | Integer  | Assistant rows only            |
| `completion_tokens` | Integer  | Assistant rows only            |
| `total_tokens`      | Integer  | Assistant rows only            |
| `retrieval_ms`      | Float    | FAISS search duration          |
| `first_token_ms`    | Float    | Time to first token            |
| `total_ms`          | Float    | Full round-trip                |
| `docs_retrieved`    | Integer  | FAISS hits used as context     |

---

## Running Tests

```bash
pytest
```

Test configuration is in `pytest.ini`. Tests use `pytest-asyncio` for async endpoint testing.

---

## Customization

**Tune the chatbot system prompt** — Edit `_SYSTEM_TEMPLATE` in `services/chatbot.py`.

**Change retrieval depth** — Set `CHATBOT_RETRIEVAL_K` in `.env`.

**Change the FAISS refresh interval** — Set `CHATBOT_INDEX_TTL` in `.env`.

**Tune the portrait enhancement prompt** — Edit `services/prompt_builder.py`.

**Change the LLM model** — Set `OPENAI_PROMPT_MODEL` in `.env`.

**Add art styles** — Insert rows into the `styles` table or re-run `scripts/seed_styles.py`.

**Add historical figures** — Edit `scripts/figures_data.json` and run `seed_figures.py`. Alternatively `POST /api/figures` — the FAISS index is invalidated automatically.

**Adjust rate limits** — Edit the decorator on the generate route in `routers/generate.py`.
