import { useEffect, useRef } from "react";

type Props = { removeRootball: boolean };

function gauss(i: number, j: number, ci: number, cj: number, s: number) {
  return Math.exp(-((i - ci) ** 2 + (j - cj) ** 2) / s);
}

function sample(i: number, j: number, removeRootball: boolean) {
  const dune = 0.22 * Math.sin(i * 0.33) + 0.12 * Math.cos(j * 0.27);
  const root = 0.9 * gauss(i, j, 30, 16, 16);
  const pit = -0.42 * gauss(i, j, 31, 21, 12);
  const dent = -0.2 * gauss(i, j, 14, 27, 9);
  if (removeRootball) return dune + pit + dent;
  return dune + root + pit + dent;
}

function colorFor(h: number, removeRootball: boolean) {
  if (removeRootball && h < -0.08) return [198, 161, 90];
  if (!removeRootball && h > 0.45) return [168, 148, 112];
  const t = Math.min(1, Math.max(0, (h + 0.45) / 1.3));
  const dark = [28, 25, 20];
  const light = [196, 184, 164];
  return [
    dark[0]! + (light[0]! - dark[0]!) * t,
    dark[1]! + (light[1]! - dark[1]!) * t,
    dark[2]! + (light[2]! - dark[2]!) * t,
  ];
}

export function MeshCanvas({ removeRootball }: Props) {
  const imgRef = useRef<HTMLImageElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    const img = imgRef.current;
    if (!wrap || !img) return;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const paint = () => {
      const cssW = Math.max(280, Math.floor(wrap.clientWidth));
      const cssH = Math.round(Math.max(320, cssW * 0.92));
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.floor(cssW * dpr);
      canvas.height = Math.floor(cssH * dpr);
      const w = canvas.width;
      const h = canvas.height;
      ctx.fillStyle = "#14120e";
      ctx.fillRect(0, 0, w, h);

      const N = 40;
      const scale = Math.min(w, h) / (N * 1.15);
      const ox = w * 0.52;
      const oy = h * 0.16;
      const project = (i: number, j: number, height: number) => {
        const x = (i - j) * Math.cos(Math.PI / 6) * scale;
        const y = (i + j) * Math.sin(Math.PI / 6) * scale - height * scale * 2.2;
        return [ox + x, oy + y] as const;
      };

      for (let j = 0; j < N - 1; j++) {
        for (let i = 0; i < N - 1; i++) {
          const h00 = sample(i, j, removeRootball);
          const h10 = sample(i + 1, j, removeRootball);
          const h01 = sample(i, j + 1, removeRootball);
          const h11 = sample(i + 1, j + 1, removeRootball);
          const p00 = project(i, j, h00);
          const p10 = project(i + 1, j, h10);
          const p11 = project(i + 1, j + 1, h11);
          const p01 = project(i, j + 1, h01);
          const avg = (h00 + h10 + h01 + h11) / 4;
          const c = colorFor(avg, removeRootball);
          ctx.beginPath();
          ctx.moveTo(p00[0], p00[1]);
          ctx.lineTo(p10[0], p10[1]);
          ctx.lineTo(p11[0], p11[1]);
          ctx.lineTo(p01[0], p01[1]);
          ctx.closePath();
          ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
          ctx.fill();
          ctx.strokeStyle = "rgba(16,15,12,0.35)";
          ctx.stroke();
        }
      }

      ctx.fillStyle = "#efe8dc";
      ctx.font = `${Math.round(13 * dpr)}px Atkinson Hyperlegible, sans-serif`;
      ctx.fillText(
        removeRootball ? "Rootball mesh removed · residual dents in brass" : "Rootball still on the surface",
        16 * dpr,
        h - 18 * dpr,
      );
      img.src = canvas.toDataURL("image/png");
      img.style.width = `${cssW}px`;
      img.style.height = `${cssH}px`;
    };

    paint();
    const obs = new ResizeObserver(paint);
    obs.observe(wrap);
    return () => obs.disconnect();
  }, [removeRootball]);

  return (
    <div ref={wrapRef} className="w-full">
      <img
        ref={imgRef}
        alt="Synthetic dune mesh. Removing the rootball leaves residual dents. The dents are training geometry, not a grave."
        className="block w-full rounded-md bg-surface-2"
      />
    </div>
  );
}
