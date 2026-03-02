'use client';

import { useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../../lib/api';

type RecipeData = {
  title: string;
  description: string;
  ingredients: string[];
  steps: string[];
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  servings: number | null;
  notes: string;
};

type StatusResponse = { status: 'queued' | 'processing' | 'ready' | 'error'; progress: number; error_message: string | null };
type RecordResponse = { id: string; status: string; progress: number; error_message: string | null; recipe_json: RecipeData | null };

export default function RecipeDetailPage({ params }: { params: { id: string } }) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [record, setRecord] = useState<RecordResponse | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const recipe = useMemo(() => record?.recipe_json ?? null, [record]);

  useEffect(() => {
    let interval: NodeJS.Timeout | undefined;

    const poll = async () => {
      try {
        const s = await apiFetch<StatusResponse>(`/api/recipes/${params.id}/status`);
        setStatus(s);
        if (s.status === 'ready' || s.status === 'error') {
          const rec = await apiFetch<RecordResponse>(`/api/recipes/${params.id}`);
          setRecord(rec);
          if (interval) clearInterval(interval);
        }
      } catch (e) {
        setError((e as Error).message);
        if (interval) clearInterval(interval);
      }
    };

    poll();
    interval = setInterval(poll, 3000);
    return () => interval && clearInterval(interval);
  }, [params.id]);

  const saveRecipe = async () => {
    if (!record?.recipe_json) return;
    setSaving(true);
    try {
      const updated = await apiFetch<RecordResponse>(`/api/recipes/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(record.recipe_json),
      });
      setRecord(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <main style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <a href="/">← Back</a>
      <h1>Recipe Job {params.id}</h1>
      {status && <p>Status: {status.status} ({status.progress}%)</p>}
      {status?.error_message && <p style={{ color: 'red' }}>{status.error_message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {recipe && (
        <section>
          <label>Title <input value={recipe.title} onChange={(e) => setRecord((r) => r ? { ...r, recipe_json: { ...r.recipe_json!, title: e.target.value } } : r)} /></label>
          <p>{recipe.description}</p>

          <h2>Ingredients</h2>
          <ul>
            {recipe.ingredients.map((ing, i) => (
              <li key={i}>
                <label>
                  <input
                    type="checkbox"
                    checked={!!checked[`${i}-${ing}`]}
                    onChange={() => setChecked((prev) => ({ ...prev, [`${i}-${ing}`]: !prev[`${i}-${ing}`] }))}
                  />
                  {ing}
                </label>
              </li>
            ))}
          </ul>

          <h2>Steps</h2>
          <ol>
            {recipe.steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <button onClick={saveRecipe} disabled={saving}>{saving ? 'Saving...' : 'Save Recipe'}</button>
        </section>
      )}
    </main>
  );
}
