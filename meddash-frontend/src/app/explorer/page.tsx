"use client";

import { useState, useEffect } from "react";
import Link from 'next/link';

export default function Explorer() {
  const [activeTab, setActiveTab] = useState("kols");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<Record<string, string>>({});

  const fetchData = async (tab: string) => {
    setLoading(true);
    setError(null);
    setData([]);
    try {
      const res = await fetch(`http://localhost:8000/api/db/${tab}`);
      if (!res.ok) throw new Error("Failed to fetch data from API. Is FastAPI running on port 8000?");
      const json = await res.json();
      setData(json.data || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(activeTab);
  }, [activeTab]);

  const isRecentlySynced = (last_updated: any) => {
    if (!last_updated || last_updated === 0 || last_updated === "0" || last_updated === "None") return false;
    const updatedAt = new Date(last_updated);
    if (isNaN(updatedAt.getTime())) return false;
    const diffTime = Math.abs(new Date().getTime() - updatedAt.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    return diffDays < 7;
  };

  const triggerScholarSync = async (kol_id: string, current_date: any) => {
    if (isRecentlySynced(current_date)) return;
    setSyncStatus(prev => ({...prev, [kol_id]: 'syncing'}));
    try {
      const res = await fetch("http://localhost:8000/api/scholar/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kol_id: String(kol_id) })
      });
      if (!res.ok) throw new Error("Sync failed");
      setSyncStatus(prev => ({...prev, [kol_id]: 'success'}));
      // Let the backend process it for a couple seconds before polling for the update
      setTimeout(() => fetchData(activeTab), 4000);
    } catch (e) {
      setSyncStatus(prev => ({...prev, [kol_id]: 'error'}));
    }
  };

  return (
    <main style={{ padding: '3rem', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
       <div style={{ marginBottom: '2rem' }}>
         <Link href="/" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>← Back to Dashboard</Link>
       </div>
       <div className="glass-panel" style={{ padding: '2.5rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h1 style={{ marginBottom: '1.5rem', fontSize: '2.2rem' }}>PostgreSQL Inspector</h1>
          
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '2.5rem' }}>
            {['kols', 'trials', 'leads'].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '0.8rem 1.8rem',
                  borderRadius: '8px',
                  background: activeTab === tab ? 'var(--accent-blue)' : 'var(--bg-glass)',
                  color: 'white',
                  border: '1px solid var(--border-glass)',
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  fontWeight: activeTab === tab ? 'bold' : 'normal',
                  transition: 'background 0.2s',
                  fontSize: '1.1rem'
                }}
              >
                {tab.toUpperCase()} DB
              </button>
            ))}
          </div>

          {loading && <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>Loading cloud logic...</p>}
          {error && <p style={{ color: '#ef4444', background: 'rgba(239,68,68,0.1)', padding: '1rem', borderRadius: '8px' }}>{error}</p>}
          
          {!loading && !error && data.length > 0 && (
            <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '600px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
                <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-primary)', zIndex: 1 }}>
                  <tr style={{ borderBottom: '2px solid var(--border-glass)' }}>
                    {Object.keys(data[0]).map(key => (
                      <th key={key} style={{ padding: '1.2rem', color: 'var(--accent-purple)', fontSize: '0.85rem', letterSpacing: '1px' }}>
                        {key.replace(/_/g, ' ').toUpperCase()}
                      </th>
                    ))}
                    {activeTab === 'kols' && (
                      <th style={{ padding: '1.2rem', color: 'var(--accent-purple)', fontSize: '0.85rem', letterSpacing: '1px', textAlign: 'center' }}>
                        ACTIONS
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row: any, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
                      {Object.values(row).map((val: any, j) => (
                        <td key={j} style={{ padding: '1rem', fontSize: '0.95rem' }}>{String(val)}</td>
                      ))}
                      {activeTab === 'kols' && (
                        <td style={{ padding: '1rem', textAlign: 'center' }}>
                          <button 
                             onClick={() => triggerScholarSync(row.kol_id, row.last_updated_date)}
                             disabled={isRecentlySynced(row.last_updated_date) || syncStatus[row.kol_id] === 'syncing' || syncStatus[row.kol_id] === 'success'}
                             style={{
                               padding: '0.5rem 1rem', 
                               borderRadius: '4px', 
                               background: syncStatus[row.kol_id] === 'syncing' ? 'transparent' : (isRecentlySynced(row.last_updated_date) ? 'var(--bg-glass)' : 'var(--accent-blue)'),
                               border: syncStatus[row.kol_id] === 'syncing' ? '1px solid var(--accent-purple)' : 'none',
                               color: 'white',
                               cursor: (isRecentlySynced(row.last_updated_date) || syncStatus[row.kol_id]) ? 'not-allowed' : 'pointer',
                               opacity: isRecentlySynced(row.last_updated_date) ? 0.5 : 1,
                               fontSize: '0.85rem',
                               fontWeight: 'bold'
                             }}
                          >
                             {syncStatus[row.kol_id] === 'syncing' ? 'Dispatching...' : (syncStatus[row.kol_id] === 'success' ? 'Engine Triggered!' : (isRecentlySynced(row.last_updated_date) ? 'Up to date' : 'Fetch Metrics'))}
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!loading && !error && data.length === 0 && <p>No records found in this table.</p>}
       </div>
    </main>
  );
}
