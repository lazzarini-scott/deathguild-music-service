import { SongResponse } from '../api/client';

interface SongRowProps {
  song: SongResponse;
  highlight?: string;
}

export default function SongRow({ song, highlight }: SongRowProps) {
  const isHighlighted = highlight &&
    (song.artist.toLowerCase().includes(highlight) ||
     song.title.toLowerCase().includes(highlight));

  return (
    <div className={`flex items-center gap-3 py-1.5 px-3 text-sm ${
      isHighlighted ? 'bg-blood/20 rounded' : ''
    }`}>
      <span className="text-ghost/50 w-8 text-right shrink-0">
        {song.position || '—'}
      </span>
      <div className="flex-1 min-w-0">
        <span className="text-bone/90">{song.artist}</span>
        <span className="text-ghost mx-1.5">—</span>
        <span className="text-ghost">{song.title}</span>
        {song.is_request && (
          <span className="text-blood/70 text-xs ml-2">(request)</span>
        )}
      </div>
      <div className="flex gap-2 shrink-0">
        {song.spotify_url && (
          <a
            href={song.spotify_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-spotify-green/70 hover:text-spotify-green transition-colors text-xs"
            title="Spotify"
          >
            ♫
          </a>
        )}
        <a
          href={song.youtube_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-youtube-red/70 hover:text-youtube-red transition-colors text-xs"
          title="YouTube"
        >
          ▶
        </a>
      </div>
    </div>
  );
}
