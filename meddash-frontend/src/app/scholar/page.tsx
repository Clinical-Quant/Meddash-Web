"use client";

import { useState } from "react";
import Link from "next/link";

export default function ScholarEnrichmentPage() {
  const [pullId, setPullId] = useState("");
  const [kols, setKols] = useState<any[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<Set<string>>(new Set());
  const [manualScholarUrls, setManualScholarUrls] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const getKolId = (kol: any): number | null => {
    const id = kol?.id ?? kol?.kol_id;
    return Number.isFinite(id) ? Number(id) : null;
  };

  const getRowKey = (kol: any, idx: number) => {
    const kolId = getKolId(kol);
    return kolId !== null ? `kol-${kolId}` : `row-${idx}`;
  };

  const selectableRowKeys = kols
    .filter(k => Number.isFinite(k.__kolId))
    .map(k => k.__rowKey);

  const buildScholarUrl = (scholarId: string) =>
    scholarId ? `https://scholar.google.com/citations?hl=en&user=${scholarId}` : "";

  const isValidScholarInput = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return false;
    if (/^[A-Za-z0-9_-]+$/.test(trimmed)) return true;

    try {
      const url = new URL(trimmed);
      return url.hostname.includes("scholar.google.com") && !!url.searchParams.get("user");
    } catch {
      return false;
    }
  };

  const loadKols = async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!pullId.trim()) return;
    if (!silent) {
      setIsLoading(true);
      setActionStatus(null);
    }

    try {
      const res = await fetch(`http://localhost:8000/api/scholar/final_kols?pull_id=${encodeURIComponent(pullId)}`);
      if (!res.ok) throw new Error("Failed to fetch final KOLs for this pull ID.");
      const json = await res.json();
      const nextKols = (json.data || []).map((item: any, idx: number) => {
        const kolId = getKolId(item);
        const rowKey = getRowKey(item, idx);
        return { ...item, __kolId: kolId, __rowKey: rowKey };
      });
      setKols(nextKols);
      setSelectedRowKeys(prev => {
        if (silent && prev.size > 0) {
          const nextSelected = nextKols
            .filter((k: any) => Number.isFinite(k.__kolId) && prev.has(k.__rowKey))
            .map((k: any) => k.__rowKey);
          if (nextSelected.length > 0) return new Set(nextSelected);
        }
        return new Set(nextKols.filter((k: any) => Number.isFinite(k.__kolId)).map((k: any) => k.__rowKey));
      });
      setManualScholarUrls(prev => {
        const nextUrls: Record<string, string> = silent ? { ...prev } : {};
        for (const item of nextKols) {
          const serverValue = item.scholar_profile_url || buildScholarUrl(item.scholar_id || "");
          nextUrls[item.__rowKey] = serverValue || nextUrls[item.__rowKey] || "";
        }
        return nextUrls;
      });

      if (!silent) {
        if (!nextKols.length) {
          setActionStatus(`No final KOLs found for pull ID ${pullId}.`);
        } else if (!nextKols.some((k: any) => Number.isFinite(k.__kolId))) {
          setActionStatus(`Loaded ${nextKols.length} final KOLs for pull ID ${pullId}, but no valid KOL IDs were returned. Scholar sync is disabled until IDs are available.`);
        } else {
          setActionStatus(`Loaded ${nextKols.length} final KOLs for pull ID ${pullId}.`);
        }
      }
    } catch (e: any) {
      if (!silent) {
        setActionStatus(`Error: ${e.message}`);
        setKols([]);
        setSelectedRowKeys(new Set());
      }
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  };

  const toggleRowSelection = (rowKey: string) => {
    setSelectedRowKeys(prev => {
      const next = new Set(prev);
      if (next.has(rowKey)) next.delete(rowKey);
      else next.add(rowKey);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedRowKeys.size === selectableRowKeys.length) {
      setSelectedRowKeys(new Set());
    } else {
      setSelectedRowKeys(new Set(selectableRowKeys));
    }
  };

  const runManualScholarParsing = async () => {
    const rowByKey = new Map(kols.map(kol => [kol.__rowKey, kol]));
    const invalidTargets = Array.from(selectedRowKeys)
      .map(rowKey => {
        const row = rowByKey.get(rowKey);
        const scholarUrl = (manualScholarUrls[rowKey] || "").trim();
        if (!row || !scholarUrl) return null;
        return {
          name: row.name,
          scholar_url: scholarUrl
        };
      })
      .filter((target): target is { name: string; scholar_url: string } => !!target && !isValidScholarInput(target.scholar_url));

    if (invalidTargets.length > 0) {
      const previewNames = invalidTargets.slice(0, 3).map(target => target.name).join(", ");
      setActionStatus(`Only Google Scholar profile URLs or raw Scholar user IDs are allowed. Fix invalid entries for: ${previewNames}${invalidTargets.length > 3 ? "..." : ""}`);
      return;
    }

    const targets = Array.from(selectedRowKeys)
      .map(rowKey => {
        const row = rowByKey.get(rowKey);
        if (!row || !Number.isFinite(row.__kolId)) return null;
        return {
          kol_id: row.__kolId,
          scholar_url: (manualScholarUrls[rowKey] || "").trim()
        };
      })
      .filter((target): target is { kol_id: number; scholar_url: string } => !!target && !!target.scholar_url);

    if (targets.length === 0) {
      setActionStatus("Paste at least one Scholar profile URL for a selected final KOL.");
      return;
    }

    setIsRunning(true);
    try {
      const res = await fetch("http://localhost:8000/api/scholar/run_final_sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pull_id: pullId, targets })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Manual Scholar parsing failed.");
      setActionStatus(`${json.message} View logs in System Health under Scholar Final Parsing.`);

      const poll = setInterval(async () => {
        await loadKols({ silent: true });
      }, 3000);
      setTimeout(() => clearInterval(poll), 120000);
    } catch (e: any) {
      setActionStatus(`Error: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const statusColor = (status: string) => {
    if (status === "scholar_verified") return { bg: "rgba(16,185,129,0.2)", fg: "#34d399" };
    if (status === "scholar_failed") return { bg: "rgba(239,68,68,0.2)", fg: "#ef4444" };
    return { bg: "rgba(100,116,139,0.2)", fg: "#94a3b8" };
  };

  return (
    <main style={{ padding: "3rem", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: "1.5rem", display: "flex", gap: "2rem" }}>
        <Link href="/" style={{ color: "var(--accent-blue)", fontWeight: "bold" }}>Back to Dashboard</Link>
        <Link href="/health" style={{ color: "var(--accent-blue)", fontWeight: "bold" }}>System Health</Link>
        <Link href="/sandbox" style={{ color: "var(--accent-purple)", fontWeight: "bold" }}>Campaign Sandbox</Link>
      </div>

      <h1 style={{ marginBottom: "0.5rem", fontSize: "2.2rem" }}>Final KOL Scholar Enrichment</h1>
      <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
        Optional manual enrichment lane for final KOLs by pull ID. Paste Scholar profile URLs only when you want to process them.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 3fr", gap: "2rem", flex: 1 }}>
        <div className="glass-panel" style={{ padding: "2rem", height: "fit-content" }}>
          <h3 style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: "0.5rem", marginBottom: "1rem", color: "var(--accent-blue)" }}>
            Final KOL Pull Selector
          </h3>

          <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Pull ID</label>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
            <input
              type="text"
              value={pullId}
              onChange={(e) => setPullId(e.target.value)}
              placeholder="e.g. 001"
              style={{ flex: 1, padding: "0.8rem", background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-glass)", borderRadius: "4px", color: "white" }}
            />
            <button onClick={() => { void loadKols(); }} disabled={isLoading} style={{ padding: "0 1rem", background: "var(--accent-blue)", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}>
              Load
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <button
              onClick={toggleSelectAll}
              disabled={kols.length === 0}
              style={{ padding: "1rem", background: "rgba(255,255,255,0.1)", color: "white", border: "1px solid var(--border-glass)", borderRadius: "4px", cursor: "pointer" }}
            >
              {selectedRowKeys.size === selectableRowKeys.length && selectableRowKeys.length > 0 ? "Deselect All" : "Select All"}
            </button>
            <button
              onClick={runManualScholarParsing}
              disabled={isRunning || selectedRowKeys.size === 0}
              style={{ padding: "1rem", background: "linear-gradient(to right, #f59e0b, #d97706)", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold" }}
            >
              {isRunning ? "Running..." : `Run Manual Scholar Parsing for ${selectedRowKeys.size} Selected KOLs`}
            </button>
            <button
              onClick={() => { void loadKols(); }}
              disabled={isLoading}
              style={{ padding: "1rem", background: "rgba(255,255,255,0.1)", color: "white", border: "1px solid var(--border-glass)", borderRadius: "4px", cursor: "pointer" }}
            >
              Refresh Final KOLs
            </button>
          </div>

          {actionStatus && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "rgba(255,255,255,0.05)", borderRadius: "4px", border: "1px solid var(--border-glass)", fontSize: "0.85rem" }}>
              {actionStatus}
            </div>
          )}
        </div>

        <div className="glass-panel" style={{ padding: "2rem", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-glass)", paddingBottom: "1rem", marginBottom: "1.5rem" }}>
            <h3 style={{ margin: 0 }}>Final KOLs for Pull ID</h3>
            <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
              <span style={{ background: "rgba(245,158,11,0.2)", color: "#f59e0b", padding: "0.3rem 0.8rem", borderRadius: "12px", fontSize: "0.8rem" }}>
                Selected: {selectedRowKeys.size}
              </span>
              <div style={{ background: "rgba(255,255,255,0.1)", padding: "0.3rem 0.8rem", borderRadius: "20px", fontSize: "0.9rem" }}>
                Total: {kols.length}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
            This page is intentionally decoupled from sandbox validation so Scholar enrichment can happen later, in batches, or by outsourced support.
          </div>

          <div style={{ flex: 1, overflowX: "auto", overflowY: "auto", maxHeight: "600px" }}>
            {kols.length === 0 ? (
              <div style={{ textAlign: "center", padding: "4rem", color: "var(--text-secondary)" }}>
                Enter a Pull ID to load final KOLs.
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase" }}>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)", width: "40px" }}>Sel</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Name</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Specialty</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Institution</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Scholar Status</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Scholar URL</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>Citations</th>
                    <th style={{ padding: "1rem", borderBottom: "1px solid var(--border-glass)" }}>h-index</th>
                  </tr>
                </thead>
                <tbody>
                  {kols.map((kol, idx) => {
                    const sc = statusColor(kol.scholar_status);
                    const rowKey = kol.__rowKey ?? getRowKey(kol, idx);
                    const hasKolId = Number.isFinite(kol.__kolId);
                    return (
                      <tr key={rowKey} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "1rem" }}>
                          <input
                            type="checkbox"
                            checked={selectedRowKeys.has(rowKey)}
                            onChange={() => toggleRowSelection(rowKey)}
                            disabled={!hasKolId}
                            title={!hasKolId ? "Missing KOL ID in final database." : ""}
                            style={{ cursor: hasKolId ? "pointer" : "not-allowed", width: "18px", height: "18px" }}
                          />
                        </td>
                        <td style={{ padding: "1rem", fontWeight: "500" }}>{kol.name}</td>
                        <td style={{ padding: "1rem", color: "var(--text-secondary)", fontSize: "0.9rem" }}>{kol.specialty || "-"}</td>
                        <td style={{ padding: "1rem", color: "var(--text-secondary)", fontSize: "0.9rem" }}>{kol.institution || "-"}</td>
                        <td style={{ padding: "1rem" }}>
                          <span style={{ padding: "0.2rem 0.6rem", borderRadius: "12px", fontSize: "0.8rem", background: sc.bg, color: sc.fg }}>
                            {kol.scholar_status}
                          </span>
                        </td>
                        <td style={{ padding: "1rem", minWidth: "360px" }}>
                          <input
                            type="text"
                            value={manualScholarUrls[rowKey] || ""}
                            onChange={(e) => {
                              const value = e.target.value;
                              setManualScholarUrls(prev => ({ ...prev, [rowKey]: value }));
                            }}
                            placeholder={hasKolId ? "Paste Scholar profile URL or raw user ID" : "Missing KOL ID for sync"}
                            style={{ width: "100%", padding: "0.65rem", background: "rgba(0,0,0,0.25)", border: "1px solid var(--border-glass)", borderRadius: "4px", color: "white", fontSize: "0.85rem" }}
                          />
                        </td>
                        <td style={{ padding: "1rem", fontWeight: kol.total_citations ? "bold" : "normal", color: kol.total_citations ? "#34d399" : "var(--text-secondary)" }}>
                          {kol.total_citations != null ? kol.total_citations.toLocaleString() : "-"}
                        </td>
                        <td style={{ padding: "1rem" }}>{kol.h_index ?? "-"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
