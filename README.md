# Reel_recipes

Upload-only MVP that converts short cooking videos (`.mp4/.mov/.webm`) into structured, editable recipes.

## Tech stack
- **Backend:** FastAPI, SQLAlchemy, SQLite, Pydantic, OpenAI SDK
- **Frontend:** Next.js (App Router), TypeScript, plain CSS
- **Media pipeline:** `ffmpeg` via safe `subprocess.run`

## Features
- Upload video and get immediate `recipe_id`
- Background processing with status polling
- Audio transcription + frame extraction
- Vision notes (best effort; falls back to transcript-only)
- Strict JSON recipe generation + Pydantic validation + one-shot JSON repair
- Recipe viewer/editor and grocery checklist
- SQLite persistence and local storage at `backend/storage/{recipe_id}`

## Repository tree

```text
Reel_recipes/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── tests/
│   │   ├── test_schema.py
│   │   └── test_status_endpoint.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── recipes/[id]/page.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/api.ts
│   ├── .env.example
│   ├── next-env.d.ts
│   ├── next.config.mjs
│   ├── package.json
│   └── tsconfig.json
├── .gitignore
├── LICENSE
└── README.md
```

## Local setup

### 1) Install ffmpeg
- **macOS:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
- **Windows:** install from https://ffmpeg.org/download.html and add `ffmpeg` to `PATH`

Verify:
```bash
ffmpeg -version
```

### 2) Backend setup (port 8000)
```bash
cd backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
# edit .env and set OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 3) Frontend setup (port 3000)
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000.

## API endpoints
- `POST /api/recipes/upload` (multipart file)
- `GET /api/recipes/{id}/status`
- `GET /api/recipes/{id}`
- `PUT /api/recipes/{id}`
- `GET /api/recipes`

## Recipe JSON schema
```json
{
  "title": "string",
  "servings": 2,
  "total_time_minutes": 25,
  "ingredients": [
    {"item": "onion", "quantity": 1, "unit": null, "prep": "diced"}
  ],
  "steps": [
    {"n": 1, "text": "Heat oil in pan.", "timer_seconds": 60}
  ],
  "equipment": ["pan"],
  "notes": ["Adjust salt to taste"]
}
```

## Troubleshooting
- **`ffmpeg` not found**
  - Ensure `ffmpeg -version` works in the same shell used to run backend.
- **OpenAI auth error / missing key**
  - Check `OPENAI_API_KEY` in `backend/.env`.
- **Model returns invalid JSON**
  - App retries once with a strict JSON-fix prompt. If still invalid, recipe status becomes `error` and error message is stored.
- **Large upload issues**
  - Keep files short for MVP; increase server/file limits via reverse proxy or app settings if needed.

## Running tests
```bash
cd backend
python -m pytest
```

## Notes
- Upload-only by design (no URL ingestion/scraping).
- Works locally on Windows/macOS/Linux with Python 3.11+ and Node 18+.
