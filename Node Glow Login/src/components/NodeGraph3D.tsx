import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function generateNodes(count: number, radius: number) {
  const nodes: THREE.Vector3[] = [];
  for (let i = 0; i < count; i++) {
    const phi = Math.acos(-1 + (2 * i) / count);
    const theta = Math.sqrt(count * Math.PI) * phi;
    nodes.push(
      new THREE.Vector3(
        radius * Math.cos(theta) * Math.sin(phi),
        radius * Math.sin(theta) * Math.sin(phi),
        radius * Math.cos(phi),
      ),
    );
  }
  return nodes;
}

function Graph() {
  const group = useRef<THREE.Group>(null!);
  const nodes = useMemo(() => generateNodes(28, 2.2), []);

  const edges = useMemo(() => {
    const lines: [THREE.Vector3, THREE.Vector3][] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (nodes[i].distanceTo(nodes[j]) < 1.6) {
          lines.push([nodes[i], nodes[j]]);
        }
      }
    }
    return lines;
  }, [nodes]);

  const lineGeometry = useMemo(() => {
    const positions: number[] = [];
    edges.forEach(([a, b]) => {
      positions.push(a.x, a.y, a.z, b.x, b.y, b.z);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    return geo;
  }, [edges]);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = t * 0.18;
    group.current.rotation.x = Math.sin(t * 0.25) * 0.25;
    group.current.position.y = Math.sin(t * 0.6) * 0.15;
  });

  return (
    <group ref={group}>
      <lineSegments geometry={lineGeometry}>
        <lineBasicMaterial
          color="#5fd4ff"
          transparent
          opacity={0.35}
        />
      </lineSegments>
      {nodes.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[0.07, 16, 16]} />
          <meshStandardMaterial
            color="#7ee8ff"
            emissive="#5fd4ff"
            emissiveIntensity={1.4}
            roughness={0.3}
          />
        </mesh>
      ))}
    </group>
  );
}

export default function NodeGraph3D() {
  return (
    <Canvas
      camera={{ position: [0, 0, 6], fov: 50 }}
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.4} />
      <pointLight position={[5, 5, 5]} intensity={1.2} color="#7ee8ff" />
      <pointLight position={[-5, -3, -2]} intensity={0.8} color="#a78bfa" />
      <Graph />
    </Canvas>
  );
}