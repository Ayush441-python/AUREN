"use client";

import { useEffect, useMemo, useRef, type ReactNode, type RefObject } from "react";
import { useFrame } from "@react-three/fiber";
import { Edges, RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { clamp, smoothstep } from "@/lib/story";

export type ArchitectureMotion = {
  emphasis: [number, number, number, number];
  opacity: [number, number, number, number];
  separation: number;
  scale: number;
  focus: number;
  reveal: number;
  pointerX: number;
  pointerY: number;
  elapsed: number;
  reducedMotion: boolean;
  variant: "hero" | "story";
};

type PlatformResources = {
  unitBox: THREE.BoxGeometry;
  node: THREE.SphereGeometry;
  pulse: THREE.SphereGeometry;
  base: THREE.MeshPhysicalMaterial;
  gold: THREE.MeshStandardMaterial;
  champagne: THREE.MeshStandardMaterial;
  muted: THREE.LineBasicMaterial;
  graph: THREE.LineBasicMaterial;
  wire: THREE.MeshBasicMaterial;
  negative: THREE.MeshStandardMaterial;
};

type PlatformShellProps = {
  index: number;
  motion: RefObject<ArchitectureMotion>;
  children: (resources: PlatformResources) => ReactNode;
};

type VisualProps = {
  motion: RefObject<ArchitectureMotion>;
  resources: PlatformResources;
};

type AllocationBlock = {
  x: number;
  z: number;
  w: number;
  d: number;
  heights: readonly [number, number];
  phase: number;
};

type StressBar = {
  x: number;
  z: number;
  w: number;
  d: number;
  heights: readonly [number, number];
  phase: number;
};

const BASE_Y = [2.55, 0.85, -0.85, -2.55] as const;

const RISK_VALUES = [
  0.02, -0.06, 0.05, 0.16, 0.1, 0.26, 0.18, 0.34, 0.28, 0.44, 0.38, 0.52, 0.48, 0.6,
] as const;

const RISK_MARKERS = [-1.7, -0.55, 0.6, 1.75] as const;

const ALLOCATION_BLOCKS: readonly AllocationBlock[] = [
  { x: -2.03, z: -0.74, w: 0.95, d: 1.02, heights: [0.28, 0.48], phase: 0.2 },
  { x: -0.98, z: -0.74, w: 1.48, d: 0.48, heights: [0.52, 0.34], phase: 0.9 },
  { x: -0.98, z: -0.2, w: 0.7, d: 0.52, heights: [0.36, 0.58], phase: 1.6 },
  { x: -0.2, z: -0.2, w: 0.8, d: 0.52, heights: [0.44, 0.3], phase: 2.2 },
  { x: 0.68, z: -0.74, w: 1.58, d: 1.02, heights: [0.55, 0.7], phase: 2.8 },
  { x: -2.03, z: 0.42, w: 0.7, d: 0.82, heights: [0.32, 0.5], phase: 3.4 },
  { x: -1.23, z: 0.42, w: 1.26, d: 0.38, heights: [0.48, 0.36], phase: 4.0 },
  { x: -1.23, z: 0.86, w: 0.58, d: 0.38, heights: [0.26, 0.42], phase: 4.6 },
  { x: -0.58, z: 0.42, w: 1.0, d: 0.82, heights: [0.6, 0.42], phase: 5.2 },
  { x: 0.53, z: 0.42, w: 1.73, d: 0.82, heights: [0.38, 0.62], phase: 5.8 },
];

const CORRELATION_NODES: readonly (readonly [number, number])[] = [
  [-2.05, -0.72],
  [-1.05, 0.62],
  [-0.1, -0.42],
  [0.85, 0.68],
  [1.95, -0.35],
  [0.35, 1.05],
  [-1.75, 0.2],
];

const CORRELATION_LINKS: readonly (readonly [number, number])[] = [
  [0, 6],
  [6, 1],
  [1, 5],
  [5, 3],
  [3, 4],
  [4, 2],
  [2, 0],
  [2, 3],
  [6, 2],
  [1, 2],
];

const GOLD_RGB = [0.831, 0.686, 0.216] as const;
const CHAMPAGNE_RGB = [0.918, 0.796, 0.514] as const;

const STRESS_BARS: readonly StressBar[] = [
  { x: -1.88, z: -0.82, w: 0.62, d: 0.68, heights: [0.28, 0.46], phase: 0.3 },
  { x: -0.63, z: -0.82, w: 0.62, d: 0.68, heights: [0.52, 0.36], phase: 1.1 },
  { x: 0.62, z: -0.82, w: 0.62, d: 0.68, heights: [0.4, 0.64], phase: 1.9 },
  { x: -1.88, z: 0, w: 0.62, d: 0.68, heights: [0.34, 0.56], phase: 2.7 },
  { x: -0.63, z: 0, w: 0.62, d: 0.68, heights: [0.62, 0.44], phase: 3.5 },
  { x: 0.62, z: 0, w: 0.62, d: 0.68, heights: [0.48, 0.72], phase: 4.3 },
  { x: -1.88, z: 0.82, w: 0.62, d: 0.68, heights: [0.44, 0.32], phase: 5.1 },
  { x: -0.63, z: 0.82, w: 0.62, d: 0.68, heights: [0.36, 0.58], phase: 5.9 },
  { x: 0.62, z: 0.82, w: 0.62, d: 0.68, heights: [0.56, 0.7], phase: 6.7 },
];

const NEGATIVE_BARS = [2, 5, 8] as const;

function createResources(): PlatformResources {
  return {
    unitBox: new THREE.BoxGeometry(1, 1, 1),
    node: new THREE.SphereGeometry(0.058, 12, 12),
    pulse: new THREE.SphereGeometry(0.028, 8, 8),
    base: new THREE.MeshPhysicalMaterial({
      color: 0x141311,
      metalness: 0.62,
      roughness: 0.26,
      clearcoat: 0.78,
      clearcoatRoughness: 0.24,
      transmission: 0.1,
      thickness: 0.16,
      attenuationColor: 0x080808,
      attenuationDistance: 1.4,
      emissive: 0x080808,
      emissiveIntensity: 0.18,
      transparent: true,
      opacity: 0.94,
      depthWrite: false,
    }),
    gold: new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      metalness: 0.92,
      roughness: 0.3,
      emissive: 0x4a390f,
      emissiveIntensity: 0.22,
      transparent: true,
      opacity: 0.88,
      depthWrite: false,
    }),
    champagne: new THREE.MeshStandardMaterial({
      color: 0xeacb83,
      metalness: 0.82,
      roughness: 0.34,
      emissive: 0x9a7a35,
      emissiveIntensity: 0.28,
      transparent: true,
      opacity: 0.96,
      depthWrite: false,
    }),
    muted: new THREE.LineBasicMaterial({
      color: 0x302a20,
      transparent: true,
      opacity: 0.8,
      depthWrite: false,
    }),
    graph: new THREE.LineBasicMaterial({
      color: 0xd4af37,
      transparent: true,
      opacity: 0.92,
      depthWrite: false,
    }),
    wire: new THREE.MeshBasicMaterial({
      color: 0xeacb83,
      wireframe: true,
      transparent: true,
      opacity: 0.2,
      depthWrite: false,
    }),
    negative: new THREE.MeshStandardMaterial({
      color: 0xf87171,
      metalness: 0.34,
      roughness: 0.48,
      emissive: 0x6b1d1d,
      emissiveIntensity: 0.18,
      transparent: true,
      opacity: 0.32,
      depthWrite: false,
    }),
  };
}

