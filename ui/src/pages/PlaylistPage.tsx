import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPlaylistByDate, PlaylistDetail } from '../api/client';
import SongRow from '../components/SongRow';

export default function PlaylistPage() {
  const { date } = useParams<{ date: string }>();
  const navigate = useNavigate();
  const [playlist, setPlaylist] = useState<PlaylistDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!date) return;
    setLoading(true);
    getPlaylistByDate(date)
      .then(setPlaylist)
      .catch(() => setError('Playlist not found'))
      .finally(() => setLoading(false));
  }, [date]);

  if (loading) return <p className="text-ghost/50 text-center mt-16">Loading...</p>;
  if (error || !playlist) return <p className="text-ghost/50 text-center mt-16">{error}</p>;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <button onClick={() => navigate(-1)} className="text-ghost hover:text-bone text-sm transition-colors cursor-pointer">
        ← Back
      </button>
      <div className="mt-6 mb-4 flex items-center gap-3">
        <h1 className="text-2xl text-bone font-bold">{playlist.date}</h1>
        <span className="text-ghost/50 text-sm">{playlist.songs.length} songs</span>
        {playlist.spotify_url && (
          <a href={playlist.spotify_url} target="_blank" rel="noopener noreferrer"
            className="text-spotify-green/70 hover:text-spotify-green text-xs transition-colors">
            Spotify ↗
          </a>
        )}
      </div>
      <div className="bg-fog/50 border border-ghost/10 rounded p-2">
        {playlist.songs.map((song) => (
          <SongRow key={song.id} song={song} />
        ))}
      </div>
    </div>
  );
}
