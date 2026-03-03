/**
 * Scheme Data Service
 * Fetches scheme data from the Python backend API (token_server.py).
 * All DB queries and web fallback are handled server-side.
 */

import { Scheme } from '../types';

const API_BASE = '/api';

async function apiFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return (await res.json()) as T;
  } catch (err) {
    console.error(`API call failed: ${path}`, err);
    return fallback;
  }
}

/** No-op — DB is managed server-side now. Kept for backward compat. */
export async function initDatabase(): Promise<void> {}

/** Search schemes via backend FTS + optional DDGS web fallback */
export async function searchSchemes(
  query: string = '',
  filters: { state?: string; category?: string; level?: string } = {},
  limit: number = 50,
): Promise<{ results: Scheme[]; webResults: Scheme[] }> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  if (filters.state) params.set('state', filters.state);
  if (filters.category) params.set('category', filters.category);
  if (filters.level) params.set('level', filters.level);
  params.set('limit', String(limit));

  const data = await apiFetch<{ results: Scheme[]; webResults: Scheme[] }>(
    `/search?${params}`,
    { results: [], webResults: [] },
  );
  return data;
}

/** Get a single scheme by slug */
export async function getSchemeById(slug: string): Promise<Scheme | null> {
  try {
    const res = await fetch(`${API_BASE}/scheme?slug=${encodeURIComponent(slug)}`);
    if (!res.ok) return null;
    return (await res.json()) as Scheme;
  } catch {
    return null;
  }
}

/** Featured schemes (highest priority) */
export async function getFeaturedSchemes(limit: number = 6): Promise<Scheme[]> {
  const data = await apiFetch<{ results: Scheme[] }>(`/featured?limit=${limit}`, { results: [] });
  return data.results;
}

/** DB stats */
export async function getDbStats(): Promise<{ total: number; central: number; state: number }> {
  return apiFetch('/stats', { total: 0, central: 0, state: 0 });
}

/** All unique categories */
export async function getAllCategories(): Promise<string[]> {
  const data = await apiFetch<{ categories: string[] }>('/categories', { categories: [] });
  return data.categories;
}

/** All unique states */
export async function getAllStates(): Promise<string[]> {
  const data = await apiFetch<{ states: string[] }>('/states', { states: [] });
  return data.states;
}

/** Alias kept for backward compat */
export async function getSchemesByCategory(category: string, limit = 10): Promise<Scheme[]> {
  const { results } = await searchSchemes('', { category }, limit);
  return results;
}
