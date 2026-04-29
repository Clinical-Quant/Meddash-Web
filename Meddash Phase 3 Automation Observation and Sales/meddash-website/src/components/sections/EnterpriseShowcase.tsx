export default function EnterpriseShowcase() {
  return (
    <section id="enterprise" className="px-6 md:px-10 py-16">
      <h2 className="text-3xl font-semibold text-white mb-4">Enterprise Services</h2>
      <p className="text-slate-300 max-w-3xl mb-8">Built for biotech teams needing signal over noise across KOL influence, therapeutic landscapes, and catalyst timing.</p>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-meddash-cyan/40 bg-meddash-surface p-6">
          <h3 className="text-meddash-cyan font-semibold">KOL Intelligence Brief</h3>
          <p className="text-white text-2xl mt-2">$2,450</p>
          <p className="text-slate-300 mt-2">72-hour delivery with strategic action points.</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-meddash-surface p-6">
          <h3 className="text-meddash-emerald font-semibold">Catalyst Interpretation</h3>
          <p className="text-slate-300 mt-2">Event context + impact framing for teams and stakeholders.</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-meddash-surface p-6">
          <h3 className="text-white font-semibold">Custom Research Sprint</h3>
          <p className="text-slate-300 mt-2">Focused therapeutic and competitive intelligence in rapid cycles.</p>
        </div>
      </div>
    </section>
  );
}