import { useEffect, useMemo, useRef, useState } from "react";
import {
  Aperture,
  BookOpen,
  Compass,
  Eye,
  Layers,
  Mountain,
  Waves,
} from "lucide-react";
import { CASE, LANES } from "@/lib/forensic/case";
import { YEAR_PRESETS, epochForYear } from "@/lib/forensic/epochs";
import { CACHES, SUBJECT_MODELS, cacheById, modelById } from "@/lib/forensic/models";
import {
  MATERIALS,
  SENSOR_LABEL,
  VERDICT_LABEL,
  callsFor,
  materialById,
  waveReport,
  type SensorId,
  type Surface,
} from "@/lib/forensic/physics";
import { MeshCanvas } from "@/components/mesh-canvas";
import { RoadPane } from "@/components/road-pane";
import { SceneCanvas } from "@/components/scene-canvas";

type Mode = "file" | "reprocess" | "waves" | "models" | "mesh" | "lanes" | "road";

const INTAKES = [
  {
    id: "sar",
    name: "SAR strip",
    path: "Apply the year kernel, then stop at gamma-nought. A cell bigger than the object is the end of the claim.",
  },
  {
    id: "gpr",
    name: "GPR line",
    path: "Do not run it through the SAR kernel. Read velocity, salt, and target size on the wave desk.",
  },
  {
    id: "lidar",
    name: "LiDAR cloud",
    path: "Classify ground, subtract rootballs, read residual relief. That is the mesh view.",
  },
  {
    id: "vhr",
    name: "Aerial photo",
    path: "Contrast, invert, chromalock. Illumination only. No radiometry is invented.",
  },
  {
    id: "plat",
    name: "Paper grid",
    path: "A 1970s drawing is not a score layer. Do not upscale it into bone, teeth, or metal.",
  },
  {
    id: "gpx",
    name: "Field track",
    path: "A GPX shows where a person walked. It is not a sensor return.",
  },
] as const;

const MODES: { id: Mode; label: string; icon: typeof Aperture }[] = [
  { id: "file", label: "File", icon: BookOpen },
  { id: "reprocess", label: "Reprocess", icon: Aperture },
  { id: "waves", label: "Waves", icon: Waves },
  { id: "models", label: "Models", icon: Compass },
  { id: "mesh", label: "Mesh", icon: Mountain },
  { id: "lanes", label: "Open water", icon: Layers },
  { id: "road", label: "Road sight", icon: Eye },
];

const STORE = "forensicfinders.desk.v1";

const SENSOR_ORDER: SensorId[] = ["sar", "lidar", "gpr", "vhr", "mag", "pi"];

