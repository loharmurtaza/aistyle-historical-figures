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
| Add historical figures    | `frontend/app/figures/page.tsx` — `FIGURES` array           |
| Tune prompt engineering   | `backend/services/prompt_builder.py`                        |
| Change enhancement model  | `OPENAI_MODEL` in `backend/.env`                            |
| Adjust rate limits        | `backend/routers/generate.py`                               |
