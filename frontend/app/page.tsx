'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { API_URL } from '../components/api';

type RecipeListItem = { id: number; status: string; source_filename: string; created_at: string };

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState('');
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);

  async function loadRecipes() {
    const res = await fetch(`${API_URL}/api/recipes`);
    if (res.ok) setRecipes(await res.json());
  }

  useEffect(() => {
    loadRecipes();
  }, []);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setProgress('Uploading...');
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_URL}/api/recipes/upload`, { method: 'POST', body: formData });
    if (!res.ok) {
      setProgress('Upload failed');
      setUploading(false);
      return;
    }
    const data = await res.json();
    setProgress(`Uploaded! Recipe ID ${data.id}`);
    setUploading(false);
    loadRecipes();
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
