import { useEffect, useRef } from "react";
import { epochForYear } from "@/lib/forensic/epochs";
import { modelById } from "@/lib/forensic/models";

export type SceneProps = {
  year: number;
  reprocessed: boolean;
  wipe: number;
  contrast: number;
  invert: boolean;
  chromalock: boolean;
  showPhantom: boolean;
  modelId: string;
  reticle: { x: number; y: number };
  userImage: HTMLImageElement | null;
  onPlace: (p: { x: number; y: number }) => void;
};

const WIDTH_MI = 1.85;
const HEIGHT_MI = 5.2;
const IPP = { x: 0.52, y: 0.44 };
const PIER = { x: 0.8, y: 0.18 };
const PHANTOM = { x: 0.37, y: 0.66 };

type Cover =
  | "ocean"
  | "beach"
  | "dune"
  | "road"
  | "lot"
  | "roof"
  | "river"
  | "mangrove"
  | "metal"
  | "dielectric"
  | "fiber";

const DB: Record<Cover, number> = {
  ocean: -16,
  river: -14,
  beach: -8,
  dune: -5.5,
  mangrove: -4,
  lot: -2,
  road: 2.5,
  roof: 7,
  fiber: -3,
  dielectric: 3.5,
  metal: 11,
};

function hash(x: number, y: number, s: number) {
  let n = Math.imul(x + s * 13, 374761393) + Math.imul(y + 19, 668265263);
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n >>> 0) % 100000) / 100000;
}

function coverAt(nx: number, ny: number, showPhantom: boolean): Cover {
  if (showPhantom) {
    const dx = (nx - PHANTOM.x) * (WIDTH_MI / HEIGHT_MI);
    const dy = ny - PHANTOM.y;
    const r = Math.hypot(dx * 8, dy * 5.5);
    if (r < 0.012) return "metal";
    if (r < 0.03) return "dielectric";
    if (r < 0.045) return "fiber";
  }
  if (nx < 0.16) return "river";
  if (nx < 0.23) return "mangrove";
  if (nx > 0.86) return "ocean";
  if (nx > 0.78) return "beach";
  if (nx > 0.68) return "dune";
  if (nx > 0.485 && nx < 0.56) return "road";
  const block = Math.floor(ny * 26);
  const gate = hash(block, 4, 11);
  if (nx > 0.38 && nx < 0.5 && gate > 0.42) {
    const along = Math.abs(ny * 26 - block - 0.45);
    if (along < 0.22) return hash(block, 2, 5) > 0.45 ? "roof" : "lot";
  }
  if (nx >= 0.545 && nx <= 0.68) return "dune";
  return "lot";
}

function lerp(a: number[], b: number[], k: number) {
  return [a[0]! + (b[0]! - a[0]!) * k, a[1]! + (b[1]! - a[1]!) * k, a[2]! + (b[2]! - a[2]!) * k];
}

function boneRamp(t: number) {
  const u = Math.min(1, Math.max(0, t));
  if (u < 0.5) return lerp([18, 16, 13], [96, 84, 68], u / 0.5);
  return lerp([96, 84, 68], [239, 232, 220], (u - 0.5) / 0.5);
}

function lockColor(cover: Cover): number[] | null {
  if (cover === "metal") return [198, 161, 90];
  if (cover === "dielectric") return [138, 168, 144];
  if (cover === "fiber") return [214, 196, 164];
  return null;
}

function speckle(x: number, y: number, looks: number) {
  const L = Math.min(6, Math.max(1, Math.round(looks)));
  let s = 0;
  for (let k = 0; k < L; k++) s += -Math.log(Math.max(1e-4, hash(x + k * 3, y, 40 + k)));
  return s / L;
}

