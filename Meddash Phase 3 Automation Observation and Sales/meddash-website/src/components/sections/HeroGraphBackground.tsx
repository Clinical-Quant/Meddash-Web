export default function HeroGraphBackground() {
  const rows = 10;
  const cols = 13;

  type Node = {
    id: string;
    x: number;
    y: number;
    r: number;
    c: number;
    pulse: boolean;
    pulseDelay: string;
    pulseDuration: string;
    pulseStrength: number;
  };
  const nodes: Node[] = [];

  for (let r = 0; r < rows; r++) {
    const y = 88 - r * 7.2;
    const perspective = 1 - r * 0.045; // tighter spacing as it goes upward
    const xStep = 8.2 * perspective;
    const xStart = 2 + (r % 2 ? xStep * 0.5 : 0);

    for (let c = 0; c < cols; c++) {
      const x = xStart + c * xStep;
      if (x <= 98) {
        const pulseSeed = (r * 17 + c * 31) % 100;
        const pulse = pulseSeed < 24; // ~24% of nodes pulse softly
        const pulseDelay = `${((r * 0.27 + c * 0.19) % 2.8).toFixed(2)}s`;
        const pulseDuration = `${(2.2 + ((r * 7 + c * 3) % 16) / 10).toFixed(2)}s`;
        const pulseStrength = 0.75 + (((r * 11 + c * 5) % 20) / 100);

        nodes.push({
          id: `n-${r}-${c}`,
          x,
          y,
          r,
          c,
          pulse,
          pulseDelay,
          pulseDuration,
          pulseStrength,
        });
      }
    }
  }

  const byKey = new Map(nodes.map((n) => [`${n.r}:${n.c}`, n]));

  const edges: Array<[Node, Node]> = [];
  for (const n of nodes) {
    const right = byKey.get(`${n.r}:${n.c + 1}`);
    const upA = byKey.get(`${n.r + 1}:${n.c}`);
    const upB = byKey.get(`${n.r + 1}:${n.c - 1}`);

    if (right) edges.push([n, right]);
    if (upA) edges.push([n, upA]);
    if (upB) edges.push([n, upB]);
  }

  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <svg className="h-full w-full opacity-[0.54]" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="honeyEdge" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#9ec6d8" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#d3e8ff" stopOpacity="0.72" />
            <stop offset="100%" stopColor="#9ec6d8" stopOpacity="0.26" />
          </linearGradient>
        </defs>

        <g transform="translate(6,-3) rotate(-12 50 50) skewX(-14)">
          {edges.map(([a, b], idx) => (
            <line
              key={`e-${idx}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke="url(#honeyEdge)"
              strokeWidth="0.16"
            />
          ))}

          {nodes.map((n) => {
            const depth = 1 - n.r * 0.055;
            const haloRadius = (1.3 * depth + 0.28) * n.pulseStrength;
            return (
              <g key={n.id}>
                {n.pulse ? (
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={haloRadius}
                    fill="#bfe2ff"
                    opacity={0.15 + depth * 0.08}
                    className="hero-node-glow"
                    style={{
                      animationDelay: n.pulseDelay,
                      animationDuration: n.pulseDuration,
                    }}
                  />
                ) : null}
                <circle cx={n.x} cy={n.y} r={0.9 * depth + 0.2} fill="#cfe6ff" opacity={0.3 + depth * 0.25} />
                <circle cx={n.x} cy={n.y} r={0.33 * depth + 0.12} fill="#f1f8ff" opacity={0.95} />
              </g>
            );
          })}
        </g>
      </svg>

      <div className="absolute inset-0 z-20 opacity-[0.32] mix-blend-screen hero-scanline bg-[linear-gradient(to_bottom,transparent_0%,rgba(195,225,255,0.9)_50%,transparent_100%)]" />
    </div>
  );
}
