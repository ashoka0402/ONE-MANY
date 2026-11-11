"use client";

import Particles, { ParticlesProvider } from "@tsparticles/react";
import type { Engine, ISourceOptions } from "@tsparticles/engine";
import { loadSlim } from "@tsparticles/slim";

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
    move: { enable: true, speed: 0.3, outModes: { default: "bounce" } },
  },
  interactivity: { events: { onClick: { enable: false }, onHover: { enable: false } } },
};

// tsParticles v4 uses ParticlesProvider; initParticlesEngine was removed from its React export.
const initializeParticles = async (engine: Engine): Promise<void> => {
  await loadSlim(engine);
};

export default function ParticleField() {
  return (
    <ParticlesProvider init={initializeParticles}>
      <Particles id="shared-possibilities" options={options} />
    </ParticlesProvider>
  );
}