function createGridGeometry() {
  const positions: number[] = [];

  for (let index = -4; index <= 4; index += 1) {
    const x = index * 0.6;
    positions.push(x, 0, -1.38, x, 0, 1.38);
  }

  for (let index = -2; index <= 2; index += 1) {
    const z = index * 0.55;
    positions.push(-2.42, 0, z, 2.42, 0, z);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  return geometry;
}

function riskY(index: number, time: number, emphasis: number) {
  return RISK_VALUES[index] + Math.sin(time * 0.72 + index * 0.42) * 0.035 * (0.4 + emphasis);
}

function stressHeight(
  bar: StressBar,
  time: number,
  emphasis: number,
  segment: number,
  blend: number,
) {
  const from = segment === 0 ? bar.heights[0] : bar.heights[1];
  const to = segment === 0 ? bar.heights[1] : bar.heights[0];
  return (
    from +
    (to - from) * blend +
    Math.sin(time * 0.62 + bar.phase) * 0.02 * (0.35 + emphasis)
  );
}

function createRiskPath() {
  const positions = new Float32Array((RISK_VALUES.length - 1) * 6);

  for (let index = 0; index < RISK_VALUES.length - 1; index += 1) {
    const offset = index * 6;
    positions[offset] = -2.25 + (4.5 * index) / (RISK_VALUES.length - 1);
    positions[offset + 1] = RISK_VALUES[index];
    positions[offset + 2] = 0;
    positions[offset + 3] = -2.25 + (4.5 * (index + 1)) / (RISK_VALUES.length - 1);
    positions[offset + 4] = RISK_VALUES[index + 1];
    positions[offset + 5] = 0;
  }

  const attribute = new THREE.BufferAttribute(positions, 3);
  attribute.setUsage(THREE.DynamicDrawUsage);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", attribute);
  return { geometry, positions };
}

function createLinkGeometry() {
  const positions = new Float32Array(CORRELATION_LINKS.length * 6);
  const colors = new Float32Array(CORRELATION_LINKS.length * 6);

  for (let index = 0; index < CORRELATION_LINKS.length; index += 1) {
    const from = CORRELATION_NODES[CORRELATION_LINKS[index][0]];
    const to = CORRELATION_NODES[CORRELATION_LINKS[index][1]];
    const offset = index * 6;
    positions[offset] = from[0];
    positions[offset + 1] = 0.14;
    positions[offset + 2] = from[1];
    positions[offset + 3] = to[0];
    positions[offset + 4] = 0.14;
    positions[offset + 5] = to[1];
    colors[offset] = GOLD_RGB[0];
    colors[offset + 1] = GOLD_RGB[1];
    colors[offset + 2] = GOLD_RGB[2];
    colors[offset + 3] = GOLD_RGB[0];
    colors[offset + 4] = GOLD_RGB[1];
    colors[offset + 5] = GOLD_RGB[2];
  }

  const colorAttribute = new THREE.BufferAttribute(colors, 3);
  colorAttribute.setUsage(THREE.DynamicDrawUsage);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", colorAttribute);
  return { geometry, colors };
}

function PlatformShell({ index, motion, children }: PlatformShellProps) {
  const groupRef = useRef<THREE.Group>(null);
  const resources = useMemo(() => createResources(), []);

  useEffect(() => {
    return () => {
      Object.values(resources).forEach((resource) => resource.dispose());
    };
  }, [resources]);

  useFrame(() => {
    const group = groupRef.current;
    if (!group) return;

    const state = motion.current;
    let focusIndex = 0;
    let strongest = -1;
    for (let layer = 0; layer < 4; layer += 1) {
      if (state.emphasis[layer] > strongest) {
        strongest = state.emphasis[layer];
        focusIndex = layer;
      }
    }

    const emphasis = clamp(state.emphasis[index]);
    const layerOpacity = clamp(state.opacity[index]);
    const storyMotion = state.variant === "story" && !state.reducedMotion;
    const awayDirection = index <= focusIndex ? 1 : -1;
    const away = storyMotion ? (1 - emphasis) * awayDirection * 0.7 : 0;
    const idleY = state.reducedMotion
      ? 0
      : Math.sin(state.elapsed * 0.34 + index * 1.2) * 0.018;
    const idleRotationY = state.reducedMotion
      ? 0
      : Math.sin(state.elapsed * 0.16 + index * 0.6) * 0.012;
    const idleRotationX = state.reducedMotion
      ? 0
      : Math.sin(state.elapsed * 0.13 + index * 0.4) * 0.006;
    const parallaxX = state.variant === "hero" ? state.pointerX * 0.05 : state.pointerX * 0.014;
    const parallaxZ = state.variant === "hero" ? -state.pointerY * 0.04 : -state.pointerY * 0.012;
    const scale =
      state.scale * (0.92 + emphasis * 0.1) * (0.96 + layerOpacity * 0.04);

    group.position.set(
      (index - focusIndex) * (1 - emphasis) * 0.12 + parallaxX,
      BASE_Y[index] * state.separation + away + idleY,
      parallaxZ,
    );
    group.rotation.set(idleRotationX, idleRotationY, 0);
    group.scale.setScalar(scale);
    group.visible = layerOpacity > 0.015;

    group.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.material) return;
      if (Array.isArray(mesh.material)) {
        for (const material of mesh.material) {
          const baseOpacity =
            typeof material.userData.baseOpacity === "number"
              ? material.userData.baseOpacity
              : material.opacity;
          material.userData.baseOpacity = baseOpacity;
          material.opacity = baseOpacity * layerOpacity;
        }
      } else {
        const material = mesh.material;
        const baseOpacity =
          typeof material.userData.baseOpacity === "number"
            ? material.userData.baseOpacity
            : material.opacity;
        material.userData.baseOpacity = baseOpacity;
        material.opacity = baseOpacity * layerOpacity;
      }
    });
  }, -1);

  return (
    <group ref={groupRef}>
      <RoundedBox
        args={[5.8, 0.16, 3.6]}
        radius={0.06}
        smoothness={3}
        bevelSegments={2}
        material={resources.base}
      >
        <Edges threshold={18} color="#D4AF37" lineWidth={0.9} transparent opacity={0.84} />
      </RoundedBox>

      <mesh
        geometry={resources.unitBox}
        material={resources.gold}
        position={[0, 0.095, 1.78]}
        scale={[5.42, 0.012, 0.014]}
      />
      <mesh
        geometry={resources.unitBox}
        material={resources.gold}
        position={[0, 0.095, -1.78]}
        scale={[5.42, 0.012, 0.014]}
      />
      <mesh
        geometry={resources.unitBox}
        material={resources.gold}
        position={[2.88, 0.095, 0]}
        scale={[0.014, 0.012, 3.3]}
      />
      <mesh
        geometry={resources.unitBox}
        material={resources.gold}
        position={[-2.88, 0.095, 0]}
        scale={[0.014, 0.012, 3.3]}
      />
      <mesh
        geometry={resources.unitBox}
        material={resources.champagne}
        position={[-2.5, 0.102, 1.48]}
        scale={[0.42, 0.01, 0.016]}
      />
      <mesh
        geometry={resources.unitBox}
        material={resources.champagne}
        position={[2.5, 0.102, -1.48]}
        scale={[0.42, 0.01, 0.016]}
      />

      <group position={[0, 0.14, 0]}>{children(resources)}</group>
    </group>
  );
}

