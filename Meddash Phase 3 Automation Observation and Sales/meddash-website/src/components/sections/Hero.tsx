import Scene3D from "@/components/3d/Scene";
import HeroGraphBackground from "@/components/sections/HeroGraphBackground";

export default function Hero() {
  return (
    <section className="relative overflow-hidden min-h-[78vh] flex items-center px-6 md:px-10">
      <Scene3D />
      <HeroGraphBackground />
      <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/35 via-[#05070d]/60 to-[#05070d]" />
      <div className="relative z-20 max-w-4xl">
        <p className="text-meddash-cyan tracking-[0.2em] uppercase text-xs md:text-sm mb-4">Meddash.ai</p>
        <h1 className="text-4xl md:text-6xl font-semibold leading-tight text-white">
          Therapeutic Intelligence for Biotech Teams
        </h1>
        <p className="mt-5 text-base md:text-lg text-slate-300 max-w-2xl">
          KOL intelligence, biotech catalyst tracking, and clinical-trial search — unified into one high-signal decision layer.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="#lead" className="rounded-xl bg-meddash-cyan text-black px-5 py-3 font-semibold hover:opacity-90">Request Brief</a>
          <a href="#calendar" className="rounded-xl border border-meddash-emerald/70 text-meddash-emerald px-5 py-3 font-semibold hover:bg-meddash-emerald/10">Explore Catalysts</a>
        </div>
      </div>
    </section>
  );
}