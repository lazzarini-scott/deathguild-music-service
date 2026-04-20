import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getYears, getPlaylists, searchSongs, PlaylistSummary, SongSearchResult } from '../api/client';
import Header from '../components/Header';
import SearchBar from '../components/SearchBar';
import YearSelector from '../components/YearSelector';
import PlaylistCard from '../components/PlaylistCard';
import SearchResults from '../components/SearchResults';

const LIMIT = 50;

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlQuery = searchParams.get('q');
  const urlYear = searchParams.get('year');

  const [years, setYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number | null>(urlYear ? Number(urlYear) : null);
  const [playlists, setPlaylists] = useState<PlaylistSummary[]>([]);
  const [playlistTotal, setPlaylistTotal] = useState(0);
  const [playlistOffset, setPlaylistOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  const [searchQuery, setSearchQuery] = useState<string | null>(urlQuery);
  const [searchResults, setSearchResults] = useState<SongSearchResult[] | null>(null);
  const [searchTotal, setSearchTotal] = useState(0);

  useEffect(() => {
    getYears().then(setYears).catch(console.error);
  }, []);

  // Re-run search when mounting with a query param (e.g. navigating back)
  useEffect(() => {
    if (urlQuery && !searchResults) {
      searchSongs({ q: urlQuery, offset: 0, limit: LIMIT })
        .then((data) => {
          setSearchResults(data.items);
          setSearchTotal(data.total);
        })
        .catch(console.error);
    }
  }, [urlQuery, searchResults]);

  const loadPlaylists = useCallback(async (year: number | null, offset = 0) => {
    setLoading(true);
    try {
      const data = await getPlaylists({ year, offset, limit: LIMIT });
      setPlaylists(prev => offset === 0 ? data.items : [...prev, ...data.items]);
      setPlaylistTotal(data.total);
      setPlaylistOffset(offset);
    } catch (err) {
      console.error('Failed to load playlists', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedYear && !searchQuery) {
      loadPlaylists(selectedYear, 0);
    } else if (!searchQuery) {
      setPlaylists([]);
      setPlaylistTotal(0);
    }
  }, [selectedYear, loadPlaylists, searchQuery]);

  function updateUrl(q: string | null, year: number | null) {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (year) params.set('year', String(year));
    setSearchParams(params, { replace: true });
  }

  async function handleSearch(query: string) {
    setSelectedYear(null);
    setPlaylists([]);
    setPlaylistTotal(0);
    setSearchQuery(query);
    updateUrl(query, null);
    setLoading(true);
    try {
      const data = await searchSongs({ q: query, offset: 0, limit: LIMIT });
      setSearchResults(data.items);
      setSearchTotal(data.total);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setLoading(false);
    }
  }

  function handleClearSearch() {
    setSearchQuery(null);
    setSearchResults(null);
    setSearchTotal(0);
    updateUrl(null, selectedYear);
    if (selectedYear) {
      loadPlaylists(selectedYear, 0);
    } else {
      setPlaylists([]);
      setPlaylistTotal(0);
    }
  }

  function handleSelectYear(year: number | null) {
    setSelectedYear(year);
    if (year) {
      setSearchQuery(null);
      setSearchResults(null);
    }
    updateUrl(null, year);
  }

  function handleLoadMore() {
    loadPlaylists(selectedYear, playlistOffset + LIMIT);
  }

  const hasMorePlaylists = playlists.length < playlistTotal;

  return (
    <div className="max-w-3xl mx-auto px-4 pb-16">
      <Header />
      <SearchBar onSearch={handleSearch} onClear={handleClearSearch} initialValue={searchQuery ?? ''} />
      <YearSelector years={years} selectedYear={selectedYear} onSelect={handleSelectYear} />

      {searchQuery && searchResults && (
        <SearchResults results={searchResults} total={searchTotal} query={searchQuery} />
      )}

      {playlists.length > 0 && (
        <div>
          <div className="text-ghost text-sm mb-3 text-center">
            {playlistTotal} playlist{playlistTotal !== 1 ? 's' : ''}
            {selectedYear && ` in ${selectedYear}`}
          </div>
          {playlists.map((p) => (
            <PlaylistCard
              key={p.id}
              playlist={p}
              highlight={searchQuery?.toLowerCase()}
            />
          ))}
          {hasMorePlaylists && (
            <button
              onClick={handleLoadMore}
              disabled={loading}
              className="w-full py-3 mt-2 text-ghost hover:text-bone bg-tombstone/40 hover:bg-tombstone/60 rounded transition-colors text-sm tracking-wide"
            >
              {loading ? 'Loading...' : 'Load more'}
            </button>
          )}
        </div>
      )}

      {!loading && !searchQuery && !selectedYear && playlists.length === 0 && (
        <p className="text-ghost/50 text-center text-sm mt-8">
          Select a year or search to explore playlists
        </p>
      )}

      {loading && playlists.length === 0 && !searchResults && (
        <p className="text-ghost/50 text-center text-sm mt-8">Loading...</p>
      )}
    </div>
  );
}
