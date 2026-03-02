export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

function snippet(text: string): string {
  return text.replace(/\s+/g, ' ').trim().slice(0, 200);
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  const bodyText = await res.text();

  if (!res.ok) {
    throw new Error(`Request failed (${res.status}): ${snippet(bodyText)}`);
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.toLowerCase().includes('application/json')) {
    throw new Error(`Expected JSON but got '${contentType || 'unknown'}' (${res.status}): ${snippet(bodyText)}`);
  }

  try {
    return JSON.parse(bodyText) as T;
  } catch (error) {
    throw new Error(`Invalid JSON response (${res.status}): ${snippet(bodyText)} | ${(error as Error).message}`);
  }
}
