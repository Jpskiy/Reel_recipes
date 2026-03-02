'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';

type RecipeListItem = { id: number; status: string; source_filename: string; created_at: string };
type UploadResponse = { id: number; status: string };

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);

  async function loadRecipes() {
    try {
      const data = await apiFetch<RecipeListItem[]>('/api/recipes');
      setRecipes(data);
      setError('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadRecipes();
  }, []);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setProgress('Uploading...');
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const data = await apiFetch<UploadResponse>('/api/recipes/upload', { method: 'POST', body: formData });
      setProgress(`Uploaded! Recipe ID ${data.id}`);
      loadRecipes();
    } catch (err) {
      setProgress('Upload failed');
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <main>
      <h1>Reel Recipes MVP</h1>
      <div className="card">
        <h2>Upload cooking video</h2>
        <form onSubmit={onUpload} className="row">
          <input type="file" accept="video/mp4,video/quicktime,video/webm" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <button disabled={uploading || !file}>{uploading ? 'Uploading...' : 'Upload'}</button>
        </form>
        <p>{progress}</p>
        {error && <p style={{ color: '#b00020' }}>Request error: {error}</p>}
      </div>

      <div className="card">
        <h2>Recent recipes</h2>
        <ul>
          {recipes.map((r) => (
            <li key={r.id}>
              <Link href={`/recipes/${r.id}`}>#{r.id} - {r.source_filename}</Link> ({r.status})
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
