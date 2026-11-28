"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { clamp, segmentProgress, storyState } from "@/lib/story";
import { Platforms, type ArchitectureMotion } from "./Platforms";

type ArchitectureSceneProps = {
  variant: "hero" | "story";
};

type CameraKeyframe = {
  position: readonly [number, number, number];
  target: readonly [number, number, number];
  fov: number;
  zoom: number;
  separation: number;
  scale: number;
  emphasis: readonly [number, number, number, number];
  opacity: readonly [number, number, number, number];
};

type CameraSample = {
  position: THREE.Vector3;
  target: THREE.Vector3;
  fov: number;
  zoom: number;
  separation: number;
  scale: number;
  emphasis: [number, number, number, number];
  opacity: [number, number, number, number];
};

const KEYFRAMES: readonly CameraKeyframe[] = [
  {
    position: [9.6, 8.6, 11.2],
    target: [0, 0, 0],
    fov: 32,
    zoom: 1,
    separation: 1,
    scale: 1,
    emphasis: [0.82, 0.82, 0.82, 0.82],
    opacity: [1, 1, 1, 1],
  },
  {
    position: [5.4, 7.35, 6.4],
    target: [0, 2.93, 0],
    fov: 30,
    zoom: 1.32,
    separation: 1.15,
    scale: 1.05,
    emphasis: [1, 0.2, 0.16, 0.14],
    opacity: [1, 0.26, 0.2, 0.18],
  },
  {
    position: [5.6, 5.05, 6.6],
    target: [0, 1, 0],
    fov: 30,
    zoom: 1.3,
    separation: 1.18,
    scale: 1.05,
    emphasis: [0.18, 1, 0.16, 0.14],
    opacity: [0.24, 1, 0.2, 0.18],
  },
  {
    position: [5.7, 3, 6.6],
    target: [0, -1, 0],
    fov: 30,
    zoom: 1.3,
    separation: 1.18,
    scale: 1.05,
    emphasis: [0.16, 0.18, 1, 0.16],
    opacity: [0.2, 0.24, 1, 0.2],
  },
  {
    position: [5.35, 1.1, 6.3],
    target: [0, -2.93, 0],
    fov: 30,
    zoom: 1.32,
    separation: 1.15,
    scale: 1.05,
    emphasis: [0.14, 0.16, 0.18, 1],
    opacity: [0.18, 0.2, 0.24, 1],
  },
  {
    position: [12, 9.4, 14.6],
    target: [0, 0, 0],
    fov: 36,
    zoom: 0.86,
    separation: 1.55,
    scale: 0.9,
    emphasis: [0.34, 0.34, 0.34, 0.34],
    opacity: [0.16, 0.16, 0.16, 0.16],
  },
];

function lerp(from: number, to: number, t: number) {
  return from + (to - from) * t;
}

function sampleKeyframes(
  progress: number,
  out: CameraSample,
  scratchA: THREE.Vector3,
  scratchB: THREE.Vector3,
) {
  const value = clamp(progress);
  const steps = KEYFRAMES.length - 1;
  const scaled = value * steps;
  const index = Math.min(steps - 1, Math.floor(scaled));
  const t = segmentProgress(value, index / steps, (index + 1) / steps);
  const from = KEYFRAMES[index];
  const to = KEYFRAMES[index + 1];

  scratchA.set(from.position[0], from.position[1], from.position[2]);
  scratchB.set(to.position[0], to.position[1], to.position[2]);
  out.position.lerpVectors(scratchA, scratchB, t);

  scratchA.set(from.target[0], from.target[1], from.target[2]);
  scratchB.set(to.target[0], to.target[1], to.target[2]);
  out.target.lerpVectors(scratchA, scratchB, t);

  out.fov = lerp(from.fov, to.fov, t);
  out.zoom = lerp(from.zoom, to.zoom, t);
  out.separation = lerp(from.separation, to.separation, t);
  out.scale = lerp(from.scale, to.scale, t);

  for (let index = 0; index < 4; index += 1) {
    out.emphasis[index] = lerp(from.emphasis[index], to.emphasis[index], t);
    out.opacity[index] = lerp(from.opacity[index], to.opacity[index], t);
  }
}

function RendererLifecycle() {
  const gl = useThree((state) => state.gl);

  useEffect(() => {
    return () => {
      gl.renderLists.dispose();
      gl.dispose();
    };
  }, [gl]);

  return null;
}

