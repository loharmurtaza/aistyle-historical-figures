# ChronoCanvasAI — Backend

FastAPI backend for AI-powered historical portrait generation. Orchestrates prompt enhancement with GPT-4o-mini and image generation with DALL·E 3 through a LangGraph pipeline.

---

## Tech Stack

| Technology          | Version | Purpose                             |
|---------------------|---------|-------------------------------------|
| FastAPI             | 0.111.0 | Async REST API framework            |
| LangChain           | 0.2.6   | LLM chain orchestration             |
| LangGraph           | 0.1.19  | Multi-step generation workflow      |  
| langchain-openai    | 0.1.13  | GPT-4o-mini + DALL·E 3 wrappers     |
| SQLAlchemy          | 2.0.31  | Async ORM for portrait persistence  |
| SQLite + aiosqlite  | —       | Local database                      |
| slowapi             | 0.1.9   | Rate limiting (10 req/min per IP)   |
| Uvicorn             | 0.30.1  | ASGI server                         |
| Pydantic            | v2      | Request/response validation         |

---

## Project Structure

```
backend/
├── main.py                     # FastAPI app, CORS, rate limiting, lifespan
├── config.py                   # Environment variable loader (pydantic-settings)
├── database.py                 # SQLAlchemy async engine + session factory
├── llm.py                      # OpenAI LLM instance configuration
├── logger.py                   # Logging setup
├── rate_limit.py               # slowapi limiter instance
├── requirements.txt
├── .env.example                # Environment variable template
├── pytest.ini
│
├── models/
│   ├── portrait.py             # Portrait ORM model (SQLAlchemy) — stores image bytes
│   └── schemas.py              # Pydantic schemas (requests + responses)
│
├── routers/
│   ├── health.py               # GET /api/health
│   ├── generate.py             # POST /api/generate
│   ├── enhance_prompt.py       # POST /api/enhance-prompt
│   ├── gallery.py              # GET/DELETE /api/gallery + featured + image endpoints
│   └── styles.py               # GET /api/styles
│
└── services/
    ├── image_generator.py      # LangGraph pipeline (enhance → generate → sanitize/soften → retry)
    ├── prompt_builder.py       # GPT-4o-mini prompt chains + sanitize chain
    └── gallery.py              # Database CRUD for portraits
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- An OpenAI API key with access to GPT-4o-mini and DALL·E 3

### Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in your values (see Environment Variables below)

# Start the server
uvicorn main:app --reload --port 3001
```

Server runs at `http://localhost:3001`.

---

## Environment Variables

Copy `.env.example` to `.env` and set the following:

| Variable            | Required  | Default                   | Description                   |
|---------------------|-----------|---------------------------|-------------------------------|
| `OPENAI_API_KEY`    | Yes       | —                         | OpenAI API key                |
| `PORT`              | No        | `3001`                    | Server port                   |
| `FRONTEND_URL`      | No        | `http://localhost:3000`   | Allowed CORS origin           |
| `LOG_LEVEL`         | No        | `INFO`                    | Logging level                 | 
| `OPENAI_MODEL`      | No        | `gpt-4o-mini`             | Model for prompt enhancement  |
| `LANGCHAIN_API_KEY` | No        | —                         | LangSmith tracing (optional)  |

---

## API Reference

### `POST /api/generate`

Generates a portrait for a historical figure in a given art style.

Rate limited to **10 requests per minute per IP**.

**Request**
```json
{
  "figure": "Napoleon Bonaparte standing on a misty battlefield",
  "style": "renaissance",
  "session_id": "optional-session-id"
}
```

**Response**
```json
{
  "imageUrl": "https://oaidalleapiprodscus.blob.core.windows.net/...",
  "revisedPrompt": "A detailed oil painting in the Renaissance style..."
}
```

---

### `POST /api/enhance-prompt`

Returns an enhanced version of the user's prompt without generating an image. Useful for previewing what GPT-4o-mini produces.

**Request**
```json
{
  "figure": "Cleopatra in her palace",
  "style": "watercolor",
  "session_id": "optional-session-id"
}
```

