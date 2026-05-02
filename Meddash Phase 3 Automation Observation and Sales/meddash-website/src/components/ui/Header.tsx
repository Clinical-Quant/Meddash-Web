export default function Header() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-[#05070d]/70 border-b border-white/10">
      <nav className="px-6 md:px-10 py-4 flex items-center justify-between">
        <a href="#" className="font-semibold text-white">Meddash.ai</a>
        <div className="hidden md:flex items-center gap-6 text-sm text-slate-300">
          <a href="https://lite.meddash.ai" target="_blank" rel="noopener noreferrer" className="rounded-full bg-meddash-emerald text-black px-3 py-1 font-semibold hover:brightness-95">Meddash Lite $19</a>
          <a href="#features" className="hover:text-meddash-cyan">Features</a>
          <a href="#calendar" className="hover:text-meddash-cyan">Calendar</a>
          <a href="#enterprise" className="hover:text-meddash-cyan">Enterprise</a>

          <details className="relative group">
            <summary className="list-none cursor-pointer hover:text-meddash-cyan flex items-center gap-1">
              Read
              <span className="text-xs">▾</span>
            </summary>
            <div className="absolute top-7 left-0 min-w-52 rounded-lg border border-white/10 bg-[#0b1220] p-2 shadow-xl">
              <a href="/blog" className="block rounded-md px-3 py-2 hover:bg-white/5 hover:text-meddash-cyan">Read more</a>
              <a
                href="https://madebydoc.substack.com/s/meddash"
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-md px-3 py-2 hover:bg-white/5 hover:text-meddash-cyan"
              >
                Meddash Substack Newsletter
              </a>
            </div>
          </details>

          <a href="/services/kol-intelligence-brief" className="hover:text-meddash-cyan">Services</a>
          <a href="#lead" className="hover:text-meddash-cyan">Contact</a>

          <a
            href="https://www.linkedin.com/company/meddash-ai/?viewAsMember=true"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Meddash LinkedIn"
            className="text-slate-300 hover:text-meddash-cyan"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
              <path d="M6.94 8.5H3.56V20h3.38V8.5ZM5.25 3A1.97 1.97 0 1 0 5.3 6.94 1.97 1.97 0 0 0 5.25 3ZM20.44 13.44c0-3.3-1.76-4.84-4.1-4.84-1.9 0-2.74 1.04-3.22 1.77V8.5H9.75V20h3.37v-5.7c0-1.5.28-2.95 2.14-2.95 1.83 0 1.86 1.72 1.86 3.04V20h3.38v-6.56Z" />
            </svg>
          </a>
        </div>
      </nav>
    </header>
  );
}
