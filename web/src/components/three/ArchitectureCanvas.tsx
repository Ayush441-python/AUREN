"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { advance, Canvas, type RootState } from "@react-three/fiber";
import { ACESFilmicToneMapping } from "three";
import { cn } from "@/lib/cn";
import SceneFallback from "./SceneFallback";
import { ArchitectureScene } from "./ArchitectureScene";

export type ArchitectureCanvasProps = {
  variant?: "hero" | "story";
  className?: string;
  active?: boolean;
  onReady?: () => void;
};

const DPR: [number, number] = [1, 1.6];

const GL_OPTIONS = {
  antialias: true,
  alpha: true,
  powerPreference: "high-performance" as const,
};

const CAMERA_OPTIONS = {
  position: [9.6, 8.6, 11.2] as [number, number, number],
  fov: 32,
  near: 0.1,
  far: 100,
};

function detectWebGL() {
  if (typeof window === "undefined" || typeof document === "undefined") return false;

  try {
    const canvas = document.createElement("canvas");
    const context =
      canvas.getContext("webgl2", { powerPreference: "high-performance" }) ??
      canvas.getContext("webgl", { powerPreference: "high-performance" });

    if (!context) return false;

    context.getExtension("WEBGL_lose_context")?.loseContext();
    return true;
  } catch {
    return false;
  }
}

export default function ArchitectureCanvas({
  variant = "hero",
  className,
  active = true,
  onReady,
}: ArchitectureCanvasProps) {
  const [webglSupported, setWebglSupported] = useState<boolean | null>(null);
  const onReadyRef = useRef(onReady);
  const notifiedRef = useRef(false);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setWebglSupported(detectWebGL()));
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, []);

  const notifyReady = useCallback(() => {
    if (notifiedRef.current) return;
    notifiedRef.current = true;
    onReadyRef.current?.();
  }, []);

  useEffect(() => {
    if (webglSupported === false) notifyReady();
  }, [webglSupported, notifyReady]);

  const handleCreated = useCallback(
    (state: RootState) => {
      state.gl.setClearColor(0x080808, 0);
      state.gl.toneMapping = ACESFilmicToneMapping;
      state.gl.toneMappingExposure = 1.05;
      notifyReady();

      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = requestAnimationFrame(() => {
        frameRef.current = null;
        advance(performance.now(), false, state);
      });
    },
    [notifyReady],
  );

  return (
    <>
      <div className={cn("relative isolate h-full w-full", className)} aria-hidden="true">
        {webglSupported === true ? (
          <Canvas
            dpr={DPR}
            gl={GL_OPTIONS}
            camera={CAMERA_OPTIONS}
            frameloop={active ? "always" : "never"}
            onCreated={handleCreated}
          >
            <ArchitectureScene variant={variant} />
          </Canvas>
        ) : (
          <SceneFallback variant={variant} className="h-full w-full" />
        )}
      </div>
      <p className="sr-only">
        Illustrative AUREN architecture visual: four stacked layers representing risk intelligence,
        exposure and allocation, correlation intelligence, and stress testing. It is a conceptual
        illustration and does not display real portfolio data.
      </p>
    </>
  );
}
