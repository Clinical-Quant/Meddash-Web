import "./globals.css";
import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: '4rem', display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh' }}>
      <div className="glass-panel" style={{ padding: '3.5rem', maxWidth: '800px', width: '100%', textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem', background: 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Meddash Phase 2 UI
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem', marginBottom: '3rem' }}>
          Master Command Center & PostgreSQL Visualizer
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '2rem' }}>
          <Link href="/control" style={{ display: 'block' }}>
            <div className="glass-panel card-hover" style={{ padding: '1.5rem', textAlign: 'left', height: '100%' }}>
              <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Crawler Control</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>Configure active parameters, inject MeSH blocks, and execute data pipelines.</p>
            </div>
          </Link>
          <Link href="/explorer" style={{ display: 'block' }}>
            <div className="glass-panel card-hover" style={{ padding: '1.5rem', textAlign: 'left', height: '100%' }}>
              <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Data Inspector</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>View and filter live data from the PostgreSQL cluster.</p>
            </div>
          </Link>
          <Link href="/health" style={{ display: 'block' }}>
            <div className="glass-panel card-hover" style={{ padding: '1.5rem', textAlign: 'left', height: '100%' }}>
              <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>System Health & Override</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>Monitor automated crons and stream Python logs natively.</p>
            </div>
          </Link>
          <Link href="/scholar" style={{ display: 'block' }}>
            <div className="glass-panel card-hover" style={{ padding: '1.5rem', textAlign: 'left', height: '100%' }}>
              <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Scholar Enrichment</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>Optionally enrich final KOLs by pull ID with pasted Google Scholar profile URLs.</p>
            </div>
          </Link>
          <div className="glass-panel card-hover" style={{ padding: '1.5rem', textAlign: 'left' }}>
            <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Generative Products</h3>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>Export KOL Briefs and TA Landscapes locally via API.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
