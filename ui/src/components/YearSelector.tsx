interface YearSelectorProps {
  years: number[];
  selectedYear: number | null;
  onSelect: (year: number | null) => void;
}

export default function YearSelector({ years, selectedYear, onSelect }: YearSelectorProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2 mb-8">
      {years.map((year) => (
        <button
          key={year}
          onClick={() => onSelect(year === selectedYear ? null : year)}
          className={`px-4 py-1.5 rounded text-sm tracking-wide transition-colors ${
            year === selectedYear
              ? 'bg-blood text-bone'
              : 'bg-tombstone/60 text-ghost hover:text-bone hover:bg-tombstone'
          }`}
        >
          {year}
        </button>
      ))}
    </div>
  );
}
