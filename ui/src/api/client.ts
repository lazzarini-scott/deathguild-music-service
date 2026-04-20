const API_BASE = import.meta.env.VITE_API_URL || '';
const BASE = `${API_BASE}/v1`;

export interface SongSearchResult {
  id: number;
  artist: string;
  title: string;
  occurrence_count: number;
  spotify_id: string | null;
  youtube_url: string;
  spotify_url: string | null;
}

export interface SongPlaylistAppearance {
  id: number;
  date: string;
  position: number;
  spotify_id: string | null;
  spotify_url: string | null;
}

export interface SongResponse {
  id: number;
  artist: string;
  title: string;
  position: number;
  is_request: boolean;
  spotify_id: string | null;
  youtube_url: string;
  spotify_url: string | null;
}

export interface PlaylistSummary {
  id: number;
  date: string;
  song_count: number;
  spotify_id: string | null;
  spotify_url: string | null;
}

export interface PlaylistDetail {
  id: number;
  date: string;
  spotify_id: string | null;
  spotify_url: string | null;
  songs: SongResponse[];
}

export interface PaginatedResponse<T> {
  total: number;
  offset: number;
  limit: number;
  items: T[];
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function getYears(): Promise<number[]> {
  return fetchJson<number[]>(`${BASE}/playlists/years`);
}

export async function getPlaylists(params: {
  year?: number | null;
  offset?: number;
  limit?: number;
}): Promise<PaginatedResponse<PlaylistSummary>> {
  const search = new URLSearchParams({
    offset: String(params.offset ?? 0),
    limit: String(params.limit ?? 50),
  });
  if (params.year) search.set('year', String(params.year));
  return fetchJson(`${BASE}/playlists?${search}`);
}

export async function getPlaylistByDate(date: string): Promise<PlaylistDetail> {
  return fetchJson(`${BASE}/playlists/${date}`);
}

export async function searchSongs(params: {
  q: string;
  offset?: number;
  limit?: number;
}): Promise<PaginatedResponse<SongSearchResult>> {
  const search = new URLSearchParams({
    q: params.q,
    offset: String(params.offset ?? 0),
    limit: String(params.limit ?? 50),
  });
  return fetchJson(`${BASE}/songs?${search}`);
}

export async function getSongPlaylists(params: {
  songId: number;
  offset?: number;
  limit?: number;
}): Promise<PaginatedResponse<SongPlaylistAppearance>> {
  const search = new URLSearchParams({
    offset: String(params.offset ?? 0),
    limit: String(params.limit ?? 50),
  });
  return fetchJson(`${BASE}/songs/${params.songId}/playlists?${search}`);
}
