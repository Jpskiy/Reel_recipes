'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../../lib/api';

type RecipeData = {
  title: string;
  servings: number | null;
  total_time_minutes: number | null;
  ingredients: { item: string; quantity: number | null; unit: string | null; prep: string | null }[];
  steps: { n: number; text: string; timer_seconds: number | null }[];
  equipment: string[];
  notes: string[];
};

type StatusResponse = { status: 'uploaded' | 'processing' | 'ready' | 'error'; progress: number; error: string | null };
type RecipeResponse = {
  id: number;
  status: string;
  transcript_text: string;
  vision_notes: string;
  recipe: RecipeData | null;
  error_message: string | null;
};

export default function RecipePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [recipeData, setRecipeData] = useState<RecipeData | null>(null);
  const [editor, setEditor] = useState('');
  const [saveMsg, setSaveMsg] = useState('');
  const [error, setError] = useState('');

  async function loadStatus() {
    try {
      const data = await apiFetch<StatusResponse>(`/api/recipes/${id}/status`);
      setStatus(data);
      setError('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadRecipe() {
    try {
      const data = await apiFetch<RecipeResponse>(`/api/recipes/${id}`);
      setRecipeData(data.recipe);
      setEditor(JSON.stringify(data.recipe, null, 2));
      setError('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 2000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    if (status?.status === 'ready') loadRecipe();
  }, [status?.status]);

  const groceryItems = useMemo(() => recipeData?.ingredients.map((i) => `${i.quantity ?? ''} ${i.unit ?? ''} ${i.item}`.trim()) ?? [], [recipeData]);

  async function saveEdits() {
    try {
      const parsed = JSON.parse(editor);
      await apiFetch<RecipeResponse>(`/api/recipes/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe: parsed }),
      });
      setSaveMsg('Saved successfully');
      setRecipeData(parsed);
      setError('');
    } catch (err) {
      setSaveMsg('Failed to save');
      setError((err as Error).message);
    }
  }

  return (
    <main>
      <Link href="/">← Back</Link>
      <h1>Recipe #{id}</h1>
      <div className="card">
        <h2>Status</h2>
        <p>{status ? `${status.status} (${status.progress}%)` : 'Loading...'}</p>
        {status?.error && <p>Error: {status.error}</p>}
        {error && <p style={{ color: '#b00020' }}>Request error: {error}</p>}
      </div>

      {recipeData && (
        <>
          <div className="card">
            <h2>{recipeData.title}</h2>
            <p>Servings: {recipeData.servings ?? 'N/A'} | Total time: {recipeData.total_time_minutes ?? 'N/A'} min</p>
            <h3>Ingredients</h3>
            <ul>{recipeData.ingredients.map((i, idx) => <li key={idx}>{i.quantity ?? ''} {i.unit ?? ''} {i.item} {i.prep ? `(${i.prep})` : ''}</li>)}</ul>
            <h3>Steps</h3>
            <ol>{recipeData.steps.map((s) => <li key={s.n}>{s.text}</li>)}</ol>
          </div>

          <div className="card">
            <h3>Grocery list</h3>
            {groceryItems.map((item, idx) => (
              <label key={idx} style={{ display: 'block' }}>
                <input type="checkbox" /> {item}
              </label>
            ))}
          </div>

          <div className="card">
            <h3>Edit recipe JSON</h3>
            <textarea value={editor} onChange={(e) => setEditor(e.target.value)} />
            <button onClick={saveEdits}>Save</button>
            <p>{saveMsg}</p>
          </div>
        </>
      )}
    </main>
  );
}
