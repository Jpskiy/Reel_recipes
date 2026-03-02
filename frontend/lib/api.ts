export async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const contentType = response.headers.get('content-type') || '';

  if (!response.ok) {
    const errorText = contentType.includes('application/json')
      ? JSON.stringify(await response.json())
      : await response.text();
    throw new Error(`API ${response.status}: ${errorText}`);
  }

  if (!contentType.includes('application/json')) {
    const text = await response.text();
    throw new Error(`Expected JSON but received '${contentType || 'unknown'}': ${text.slice(0, 500)}`);
  }

  return response.json() as Promise<T>;
}
