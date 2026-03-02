# Reel_recipes

Upload-only MVP that converts short cooking videos (`.mp4/.mov/.webm`) into structured, editable recipes fully offline on a local machine after the required models are downloaded.

## Tech stack
- **Backend:** FastAPI, SQLAlchemy, SQLite, Pydantic, `faster-whisper`, Ollama HTTP API
- **Frontend:** Next.js (App Router), TypeScript, plain CSS
- **Media pipeline:** `ffmpeg` via safe `subprocess.run`

## Features
- Upload video and get an immediate `recipe_id`
- Background processing with status polling
- Local audio transcription with `faster-whisper`
- Local recipe JSON generation with Ollama
- Strict schema validation with a one-shot JSON repair retry
- Optional local vision notes with Ollama + `llava` (disabled by default)
- SQLite persistence and local storage at `backend/storage/{recipe_id}`

## Repository tree

```text
Reel_recipes/
|-- backend/
|   |-- app/
|   |   |-- llm/
|   |   |   |-- __init__.py
|   |   |   `-- ollama_client.py
|   |   |-- transcribe/
|   |   |   |-- __init__.py
|   |   |   `-- local_whisper.py
|   |   |-- __init__.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- schemas.py
|   |   `-- services.py
|   |-- tests/
|   |   |-- test_ollama_recipe_generation.py
|   |   |-- test_schema.py
|   |   `-- test_status_endpoint.py
|   |-- .env.example
|   `-- requirements.txt
|-- frontend/
|   |-- app/
|   |   |-- recipes/[id]/page.tsx
|   |   |-- globals.css
|   |   |-- layout.tsx
|   |   `-- page.tsx
|   |-- components/api.ts
|   |-- .env.example
|   |-- next-env.d.ts
|   |-- next.config.mjs
|   |-- package.json
|   `-- tsconfig.json
|-- .gitignore
|-- LICENSE
`-- README.md
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

### 2) Install Ollama
- **Windows/macOS:** install from https://ollama.com/download
- **Linux:** follow the install instructions at https://ollama.com/download/linux

Start Ollama, then pull the local recipe model:
```bash
ollama pull qwen2.5:7b-instruct
```

Optional vision model:
```bash
ollama pull llava:7b
```

### 3) Backend setup (port 8000)
```bash
cd backend
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Default backend settings are already local-only:
- `TRANSCRIPTION_MODEL_SIZE=small`
- `TRANSCRIPTION_DEVICE=cpu`
- `TRANSCRIPTION_COMPUTE_TYPE=int8`
- `OLLAMA_HOST=http://localhost:11434`
- `RECIPE_MODEL=qwen2.5:7b-instruct`
- `ENABLE_VISION=false`

To enable optional frame analysis, set:
- `ENABLE_VISION=true`
- `VISION_MODEL=llava:7b`

### 4) Frontend setup (port 3000)
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000.

## API endpoints
- `POST /api/recipes/upload` returns `{id, status}`
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
  - Ensure `ffmpeg -version` works in the same shell used to run the backend.
- **Ollama connection refused**
  - Start Ollama and confirm `OLLAMA_HOST` matches the running instance, usually `http://localhost:11434`.
- **Model not found**
  - Run `ollama pull qwen2.5:7b-instruct` and, if vision is enabled, `ollama pull llava:7b`.
- **Transcription slow**
  - Use `TRANSCRIPTION_MODEL_SIZE=tiny` or `base`, or switch to `TRANSCRIPTION_DEVICE=cuda` with `TRANSCRIPTION_COMPUTE_TYPE=float16` on a compatible GPU.
- **Model returns invalid JSON**
  - The app retries once with a strict repair prompt. If the repair also fails, recipe status becomes `error` and the error message is stored.

## Running tests
```bash
cd backend
python -m pytest
```

## Notes
- Upload-only by design (no URL ingestion or scraping).
- The app runs end-to-end offline after the local models have been downloaded.
- Works locally on Windows, macOS, and Linux with Python 3.11+ and Node 18+.
