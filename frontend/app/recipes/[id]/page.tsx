'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { API_URL, RecipeData } from '../../../components/api';

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

  async function loadStatus() {
    const res = await fetch(`${API_URL}/api/recipes/${id}/status`);
    if (res.ok) setStatus(await res.json());
  }

  async function loadRecipe() {
    const res = await fetch(`${API_URL}/api/recipes/${id}`);
    if (!res.ok) return;
    const data: RecipeResponse = await res.json();
    setRecipeData(data.recipe);
    setEditor(JSON.stringify(data.recipe, null, 2));
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
      const res = await fetch(`${API_URL}/api/recipes/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe: parsed }),
      });
      if (res.ok) {
        setSaveMsg('Saved successfully');
        setRecipeData(parsed);
      } else {
        setSaveMsg('Failed to save');
      }
    } catch {
      setSaveMsg('Invalid JSON');
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
