"use client";

import { useMemo, useRef } from "react";
import { Points } from "three";
import { useFrame } from "@react-three/fiber";

export function ParticleField() {
  const pointsRef = useRef<Points>(null);
  const positions = useMemo(() => {
    const pseudo = (seed: number) => {
      const x = Math.sin(seed * 12.9898) * 43758.5453;
      return x - Math.floor(x);
    };

    const arr = new Float32Array(1200 * 3);
    for (let i = 0; i < 1200; i++) {
      arr[i * 3] = (pseudo(i + 1) - 0.5) * 30;
      arr[i * 3 + 1] = (pseudo(i + 5001) - 0.5) * 16;
      arr[i * 3 + 2] = (pseudo(i + 9001) - 0.5) * 20;
    }
    return arr;
  }, []);

  useFrame(({ clock }) => {
    if (!pointsRef.current) return;
    pointsRef.current.rotation.y = clock.elapsedTime * 0.03;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#00d9ff" size={0.03} transparent opacity={0.7} />
    </points>
  );
}