export function Workbench() {
  const [mode, setMode] = useState<Mode>("reprocess");
  const [year, setYear] = useState(1977);
  const [reprocessed, setReprocessed] = useState(false);
  const [wipe, setWipe] = useState(0.52);
  const [contrast, setContrast] = useState(1.2);
  const [invert, setInvert] = useState(false);
  const [chromalock, setChromalock] = useState(true);
  const [showPhantom, setShowPhantom] = useState(true);
  const [surface, setSurface] = useState<Surface>("dry");
  const [modelId, setModelId] = useState("abduction");
  const [cacheId, setCacheId] = useState("dune");
  const [materialId, setMaterialId] = useState("gold-horn");
  const [mhz, setMhz] = useState(500);
  const [removeRoot, setRemoveRoot] = useState(true);
  const [intake, setIntake] = useState<(typeof INTAKES)[number]["id"]>("sar");
  const [note, setNote] = useState("");
  const [reticle, setReticle] = useState({ x: 0.37, y: 0.66 });
  const [userImage, setUserImage] = useState<HTMLImageElement | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORE);
      if (!raw) return;
      const s = JSON.parse(raw) as Partial<{
        year: number;
        mode: Mode;
        contrast: number;
        invert: boolean;
        chromalock: boolean;
        showPhantom: boolean;
        surface: Surface;
        modelId: string;
        cacheId: string;
        materialId: string;
        mhz: number;
        removeRoot: boolean;
        note: string;
        intake: (typeof INTAKES)[number]["id"];
      }>;
      if (typeof s.year === "number") setYear(s.year);
      if (s.mode) setMode(s.mode);
      if (typeof s.contrast === "number") setContrast(s.contrast);
      if (typeof s.invert === "boolean") setInvert(s.invert);
      if (typeof s.chromalock === "boolean") setChromalock(s.chromalock);
      if (typeof s.showPhantom === "boolean") setShowPhantom(s.showPhantom);
      if (s.surface) setSurface(s.surface);
      if (s.modelId) setModelId(s.modelId);
      if (s.cacheId) setCacheId(s.cacheId);
      if (s.materialId) setMaterialId(s.materialId);
      if (typeof s.mhz === "number") setMhz(s.mhz);
      if (typeof s.removeRoot === "boolean") setRemoveRoot(s.removeRoot);
      if (typeof s.note === "string") setNote(s.note);
      if (s.intake) setIntake(s.intake);
    } catch {
      /* keep defaults */
    }
  }, []);

  useEffect(() => {
    const payload = {
      year,
      mode,
      contrast,
      invert,
      chromalock,
      showPhantom,
      surface,
      modelId,
      cacheId,
      materialId,
      mhz,
      removeRoot,
      note,
      intake,
    };
    localStorage.setItem(STORE, JSON.stringify(payload));
  }, [
    year,
    mode,
    contrast,
    invert,
    chromalock,
    showPhantom,
    surface,
    modelId,
    cacheId,
    materialId,
    mhz,
    removeRoot,
    note,
    intake,
  ]);

  const epoch = epochForYear(year);
  const material = materialById(materialId);
  const report = waveReport(mhz, materialId, surface);
  const calls = callsFor(materialId, surface, epoch.resolutionM);
  const model = modelById(modelId);
  const cache = cacheById(cacheId);
  const intakeRow = INTAKES.find((i) => i.id === intake) ?? INTAKES[0];

  const task = useMemo(() => {
    if (year <= 1977) {
      return "No street-scale SAR of this afternoon exists to reprocess. Seasat flew in 1978. A new line is the only instrument, and only where the card says so.";
    }
    const viable = SENSOR_ORDER.filter((id) => calls[id].verdict === "survey");
    if (viable.length === 0) {
      return "Nothing in this stack can see the selected artifact under the selected ground. Change the ground, or stop.";
    }
    return `If you spend money, spend it on ${viable.map((id) => SENSOR_LABEL[id]).join(" and ")}. Not on stretching the ${year} archive.`;
  }, [year, calls]);

  function loadStill(file: File | undefined) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      setUserImage(img);
      setReprocessed(true);
      setWipe(0.5);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }

  function nudge(dx: number, dy: number) {
    setReticle((p) => ({
      x: Math.min(0.96, Math.max(0.04, p.x + dx)),
      y: Math.min(0.96, Math.max(0.04, p.y + dy)),
    }));
  }

  return (
    <main className="min-h-screen bg-bg text-fg">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-4">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-surface text-brass">
              <Aperture className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <p className="eyebrow">Cold-case illumination</p>
              <h1 className="display text-3xl text-fg">Forensicfinders</h1>
            </div>
          </div>
          <p className="text-sm text-muted">
            {CASE.name} · {CASE.missing} · Cocoa Beach
          </p>
        </header>

        <p className="panel px-4 py-3 text-sm text-muted">
          Planning instrument for raw SAR, LiDAR, GPR, photos, and paper grids.
          It does not detect remains, and it does not write a find into a GPS or a drone file.
          The phantom on the sheet is drawn so the operators can be seen.
        </p>

        <nav className="flex gap-2 overflow-x-auto pb-1" aria-label="Desk sections">
          {MODES.map((item) => {
            const Icon = item.icon;
            const on = mode === item.id;
            return (
              <button
                key={item.id}
                type="button"
                aria-pressed={on}
                onClick={() => setMode(item.id)}
                className={`flex min-h-11 shrink-0 items-center gap-2 rounded-md px-3 text-sm ${
                  on ? "bg-brass text-brass-ink" : "bg-surface text-fg"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {mode === "file" && <FilePane note={note} setNote={setNote} />}

        {mode === "reprocess" && (
          <section className="grid gap-4 lg:grid-cols-5">
            <div className="panel p-3 lg:col-span-3">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <p className="eyebrow">{userImage ? "Your still" : "Synthetic island sheet"}</p>
                <p className="text-sm text-muted">
                  {userImage
                    ? "Left is the still. Right is illumination only."
                    : reprocessed
                      ? `Left is ${year}. Right is the 2026 standard.`
                      : `${year} archive. Not yet pulled to the current standard.`}
                </p>
              </div>
              <SceneCanvas
                year={year}
                reprocessed={reprocessed || Boolean(userImage)}
                wipe={wipe}
                contrast={contrast}
                invert={invert}
                chromalock={chromalock}
                showPhantom={showPhantom && !userImage}
                modelId={modelId}
                reticle={reticle}
                userImage={userImage}
                onPlace={setReticle}
              />
              <p className="mt-3 text-sm text-muted">
                Cells are drawn large enough to see. The real posting is {epoch.resolutionM} m.
                Tap the sheet to park the chromalock reticle. IPP is the published last-seen corner, not a recovery.
              </p>
            </div>
            <div className="flex flex-col gap-3 lg:col-span-2">
              <div className="panel flex flex-col gap-3 p-4">
                <label className="flex flex-col gap-2 text-sm">
                  <span className="flex items-center justify-between">
                    <span>Acquisition year</span>
                    <span className="text-brass">{year}</span>
                  </span>
                  <input
                    type="range"
                    min={1960}
                    max={2026}
                    value={year}
                    onChange={(e) => {
                      setYear(Number(e.target.value));
                      setReprocessed(false);
                    }}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  {YEAR_PRESETS.map((p) => (
                    <button
                      key={p.year}
                      type="button"
                      className="min-h-11 rounded-md bg-surface-2 px-3 text-sm text-fg"
                      onClick={() => {
                        setYear(p.year);
                        setReprocessed(false);
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="min-h-11 rounded-md bg-brass px-3 text-sm text-brass-ink"
                  onClick={() => {
                    setReprocessed(true);
                    setWipe(0.48);
                  }}
                >
                  Reprocess {year} to the 2026 standard
                </button>
                {reprocessed && (
                  <label className="flex flex-col gap-2 text-sm">
                    <span>Wipe</span>
                    <input
                      type="range"
                      min={0.05}
                      max={0.95}
                      step={0.01}
                      value={wipe}
                      onChange={(e) => setWipe(Number(e.target.value))}
                    />
                  </label>
                )}
              </div>

              <div className="panel flex flex-col gap-3 p-4">
                <p className="eyebrow">Illuminate</p>
                <label className="flex flex-col gap-2 text-sm">
                  <span className="flex justify-between">
                    Contrast <span className="text-muted">{contrast.toFixed(2)}</span>
                  </span>
                  <input
                    type="range"
                    min={0.6}
                    max={2.4}
                    step={0.05}
                    value={contrast}
                    onChange={(e) => setContrast(Number(e.target.value))}
                  />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Toggle on={invert} label="Invert ground" set={setInvert} />
                  <Toggle on={chromalock} label="Chromalock" set={setChromalock} />
                  <Toggle on={showPhantom} label="Show phantom" set={setShowPhantom} />
                  <button
                    type="button"
                    className="min-h-11 rounded-md bg-surface-2 px-3 text-sm text-fg"
                    onClick={() => fileRef.current?.click()}
                  >
                    Load a still
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => loadStill(e.target.files?.[0])}
                  />
                </div>
                {userImage && (
                  <button
                    type="button"
                    className="min-h-11 rounded-md bg-surface-2 px-3 text-sm"
                    onClick={() => setUserImage(null)}
                  >
                    Return to the island sheet
                  </button>
                )}
                <div className="flex gap-2">
                  <Nudge label="N" onClick={() => nudge(0, -0.02)} />
                  <Nudge label="E" onClick={() => nudge(0.02, 0)} />
                  <Nudge label="S" onClick={() => nudge(0, 0.02)} />
                  <Nudge label="W" onClick={() => nudge(-0.02, 0)} />
                </div>
                <p className="text-sm text-muted">
                  Invert is I′ = 1 − I outside the reticle. Inside it, and on the phantom, the color stays.
                </p>
              </div>

              <div className="panel flex flex-col gap-2 p-4">
                <p className="eyebrow">{epoch.name}</p>
                <p className="text-sm">
                  {epoch.platform}. {epoch.band}. {epoch.wavelengthCm} cm. {epoch.polarization}.
                </p>
                <p className="text-sm text-muted">{epoch.calibration}</p>
                <p className="text-sm text-fg">{epoch.archiveNote}</p>
                <ol className="list-decimal pl-4 text-sm text-muted">
                  {epoch.kernel.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
            </div>
          </section>
        )}

        {mode === "waves" && (
          <section className="grid gap-4 lg:grid-cols-5">
            <div className="panel p-4 lg:col-span-3">
              <p className="eyebrow">What can actually return</p>
              <h2 className="display mt-2 text-2xl">{material.name}</h2>
              <p className="mt-2 text-sm text-muted">{material.note}</p>
              <p className="mt-3 text-sm">{task}</p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-muted">
                    <tr>
                      <th className="py-2 pr-3 font-normal">Sensor</th>
                      <th className="py-2 pr-3 font-normal">Call</th>
                      <th className="py-2 font-normal">Why</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SENSOR_ORDER.map((id) => (
                      <tr key={id} className="border-t border-line align-top">
                        <td className="py-3 pr-3">{SENSOR_LABEL[id]}</td>
                        <td className="py-3 pr-3 text-brass">{VERDICT_LABEL[calls[id].verdict]}</td>
                        <td className="py-3 text-muted">{calls[id].why}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="flex flex-col gap-3 lg:col-span-2">
              <div className="panel flex flex-col gap-3 p-4">
                <label className="flex flex-col gap-2 text-sm">
                  Artifact
                  <select
                    value={materialId}
                    onChange={(e) => setMaterialId(e.target.value)}
                    className="min-h-11 rounded-md bg-surface-2 px-2"
                  >
                    {MATERIALS.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="text-sm text-muted">Size: {material.sizeCm}</p>
                <div className="grid grid-cols-3 gap-2">
                  {(
                    [
                      ["dry", "Dry dune"],
                      ["wet", "Wet sand"],
                      ["muck", "Muck"],
                    ] as const
                  ).map(([id, label]) => (
                    <button
                      key={id}
                      type="button"
                      aria-pressed={surface === id}
                      onClick={() => setSurface(id)}
                      className={`min-h-11 rounded-md px-2 text-sm ${
                        surface === id ? "bg-brass text-brass-ink" : "bg-surface-2 text-fg"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <label className="flex flex-col gap-2 text-sm">
                  <span className="flex justify-between">
                    GPR frequency <span className="text-brass">{mhz} MHz</span>
                  </span>
                  <input
                    type="range"
                    min={100}
                    max={1500}
                    step={50}
                    value={mhz}
                    onChange={(e) => setMhz(Number(e.target.value))}
                  />
                </label>
              </div>
              <div className="panel flex flex-col gap-2 p-4 text-sm">
                <p className="eyebrow">In the ground</p>
                <p>The wave travels in the sand, not in the object. v = ω / β, with α and β from εr and σ.</p>
                <p>Round trip to depth z loses 2 × (8.686 α) × z decibels. The 40 dB line is a chosen fade, not a law.</p>
                <p>A flat interface reflects R = (√ε₂ − √ε₁) / (√ε₂ + √ε₁). Power is R². Metal is the R = −1 limit.</p>
                <p className="text-muted">
                  Host εr {report.epsHost}, assumed σ {report.sigma} S/m. Phase velocity{" "}
                  {(report.wave.vPhase / 1e6).toFixed(1)} m/µs. Wavelength{" "}
                  {(report.wave.lambdaM * 100).toFixed(1)} cm. If bandwidth equals the center frequency, range
                  resolution is {(report.wave.rangeResM * 100).toFixed(1)} cm.
                </p>
                <p className="text-muted">
                  Loss tangent {report.wave.lossTangent.toFixed(3)}. One-way {report.wave.dbPerM.toFixed(2)} dB/m.
                  Two-way 40 dB at{" "}
                  {report.wave.fadeDepthM > 1000
                    ? "more than a kilometre"
                    : `${report.wave.fadeDepthM.toFixed(2)} m`}
                  .{" "}
                  {report.wave.fadeDepthM < 1
                    ? "Past that depth the wave is gone. A missing echo is not a clear bill of health."
                    : "Here the limit is contrast and size, not the fade depth. None of these numbers is a detection."}
                </p>
                {report.refl ? (
                  <p className="text-muted">
                    {report.refl.pec
                      ? "Perfect-conductor limit: all of the power that arrives can reflect. The wave still has to arrive, and a 3 cm horn is not a flat wall."
                      : `Interface power reflection ${(report.refl.power * 100).toFixed(2)}% (R = ${report.refl.amplitude.toFixed(3)}). A small number means the object and the sand look alike.`}
                  </p>
                ) : (
                  <p className="text-muted">This row is the host. It sets speed and loss. It is not a target.</p>
                )}
                {report.small && report.sizeM != null ? (
                  <p>
                    Characteristic size {(report.sizeM * 100).toFixed(1)} cm is under λ/10. The echo of an
                    electrically small object is weak even when R is not.
                  </p>
                ) : null}
              </div>
              <div className="panel p-4 text-sm">
                <p className="eyebrow">Record in hand</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {INTAKES.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      aria-pressed={intake === item.id}
                      onClick={() => setIntake(item.id)}
                      className={`min-h-11 rounded-md px-3 text-sm ${
                        intake === item.id ? "bg-celadon text-celadon-ink" : "bg-surface-2 text-fg"
                      }`}
                    >
                      {item.name}
                    </button>
                  ))}
                </div>
                <p className="mt-3 text-muted">{intakeRow.path}</p>
              </div>
            </div>
          </section>
        )}

        {mode === "models" && (
          <section className="grid gap-4 lg:grid-cols-2">
            <div className="panel flex flex-col gap-3 p-4">
              <p className="eyebrow">Lost-person rings, and the refusal</p>
              <p className="text-sm text-muted">
                ISRID is the field database behind lost-person behavior. Public writeups describe on the order of
                forty categories; some desks brief a wider set of variants. Distances here are rounded teaching
                figures, not an ISRID export. Confirm a current pull before a real mission.
              </p>
              <div className="flex flex-col gap-2">
                {SUBJECT_MODELS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    aria-pressed={modelId === item.id}
                    onClick={() => setModelId(item.id)}
                    className={`min-h-11 rounded-md px-3 text-left text-sm ${
                      modelId === item.id ? "bg-brass text-brass-ink" : "bg-surface-2 text-fg"
                    }`}
                  >
                    {item.name}
                    {item.useOnFleming === "no" ? " · do not brief on this file" : ""}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-3">
              <div className="panel p-4">
                <h2 className="display text-2xl">{model.name}</h2>
                <p className="mt-2 text-sm">{model.caution}</p>
                {model.ringsMi ? (
                  <p className="mt-3 text-sm text-muted">
                    Teaching rings, miles: 25% {model.ringsMi.p25} · 50% {model.ringsMi.p50} · 75%{" "}
                    {model.ringsMi.p75} · 95% {model.ringsMi.p95}. Switch to Reprocess to see them on the sheet.
                  </p>
                ) : (
                  <p className="mt-3 text-sm text-muted">
                    No ring. The sheet draws the stated southbound direction, the river edge, and the surf edge.
                  </p>
                )}
                <ul className="mt-3 list-disc pl-4 text-sm text-muted">
                  {model.behavior.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
              <div className="panel p-4">
                <p className="eyebrow">Suitcase and cache desk</p>
                <label className="mt-3 flex flex-col gap-2 text-sm">
                  Concealment
                  <select
                    value={cacheId}
                    onChange={(e) => setCacheId(e.target.value)}
                    className="min-h-11 rounded-md bg-surface-2 px-2"
                  >
                    {CACHES.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </label>
                <h2 className="display mt-3 text-xl">{cache.name}</h2>
                <p className="mt-1 text-sm text-muted">{cache.where}</p>
                <dl className="mt-3 flex flex-col gap-2 text-sm">
                  <div>
                    <dt className="text-brass">SAR</dt>
                    <dd>{cache.sar}</dd>
                  </div>
                  <div>
                    <dt className="text-brass">LiDAR</dt>
                    <dd>{cache.lidar}</dd>
                  </div>
                  <div>
                    <dt className="text-brass">GPR</dt>
                    <dd>{cache.gpr}</dd>
                  </div>
                  <div>
                    <dt className="text-brass">Metal</dt>
                    <dd>{cache.metal}</dd>
                  </div>
                  <div>
                    <dt className="text-brass">On this island</dt>
                    <dd>{cache.island}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </section>
        )}

        {mode === "mesh" && (
          <section className="grid gap-4 lg:grid-cols-5">
            <div className="panel p-3 lg:col-span-3">
              <MeshCanvas removeRootball={removeRoot} />
            </div>
            <div className="panel flex flex-col gap-3 p-4 lg:col-span-2">
              <p className="eyebrow">Rootball residual</p>
              <h2 className="display text-2xl">See the dent, not a story</h2>
              <p className="text-sm text-muted">
                Forestry clouds already treat a tipped-tree rootball as a false hill. Subtract that mesh. The pit
                under it, and any smaller dent in the same patch, is what remains. Hurricanes move this island.
                A dent without a date is weather.
              </p>
              <button
                type="button"
                aria-pressed={removeRoot}
                onClick={() => setRemoveRoot((v) => !v)}
                className="min-h-11 rounded-md bg-brass px-3 text-sm text-brass-ink"
              >
                {removeRoot ? "Rootball removed" : "Put the rootball back"}
              </button>
              <ul className="list-disc pl-4 text-sm text-muted">
                <li>Synthetic rootball, about 0.9 m of false ground.</li>
                <li>Pit under it, about 0.4 m.</li>
                <li>Smaller residual dent, about 0.2 m, drawn so you can see a second shape survive the subtract.</li>
              </ul>
              <p className="text-sm">
                A settled hole of this size can be a rootball pit, a lot grade, or a storm. It is not a burial
                until someone digs it with the agency of record.
              </p>
            </div>
          </section>
        )}

        {mode === "road" && <RoadPane />}

        {mode === "lanes" && (
          <section className="grid gap-3 md:grid-cols-2">
            {LANES.map((lane) => (
              <article key={lane.id} className="panel flex flex-col gap-2 p-4">
                <p className="eyebrow">Open water</p>
                <h2 className="display text-2xl">{lane.title}</h2>
                <p className="text-sm">{lane.gap}</p>
                <p className="text-sm text-muted">Who pays: {lane.who}</p>
                <p className="text-sm text-celadon">On this desk: {lane.here}</p>
              </article>
            ))}
            <article className="panel flex flex-col gap-2 p-4 md:col-span-2">
              <p className="eyebrow">What was not compiled</p>
              <p className="text-sm">
                A script that turns sine of latitude into a bone score, a dental score, and a metal score, then
                writes those numbers into a Garmin file and a drone mission, is not a multi-sensor detection.
                The weather address in that script is not an ERA5 endpoint. The soil flag it reads is not the
                flag it sets. No house is plotted here. No waypoint is stamped with an anomaly. Leads go to the
                numbers on the file tab.
              </p>
            </article>
          </section>
        )}
      </div>
    </main>
  );
}

function Toggle({
  on,
  label,
  set,
}: {
  on: boolean;
  label: string;
  set: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={() => set(!on)}
      className={`min-h-11 rounded-md px-3 text-sm ${on ? "bg-celadon text-celadon-ink" : "bg-surface-2 text-fg"}`}
    >
      {label}
    </button>
  );
}

function Nudge({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-11 w-11 items-center justify-center rounded-md bg-surface-2 text-sm"
      aria-label={`Nudge reticle ${label}`}
    >
      {label}
    </button>
  );
}

function FilePane({ note, setNote }: { note: string; setNote: (v: string) => void }) {
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="panel flex flex-col gap-4 p-4 lg:col-span-2">
        <div>
          <p className="eyebrow">{CASE.short}</p>
          <h2 className="display mt-1 text-3xl">{CASE.name}</h2>
          <p className="mt-2 text-sm text-muted">
            {CASE.missing} · age {CASE.age} · born {CASE.born} · {CASE.from}
          </p>
          <p className="mt-1 text-sm text-muted">{CASE.stature}</p>
          <p className="mt-2 text-sm">{CASE.class}</p>
        </div>
        <div>
          <p className="eyebrow">Last seen, as publicly reported</p>
          <ul className="mt-2 list-disc pl-4 text-sm">
            {CASE.narrative.map((line) => (
              <li key={line} className="mt-1">
                {line}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="eyebrow">What a sensor would be asked about</p>
          <ul className="mt-2 list-disc pl-4 text-sm text-muted">
            {CASE.body.map((line) => (
              <li key={line}>{line}</li>
            ))}
            {CASE.worn.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-muted">{CASE.suspect}</p>
        <label className="flex flex-col gap-2 text-sm">
          Desk note, kept on this browser only
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={4}
            className="rounded-md bg-surface-2 p-3 text-fg"
            placeholder="Questions for the agency. Not a find log."
          />
        </label>
      </div>
      <aside className="flex flex-col gap-3">
        <div className="panel p-4">
          <p className="eyebrow">If you know something</p>
          <ul className="mt-3 flex flex-col gap-3 text-sm">
            {CASE.contacts.map((c) => (
              <li key={c.phone}>
                <p>{c.name}</p>
                <a className="text-brass" href={`tel:${c.phone.replace(/[^\d+]/g, "")}`}>
                  {c.phone}
                </a>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel p-4 text-sm">
          <p className="eyebrow">Numbers, as published</p>
          <ul className="mt-2">
            {CASE.numbers.map((n) => (
              <li key={n.label}>
                {n.label} {n.value}
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </section>
  );
}
