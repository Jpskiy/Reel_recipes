'use client';

import { FormEvent, useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';

type RecipeListItem = { id: string; status: string; progress: number; created_at: string };

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [recent, setRecent] = useState<RecipeListItem[]>([]);

  const loadRecent = async () => {
    const items = await apiFetch<RecipeListItem[]>('/api/recipes');
    setRecent(items);
  };

  useEffect(() => {
    loadRecent().catch((err) => setMessage(err.message));
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const form = new FormData();
    form.append('file', file);

    try {
      const data = await apiFetch<{ id: string; status: string }>('/api/recipes/upload', {
        method: 'POST',
        body: form,
      });
      setMessage(`Uploaded. Job ID: ${data.id}`);
      setFile(null);
      await loadRecent();
    } catch (err) {
      setMessage((err as Error).message);
    }
  };

  return (
    <main style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>Reel Recipes Local MVP</h1>
      <p>Upload a video file to extract a recipe using local faster-whisper + Ollama.</p>

      <form onSubmit={onSubmit}>
        <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button type="submit" disabled={!file}>Upload</button>
      </form>
      {message && <p>{message}</p>}

      <h2>Recent Recipes</h2>
      <ul>
        {recent.map((item) => (
          <li key={item.id}>
            <a href={`/recipes/${item.id}`}>{item.id}</a> — {item.status} ({item.progress}%)
          </li>
        ))}
      </ul>
    </main>
  );
}
