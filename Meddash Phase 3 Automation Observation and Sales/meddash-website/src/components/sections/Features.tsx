const features = [
  { title: "Intelligent KOL Briefs", desc: "Decision-ready expert influence maps and strategic context for biotech teams." },
  { title: "Therapeutic Area Landscape Briefs", desc: "Focused therapeutic landscape intelligence for early- and mid-stage biotech decisions." },
  { title: "Biotech Catalyst Interpretation", desc: "Event context + impact framing across FDA, SEC, and clinical milestones." },
  { title: "Meddash Lite", desc: "Fast, lightweight trial and catalyst signal discovery for rapid team workflows." },
];

export default function Features() {
  return (
    <section id="features" className="px-6 md:px-10 py-16 bg-meddash-surface">
      <h2 className="text-3xl font-semibold text-white mb-8">Key Highlights</h2>
      <div className="grid md:grid-cols-2 gap-4">
        {features.map((f) => (
          <article key={f.title} className="rounded-2xl border border-white/10 bg-meddash-surface-2 p-6">
            <h3 className="text-xl text-meddash-cyan font-semibold">{f.title}</h3>
            <p className="text-slate-300 mt-2">{f.desc}</p>
          </article>
        ))}
      </div>
    </section>
  );
}