function drawRadar(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  props: SceneProps,
) {
  const epoch = epochForYear(props.year);
  const prior = new Float32Array(w * h);
  const covers: Cover[] = new Array(w * h);
  for (let y = 0; y < h; y++) {
    const ny = y / h;
    for (let x = 0; x < w; x++) {
      const c = coverAt(x / w, ny, props.showPhantom);
      const i = y * w + x;
      covers[i] = c;
      prior[i] = DB[c];
    }
  }

  const visualBlock = Math.max(1, Math.min(18, Math.round(epoch.resolutionM / 2.4)));
  const archive = new Float32Array(w * h);
  for (let by = 0; by < h; by += visualBlock) {
    for (let bx = 0; bx < w; bx += visualBlock) {
      let sum = 0;
      let n = 0;
      const y1 = Math.min(h, by + visualBlock);
      const x1 = Math.min(w, bx + visualBlock);
      for (let y = by; y < y1; y++) {
        for (let x = bx; x < x1; x++) {
          sum += prior[y * w + x]!;
          n++;
        }
      }
      const mean = sum / n;
      const mul = speckle(bx, by, epoch.looks);
      const speckDb = (mul - 1) * (2.1 / Math.sqrt(epoch.looks));
      const stripe =
        epoch.stripe * 2.4 * Math.sin((by / h) * Math.PI * 9) +
        epoch.stripe * (bx / w - 0.5) * 4;
      const value = mean + speckDb + stripe + epoch.biasDb;
      for (let y = by; y < y1; y++) {
        for (let x = bx; x < x1; x++) archive[y * w + x] = value;
      }
    }
  }

  const processed = new Float32Array(archive);
  if (props.reprocessed) {
    const rowMean = new Float32Array(h);
    let global = 0;
    for (let y = 0; y < h; y++) {
      let s = 0;
      for (let x = 0; x < w; x++) s += archive[y * w + x]!;
      rowMean[y] = s / w;
      global += rowMean[y]!;
    }
    global /= h;
    for (let y = 0; y < h; y++) {
      const delta = (rowMean[y]! - global) * Math.min(1, epoch.stripe + 0.35);
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        const ramp = epoch.stripe * (x / w - 0.5) * 4;
        processed[i] = archive[i]! - delta - ramp - epoch.biasDb;
      }
    }
    const blur = new Float32Array(processed);
    const rad = epoch.looks < 3 ? 2 : 1;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let s = 0;
        let n = 0;
        for (let dy = -rad; dy <= rad; dy++) {
          const yy = y + dy;
          if (yy < 0 || yy >= h) continue;
          for (let dx = -rad; dx <= rad; dx++) {
            const xx = x + dx;
            if (xx < 0 || xx >= w) continue;
            s += processed[yy * w + xx]!;
            n++;
          }
        }
        blur[y * w + x] = s / n;
      }
    }
    for (let i = 0; i < blur.length; i++) {
      processed[i] = blur[i]! * 0.62 + prior[i]! * 0.38;
    }
  }

  const image = ctx.createImageData(w, h);
  const wipeX = props.reprocessed ? Math.round(props.wipe * w) : w;
  const rx = props.reticle.x * w;
  const ry = props.reticle.y * h;
  const lockR = Math.max(18, Math.min(w, h) * 0.055);

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const db = x < wipeX ? archive[i]! : processed[i]!;
      const cover = covers[i]!;
      const lockedKind = lockColor(cover);
      const inReticle = (x - rx) ** 2 + (y - ry) ** 2 < lockR * lockR;
      const locked = props.chromalock && (lockedKind !== null || inReticle);
      let t = (db + 18) / 28;
      t = (t - 0.5) * props.contrast + 0.5;
      if (props.invert && !locked) t = 1 - t;
      const rgb = locked && lockedKind ? lockedKind : boneRamp(t);
      const o = i * 4;
      image.data[o] = rgb[0]!;
      image.data[o + 1] = rgb[1]!;
      image.data[o + 2] = rgb[2]!;
      image.data[o + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);

  ctx.save();
  ctx.strokeStyle = "rgba(198,161,90,0.9)";
  ctx.fillStyle = "rgba(239,232,220,0.92)";
  ctx.lineWidth = 1;
  ctx.font = "14px Atkinson Hyperlegible, sans-serif";

  if (props.reprocessed && wipeX > 8 && wipeX < w - 8) {
    ctx.beginPath();
    ctx.moveTo(wipeX + 0.5, 0);
    ctx.lineTo(wipeX + 0.5, h);
    ctx.stroke();
  }

  const model = modelById(props.modelId);
  if (model.ringsMi) {
    ctx.strokeStyle = "rgba(138,168,144,0.85)";
    const rings = [
      ["25", model.ringsMi.p25],
      ["50", model.ringsMi.p50],
      ["75", model.ringsMi.p75],
      ["95", model.ringsMi.p95],
    ] as const;
    for (const [label, miles] of rings) {
      ctx.beginPath();
      ctx.ellipse(
        IPP.x * w,
        IPP.y * h,
        (miles / WIDTH_MI) * w,
        (miles / HEIGHT_MI) * h,
        0,
        0,
        Math.PI * 2,
      );
      ctx.stroke();
      ctx.fillText(label, IPP.x * w + 6, IPP.y * h - (miles / HEIGHT_MI) * h - 4);
    }
  } else {
    ctx.strokeStyle = "rgba(138,168,144,0.95)";
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(0.522 * w, IPP.y * h);
    ctx.lineTo(0.522 * w, h - 16);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillText("stated direction, south on A1A", 12, h - 18);
    ctx.strokeStyle = "rgba(198,161,90,0.7)";
    ctx.strokeRect(4, 4, 0.2 * w, h - 8);
    ctx.strokeRect(0.8 * w, 4, w * 0.18, h - 8);
    ctx.fillText("river", 10, 18);
    ctx.fillText("surf", w - 42, 18);
  }

  function pin(nx: number, ny: number, label: string) {
    const px = nx * w;
    const py = ny * h;
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(198,161,90,1)";
    ctx.fill();
    ctx.fillStyle = "rgba(16,15,12,0.78)";
    const tw = ctx.measureText(label).width;
    ctx.fillRect(px + 8, py - 14, tw + 8, 16);
    ctx.fillStyle = "rgba(239,232,220,0.95)";
    ctx.fillText(label, px + 12, py - 2);
  }

  pin(IPP.x, IPP.y, "IPP  Osceola & A1A");
  pin(PIER.x, PIER.y, "Pier, frequented");
  if (props.showPhantom) pin(PHANTOM.x, PHANTOM.y, "Phantom");

  ctx.beginPath();
  ctx.arc(rx, ry, lockR, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(198,161,90,0.95)";
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(rx - 8, ry);
  ctx.lineTo(rx + 8, ry);
  ctx.moveTo(rx, ry - 8);
  ctx.lineTo(rx, ry + 8);
  ctx.stroke();
  ctx.restore();
}

