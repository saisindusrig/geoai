"use client";

function HeroSceneFallback() {
  return (
    <div className="absolute inset-0 overflow-hidden bg-[radial-gradient(ellipse_at_center,rgba(178,187,171,0.22),transparent_58%)]">
      <div className="absolute left-1/2 top-1/2 h-[min(64vw,34rem)] w-[min(64vw,34rem)] -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/20 bg-primary/10 shadow-[0_0_120px_rgba(178,187,171,0.22)]" />
      <div className="absolute inset-x-[18%] bottom-[22%] h-px bg-gradient-to-r from-transparent via-primary/35 to-transparent" />
      <div className="absolute inset-y-[24%] left-1/2 w-px bg-gradient-to-b from-transparent via-primary/20 to-transparent" />
    </div>
  );
}

export default function HeroEarthAnimation() {
  return (
    <div className="relative h-full w-full">
      <HeroSceneFallback />
      <div className="absolute inset-0 bg-gradient-to-b from-background-secondary/10 via-transparent to-background-secondary/20" />
      <video
        aria-hidden="true"
        autoPlay
        className="absolute inset-0 h-full w-full object-cover opacity-85"
        loop
        muted
        playsInline
        preload="metadata"
        tabIndex={-1}
      >
        <source src="/videos/hero-mall-loop.mp4" type="video/mp4" />
      </video>
    </div>
  );
}
