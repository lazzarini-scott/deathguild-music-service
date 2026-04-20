export default function Header() {
  return (
    <header className="py-10 text-center">
      <div className="mx-auto w-48 h-48 rounded-full bg-tombstone/50 border border-ghost/20 flex items-center justify-center mb-4">
        <span className="text-ghost text-xs uppercase tracking-widest">Logo</span>
      </div>
      <h1 className="text-4xl font-bold tracking-wider uppercase text-bone/90">
        Death Guild
      </h1>
      <p className="text-ghost text-sm mt-2 tracking-wide">
        San Francisco&apos;s longest-running goth &amp; industrial night
      </p>
    </header>
  );
}
