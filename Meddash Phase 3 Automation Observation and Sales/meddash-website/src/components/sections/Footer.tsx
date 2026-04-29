export default function Footer() {
  return (
    <footer className="px-6 md:px-10 py-10 border-t border-white/10 text-slate-400 text-sm">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <p>© {new Date().getFullYear()} Meddash.ai</p>
        <p>Therapeutic Intelligence • KOL Signals • Biotech Catalysts</p>
      </div>
    </footer>
  );
}