# Reel_recipes

Upload-only MVP that converts short cooking videos (`.mp4/.mov/.webm`) into structured recipes (ingredients, steps, metadata) using a FastAPI backend and Next.js frontend.

## Local Development

### 0) Prerequisites
- Python 3.11+
- Node.js 18+
- ffmpeg installed and available in `PATH`
- Ollama installed/running locally (for local model checks in this repo workflow)
- OpenAI API key for transcription/recipe generation in backend

Verify tools:
```powershell
ffmpeg -version
ollama list
curl.exe http://localhost:11434/api/tags
```

---

### 1) Backend (Windows PowerShell - primary)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Expected: FastAPI running on `http://localhost:8000`.

#### macOS/Linux notes
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

---

### 2) Frontend (Windows PowerShell - primary)
```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Expected: Next.js running on `http://localhost:3000`.

#### Important API routing behavior
- Default recommended setting:
  - `NEXT_PUBLIC_API_URL=` (blank)
  - Frontend uses relative `/api/*`
  - Next.js rewrite proxies `/api/*` to `http://localhost:8000/api/*`
- Optional direct mode:
  - Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`
  - Frontend calls backend directly, bypassing rewrite.

This prevents the common `Unexpected token <` JSON parse error caused by receiving HTML from the Next dev server instead of JSON from FastAPI.

## Test the Build (End-to-End Checklist)

### 1) Verify prerequisites
```powershell
ffmpeg -version
```
Expected: ffmpeg version info.

```powershell
ollama list
```
Expected: list includes `qwen2.5:7b-instruct`.

```powershell
curl.exe http://localhost:11434/api/tags
```
Expected: JSON payload with installed models.

### 2) Verify backend is reachable
```powershell
curl.exe http://localhost:8000/api/recipes
```
Expected: JSON array, often `[]` on first run.

### 3) Verify frontend proxy works (prevents `Unexpected token <`)
```powershell
curl.exe -i http://localhost:3000/api/recipes
```
Expected:
- HTTP `200`
- JSON body (`[]` or recipe list)

If this returns HTML, rewrites or env config are wrong.

### 4) Upload sample video via API (no UI)
```powershell
curl.exe -F "file=@PATH_TO_VIDEO" http://localhost:8000/api/recipes/upload
```
Expected: JSON like:
```json
{"id": 1, "status": "uploaded"}
```
or `processing` depending on timing.

Poll status:
```powershell
curl.exe http://localhost:8000/api/recipes/<id>/status
```
Expected progression: `uploaded/processing` -> `ready` (or `error` with message).

Fetch final recipe:
```powershell
curl.exe http://localhost:8000/api/recipes/<id>
```
Expected: response includes populated `recipe` object with ingredients and steps.

### 5) UI test
1. Open `http://localhost:3000`.
2. Upload a video.
3. Open the created recipe detail page.
4. Confirm status updates and recipe renders.
5. Edit JSON and save.

If something fails, check:
- Backend terminal logs.
- `GET /api/recipes/<id>/status` for `error` text.
- `GET /api/recipes/<id>` for persisted payload.

## Troubleshooting

### `Unhandled Rejection: SyntaxError: Unexpected token <`
Cause: frontend got HTML (usually Next 404/error page) instead of JSON.
Fix:
1. Ensure backend is running on `http://localhost:8000`.
2. Ensure `frontend/next.config.mjs` includes rewrite `/api/:path* -> http://localhost:8000/api/:path*`.
3. Ensure `.env.local` has `NEXT_PUBLIC_API_URL=` (blank) for proxy mode, or explicitly set `http://localhost:8000` for direct mode.
4. Validate with:
```powershell
curl.exe -i http://localhost:3000/api/recipes
```

### `connection refused localhost:11434`
Ollama is not running.
```powershell
ollama serve
```
Then retry:
```powershell
curl.exe http://localhost:11434/api/tags
```

### `model not found`
```powershell
ollama pull qwen2.5:7b-instruct
```
Then verify with `ollama list`.

### `ModuleNotFoundError: faster_whisper`
Install missing dependency in your active venv.
```powershell
pip install faster-whisper
```
If needed, add it to `backend/requirements.txt`.

### `ffmpeg not found`
Install ffmpeg and ensure it is on PATH, then verify:
```powershell
ffmpeg -version
```

## API Endpoints
- `POST /api/recipes/upload`
- `GET /api/recipes/{id}/status`
- `GET /api/recipes/{id}`
- `PUT /api/recipes/{id}`
- `GET /api/recipes`

## License
MIT
