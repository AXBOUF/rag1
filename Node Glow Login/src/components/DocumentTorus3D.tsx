import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

type CardKind = "letter" | "memo" | "spread" | "annotated" | "grid" | "manifesto";

function rndFn(seed: number) {
  return (n: number) => {
    const x = Math.sin(seed * 9999 + n * 137.13) * 10000;
    return x - Math.floor(x);
  };
}

function makeCardTexture(kind: CardKind, seed: number): THREE.CanvasTexture {
  const w = 320;
  const h = 420;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const rnd = rndFn(seed);

  // Aged paper background
  const bgShade = 240 + Math.floor(rnd(0) * 12);
  ctx.fillStyle = `rgb(${bgShade},${bgShade - 4},${bgShade - 12})`;
  ctx.fillRect(0, 0, w, h);

  // Paper grain speckle
  for (let i = 0; i < 220; i++) {
    ctx.fillStyle = `rgba(0,0,0,${rnd(i + 50) * 0.05})`;
    ctx.fillRect(rnd(i) * w, rnd(i + 1) * h, 1, 1);
  }

  // Subtle edge
  ctx.strokeStyle = "rgba(0,0,0,0.12)";
  ctx.lineWidth = 1;
  ctx.strokeRect(0.5, 0.5, w - 1, h - 1);

  const ink = "rgba(20,18,16,0.85)";
  const yellow = "rgba(255,221,0,0.55)";
  const red = "#d62828";

  const drawLine = (x: number, y: number, lw: number, h2 = 3) => {
    ctx.fillStyle = ink;
    ctx.fillRect(x, y, lw, h2);
  };

  const drawHighlight = (x: number, y: number, lw: number, h2 = 10) => {
    ctx.fillStyle = yellow;
    ctx.fillRect(x, y - h2 + 4, lw, h2);
  };

  const drawParagraph = (x: number, y: number, lines: number, maxW: number, highlightChance = 0.12) => {
    for (let i = 0; i < lines; i++) {
      const lw = 40 + rnd(i + 100) * (maxW - 40);
      if (rnd(i + 200) < highlightChance) drawHighlight(x, y + i * 11, lw);
      drawLine(x, y + i * 11, lw, 2);
    }
  };

  if (kind === "letter") {
    // Address block top-right
    drawParagraph(w - 130, 30, 4, 110, 0.25);
    // Date left
    drawLine(28, 95, 90, 2);
    // Salutation
    ctx.fillStyle = ink;
    ctx.font = "italic 14px serif";
    ctx.fillText("Dear —,", 28, 130);
    // Body
    drawParagraph(28, 150, 16, w - 56, 0.2);
    // Signature scribble
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(30, h - 50);
    for (let i = 0; i < 60; i++) {
      ctx.lineTo(30 + i * 2, h - 50 + Math.sin(i * 0.6 + rnd(0) * 5) * 8);
    }
    ctx.stroke();
  } else if (kind === "memo") {
    // Black header band
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, w, 60);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 11px monospace";
    ctx.fillText("MEMORANDUM", 18, 24);
    ctx.font = "9px monospace";
    ctx.fillText("N° " + Math.floor(rnd(2) * 9999).toString().padStart(4, "0"), 18, 42);
    // Two-column body
    drawParagraph(18, 80, 18, 130, 0.15);
    drawParagraph(165, 80, 18, 135, 0.15);
    // Red stamp circle
    ctx.strokeStyle = red;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(w - 55, h - 55, 32, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = red;
    ctx.font = "bold 9px monospace";
    ctx.fillText("CONF.", w - 71, h - 52);
  } else if (kind === "spread") {
    // Image plate top
    const hue = Math.floor(rnd(1) * 60) + 15;
    const g = ctx.createLinearGradient(0, 0, w, 200);
    g.addColorStop(0, `hsl(${hue},45%,55%)`);
    g.addColorStop(1, `hsl(${hue + 30},35%,30%)`);
    ctx.fillStyle = g;
    ctx.fillRect(20, 24, w - 40, 180);
    // halftone dots
    for (let yy = 0; yy < 18; yy++) {
      for (let xx = 0; xx < 28; xx++) {
        const r = (Math.sin(xx * 0.6 + yy * 0.4) + 1) * 1.6;
        ctx.fillStyle = `rgba(0,0,0,${0.18 + rnd(xx + yy * 30) * 0.1})`;
        ctx.beginPath();
        ctx.arc(28 + xx * 10, 32 + yy * 10, r, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    // caption
    ctx.fillStyle = ink;
    ctx.font = "9px monospace";
    ctx.fillText("FIG. " + Math.floor(rnd(3) * 99) + " — plate study", 22, 222);
    drawParagraph(22, 240, 14, w - 44, 0.18);
  } else if (kind === "annotated") {
    // Big display word
    ctx.fillStyle = ink;
    ctx.font = "bold 56px serif";
    const words = ["Form", "Index", "Notes", "Atlas", "Trace"];
    const word = words[Math.floor(rnd(4) * words.length)];
    ctx.fillText(word, 24, 78);
    // Underline red
    ctx.fillStyle = red;
    ctx.fillRect(24, 88, 200, 3);
    // marginal column lines
    drawParagraph(24, 110, 22, w - 100, 0.25);
    // right margin annotations
    ctx.strokeStyle = red;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w - 90, 130);
    ctx.lineTo(w - 30, 150);
    ctx.stroke();
    ctx.font = "italic 10px serif";
    ctx.fillStyle = red;
    ctx.fillText("see §iv", w - 70, 165);
    // small box
    ctx.strokeStyle = ink;
    ctx.strokeRect(w - 80, 200, 60, 50);
  } else if (kind === "grid") {
    // Modular grid of small swatches
    ctx.fillStyle = ink;
    ctx.font = "bold 10px monospace";
    ctx.fillText("PLATE / 04", 20, 28);
    const cols = 4;
    const rows = 6;
    const cw = (w - 60) / cols;
    const ch = (h - 80) / rows;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = 20 + c * (cw + 4);
        const y = 50 + r * (ch + 4);
        const v = rnd(r * cols + c);
        if (v > 0.7) {
          ctx.fillStyle = `hsl(${Math.floor(v * 60)},70%,50%)`;
        } else if (v > 0.4) {
          ctx.fillStyle = "#1a1a1a";
        } else {
          ctx.fillStyle = "#e9e3d2";
        }
        ctx.fillRect(x, y, cw, ch);
        ctx.strokeStyle = "rgba(0,0,0,0.4)";
        ctx.strokeRect(x + 0.5, y + 0.5, cw - 1, ch - 1);
      }
    }
  } else {
    // manifesto: rotated/highlighted typography
    ctx.save();
    ctx.translate(28, 70);
    ctx.fillStyle = yellow;
    ctx.fillRect(-4, -28, 200, 36);
    ctx.fillStyle = ink;
    ctx.font = "bold 28px serif";
    ctx.fillText("typografie", 0, 0);
    ctx.restore();
    ctx.fillStyle = red;
    ctx.font = "italic 14px serif";
    ctx.fillText("a manifesto.", 28, 110);
    drawParagraph(28, 140, 18, w - 56, 0.3);
    // bottom rule
    ctx.fillStyle = ink;
    ctx.fillRect(28, h - 40, w - 56, 1);
    ctx.font = "9px monospace";
    ctx.fillText("01 / 12", 28, h - 22);
    ctx.fillText("BASEL — 1986", w - 90, h - 22);
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.anisotropy = 8;
  tex.needsUpdate = true;
  return tex;
}

const KINDS: CardKind[] = ["letter", "memo", "spread", "annotated", "grid", "manifesto"];

function Torus() {
  const group = useRef<THREE.Group>(null!);

  const cards = useMemo(() => {
    const items: {
      pos: THREE.Vector3;
      rot: THREE.Euler;
      tex: THREE.CanvasTexture;
    }[] = [];
    const ringCount = 2;
    const perRing = 22;
    const R = 2.6; // major radius
    const rOffset = 0.35; // minor offset between rings
    let seed = 1;
    for (let r = 0; r < ringCount; r++) {
      const yOff = (r - (ringCount - 1) / 2) * rOffset * 2;
      for (let i = 0; i < perRing; i++) {
        const u = (i / perRing) * Math.PI * 2 + (r % 2 ? Math.PI / perRing : 0);
        const x = Math.cos(u) * R;
        const z = Math.sin(u) * R;
        const y = yOff + Math.sin(u * 3 + r) * 0.08;
        // face outward (tangent to ring)
        const rotY = -u + Math.PI / 2;
        const rotZ = (r === 0 ? 1 : -1) * 0.12;
        const kind = KINDS[(i + r) % KINDS.length];
        items.push({
          pos: new THREE.Vector3(x, y, z),
          rot: new THREE.Euler(0, rotY, rotZ),
          tex: makeCardTexture(kind, seed++),
        });
      }
    }
    return items;
  }, []);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.getElapsedTime();
    group.current.rotation.y = t * 0.25;
    group.current.rotation.x = Math.sin(t * 0.3) * 0.15 - 0.35;
    group.current.position.y = Math.sin(t * 0.6) * 0.15;
  });

  return (
    <group ref={group}>
      {cards.map((c, i) => (
        <mesh key={i} position={c.pos} rotation={c.rot}>
          <planeGeometry args={[0.7, 0.9]} />
          <meshBasicMaterial
            map={c.tex}
            side={THREE.DoubleSide}
            toneMapped={false}
          />
        </mesh>
      ))}
    </group>
  );
}

export default function DocumentTorus3D() {
  return (
    <Canvas
      camera={{ position: [0, 0, 6], fov: 45 }}
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
    >
      <Torus />
    </Canvas>
  );
}