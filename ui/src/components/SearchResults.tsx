import { useState } from 'react';
import { Link } from 'react-router-dom';
import { SongSearchResult, SongPlaylistAppearance, getSongPlaylists } from '../api/client';

interface SearchResultsProps {
  results: SongSearchResult[];
  total: number;
  query: string;
}

function SongResult({ song }: { song: SongSearchResult }) {
  const [appearances, setAppearances] = useState<SongPlaylistAppearance[] | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    if (!expanded && !appearances) {
      setLoading(true);
      try {
        const data = await getSongPlaylists({ songId: song.id });
        setAppearances(data.items);
      } catch (err) {
        console.error('Failed to load appearances', err);
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  }

  return (
    <div className="border-b border-ghost/10 last:border-b-0">
      <button
        onClick={toggle}
        className="w-full flex items-center gap-3 py-2 px-3 text-sm text-left cursor-pointer hover:bg-tombstone/20 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <span className="text-bone/90">{song.artist}</span>
          <span className="text-ghost mx-1.5">—</span>
          <span className="text-ghost">{song.title}</span>
        </div>
        <span className="text-blood/80 text-xs shrink-0">
          {song.occurrence_count}×
        </span>
        <div className="flex gap-2 shrink-0">
          {song.spotify_url && (
            <a href={song.spotify_url} target="_blank" rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-spotify-green/70 hover:text-spotify-green transition-colors text-xs">♫</a>
          )}
          <a href={song.youtube_url} target="_blank" rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-youtube-red/70 hover:text-youtube-red transition-colors text-xs">▶</a>
        </div>
        <span className="text-ghost/40 text-sm">{expanded ? '▾' : '▸'}</span>
      </button>

      {expanded && (
        <div className="pl-6 pb-2">
          {loading && <p className="text-ghost/50 text-xs px-3 py-1">Loading...</p>}
          {appearances?.map((a) => (
            <div key={a.id} className="flex items-center gap-3 py-1 px-3 text-xs">
              <Link to={`/playlist/${a.date}`} className="text-bone/70 hover:text-bone underline decoration-ghost/30 transition-colors">
                {a.date}
              </Link>
              <span className="text-ghost/50">position {a.position}</span>
              {a.spotify_url && (
                <a href={a.spotify_url} target="_blank" rel="noopener noreferrer"
                  className="text-spotify-green/70 hover:text-spotify-green transition-colors">
                  playlist ↗
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SearchResults({ results, total, query }: SearchResultsProps) {
  return (
    <div className="mb-8">
      <div className="text-ghost text-sm mb-4 text-center">
        <span className="text-bone font-medium">{total}</span> result{total !== 1 ? 's' : ''} for{' '}
        <span className="text-bone/80">&ldquo;{query}&rdquo;</span>
      </div>
      <div className="bg-fog/50 border border-ghost/10 rounded">
        {results.map((song) => (
          <SongResult key={song.id} song={song} />
        ))}
      </div>
    </div>
  );
}