function RiskVisual({ motion, resources }: VisualProps) {
  const path = useMemo(() => createRiskPath(), []);
  const gridGeometry = useMemo(() => createGridGeometry(), []);
  const positionsRef = useRef(path.positions);
  const attributeRef = useRef(path.geometry.getAttribute("position") as THREE.BufferAttribute);
  const pointsRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    return () => {
      path.geometry.dispose();
      gridGeometry.dispose();
    };
  }, [path, gridGeometry]);

  useFrame(() => {
    const current = motion.current;
    const time = current.reducedMotion ? 0 : current.elapsed;
    const emphasis =
      current.variant === "story" && !current.reducedMotion ? current.emphasis[0] : 0.5;
    const positions = positionsRef.current;

    for (let index = 0; index < RISK_VALUES.length - 1; index += 1) {
      const offset = index * 6;
      positions[offset + 1] = riskY(index, time, emphasis);
      positions[offset + 4] = riskY(index + 1, time, emphasis);
    }
    attributeRef.current.needsUpdate = true;

    const points = pointsRef.current;
    if (!points) return;

    for (let index = 0; index < RISK_VALUES.length; index += 1) {
      const pulse = 0.86 + Math.sin(time * 1.4 + index * 0.65) * 0.16 * (0.4 + emphasis);
      dummy.position.set(
        -2.25 + (4.5 * index) / (RISK_VALUES.length - 1),
        riskY(index, time, emphasis),
        0.03,
      );
      dummy.scale.setScalar(pulse);
      dummy.updateMatrix();
      points.setMatrixAt(index, dummy.matrix);
    }
    points.instanceMatrix.needsUpdate = true;
  });

  return (
    <group>
      <lineSegments geometry={gridGeometry} material={resources.muted} position={[0, 0.005, 0]} />
      <lineSegments geometry={path.geometry} material={resources.graph} position={[0, 0.04, 0]} />
      <instancedMesh
        ref={pointsRef}
        args={[resources.node, resources.champagne, RISK_VALUES.length]}
      />
      {RISK_MARKERS.map((x) => (
        <group key={x} position={[x, 0, 0.02]}>
          <mesh
            geometry={resources.unitBox}
            material={resources.gold}
            position={[0, 0.33, 0]}
            scale={[0.012, 0.58, 0.012]}
          />
          <mesh
            geometry={resources.unitBox}
            material={resources.champagne}
            position={[0, 0.61, 0]}
            scale={[0.1, 0.012, 0.012]}
          />
        </group>
      ))}
      <mesh
        geometry={resources.unitBox}
        material={resources.gold}
        position={[0, 0.63, 0]}
        scale={[3.9, 0.008, 0.008]}
      />
    </group>
  );
}

