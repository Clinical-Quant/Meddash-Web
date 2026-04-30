import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Custom Research Sprint | Meddash.ai",
  description:
    "Therapeutic area landscape and biotech company intelligence delivered in focused, rapid-cycle custom research sprints.",
  alternates: { canonical: "https://meddash.ai/services/custom-research-sprint" },
};

export default function CustomResearchSprintPage() {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 md:px-10 py-16">
      <section className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-semibold text-white">Custom Research Sprint</h1>
        <p className="mt-4 text-slate-300">
          Get a tailored therapeutic area landscape and biotech company intelligence package built around your immediate strategic question.
        </p>
        <ul className="mt-6 list-disc list-inside text-slate-200 space-y-2">
          <li>Scope definition aligned to business decision timeline</li>
          <li>Evidence synthesis from public, trial, and publication signals</li>
          <li>Clear recommendation pathways with execution next steps</li>
        </ul>
        <a href="/#lead?utm_source=service&utm_medium=sprint" className="inline-block mt-8 rounded-lg bg-meddash-cyan text-black font-semibold px-5 py-3">
          Request Brief
        </a>
      </section>
    </main>
  );
}
