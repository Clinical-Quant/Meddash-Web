const features = [
  { title: "KOL Intelligence Briefs", desc: "Decision-ready expert influence maps and therapeutic context in 72h." },
  { title: "Catalyst Calendar", desc: "FDA, SEC, and trial milestones on one timeline." },
  { title: "Trial Search Lite", desc: "Fast trial discovery workflow for teams and analysts." },
  { title: "Enterprise Research", desc: "Custom medical affairs intelligence for biotech operators." },
];

export default function Features() {
  return (
    <section id="features" className="px-6 md:px-10 py-16 bg-meddash-surface">
      <h2 className="text-3xl font-semibold text-white mb-8">What Meddash Delivers</h2>
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