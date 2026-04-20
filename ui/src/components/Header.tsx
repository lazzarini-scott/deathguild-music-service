import logo from '../assets/dg_logo.jpeg';

export default function Header() {
  return (
    <header className="py-10 text-center">
      <img
        src={logo}
        alt="Death Guild"
        className="mx-auto w-48 h-48 rounded-full object-cover border border-ghost/20 mb-4"
      />
      <h1 className="text-4xl font-bold tracking-wider uppercase text-bone/90">
        Death Guild
      </h1>
      <p className="text-ghost text-sm mt-2 tracking-wide">
        San Francisco&apos;s longest-running goth &amp; industrial night
      </p>
    </header>
  );
}
