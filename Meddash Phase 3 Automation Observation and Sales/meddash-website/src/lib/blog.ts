export type BlogPost = {
  slug: string;
  title: string;
  description: string;
  publishedAt: string;
  keywords: string[];
  body: string[];
};

export const blogPosts: BlogPost[] = [
  {
    slug: "kol-identification-framework-early-stage-biotech",
    title: "KOL Identification Framework for Early-Stage Biotech",
    description:
      "A practical KOL identification framework for early-stage biotech teams that need fast, decision-ready expert mapping.",
    publishedAt: "2026-04-30",
    keywords: ["KOL identification platform", "medical affairs analytics", "biotech KOL mapping"],
    body: [
      "Most early-stage biotech teams over-index on famous names and under-index on active signal density. The result is delayed engagement and weaker trial support.",
      "Start with three filters: publication velocity in your target mechanism, clinical trial investigator overlap, and recent speaking activity in your indication.",
      "Then score experts by relevance and accessibility. Relevance protects strategic alignment; accessibility protects timeline execution.",
      "Teams that apply this structure reduce KOL shortlisting cycles and improve first-contact quality. Request a Meddash brief to receive a therapeutic-area specific KOL map.",
    ],
  },
  {
    slug: "track-biotech-catalysts-without-signal-overload",
    title: "How to Track Biotech Catalysts Without Signal Overload",
    description:
      "A signal-first method to track biotech catalysts across FDA, SEC, and clinical milestones without dashboard fatigue.",
    publishedAt: "2026-04-30",
    keywords: ["biotech catalyst tracking", "clinical trial intelligence", "medical affairs technology solutions"],
    body: [
      "Catalyst tracking fails when every event looks equally urgent. Biotech teams need ranking logic, not just event feeds.",
      "Group events into regulatory, clinical, and financing streams, then assign impact tiers based on timing, probability, and decision dependency.",
      "A weekly review cadence with a monthly scenario layer is usually enough for small teams to stay current without operational drag.",
      "Meddash consolidates FDA, SEC, and trial milestones into one workflow so teams can prioritize action windows instead of chasing noise.",
    ],
  },
  {
    slug: "clinical-trial-search-workflow-medical-affairs",
    title: "Clinical Trial Search Workflow for Medical Affairs Teams",
    description:
      "A repeatable clinical trial search workflow for medical affairs teams that need faster landscape clarity and KOL alignment.",
    publishedAt: "2026-04-30",
    keywords: ["clinical trial search", "therapeutic area landscape", "medical affairs workflow"],
    body: [
      "Trial search becomes valuable when it is tied to a decision path, not when it is a static query list.",
      "Define the therapeutic scope, extract active and recently completed studies, and map principal investigators to your KOL universe.",
      "Flag protocol patterns, enrollment friction signals, and competitive overlap. These signals determine both engagement strategy and timing.",
      "Use this workflow before every major planning cycle to maintain an updated therapeutic landscape with execution-level clarity.",
    ],
  },
];

export function getPostBySlug(slug: string) {
  return blogPosts.find((post) => post.slug === slug);
}
