"use client";

import { useState, useEffect } from "react";
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function CrawlerControl() {
  const router = useRouter();
  const [diseaseName, setDiseaseName] = useState("");
  const [meshId, setMeshId] = useState("");
  const [phases, setPhases] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [pullId, setPullId] = useState("");
  const [maxResults, setMaxResults] = useState<number>(50);
  
  const [targetEngine, setTargetEngine] = useState("ct_crawler");
  const [isExecuting, setIsExecuting] = useState(false);
  const [responseMsg, setResponseMsg] = useState<string | null>(null);
  const [isEngineRunning, setIsEngineRunning] = useState(false);

  // Poll background status of selected engine
  useEffect(() => {
    let active = true;
    const checkStatus = async () => {
      try {
        const checkTarget = targetEngine === "sequential_ct_bio" ? "sequential_ct_bio" : targetEngine;
        const res = await fetch(`http://localhost:8000/api/system/logs/${checkTarget}`);
        const json = await res.json();
        if (active) setIsEngineRunning(json.running);
      } catch (e) {
        if (active) setIsEngineRunning(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 2000);
    return () => { active = false; clearInterval(interval); };
  }, [targetEngine]);

  const toggleArray = (array: string[], setArray: any, value: string) => {
    if (array.includes(value)) setArray(array.filter(v => v !== value));
    else setArray([...array, value]);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    setResponseMsg(null);
    
    // Construct the payload mapping Phase 4 requirements
    const payload = {
        engine: targetEngine,
        disease_name: diseaseName,
        mesh_id: meshId,
        phases: phases,
        statuses: statuses,
        date_from: dateFrom,
        date_to: dateTo,
        pull_id: pullId,
        max_results: maxResults
    };

    try {
      const res = await fetch(`http://localhost:8000/api/system/run_advanced`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Execution failed.");
      
      setResponseMsg(`✅ LAUNCH SUCCESS: ${json.message}. Navigate to System Health to monitor logs.`);
    } catch (err: any) {
      setResponseMsg(`❌ ERROR: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <main style={{ padding: '3rem', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
       <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <Link href="/" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>← Back to Dashboard</Link>
         <Link href="/sandbox" style={{ 
            color: 'var(--accent-purple)', 
            fontWeight: 'bold', 
            padding: '0.6rem 1.2rem', 
            background: 'rgba(139, 92, 246, 0.15)', 
            borderRadius: '6px', 
            border: '1px solid var(--accent-purple)',
            textDecoration: 'none',
            transition: 'all 0.2s ease-in-out'
          }}>
            Go to Campaign Sandbox / Validation Bay →
         </Link>
       </div>
       
       <h1 style={{ marginBottom: '2rem', fontSize: '2.2rem' }}>Crawler Pipeline Control</h1>

       <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', flex: 1 }}>
         
         {/* LEFT: THE FORM CONTROLS */}
         <div className="glass-panel" style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            {/* Target Definition */}
            <div>
               <h3 style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--accent-purple)' }}>
                   1. Core Clinical Target 
               </h3>
               <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Target Disease Name</label>
                       <input 
                         type="text" 
                         value={diseaseName} 
                         onChange={(e) => setDiseaseName(e.target.value)} 
                         style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} 
                       />
                   </div>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>MeSH Ontology ID</label>
                       <input 
                         type="text" 
                         value={meshId} 
                         onChange={(e) => setMeshId(e.target.value)} 
                         style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} 
                       />
                   </div>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>ICD-10 Code</label>
                       <input 
                         type="text" 
                         value={""} 
                         placeholder="Search..."
                         onChange={() => {}} 
                         style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} 
                       />
                   </div>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>SNOMED CT Concept ID</label>
                       <input 
                         type="text" 
                         value={""} 
                         placeholder="Search..."
                         onChange={() => {}} 
                         style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} 
                       />
                   </div>
                   <div style={{ gridColumn: 'span 2', marginTop: '1rem' }}>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '1rem', fontWeight: 'bold', color: 'var(--accent-blue)' }}>Campaign Sandbox Pull ID (Optional)</label>
                       <input 
                         type="text" 
                         value={pullId} 
                         placeholder="e.g. CAMP_PFIZER_01"
                         onChange={(e) => setPullId(e.target.value)} 
                         style={{ width: '100%', padding: '0.8rem', background: 'rgba(59,130,246,0.1)', border: '1px solid var(--accent-blue)', borderRadius: '4px', color: 'white' }} 
                       />
                   </div>
               </div>
            </div>

            {/* Trial Parameters */}
            <div>
               <h3 style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem', color: 'var(--accent-purple)' }}>
                   2. Trial Extrapolation Filters
               </h3>
               
               <div style={{ display: 'flex', gap: '3rem', marginBottom: '1.5rem' }}>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Phase Filter</label>
                       {['PHASE1', 'PHASE2', 'PHASE3', 'PHASE4'].map(ph => (
                           <label key={ph} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', fontSize: '0.95rem' }}>
                               <input type="checkbox" checked={phases.includes(ph)} onChange={() => toggleArray(phases, setPhases, ph)} />
                               {ph}
                           </label>
                       ))}
                   </div>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Status Filter</label>
                       {['RECRUITING', 'COMPLETED', 'SUSPENDED', 'UNKNOWN'].map(st => (
                           <label key={st} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', fontSize: '0.95rem' }}>
                               <input type="checkbox" checked={statuses.includes(st)} onChange={() => toggleArray(statuses, setStatuses, st)} />
                               {st}
                           </label>
                       ))}
                   </div>
               </div>

               <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Time Period (From)</label>
                       <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} />
                   </div>
                   <div>
                       <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Time Period (To)</label>
                       <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }} />
                   </div>
               </div>
            </div>

         </div>

         {/* RIGHT: EXECUTION BAY */}
         <div className="glass-panel" style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column' }}>
             <h3 style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1.5rem', color: 'var(--accent-purple)' }}>
                   3. Engine Selection & Launch
             </h3>

             <div style={{ marginBottom: '1.5rem' }}>
                 <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Extract Volume Limit (Items)</label>
                 <select 
                    value={maxResults} 
                    onChange={(e) => setMaxResults(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-glass)', borderRadius: '4px', color: 'white' }}
                 >
                     {[10, 25, 50, 100, 200, 500, 1000].map(val => (
                         <option key={val} value={val}>{val} Records</option>
                     ))}
                     <option value={999999}>Max Possible (All)</option>
                 </select>
             </div>

             <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Routing Destination</label>
             <select 
                value={targetEngine} 
                onChange={(e) => setTargetEngine(e.target.value)}
                style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--accent-blue)', borderRadius: '4px', color: 'white', marginBottom: '2rem' }}
             >
                 <option value="kol_engine">KOL Data Engine</option>
                 <option value="ct_crawler">Clinical Trials Crawler</option>
                 <option value="biocrawler">BioCrawler GTM Engine</option>
                 <option value="sequential_ct_bio">Sequential Pipeline (CT to BioCrawler)</option>
             </select>

             {/* Summary Readout */}
             <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.5rem', borderRadius: '4px', border: '1px solid var(--border-glass)', marginBottom: '2rem', flex: 1 }}>
                 <p style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>// EXECUTION PAYLOAD COMPILED</p>
                 <p style={{ fontSize: '0.9rem' }}><strong>Target:</strong> {meshId || diseaseName || "Global Net"}</p>
                 <p style={{ fontSize: '0.9rem' }}><strong>Phases:</strong> {phases.length > 0 ? phases.join(", ") : "All"}</p>
                 <p style={{ fontSize: '0.9rem' }}><strong>Status:</strong> {statuses.length > 0 ? statuses.join(", ") : "All"}</p>
                 <p style={{ fontSize: '0.9rem' }}><strong>Date Block:</strong> {dateFrom || "Genesis"} {"->"} {dateTo || "Present"}</p>
             </div>

             <button 
                onClick={handleExecute}
                disabled={isExecuting}
                style={{
                  width: '100%',
                  padding: '1.2rem',
                  background: isExecuting ? 'var(--bg-glass)' : 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isExecuting ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                  fontSize: '1.1rem',
                  boxShadow: '0 4px 14px rgba(59, 130, 246, 0.3)',
                  transition: 'transform 0.1s'
                }}
             >
                {isExecuting ? "TRANSMITTING COMMAND..." : "INITIATE CRAWLER OBERRIDE"}
             </button>

              {responseMsg && (
                 <div style={{ marginTop: '1.5rem', padding: '1rem', background: responseMsg.includes("ERROR") ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)', color: responseMsg.includes("ERROR") ? '#ef4444' : '#10b981', borderRadius: '4px', border: `1px solid ${responseMsg.includes("ERROR") ? '#ef4444' : '#10b981'}`, fontSize: '0.9rem' }}>
                     {responseMsg}
                 </div>
             )}

             {/* SMOOTH UI HANDOFF TO SANDBOX */}
             {!isEngineRunning && !isExecuting && pullId && responseMsg && !responseMsg.includes("ERROR") && targetEngine === "kol_engine" && (
                 <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid var(--accent-purple)', borderRadius: '8px', textAlign: 'center' }}>
                     <h4 style={{ color: 'var(--accent-purple)', marginBottom: '0.5rem' }}>Engine Scrape Staged Successfully</h4>
                     <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>The raw records have been held in isolation. Proceed to the Sandbox to execute deduplication, disambiguation, and commit.</p>
                     <button 
                        onClick={() => router.push('/sandbox')}
                        style={{ padding: '0.8rem 2rem', background: 'var(--accent-purple)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                     >
                        Enter Sandbox Validation Bay →
                     </button>
                 </div>
             )}
         </div>

       </div>
    </main>
  );
}