function AllocationVisual({ motion, resources }: VisualProps) {
  const solidRef = useRef<THREE.InstancedMesh>(null);
  const wireRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame(() => {
    const solid = solidRef.current;
    const wire = wireRef.current;
    if (!solid || !wire) return;

    const current = motion.current;
    const time = current.reducedMotion ? 0 : current.elapsed;
    const emphasis =
      current.variant === "story" && !current.reducedMotion ? current.emphasis[1] : 0.5;
    const cycle = (time * 0.11) % 1;
    const segment = Math.floor(cycle * 2);
    const blend = smoothstep(cycle * 2 - segment);

    for (let index = 0; index < ALLOCATION_BLOCKS.length; index += 1) {
      const block = ALLOCATION_BLOCKS[index];
      let height = block.heights[0] + (block.heights[1] - block.heights[0]) * blend;
      if (segment === 1) {
        height = block.heights[1] + (block.heights[0] - block.heights[1]) * blend;
      }
      height += Math.sin(time * 0.8 + block.phase) * 0.025 * (0.35 + emphasis);

      dummy.position.set(block.x, height / 2, block.z);
      dummy.scale.set(block.w, height, block.d);
      dummy.updateMatrix();
      solid.setMatrixAt(index, dummy.matrix);

      dummy.scale.set(block.w * 1.012, height + 0.012, block.d * 1.012);
      dummy.updateMatrix();
      wire.setMatrixAt(index, dummy.matrix);
    }

    solid.instanceMatrix.needsUpdate = true;
    wire.instanceMatrix.needsUpdate = true;
  });

  return (
    <group>
      <instancedMesh
        ref={solidRef}
        args={[resources.unitBox, resources.gold, ALLOCATION_BLOCKS.length]}
      />
      <instancedMesh
        ref={wireRef}
        args={[resources.unitBox, resources.wire, ALLOCATION_BLOCKS.length]}
      />
    </group>
  );
}

