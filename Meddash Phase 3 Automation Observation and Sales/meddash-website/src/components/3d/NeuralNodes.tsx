"use client";

import { useMemo } from "react";
import { Line } from "@react-three/drei";

export function NeuralNodes({ count = 24 }: { count?: number }) {
  const points = useMemo(() => {
    const pseudo = (seed: number) => {
      const x = Math.sin(seed * 12.9898) * 43758.5453;
      return x - Math.floor(x);
    };

    const p: [number, number, number][] = [];
    for (let i = 0; i < count; i++) {
      p.push([(pseudo(i + 1) - 0.5) * 12, (pseudo(i + 101) - 0.5) * 6, (pseudo(i + 1001) - 0.5) * 8]);
    }
    return p;
  }, [count]);

  const links = useMemo(() => {
    const l: [number, number][] = [];
    for (let i = 0; i < points.length; i++) {
      for (let j = i + 1; j < points.length; j++) {
        const dx = points[i][0] - points[j][0];
        const dy = points[i][1] - points[j][1];
        const dz = points[i][2] - points[j][2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d < 2.8) l.push([i, j]);
      }
    }
    return l.slice(0, 40);
  }, [points]);

  return (
    <group>
      {points.map((p, i) => (
        <mesh key={`n-${i}`} position={p}>
          <sphereGeometry args={[0.04, 10, 10]} />
          <meshStandardMaterial color="#00d9ff" emissive="#00d9ff" emissiveIntensity={0.5} />
        </mesh>
      ))}

      {links.map(([a, b], i) => (
        <Line key={`l-${i}`} points={[points[a], points[b]]} color="#00ff88" lineWidth={1} transparent opacity={0.45} />
      ))}
    </group>
  );
}
