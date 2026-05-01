export default function HeroGraphBackground() {
  const nodes = [
    { id: "n1", x: 8, y: 24 }, { id: "n2", x: 20, y: 30 }, { id: "n3", x: 33, y: 22 },
    { id: "n4", x: 46, y: 29 }, { id: "n5", x: 59, y: 23 }, { id: "n6", x: 72, y: 30 },
    { id: "n7", x: 86, y: 24 }, { id: "n8", x: 14, y: 60 }, { id: "n9", x: 28, y: 67 },
    { id: "n10", x: 44, y: 63 }, { id: "n11", x: 60, y: 70 }, { id: "n12", x: 77, y: 64 },
  ];

  const edges: Array<[number, number]> = [
    [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6],
    [7, 8], [8, 9], [9, 10], [10, 11],
    [1, 7], [2, 8], [3, 9], [4, 10], [5, 11],
  ];

  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <svg className="h-full w-full opacity-[0.5] hero-graph-drift" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="heroGridEdge" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#9ec6d8" stopOpacity="0.45" />
            <stop offset="50%" stopColor="#b7d6ee" stopOpacity="0.78" />
            <stop offset="100%" stopColor="#9ec6d8" stopOpacity="0.45" />
          </linearGradient>
        </defs>

        {edges.map(([a, b], idx) => (
          <line
            key={`edge-${idx}`}
            x1={nodes[a].x}
            y1={nodes[a].y}
            x2={nodes[b].x}
            y2={nodes[b].y}
            stroke="url(#heroGridEdge)"
            strokeWidth="0.24"
          />
        ))}

        {nodes.map((node) => (
          <g key={node.id}>
            <circle cx={node.x} cy={node.y} r="1.15" fill="#d7e4f1" opacity="0.46" />
            <circle cx={node.x} cy={node.y} r="0.48" fill="#e6f1ff" opacity="0.95" />
          </g>
        ))}
      </svg>

      <div className="absolute inset-0 z-20 opacity-[0.32] mix-blend-screen hero-scanline bg-[linear-gradient(to_bottom,transparent_0%,rgba(195,225,255,0.9)_50%,transparent_100%)]" />
    </div>
  );
}