function CorrelationVisual({ motion, resources }: VisualProps) {
  const link = useMemo(() => createLinkGeometry(), []);
  const linkMaterial = useMemo(
    () =>
      new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.82,
        depthWrite: false,
      }),
    [],
  );
  const colorsRef = useRef(link.geometry.getAttribute("color") as THREE.BufferAttribute);
  const nodesRef = useRef<THREE.InstancedMesh>(null);
  const pulsesRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    return () => {
      link.geometry.dispose();
      linkMaterial.dispose();
    };
  }, [link, linkMaterial]);

  useFrame(() => {
    const nodes = nodesRef.current;
    const pulses = pulsesRef.current;
    if (!nodes || !pulses) return;

    const current = motion.current;
    const time = current.reducedMotion ? 0 : current.elapsed;
    const emphasis =
      current.variant === "story" && !current.reducedMotion ? current.emphasis[2] : 0.5;

    for (let index = 0; index < CORRELATION_NODES.length; index += 1) {
      const node = CORRELATION_NODES[index];
      const bob = Math.sin(time * 0.6 + index * 0.8) * 0.035 * (0.4 + emphasis);
      dummy.position.set(node[0], 0.16 + bob, node[1]);
      dummy.scale.setScalar(1.05 + Math.sin(time + index) * 0.1 * emphasis);
      dummy.updateMatrix();
      nodes.setMatrixAt(index, dummy.matrix);
    }
    nodes.instanceMatrix.needsUpdate = true;

    const colors = colorsRef.current;
    for (let index = 0; index < CORRELATION_LINKS.length; index += 1) {
      const intensity = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(time * 0.7 + index * 0.83));
      const rgb = index % 3 === 0 ? CHAMPAGNE_RGB : GOLD_RGB;
      const offset = index * 6;
      colors.array[offset] = rgb[0] * intensity;
      colors.array[offset + 1] = rgb[1] * intensity;
      colors.array[offset + 2] = rgb[2] * intensity;
      colors.array[offset + 3] = rgb[0] * intensity;
      colors.array[offset + 4] = rgb[1] * intensity;
      colors.array[offset + 5] = rgb[2] * intensity;

      const fromIndex = CORRELATION_LINKS[index][0];
      const toIndex = CORRELATION_LINKS[index][1];
      const from = CORRELATION_NODES[fromIndex];
      const to = CORRELATION_NODES[toIndex];
      const travel = (time * 0.24 + index * 0.137) % 1;
      dummy.position.set(
        from[0] + (to[0] - from[0]) * travel,
        0.18 + Math.sin(travel * Math.PI) * 0.05,
        from[1] + (to[1] - from[1]) * travel,
      );
      dummy.scale.setScalar(0.7 + intensity * 0.7);
      dummy.updateMatrix();
      pulses.setMatrixAt(index, dummy.matrix);
    }
    colors.needsUpdate = true;
    pulses.instanceMatrix.needsUpdate = true;
  });

  return (
    <group>
      <lineSegments geometry={link.geometry} material={linkMaterial} />
      <instancedMesh
        ref={nodesRef}
        args={[resources.node, resources.gold, CORRELATION_NODES.length]}
      />
      <instancedMesh
        ref={pulsesRef}
        args={[resources.pulse, resources.champagne, CORRELATION_LINKS.length]}
      />
    </group>
  );
}

