import Link from "next/link";
import type { Metadata } from "next";
import { blogPosts } from "@/lib/blog";

export const metadata: Metadata = {
  title: "Meddash Insights | Biotech Therapeutic Intelligence",
  description:
    "Read Meddash insights on KOL identification, catalyst tracking, and clinical trial intelligence for biotech teams.",
  alternates: {
    canonical: "https://meddash.ai/blog",
  },
};

export default function BlogIndexPage() {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 md:px-10 py-16">
      <section className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-semibold text-white">Meddash Insights</h1>
        <p className="text-slate-300 mt-4">
          Decision-ready perspectives for medical affairs and biotech teams.
        </p>

        <div className="mt-10 space-y-4">
          {blogPosts.map((post) => (
            <article key={post.slug} className="rounded-2xl border border-white/10 bg-meddash-surface p-6">
              <p className="text-xs tracking-wider uppercase text-meddash-cyan">{post.publishedAt}</p>
              <h2 className="text-2xl font-semibold text-white mt-2">{post.title}</h2>
              <p className="text-slate-300 mt-3">{post.description}</p>
              <Link
                href={`/blog/${post.slug}`}
                className="inline-block mt-4 rounded-lg border border-meddash-emerald/70 px-4 py-2 text-meddash-emerald hover:bg-meddash-emerald/10"
              >
                Read brief
              </Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
