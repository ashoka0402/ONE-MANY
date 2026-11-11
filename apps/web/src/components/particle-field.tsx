"use client";
import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import type { ISourceOptions } from "@tsparticles/engine";
const options: ISourceOptions = {
  fullScreen: { enable: false },
  fpsLimit: 30,
  detectRetina: false,
  pauseOnBlur: true,
  pauseOnOutsideViewport: true,
  particles: {
    number: { value: 18 },
    color: { value: ["#7c9b5d", "#a89cdb"] },
    opacity: { value: { min: 0.15, max: 0.45 } },
    size: { value: { min: 2, max: 4 } },
    links: { enable: true, distance: 95, color: "#7c9b5d", opacity: 0.12, width: 1 },
    move: { enable: true, speed: 0.3, direction: "inside", outModes: { default: "bounce" } },
  },
  interactivity: { events: { onClick: { enable: false }, onHover: { enable: false } } },
};
// Share initialization across mounts; the decorative canvas never controls page readiness.
let engineReady: Promise<void> | undefined;
export default function ParticleField() {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let active = true;
    engineReady ??= initParticlesEngine(async (engine) => { await loadSlim(engine); });
    engineReady.then(() => { if (active) setReady(true); }).catch(() => { /* The static hero remains usable if decoration cannot initialize. */ });
    return () => { active = false; };
  }, []);
  return ready ? <Particles id="shared-possibilities" options={options} /> : null;
}
