"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { DNAHelix } from "./DNAHelix";
import { NeuralNodes } from "./NeuralNodes";
import { ParticleField } from "./ParticleField";

export default function Scene3D() {
  return (
    <div className="absolute inset-0 -z-10">
      <Canvas camera={{ position: [0, 0, 9], fov: 45 }}>
        <color attach="background" args={["#05070d"]} />
        <ambientLight intensity={0.5} />
        <pointLight position={[8, 8, 8]} intensity={1.2} color="#00d9ff" />
        <pointLight position={[-8, -8, -4]} intensity={0.8} color="#00ff88" />
        <Stars radius={50} depth={20} count={1200} factor={2} saturation={0} fade speed={0.6} />
        <ParticleField />
        <DNAHelix />
        <NeuralNodes count={28} />
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.25} />
      </Canvas>
    </div>
  );
}
