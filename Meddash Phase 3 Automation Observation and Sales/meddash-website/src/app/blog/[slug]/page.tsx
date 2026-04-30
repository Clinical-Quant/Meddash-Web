import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { blogPosts, getPostBySlug } from "@/lib/blog";

export function generateStaticParams() {
  return blogPosts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = getPostBySlug(slug);

  if (!post) {
    return {};
  }

  return {
    title: `${post.title} | Meddash Insights`,
    description: post.description,
    keywords: post.keywords,
    alternates: {
      canonical: `https://meddash.ai/blog/${post.slug}`,
    },
  };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = getPostBySlug(slug);

  if (!post) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-background text-foreground px-6 md:px-10 py-16">
      <article className="max-w-3xl mx-auto">
        <p className="text-xs tracking-wider uppercase text-meddash-cyan">{post.publishedAt}</p>
        <h1 className="text-4xl font-semibold text-white mt-3">{post.title}</h1>
        <p className="text-slate-300 mt-5">{post.description}</p>

        <div className="mt-8 space-y-5 text-slate-200 leading-8">
          {post.body.map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
        </div>

        <div className="mt-10 rounded-xl border border-meddash-cyan/30 bg-meddash-surface p-5">
          <p className="text-white font-medium">Next step</p>
          <p className="text-slate-300 mt-2">
            Request a Meddash brief to receive decision-ready KOL and catalyst intelligence for your therapeutic area.
          </p>
          <a href="/#lead" className="inline-block mt-4 rounded-lg bg-meddash-cyan text-black px-4 py-2 font-semibold">
            Request Brief
          </a>
        </div>
      </article>
    </main>
  );
}
