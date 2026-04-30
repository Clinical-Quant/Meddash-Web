export default function HeroGraphBackground() {
  const nodes = [
    { id: "n1", x: 8, y: 20, r: 2.2, pulse: "hero-pulse-a" },
    { id: "n2", x: 22, y: 34, r: 1.8, pulse: "hero-pulse-b" },
    { id: "n3", x: 34, y: 18, r: 2.4, pulse: "hero-pulse-c" },
    { id: "n4", x: 48, y: 30, r: 2.1, pulse: "hero-pulse-a" },
    { id: "n5", x: 63, y: 16, r: 2.7, pulse: "hero-pulse-b" },
    { id: "n6", x: 78, y: 28, r: 1.9, pulse: "hero-pulse-c" },
    { id: "n7", x: 90, y: 20, r: 2.3, pulse: "hero-pulse-a" },
    { id: "n8", x: 14, y: 58, r: 2.1, pulse: "hero-pulse-b" },
    { id: "n9", x: 29, y: 68, r: 1.9, pulse: "hero-pulse-c" },
    { id: "n10", x: 46, y: 62, r: 2.6, pulse: "hero-pulse-a" },
    { id: "n11", x: 61, y: 74, r: 2.0, pulse: "hero-pulse-b" },
    { id: "n12", x: 79, y: 63, r: 2.4, pulse: "hero-pulse-c" },
    { id: "n13", x: 92, y: 70, r: 1.8, pulse: "hero-pulse-a" },
    { id: "n14", x: 38, y: 48, r: 2.0, pulse: "hero-pulse-b" },
    { id: "n15", x: 70, y: 46, r: 2.2, pulse: "hero-pulse-c" },
  ];

  const edges: Array<[number, number]> = [
    [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6],
    [1, 7], [7, 8], [8, 9], [9, 10], [10, 11], [11, 12],
    [2, 13], [13, 9], [4, 14], [14, 11], [3, 9], [5, 11],
    [0, 7], [6, 12],
  ];

  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <svg
        className="h-full w-full opacity-[0.14] hero-graph-drift"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="graphEdge" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00d9ff" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0.10" />
          </linearGradient>
        </defs>

        {edges.map(([a, b], idx) => (
          <line
            key={`edge-${idx}`}
            x1={nodes[a].x}
            y1={nodes[a].y}
            x2={nodes[b].x}
            y2={nodes[b].y}
            stroke="url(#graphEdge)"
            strokeWidth="0.14"
          />
        ))}

        {nodes.map((node, idx) => (
          <g key={node.id} className={node.pulse} style={{ animationDelay: `${idx * 120}ms` }}>
            <circle cx={node.x} cy={node.y} r={node.r * 1.8} fill="#00d9ff" opacity="0.06" />
            <circle cx={node.x} cy={node.y} r={node.r} fill="#9ae6ff" opacity="0.45" />
          </g>
        ))}
      </svg>

      <div className="absolute inset-0 opacity-[0.08] hero-scanline bg-[linear-gradient(to_bottom,transparent_0%,rgba(120,170,255,0.35)_48%,transparent_100%)]" />
    </div>
  );
}
