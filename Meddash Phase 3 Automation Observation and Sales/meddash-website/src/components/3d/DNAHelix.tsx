"use client";

import { useMemo, useRef } from "react";
import { Group } from "three";
import { useFrame } from "@react-three/fiber";

export function DNAHelix() {
  const group = useRef<Group>(null);

  const points = useMemo(() => {
    const out: { x: number; y: number; z: number; color: string }[] = [];
    const turns = 40;
    for (let i = 0; i < turns; i++) {
      const t = i * 0.25;
      const y = i * 0.12 - 2.4;
      out.push({ x: Math.cos(t) * 1.2, y, z: Math.sin(t) * 1.2, color: "#00d9ff" });
      out.push({ x: Math.cos(t + Math.PI) * 1.2, y, z: Math.sin(t + Math.PI) * 1.2, color: "#00ff88" });
    }
    return out;
  }, []);

  useFrame(({ clock }) => {
    if (!group.current) return;
    group.current.rotation.y = clock.elapsedTime * 0.22;
    group.current.rotation.x = Math.sin(clock.elapsedTime * 0.3) * 0.06;
  });

  return (
    <group ref={group}>
      {points.map((p, idx) => (
        <mesh key={idx} position={[p.x, p.y, p.z]}>
          <sphereGeometry args={[0.07, 16, 16]} />
          <meshStandardMaterial color={p.color} emissive={p.color} emissiveIntensity={0.8} />
        </mesh>
      ))}
    </group>
  );
}
