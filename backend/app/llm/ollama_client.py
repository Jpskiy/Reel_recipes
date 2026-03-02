import base64
from pathlib import Path

import httpx


DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=5.0, read=180.0)


class OllamaError(RuntimeError):
    pass


def _generate(payload: dict, host: str) -> str:
    endpoint = f"{host.rstrip('/')}/api/generate"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.post(endpoint, json={**payload, "stream": False})
            response.raise_for_status()
    except httpx.ConnectError as exc:
        raise OllamaError(f"Ollama not reachable at {host}. Ensure Ollama is running and OLLAMA_HOST is correct.") from exc
    except httpx.TimeoutException as exc:
        raise OllamaError(f"Ollama request to {host} timed out.") from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or "no response body"
        raise OllamaError(f"Ollama request failed with status {exc.response.status_code}: {detail}") from exc
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise OllamaError("Ollama returned a non-JSON HTTP response.") from exc

    if payload.get("error"):
        raise OllamaError(str(payload["error"]))

    content = payload.get("response")
    if not isinstance(content, str):
        raise OllamaError("Ollama response did not include a text result.")
    return content.strip()


def generate_json(prompt: str, model: str, host: str) -> str:
    return _generate({"model": model, "prompt": prompt, "format": "json"}, host)


def describe_images(prompt: str, frame_paths: list[Path], model: str, host: str) -> str:
    if not frame_paths:
        return ""
    encoded_frames = [base64.b64encode(frame.read_bytes()).decode("utf-8") for frame in frame_paths]
    return _generate({"model": model, "prompt": prompt, "images": encoded_frames}, host)