export function ArchitectureScene({ variant }: ArchitectureSceneProps) {
  const camera = useThree((state) => state.camera) as THREE.PerspectiveCamera;
  const cameraRef = useRef(camera);
  const motionRef = useRef<ArchitectureMotion>({
    emphasis: [
      KEYFRAMES[0].emphasis[0],
      KEYFRAMES[0].emphasis[1],
      KEYFRAMES[0].emphasis[2],
      KEYFRAMES[0].emphasis[3],
    ],
    opacity: [
      KEYFRAMES[0].opacity[0],
      KEYFRAMES[0].opacity[1],
      KEYFRAMES[0].opacity[2],
      KEYFRAMES[0].opacity[3],
    ],
    separation: KEYFRAMES[0].separation,
    scale: KEYFRAMES[0].scale,
    focus: 0,
    reveal: 0,
    pointerX: 0,
    pointerY: 0,
    elapsed: 0,
    reducedMotion: false,
    variant,
  });
  const sampleRef = useRef<CameraSample>({
    position: new THREE.Vector3(),
    target: new THREE.Vector3(),
    fov: 32,
    zoom: 1,
    separation: 1,
    scale: 1,
    emphasis: [0, 0, 0, 0],
    opacity: [0, 0, 0, 0],
  });
  const scratchRef = useRef({ a: new THREE.Vector3(), b: new THREE.Vector3() });
  const pointerRef = useRef({ x: 0, y: 0 });

  useLayoutEffect(() => {
    const sample = sampleRef.current;
    const activeCamera = cameraRef.current;
    sampleKeyframes(0, sample, scratchRef.current.a, scratchRef.current.b);
    activeCamera.position.copy(sample.position);
    activeCamera.lookAt(sample.target);
    activeCamera.fov = sample.fov;
    activeCamera.zoom = sample.zoom;
    activeCamera.updateProjectionMatrix();
  }, [cameraRef, sampleRef, scratchRef]);

  useFrame((state, delta) => {
    const reduced = storyState.reducedMotion;
    const sample = sampleRef.current;
    const scratch = scratchRef.current;
    const activeCamera = cameraRef.current;
    const progress = variant === "story" && !reduced ? storyState.progress : 0;
    sampleKeyframes(progress, sample, scratch.a, scratch.b);

    const pointerTargetX = variant === "hero" && !reduced ? clamp(storyState.mouseX) : 0;
    const pointerTargetY = variant === "hero" && !reduced ? clamp(storyState.mouseY) : 0;
    const smoothing = 1 - Math.exp(-Math.min(Math.max(delta, 0), 0.1) * 3.4);
    pointerRef.current.x += (pointerTargetX - pointerRef.current.x) * smoothing;
    pointerRef.current.y += (pointerTargetY - pointerRef.current.y) * smoothing;

    activeCamera.position.copy(sample.position);
    if (variant === "hero" && !reduced) {
      activeCamera.position.x += pointerRef.current.x * 0.55;
      activeCamera.position.y +=
        -pointerRef.current.y * 0.32 + Math.sin(state.clock.elapsedTime * 0.22) * 0.055;
    }
    activeCamera.lookAt(sample.target);

    if (
      Math.abs(activeCamera.fov - sample.fov) > 0.001 ||
      Math.abs(activeCamera.zoom - sample.zoom) > 0.001
    ) {
      activeCamera.fov = sample.fov;
      activeCamera.zoom = sample.zoom;
      activeCamera.updateProjectionMatrix();
    }

    const motion = motionRef.current;
    for (let index = 0; index < 4; index += 1) {
      motion.emphasis[index] = sample.emphasis[index];
      motion.opacity[index] = sample.opacity[index];
    }
    motion.separation = sample.separation;
    motion.scale = sample.scale;
    motion.focus = variant === "story" && !reduced ? clamp(progress) * 5 : 0;
    motion.reveal = 1 - sample.opacity[0];
    motion.pointerX = pointerRef.current.x;
    motion.pointerY = pointerRef.current.y;
    motion.elapsed = reduced ? 0 : state.clock.elapsedTime;
    motion.reducedMotion = reduced;
    motion.variant = variant;
  }, -2);

  return (
    <>
      <RendererLifecycle />
      <fog attach="fog" args={["#080808", 14, 32]} />
      <ambientLight intensity={0.42} color="#F5F1E8" />
      <hemisphereLight args={["#EACB83", "#080808", 0.36]} />
      <directionalLight position={[6, 10, 8]} intensity={1.45} color="#F5DFA0" />
      <directionalLight position={[-7, -4, -5]} intensity={0.34} color="#A39D90" />
      <pointLight position={[0, 4.5, 4]} intensity={12} distance={18} decay={2} color="#D4AF37" />
      <pointLight position={[-4, -2.5, 3]} intensity={6} distance={14} decay={2} color="#77736C" />
      <Platforms motion={motionRef} />
    </>
  );
}
