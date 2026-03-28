"use client";

import { useState, useEffect, useRef } from "react";
import Link from 'next/link';

export default function Health() {
  const [activeScript, setActiveScript] = useState("ct_crawler");
  const [logs, setLogs] = useState("Waiting for connection...");
  const [isRunning, setIsRunning] = useState(false);
  const [errorMSG, setErrorMSG] = useState<string | null>(null);
  const [sandboxPullId, setSandboxPullId] = useState("001");
  
  const bottomRef = useRef<HTMLDivElement>(null);

  // Resolve the actual log script name (sandbox tab uses dynamic pull_id)
  const resolvedScript =
    activeScript === "sandbox_dedup"
      ? `sandbox_dedup_${sandboxPullId}`
      : activeScript === "scholar_sync"
        ? `scholar_sync_${sandboxPullId}`
        : activeScript === "scholar_final"
          ? `scholar_final_${sandboxPullId}`
        : activeScript;

  // Poll for live logs every 1.5 seconds when looking at a script
  useEffect(() => {
    fetchLogs(resolvedScript);
    const interval = setInterval(() => {
      fetchLogs(resolvedScript);
    }, 1500);
    return () => clearInterval(interval);
  }, [resolvedScript]);

  // Auto-scroll terminal log to bottom dynamically
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const fetchLogs = async (script: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/system/logs/${script}`);
      if (!res.ok) throw new Error("API Offline or unreachable.");
      const json = await res.json();
      setLogs(json.logs);
      setIsRunning(json.running);
      setErrorMSG(null);
    } catch (err: any) {
      setErrorMSG(err.message);
      setLogs("COMMUNICATION FATAL: Cannot mount to 127.0.0.1:8000.\nCheck if 'python api_server.py' is running in the background.");
      setIsRunning(false);
    }
  };

  const triggerExecution = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/system/run?script_name=${activeScript}`, {
        method: "POST"
      });
      if (!res.ok) {
         const json = await res.json();
         throw new Error(json.detail || "Trigger failed.");
      }
      // Force instantaneous refresh of logs
      fetchLogs(resolvedScript);
    } catch (err: any) {
      alert("Execution Failed: " + err.message);
    }
  };

  const scriptCards = [
    { id: "kol_engine", name: "KOL Data Engine", intent: "Scrape Clinical Experts" },
    { id: "ct_crawler", name: "Clinical Trials Engine", intent: "Scrape NIH Database" },
    { id: "biocrawler", name: "BioCrawler Lead Gen", intent: "Map BioTech Startups" },
    { id: "ta_landscape", name: "Product Gen: TA Landscape", intent: "Compile Final PDF" },
    { id: "sandbox_dedup", name: "Sandbox Disambiguation", intent: "Campaign Dedup Engine" },
    { id: "scholar_sync", name: "Scholar Sync", intent: "Sandbox Manual Scholar Parsing" },
    { id: "scholar_final", name: "Scholar Final Parsing", intent: "Final KOL Manual Scholar Parsing" }
  ];

  return (
    <main style={{ padding: '3rem', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
       <div style={{ marginBottom: '2rem' }}>
         <Link href="/" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>← Back to Dashboard</Link>
       </div>
       
       <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '2rem', flex: 1 }}>
         {/* Sidebar Controls */}
         <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h1 style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>System Health Override</h1>
            
            {scriptCards.map(s => (
              <div 
                key={s.id}
                onClick={() => setActiveScript(s.id)}
                className="glass-panel card-hover"
                style={{
                  padding: '1.5rem',
                  border: activeScript === s.id ? '2px solid var(--accent-purple)' : '1px solid var(--border-glass)',
                  background: activeScript === s.id ? 'rgba(139, 92, 246, 0.1)' : 'var(--bg-glass)'
                }}
              >
                 <h3 style={{ marginBottom: '0.2rem' }}>{s.name}</h3>
                 <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{s.intent}</p>
                 
                 {activeScript === s.id && (
                     <div style={{ marginTop: '1.5rem' }}>
                       {/* Pull ID input for sandbox disambiguation tab */}
                       {(s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final") && (
                         <div style={{ marginBottom: '1rem' }}>
                           <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Pull ID</label>
                           <input
                             type="text"
                             value={sandboxPullId}
                             onChange={(e) => setSandboxPullId(e.target.value)}
                             onClick={(e) => e.stopPropagation()}
                             placeholder="e.g. 001"
                             style={{ width: '100%', padding: '0.5rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white', fontSize: '0.9rem' }}
                           />
                         </div>
                       )}
                       <button 
                         onClick={(e) => { e.stopPropagation(); triggerExecution(); }}
                         disabled={isRunning || s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final"}
                         style={{
                           width: '100%',
                           padding: '0.75rem',
                           background: (isRunning || s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final") ? 'var(--bg-glass)' : 'var(--accent-blue)',
                           color: (isRunning || s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final") ? 'var(--text-secondary)' : 'white',
                           border: 'none',
                           borderRadius: '4px',
                           cursor: (isRunning || s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final") ? 'not-allowed' : 'pointer',
                           fontWeight: 'bold'
                         }}
                       >
                         {s.id === "sandbox_dedup" || s.id === "scholar_sync" || s.id === "scholar_final" ? "LOG VIEWER ONLY" : isRunning ? "PROCESS ACTIVE 🔴" : "▶ RUN SCRIPT NOW"}
                       </button>
                     </div>
                 )}
              </div>
            ))}
         </div>

         {/* Virtual Terminal Window */}
         <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden', background: '#000' }}>
            <div style={{ padding: '1rem', background: '#111', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between' }}>
               <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>root@meddash: ~/{resolvedScript}.log</span>
               <span style={{ color: isRunning ? '#34d399' : '#94a3b8', fontWeight: 'bold' }}>
                  {isRunning ? "STATUS: EXECUTING" : "STATUS: ASLEEP"}
               </span>
            </div>
            <div style={{ 
                flex: 1, 
                padding: '1.5rem', 
                overflowY: 'auto', 
                fontFamily: 'Consolas, Monaco, monospace', 
                fontSize: '0.9rem',
                color: '#10b981', // Terminal Green
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap'
            }}>
               {errorMSG ? <span style={{ color: '#ef4444' }}>{errorMSG}</span> : logs}
               <div ref={bottomRef} />
            </div>
         </div>
       </div>
    </main>
  );
}