**Response**
```json
{
  "enhancedPrompt": "Cleopatra VII seated on her gilded throne..."
}
```

---

### `GET /api/gallery`

Returns paginated list of saved portraits.

**Query Parameters**

| Param       | Type    | Default | Description             |
|-------------|---------|-------  |-------------------------|
| `page`      | int     | `1`     | Page number             |
| `page_size` | int     | `12`    | Items per page (max 50) |
| `style`     | string  | —       | Filter by art style     |

**Response**
```json
{
  "items": [
    {
      "id": 1,
      "figure": "Napoleon Bonaparte",
      "style": "renaissance",
      "imageUrl": "https://...",
      "originalPrompt": "...",
      "enhancedPrompt": "...",
      "createdAt": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 12
}
```

---

### `GET /api/gallery/featured`

Returns the latest portrait ID for each of the provided figure names. Used by the home page hero section to display real generated images.

**Query Parameters**

| Param     | Type    | Description                                                         |
|-----------|---------|---------------------------------------------------------------------|
| `figures` | string  | Comma-separated figure names to search (e.g. `Cleopatra,Da Vinci`)  |

**Response**
```json
[
  { "search_term": "Cleopatra", "id": 12 },
  { "search_term": "Da Vinci", "id": null }
]
```

---

### `GET /api/gallery/{id}`

Returns a single portrait's metadata by ID.

---

### `GET /api/gallery/{id}/image`

Serves the stored PNG image bytes directly from the database. Used by the frontend instead of the original DALL·E CDN URL (which expires).

---

### `DELETE /api/gallery/{id}`

Deletes a portrait by ID.

---

### `GET /api/styles`

Returns the list of available art styles.

---

### `GET /api/health`

Health check endpoint.

---

## Generation Pipeline

The core logic lives in `services/image_generator.py` as a **LangGraph** state machine:

```
extract_figure_and_style
      ↓
enhance_prompt  (or format_prompt when enhance=False)
      ↓
generate_image
      ↓ (on content policy violation)
sanitize_figure_description → enhance_prompt → generate_image (retry once)
      ↓
download image bytes from CDN
      ↓
save portrait + image_data to gallery.db
```

1. **extract** — GPT-4o-mini parses the raw input into a clean figure title and resolved art style.
2. **enhance_prompt** — Builds a vivid DALL·E 3 prompt with historical context and style-specific language. When `enhance=false`, uses `format_prompt` instead (preserves user intent, no creative additions).
3. **generate_image** — Sends the enhanced prompt to DALL·E 3 via `DallEAPIWrapper`.
4. **sanitize + soften** — If DALL·E rejects the prompt on content policy grounds, `sanitize_figure_description` rewrites the scene description to remove combat/conflict language (e.g. "fighting" → "facing"), then re-enhances and retries once. Respects the `enhance` flag — uses `format_prompt` if enhancement was disabled.
5. **image download** — After a successful generation the image is downloaded from the CDN and stored as binary in the `image_data` column, so the gallery never depends on expiring CDN URLs.

Every successful generation is auto-saved to `gallery.db` via `services/gallery.py`.

---

## Session-Aware Prompt History

`prompt_builder.py` exposes two chains:

- `enhance_prompt(figure, style)` — Stateless, single-turn enhancement.
- `enhance_prompt_with_history(figure, style, session_id)` — History-aware chain using `RunnableWithMessageHistory`. Allows users to reference previous generations within a session (e.g., "same pose but baroque style").

---

## Running Tests

```bash
pytest
```

Test configuration is in `pytest.ini`. Tests use `pytest-asyncio` for async endpoint testing.

---

## Customization

**Change the prompt enhancement model** — Set `OPENAI_MODEL` in `.env`.

**Tune the enhancement prompt** — Edit the `ChatPromptTemplate` in `services/prompt_builder.py`.

**Add new art styles** — The backend accepts any style string; styles are defined on the frontend in `frontend/lib/constants.ts`.

**Adjust rate limits** — Edit the decorator on the generate route in `routers/generate.py`.
