export default function Header() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-[#05070d]/70 border-b border-white/10">
      <nav className="px-6 md:px-10 py-4 flex items-center justify-between">
        <a href="#" className="font-semibold text-white">Meddash.ai</a>
        <div className="hidden md:flex items-center gap-6 text-sm text-slate-300">
          <a href="#features" className="hover:text-meddash-cyan">Features</a>
          <a href="#calendar" className="hover:text-meddash-cyan">Calendar</a>
          <a href="#enterprise" className="hover:text-meddash-cyan">Enterprise</a>
          <a href="#lead" className="hover:text-meddash-cyan">Contact</a>
        </div>
      </nav>
    </header>
  );
}