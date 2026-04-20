import { useState, FormEvent } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onClear: () => void;
  initialValue?: string;
}

export default function SearchBar({ onSearch, onClear, initialValue = '' }: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed.length >= 2) onSearch(trimmed);
  }

  function handleClear() {
    setValue('');
    onClear();
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 max-w-xl mx-auto mb-8">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Search by artist, song, or date..."
        className="flex-1 bg-tombstone/60 border border-ghost/20 rounded px-4 py-2 text-bone placeholder-ghost/50 focus:outline-none focus:border-ghost/50 transition-colors"
      />
      <button
        type="submit"
        className="bg-blood/80 hover:bg-blood text-bone px-5 py-2 rounded transition-colors tracking-wide text-sm uppercase"
      >
        Search
      </button>
      {value && (
        <button
          type="button"
          onClick={handleClear}
          className="text-ghost hover:text-bone px-3 py-2 transition-colors text-sm"
        >
          Clear
        </button>
      )}
    </form>
  );
}
