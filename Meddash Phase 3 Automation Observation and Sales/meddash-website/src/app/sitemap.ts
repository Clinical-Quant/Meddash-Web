import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://meddash.ai";
  const now = new Date();

  return [
    { url: `${base}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${base}/blog`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${base}/blog/kol-identification-framework-early-stage-biotech`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${base}/blog/track-biotech-catalysts-without-signal-overload`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${base}/blog/clinical-trial-search-workflow-medical-affairs`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${base}/services/kol-intelligence-brief`, lastModified: now, changeFrequency: "monthly", priority: 0.9 },
    { url: `${base}/services/catalyst-interpretation`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${base}/services/custom-research-sprint`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
  ];
}