function drawPhoto(ctx: CanvasRenderingContext2D, w: number, h: number, props: SceneProps) {
  const img = props.userImage;
  if (!img) return;
  ctx.drawImage(img, 0, 0, w, h);
  const src = ctx.getImageData(0, 0, w, h);
  const out = ctx.createImageData(w, h);
  const wipeX = Math.round(props.wipe * w);
  const rx = props.reticle.x * w;
  const ry = props.reticle.y * h;
  const lockR = Math.max(18, Math.min(w, h) * 0.06);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const o = (y * w + x) * 4;
      const r = src.data[o]!;
      const g = src.data[o + 1]!;
      const b = src.data[o + 2]!;
      if (x < wipeX) {
        out.data[o] = r;
        out.data[o + 1] = g;
        out.data[o + 2] = b;
        out.data[o + 3] = 255;
        continue;
      }
      const inReticle = (x - rx) ** 2 + (y - ry) ** 2 < lockR * lockR;
      const locked = props.chromalock && inReticle;
      let lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
      lum = (lum - 0.5) * props.contrast + 0.5;
      if (props.invert && !locked) lum = 1 - lum;
      const rgb = locked ? [r, g, b] : boneRamp(lum);
      out.data[o] = rgb[0]!;
      out.data[o + 1] = rgb[1]!;
      out.data[o + 2] = rgb[2]!;
      out.data[o + 3] = 255;
    }
  }
  ctx.putImageData(out, 0, 0);
  ctx.strokeStyle = "rgba(198,161,90,0.95)";
  ctx.beginPath();
  ctx.arc(rx, ry, lockR, 0, Math.PI * 2);
  ctx.stroke();
  if (wipeX > 8 && wipeX < w - 8) {
    ctx.beginPath();
    ctx.moveTo(wipeX + 0.5, 0);
    ctx.lineTo(wipeX + 0.5, h);
    ctx.stroke();
  }
}

export function SceneCanvas(props: SceneProps) {
  const imgRef = useRef<HTMLImageElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    const img = imgRef.current;
    if (!wrap || !img) return;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    const paint = () => {
      const cssW = Math.max(280, Math.floor(wrap.clientWidth));
      const cssH = Math.round(cssW * 1.15);
      const scale = Math.min(1, 640 / cssW);
      canvas.width = Math.max(1, Math.floor(cssW * scale));
      canvas.height = Math.max(1, Math.floor(cssH * scale));
      if (props.userImage) drawPhoto(ctx, canvas.width, canvas.height, props);
      else drawRadar(ctx, canvas.width, canvas.height, props);
      img.src = canvas.toDataURL("image/png");
      img.style.width = `${cssW}px`;
      img.style.height = `${cssH}px`;
    };
    paint();
    const obs = new ResizeObserver(paint);
    obs.observe(wrap);
    return () => obs.disconnect();
  }, [props]);

  return (
    <div ref={wrapRef} className="w-full">
      <img
        ref={imgRef}
        alt="Synthetic barrier-island sheet. Last seen is marked. The phantom is drawn for training and is not a find."
        className="block w-full rounded-md bg-surface-2"
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          props.onPlace({
            x: (e.clientX - r.left) / r.width,
            y: (e.clientY - r.top) / r.height,
          });
        }}
      />
    </div>
  );
}