function StressVisual({ motion, resources }: VisualProps) {
  const solidRef = useRef<THREE.InstancedMesh>(null);
  const wireRef = useRef<THREE.InstancedMesh>(null);
  const negativeRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame(() => {
    const solid = solidRef.current;
    const wire = wireRef.current;
    const negative = negativeRef.current;
    if (!solid || !wire || !negative) return;

    const current = motion.current;
    const time = current.reducedMotion ? 0 : current.elapsed;
    const emphasis =
      current.variant === "story" && !current.reducedMotion ? current.emphasis[3] : 0.5;
    const cycle = (time * 0.095) % 1;
    const segment = Math.floor(cycle * 2);
    const blend = smoothstep(cycle * 2 - segment);

    for (let index = 0; index < STRESS_BARS.length; index += 1) {
      const bar = STRESS_BARS[index];
      const height = stressHeight(bar, time, emphasis, segment, blend);

      dummy.position.set(bar.x, height / 2, bar.z);
      dummy.scale.set(bar.w, height, bar.d);
      dummy.updateMatrix();
      solid.setMatrixAt(index, dummy.matrix);

      dummy.scale.set(bar.w * 1.012, height + 0.01, bar.d * 1.012);
      dummy.updateMatrix();
      wire.setMatrixAt(index, dummy.matrix);
    }

    for (let index = 0; index < NEGATIVE_BARS.length; index += 1) {
      const barIndex = NEGATIVE_BARS[index];
      const bar = STRESS_BARS[barIndex];
      const height = stressHeight(bar, time, emphasis, segment, blend);
      dummy.position.set(bar.x, height + 0.022, bar.z);
      dummy.scale.set(bar.w * 0.62, 0.016, 0.012);
      dummy.updateMatrix();
      negative.setMatrixAt(index, dummy.matrix);
    }

    solid.instanceMatrix.needsUpdate = true;
    wire.instanceMatrix.needsUpdate = true;
    negative.instanceMatrix.needsUpdate = true;
  });

  return (
    <group>
      <instancedMesh ref={solidRef} args={[resources.unitBox, resources.gold, STRESS_BARS.length]} />
      <instancedMesh ref={wireRef} args={[resources.unitBox, resources.wire, STRESS_BARS.length]} />
      <instancedMesh
        ref={negativeRef}
        args={[resources.unitBox, resources.negative, NEGATIVE_BARS.length]}
      />
    </group>
  );
}

export function Platforms({ motion }: { motion: RefObject<ArchitectureMotion> }) {
  return (
    <group>
      <PlatformShell index={0} motion={motion}>
        {(resources) => <RiskVisual motion={motion} resources={resources} />}
      </PlatformShell>
      <PlatformShell index={1} motion={motion}>
        {(resources) => <AllocationVisual motion={motion} resources={resources} />}
      </PlatformShell>
      <PlatformShell index={2} motion={motion}>
        {(resources) => <CorrelationVisual motion={motion} resources={resources} />}
      </PlatformShell>
      <PlatformShell index={3} motion={motion}>
        {(resources) => <StressVisual motion={motion} resources={resources} />}
      </PlatformShell>
    </group>
  );
}
