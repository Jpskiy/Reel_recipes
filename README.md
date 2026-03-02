# Reel Recipes (Local-only AI Upload MVP)

A clean local-first MVP that turns uploaded recipe videos into editable recipes.

## Stack
- Frontend: Next.js (TypeScript, App Router) on port 3000
- Backend: FastAPI (Python 3.11+) on port 8000
- Storage: SQLite
- AI: faster-whisper (local transcription) + Ollama (local LLM)
- Media: ffmpeg audio extraction

## Environment
Copy backend env file:

```bash
cd backend
cp .env.example .env
```

Backend variables:
- `DATABASE_URL=sqlite:///./app.db`
- `STORAGE_DIR=storage`
- `MAX_UPLOAD_MB=200`
- `OLLAMA_HOST=http://localhost:11434`
- `RECIPE_MODEL=qwen2.5:7b-instruct`
- `TRANSCRIPTION_MODEL_SIZE=small`
- `TRANSCRIPTION_DEVICE=cpu`
- `TRANSCRIPTION_COMPUTE_TYPE=int8`
- `ENABLE_VISION=false`

## Run locally

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Test the build

### Prerequisites
```bash
ffmpeg -version
```
Expected: version output with build metadata.

Install/pull Ollama model:
```bash
ollama pull qwen2.5:7b-instruct
```
Expected: model pulled successfully.

Verify Ollama:
```bash
curl.exe http://localhost:11434/api/tags
```
Expected: JSON payload listing local models.

### API + proxy checks
1) Backend recipes list:
```bash
curl.exe http://localhost:8000/api/recipes
```
Expected: JSON array `[]` or recipe items.

2) Frontend proxy rewrite:
```bash
curl.exe -i http://localhost:3000/api/recipes
```
Expected: `HTTP/1.1 200 OK` and JSON body.

3) Upload video to backend:
```bash
curl.exe -F "file=@sample.mp4" http://localhost:8000/api/recipes/upload
```
Expected: JSON with `{ "id": "...", "status": "queued" }`.

4) Poll until ready:
```bash
curl.exe http://localhost:8000/api/recipes/<ID>/status
```
Expected: JSON status transitions queued -> processing -> ready (or error).

Then fetch full recipe:
```bash
curl.exe http://localhost:8000/api/recipes/<ID>
```
Expected: JSON record with populated `recipe_json.ingredients` and `recipe_json.steps`.

## Troubleshooting
- **Ollama not reachable**: ensure Ollama app/service is running and `OLLAMA_HOST` is correct.
- **Model not found**: run `ollama pull qwen2.5:7b-instruct` and confirm via `/api/tags`.
- **ffmpeg not found**: install ffmpeg and ensure it is in `PATH`.
- **Transcription too slow**: lower `TRANSCRIPTION_MODEL_SIZE` (e.g., `base` or `tiny`).
- **JSON invalid**: pipeline retries once with a repair prompt; if it still fails, job is marked `error` with message.

## API
- `POST /api/recipes/upload` (multipart form file) -> `{id,status}`
- `GET /api/recipes/{id}/status` -> `{status,progress,error_message}`
- `GET /api/recipes/{id}` -> job record + parsed `recipe_json`
- `PUT /api/recipes/{id}` -> update `recipe_json`
- `GET /api/recipes` -> list recent recipes

## License
MIT
