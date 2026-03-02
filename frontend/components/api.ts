export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type RecipeData = {
  title: string;
  servings: number | null;
  total_time_minutes: number | null;
  ingredients: { item: string; quantity: number | null; unit: string | null; prep: string | null }[];
  steps: { n: number; text: string; timer_seconds: number | null }[];
  equipment: string[];
  notes: string[];
};
