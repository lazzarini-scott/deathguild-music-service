import { useState } from 'react';
import { PlaylistSummary, SongResponse, getPlaylistByDate } from '../api/client';
import SongRow from './SongRow';

interface PlaylistCardProps {
  playlist: PlaylistSummary;
  highlight?: string;
}

export default function PlaylistCard({ playlist, highlight }: PlaylistCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [songs, setSongs] = useState<SongResponse[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    if (!expanded && !songs) {
      setLoading(true);
      try {
        const detail = await getPlaylistByDate(playlist.date);
        setSongs(detail.songs);
      } catch (err) {
        console.error('Failed to load playlist', err);
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  }

  return (
    <div className="bg-fog/50 border border-ghost/10 rounded mb-2 transition-colors hover:border-ghost/25">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <span className="text-bone/90 font-medium">{playlist.date}</span>
          <span className="text-ghost/50 text-sm">{playlist.song_count} songs</span>
        </div>
        <div className="flex items-center gap-3">
          {playlist.spotify_url && (
            <a
              href={playlist.spotify_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-spotify-green/70 hover:text-spotify-green text-xs transition-colors"
            >
              Spotify ↗
            </a>
          )}
          <span className="text-ghost/40 text-sm">{expanded ? '▾' : '▸'}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-ghost/10 px-2 py-2">
          {loading && <p className="text-ghost/50 text-sm px-3 py-2">Loading...</p>}
          {songs?.map((song) => (
            <SongRow key={song.id} song={song} highlight={highlight} />
          ))}
        </div>
      )}
    </div>
  );
}
