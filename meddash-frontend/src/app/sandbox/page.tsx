"use client";

import { useState } from "react";
import Link from 'next/link';

export default function CampaignSandbox() {
  const [pullId, setPullId] = useState("");
  const [kols, setKols] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  
  // HITL State
  const [showHITL, setShowHITL] = useState(false);
  const [pendingPairs, setPendingPairs] = useState<any[]>([]);
  const [geminiReasonings, setGeminiReasonings] = useState<Record<number, string>>({});
  const [geminiLoading, setGeminiLoading] = useState<Record<number, boolean>>({});

  const fetchSandbox = async () => {
    if (!pullId) return;
    setIsLoading(true);
    setActionStatus(null);
    try {
      const res = await fetch(`http://localhost:8000/api/db/sandbox?pull_id=${pullId}`);
      if (!res.ok) throw new Error("Failed to fetch sandbox");
      const json = await res.json();
      setKols(json.data || []);
    } catch (e: any) {
      setActionStatus(`Error fetching: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = async (endpoint: string) => {
    if (!pullId) return;
    setIsLoading(true);
    try {
      if (endpoint === "export") {
        const res = await fetch(`http://localhost:8000/api/sandbox/${endpoint}?pull_id=${pullId}`);
        const json = await res.json();
        setActionStatus(`Export generated at: ${json.file_path}`);
        return;
      }
      
      const res = await fetch(`http://localhost:8000/api/sandbox/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pull_id: pullId })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Action failed.");
      setActionStatus(`Success: ${json.message}`);
      
      if (endpoint === "commit" || endpoint === "erase") {
          setTimeout(fetchSandbox, 1500);
      }
      if (endpoint === "run_disambiguation") {
          setActionStatus(`Success: ${json.message}. Navigate to System Health → Sandbox Disambiguation tab to monitor live logs.`);
      }
    } catch (e: any) {
      setActionStatus(`Error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPendingPairs = async () => {
    if (!pullId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/sandbox/pending_pairs?pull_id=${pullId}`);
      if (!res.ok) throw new Error("Failed to fetch pending pairs");
      const json = await res.json();
      setPendingPairs(json.data || []);
      setShowHITL(true);
      setGeminiReasonings({});
      if (json.data.length === 0) {
        setActionStatus("✅ No pending disambiguation pairs. All KOLs are resolved!");
      }
    } catch (e: any) {
      setActionStatus(`Error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const askGemini = async (pair: any) => {
    setGeminiLoading(prev => ({ ...prev, [pair.candidate_id]: true }));
    try {
      const res = await fetch("http://localhost:8000/api/sandbox/gemini_review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kol_id_a: pair.kol_id_a, kol_id_b: pair.kol_id_b, pull_id: pullId })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Gemini review failed.");
      setGeminiReasonings(prev => ({ ...prev, [pair.candidate_id]: json.reasoning }));
    } catch (e: any) {
      setGeminiReasonings(prev => ({ ...prev, [pair.candidate_id]: `Gemini Error: ${e.message}` }));
    } finally {
      setGeminiLoading(prev => ({ ...prev, [pair.candidate_id]: false }));
    }
  };

  const resolvePair = async (pair: any, decision: string) => {
    try {
      const res = await fetch("http://localhost:8000/api/sandbox/resolve_pair", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kol_id_a: pair.kol_id_a,
          kol_id_b: pair.kol_id_b,
          decision,
          pull_id: pullId,
          gemini_reasoning: geminiReasonings[pair.candidate_id] || ""
        })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Resolution failed.");
      // Remove the resolved pair from the list
      setPendingPairs(prev => prev.filter(p => p.candidate_id !== pair.candidate_id));
      setActionStatus(`✓ ${json.message}`);
      // Refresh the main KOL table
      fetchSandbox();
    } catch (e: any) {
      setActionStatus(`Error: ${e.message}`);
    }
  };

  const statusColor = (status: string) => {
    if (status === 'verified') return { bg: 'rgba(16,185,129,0.2)', fg: '#34d399' };
    if (status === 'rejected') return { bg: 'rgba(239,68,68,0.2)', fg: '#ef4444' };
    return { bg: 'rgba(245,158,11,0.2)', fg: '#fbbf24' };
  };

  return (
    <main style={{ padding: '3rem', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
       <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '2rem' }}>
         <Link href="/" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>← Back to Dashboard</Link>
         <Link href="/control" style={{ color: 'var(--accent-purple)', fontWeight: 'bold' }}>View Pipeline Control</Link>
         <Link href="/health" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>System Health</Link>
       </div>
       
       <h1 style={{ marginBottom: '0.5rem', fontSize: '2.2rem' }}>Campaign Sandbox Validation</h1>
       <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Isolate, verify, and deduplicate client pulls before global database execution.</p>

       <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '2rem', flex: 1 }}>
         
         {/* LEFT: CONTROLS */}
         <div className="glass-panel" style={{ padding: '2rem', height: 'fit-content' }}>
            <h3 style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--accent-blue)' }}>
                Target Sandbox
            </h3>
            
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Pull ID</label>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
                <input 
                    type="text" 
                    value={pullId} 
                    onChange={(e) => setPullId(e.target.value)} 
                    placeholder="e.g. CAMP_01"
                    style={{ flex: 1, padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} 
                />
                <button onClick={fetchSandbox} style={{ padding: '0 1rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Load</button>
            </div>

            <h3 style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--accent-purple)' }}>
                Sandbox Actions
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <button onClick={() => handleAction("run_disambiguation")} disabled={isLoading || kols.length === 0} style={{ padding: '1rem', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid var(--border-glass)', borderRadius: '4px', cursor: 'pointer' }}>
                    1. Run Disambiguation Engine
                </button>
                <button onClick={fetchPendingPairs} disabled={isLoading || kols.length === 0} style={{ padding: '1rem', background: 'linear-gradient(to right, #8b5cf6, #6d28d9)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                    2. Human-in-the-Loop Disambiguation
                </button>
                <button onClick={() => handleAction("export")} disabled={isLoading || kols.length === 0} style={{ padding: '1rem', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid var(--border-glass)', borderRadius: '4px', cursor: 'pointer' }}>
                    3. Export Client Text Report
                </button>
                <button onClick={() => handleAction("commit")} disabled={isLoading || kols.length === 0} style={{ padding: '1rem', background: 'linear-gradient(to right, #10b981, #059669)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                    4. Commit to Global DB
                </button>
                <button onClick={() => handleAction("erase")} disabled={isLoading || kols.length === 0} style={{ padding: '1rem', marginTop: '1rem', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: '1px solid #ef4444', borderRadius: '4px', cursor: 'pointer' }}>
                    Erase Sandbox
                </button>
            </div>

            {actionStatus && (
                 <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', border: '1px solid var(--border-glass)', fontSize: '0.85rem' }}>
                     {actionStatus}
                 </div>
            )}
         </div>

         {/* RIGHT: DATA TABLE + HITL PANEL */}
         <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* KOL Table */}
            <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: 0 }}>Staged KOLs</h3>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <span style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', padding: '0.3rem 0.8rem', borderRadius: '12px', fontSize: '0.8rem' }}>
                            Verified: {kols.filter(k => k.verification_status === 'verified').length}
                        </span>
                        <span style={{ background: 'rgba(245,158,11,0.2)', color: '#fbbf24', padding: '0.3rem 0.8rem', borderRadius: '12px', fontSize: '0.8rem' }}>
                            Pending: {kols.filter(k => k.verification_status === 'pending').length}
                        </span>
                        <div style={{ background: 'rgba(255,255,255,0.1)', padding: '0.3rem 0.8rem', borderRadius: '20px', fontSize: '0.9rem' }}>
                            Total: {kols.length}
                        </div>
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', maxHeight: '400px' }}>
                    {kols.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                            Enter a Pull ID to load staged data.
                        </div>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                                <tr style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>
                                    <th style={{ padding: '1rem', borderBottom: '1px solid var(--border-glass)' }}>Name</th>
                                    <th style={{ padding: '1rem', borderBottom: '1px solid var(--border-glass)' }}>Specialty</th>
                                    <th style={{ padding: '1rem', borderBottom: '1px solid var(--border-glass)' }}>Institution</th>
                                    <th style={{ padding: '1rem', borderBottom: '1px solid var(--border-glass)' }}>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {kols.map((kol, idx) => {
                                    const sc = statusColor(kol.verification_status);
                                    return (
                                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '1rem', fontWeight: '500' }}>{kol.name}</td>
                                            <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{kol.specialty || '—'}</td>
                                            <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{kol.institution || '—'}</td>
                                            <td style={{ padding: '1rem' }}>
                                                <span style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem', background: sc.bg, color: sc.fg }}>
                                                    {kol.verification_status}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* HITL REVIEW PANEL */}
            {showHITL && (
                <div className="glass-panel" style={{ padding: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                        <h3 style={{ margin: 0, color: '#8b5cf6' }}>🔬 Human-in-the-Loop Disambiguation</h3>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <span style={{ background: 'rgba(139,92,246,0.2)', color: '#a78bfa', padding: '0.3rem 0.8rem', borderRadius: '12px', fontSize: '0.8rem' }}>
                                Pairs Remaining: {pendingPairs.length}
                            </span>
                            <button onClick={() => setShowHITL(false)} style={{ background: 'none', border: '1px solid var(--border-glass)', color: 'var(--text-secondary)', padding: '0.3rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}>
                                Close Panel
                            </button>
                        </div>
                    </div>

                    {pendingPairs.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '3rem', color: '#34d399', fontSize: '1.1rem' }}>
                            ✅ All disambiguation pairs resolved! Ready for commit.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                            {pendingPairs.map((pair) => (
                                <div key={pair.candidate_id} style={{ border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '1.5rem', background: 'rgba(0,0,0,0.2)' }}>
                                    {/* Score header */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                        <span>Composite Score: <strong style={{ color: pair.score_total >= 0.5 ? '#fbbf24' : '#94a3b8' }}>{(pair.score_total * 100).toFixed(1)}%</strong></span>
                                        <span>Name: {(pair.score_name * 100).toFixed(0)}% | CoAuth: {(pair.score_coauthor * 100).toFixed(0)}% | MeSH: {(pair.score_mesh * 100).toFixed(0)}% | Temporal: {(pair.score_temporal * 100).toFixed(0)}%</span>
                                    </div>
                                    
                                    {/* Side-by-side KOL cards */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                        {[pair.kol_a, pair.kol_b].map((kol, idx) => (
                                            <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', padding: '1rem' }}>
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>KOL {idx === 0 ? 'A' : 'B'}</div>
                                                <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '0.5rem' }}>{kol.name}</div>
                                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>🏛 {kol.institution || 'Unknown'}</div>
                                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>🔬 {kol.specialty || 'Unknown'}</div>
                                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>🆔 {kol.orcid || 'No ORCID'}</div>
                                                {kol.mesh_tags && kol.mesh_tags.length > 0 && (
                                                    <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                                                        {kol.mesh_tags.map((tag: string, i: number) => (
                                                            <span key={i} style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa', padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: '0.7rem' }}>{tag}</span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {/* Gemini Advisory */}
                                    <div style={{ marginBottom: '1rem' }}>
                                        {geminiReasonings[pair.candidate_id] ? (
                                            <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '6px', padding: '1rem', fontSize: '0.85rem', lineHeight: '1.6' }}>
                                                <span style={{ color: '#60a5fa', fontWeight: 'bold', fontSize: '0.75rem', textTransform: 'uppercase', display: 'block', marginBottom: '0.5rem' }}>🤖 Gemini Flash 2.5 Advisory</span>
                                                {geminiReasonings[pair.candidate_id]}
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => askGemini(pair)}
                                                disabled={geminiLoading[pair.candidate_id]}
                                                style={{ padding: '0.6rem 1.5rem', background: 'rgba(59,130,246,0.2)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.4)', borderRadius: '4px', cursor: geminiLoading[pair.candidate_id] ? 'wait' : 'pointer', fontSize: '0.85rem' }}
                                            >
                                                {geminiLoading[pair.candidate_id] ? "⏳ Querying Gemini..." : "🤖 Ask Gemini Flash"}
                                            </button>
                                        )}
                                    </div>

                                    {/* Resolution Buttons */}
                                    <div style={{ display: 'flex', gap: '1rem' }}>
                                        <button
                                            onClick={() => resolvePair(pair, "same_person")}
                                            style={{ flex: 1, padding: '0.8rem', background: 'linear-gradient(to right, #10b981, #059669)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}
                                        >
                                            ✓ Same Person — Merge
                                        </button>
                                        <button
                                            onClick={() => resolvePair(pair, "two_people")}
                                            style={{ flex: 1, padding: '0.8rem', background: 'rgba(245,158,11,0.2)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.4)', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}
                                        >
                                            ✗ Two People — Keep Both
                                        </button>
                                        <button
                                            onClick={() => resolvePair(pair, "escalate")}
                                            style={{ flex: 1, padding: '0.8rem', background: 'rgba(239,68,68,0.15)', color: '#f87171', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}
                                        >
                                            → Escalate to Deep Review
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
         </div>
       </div>
    </main>
  );
}
