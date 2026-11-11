"use client";
import dynamic from "next/dynamic";
import { useReducedMotion } from "motion/react";
const ParticleField = dynamic(() => import("./particle-field"), { ssr: false });
export function HeroParticles() {
  const reduceMotion = useReducedMotion();
  return <div className="particles-layer" aria-hidden="true">{reduceMotion === false && <ParticleField />}</div>;
}
