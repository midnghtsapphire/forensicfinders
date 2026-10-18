export type Surface = "dry" | "wet" | "muck";

export type Material = {
  id: string;
  name: string;
  kind: "metal" | "bone" | "fiber" | "ceramic" | "host";
  sizeCm: string;
  /** Characteristic size for the λ/10 scatter test. Not a measured dimension. */
  sizeM?: number;
  eps: Record<Surface, number>;
  note: string;
  lock: "brass" | "celadon" | "bone";
};

/** Textbook bands, moisture-dominated. Not a lab certificate. */
export const MATERIALS: Material[] = [
  {
    id: "gold-horn",
    name: "Gold Italian horn",
    kind: "metal",
    sizeCm: "about 3–4 cm, non-ferrous",
    sizeM: 0.035,
    eps: { dry: 1, wet: 1, muck: 1 },
    note: "A conductor. GPR may ring if the loop is large enough and shallow. A magnetometer will not see gold. Salt spray on a Florida beach blinds most VLF coils; a pulse-induction coil is the less-wrong choice, and only in the top of dry sand.",
    lock: "brass",
  },
  {
    id: "eyelets",
    name: "Ferrous garment hardware",
    kind: "metal",
    sizeCm: "rivets, millimeters",
    sizeM: 0.006,
    eps: { dry: 1, wet: 1, muck: 1 },
    note: "Jeans can carry steel rivets. That is a maybe, not an inventory. A magnetometer can hear a cluster of ferrous bits in dry sand and goes quiet in salt-wet ground. SAR does not resolve them.",
    lock: "brass",
  },
  {
    id: "dental",
    name: "Upper dental partial",
    kind: "ceramic",
    sizeCm: "about 2 cm across the front teeth",
    sizeM: 0.02,
    eps: { dry: 6, wet: 12, muck: 18 },
    note: "Acrylic or ceramic in a small plate. Dielectric contrast against dry sand is modest. Only a high-frequency GPR pass, centimeters from the antenna, has a physical chance — and salt water removes that chance.",
    lock: "celadon",
  },
  {
    id: "bone",
    name: "Bone, if skeletal",
    kind: "bone",
    sizeCm: "limb scale, decimeters, if present",
    sizeM: 0.15,
    eps: { dry: 10, wet: 22, muck: 30 },
    note: "Dry cortical bone can differ from dry sand. Wet bone often matches wet sand, and the contrast collapses. No orbital radar identifies calcium. GPR contrast is a soil-moisture question, not a chemical assay.",
    lock: "celadon",
  },
  {
    id: "fiber",
    name: "Cotton shirt and denim",
    kind: "fiber",
    sizeCm: "garment scale, collapses when wet",
    sizeM: 0.2,
    eps: { dry: 2.2, wet: 20, muck: 28 },
    note: "Fiber is invisible to SAR, LiDAR, and ordinary GPR once it is buried or decayed. Color and weave are excavation facts. Remote sensing does not recover a Thirsty Turtle print.",
    lock: "bone",
  },
  {
    id: "sand",
    name: "Host sand",
    kind: "host",
    sizeCm: "the ground itself",
    eps: { dry: 4, wet: 20, muck: 35 },
    note: "Cocoa Beach sand is quartz, salt, and shell. Dry dunes are easy to dig and poor electrical contrast. The beach face sits in a saltwater wedge that soaks GPR energy within a few tens of centimeters.",
    lock: "bone",
  },
];

export type SensorId = "sar" | "lidar" | "gpr" | "vhr" | "mag" | "pi";

export type Verdict = "none" | "unlikely" | "survey" | "proxy";

export type SensorCall = { verdict: Verdict; why: string };

const C = 299_792_458;
const MU0 = 1.25663706212e-6;
const EPS0 = 1 / (MU0 * C * C);
const EARTH_M = 6_371_008.8;
const NP_TO_DB = 20 / Math.log(10);

/**
 * Order-of-magnitude conductivity. Not a sample from Cocoa Beach or the moor.
 * Dry quartz sand ~1 mS/m, moist sand ~20 mS/m, saline fill ~0.5 S/m.
 * Seawater itself is near 4 S/m, so a real salt wedge can be worse than "muck".
 */
export const SIGMA_S_PER_M: Record<Surface, number> = {
  dry: 0.001,
  wet: 0.02,
  muck: 0.5,
};

/** Uniform plane wave in a non-magnetic conducting dielectric. α and β are exact for that model. */
export function planeWave(mhz: number, epsR: number, sigma: number) {
  const f = Math.max(1, mhz) * 1e6;
  const omega = 2 * Math.PI * f;
  const eps = Math.max(epsR, 1) * EPS0;
  const lossTangent = sigma / (omega * eps);
  const disc = Math.sqrt(1 + lossTangent * lossTangent);
  const alpha = omega * Math.sqrt((MU0 * eps * (disc - 1)) / 2);
  const beta = omega * Math.sqrt((MU0 * eps * (disc + 1)) / 2);
  const vPhase = omega / beta;
  const lambdaM = (2 * Math.PI) / beta;
  const dbPerM = NP_TO_DB * alpha;
  const twoWayDbPerM = 2 * dbPerM;
  const fadeDb = 40;
  const fadeDepthM = twoWayDbPerM > 1e-9 ? fadeDb / twoWayDbPerM : Number.POSITIVE_INFINITY;
  const rangeResM = vPhase / (2 * f);
  return {
    epsR,
    sigma,
    lossTangent,
    vPhase,
    lambdaM,
    alpha,
    dbPerM,
    twoWayDbPerM,
    fadeDb,
    fadeDepthM,
    rangeResM,
  };
}

/** Normal-incidence amplitude reflection. Power fraction is R². Metal uses the perfect-conductor limit. */
export function reflection(epsHost: number, epsTarget: number, pec: boolean) {
  if (pec) return { amplitude: -1, power: 1, pec: true as const };
  const n1 = Math.sqrt(Math.max(epsHost, 1));
  const n2 = Math.sqrt(Math.max(epsTarget, 1));
  const amplitude = (n2 - n1) / (n2 + n1);
  return { amplitude, power: amplitude * amplitude, pec: false as const };
}

/** Distance to the smooth-earth horizon. k = 1 is geometry; k = 4/3 is the usual refraction allowance. */
export function horizonM(eyeM: number, k = 1) {
  const radius = EARTH_M * k;
  const h = Math.max(0, eyeM);
  return Math.sqrt(2 * radius * h + h * h);
}

/** Great-circle distance on the IUGG mean sphere. Not a location. */
export function haversineM(lat1: number, lon1: number, lat2: number, lon2: number) {
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const dp = ((lat2 - lat1) * Math.PI) / 180;
  const dl = ((lon2 - lon1) * Math.PI) / 180;
  const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * EARTH_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function gprNumbers(mhz: number, eps: number) {
  const wave = planeWave(mhz, eps, 0);
  return {
    velocityMps: wave.vPhase,
    lambdaCm: wave.lambdaM * 100,
    depthResCm: wave.rangeResM * 100,
  };
}

export function waveReport(mhz: number, materialId: string, surface: Surface) {
  const host = materialById("sand");
  const target = materialById(materialId);
  const epsHost = host.eps[surface];
  const wave = planeWave(mhz, epsHost, SIGMA_S_PER_M[surface]);
  const isHost = target.kind === "host";
  const refl = isHost ? null : reflection(epsHost, target.eps[surface], target.kind === "metal");
  const small =
    target.sizeM != null && Number.isFinite(wave.lambdaM) && target.sizeM < wave.lambdaM / 10;
  return { epsHost, sigma: SIGMA_S_PER_M[surface], wave, refl, small, sizeM: target.sizeM ?? null };
}

export function materialById(id: string): Material {
  return MATERIALS.find((m) => m.id === id) ?? MATERIALS[0]!;
}

export function callsFor(
  materialId: string,
  surface: Surface,
  resolutionM: number,
): Record<SensorId, SensorCall> {
  const m = materialById(materialId);
  const salt = surface !== "dry";
  const tiny = m.kind !== "host";

  const sar: SensorCall =
    resolutionM > 5 || tiny
      ? {
          verdict: "none",
          why: `Cell is about ${resolutionM} m. A ${m.sizeCm} object does not occupy it. Radar sees roughness of the island, not this artifact.`,
        }
      : {
          verdict: "unlikely",
          why: "Spotlight posting is fine enough for a vehicle or a pier pile, still coarse for this object.",
        };

  const lidar: SensorCall =
    m.kind === "bone" || m.kind === "host"
      ? {
          verdict: "proxy",
          why: "LiDAR sees the surface, not the object. A residual dent after rootball removal is a place to ask a question, not a burial.",
        }
      : {
          verdict: "none",
          why: "A bare-earth mesh will not carry a pendant, a plate, or cloth.",
        };

  let gpr: SensorCall;
  if (m.kind === "fiber") {
    gpr = { verdict: "none", why: "Cloth does not make a stable GPR reflection once wet." };
  } else if (m.kind === "metal") {
    gpr = salt
      ? { verdict: "unlikely", why: "Salt water attenuates the wave before a small metal object can ring." }
      : { verdict: "survey", why: "Shallow metal in dry sand can ring. Confirm with a coil, not with the radar image alone." };
  } else if (salt) {
    gpr = {
      verdict: "unlikely",
      why: "Wet or mucky salt sand drops contrast and range together. Move the line up the dune, off the swash.",
    };
  } else if (m.kind === "ceramic" || m.kind === "bone") {
    gpr = {
      verdict: "survey",
      why: "Possible only as a new, slow, high-frequency survey in dry sand. Not recoverable from an old airborne file.",
    };
  } else {
    gpr = { verdict: "proxy", why: "The host medium sets velocity. It is not itself a target." };
  }

  const vhr: SensorCall = {
    verdict: m.kind === "host" ? "proxy" : "none",
    why:
      m.kind === "host"
        ? "Aerial photos show paths, lots, and dune cuts. They do not show a buried object."
        : "A buried artifact has no optical pixel.",
  };

  const mag: SensorCall =
    materialId === "eyelets"
      ? salt
        ? { verdict: "unlikely", why: "Ferrous signal falls off fast and salt soil is noisy." }
        : { verdict: "survey", why: "A ferrous cluster is a magnetometer question. Gold is not." }
      : {
          verdict: "none",
          why: "Magnetometers hear iron. Gold, bone, ceramic, and cotton are silent.",
        };

  const pi: SensorCall =
    m.kind === "metal"
      ? salt
        ? {
            verdict: "unlikely",
            why: "Pulse induction tolerates salt better than VLF and still loses small gold under wet saline sand.",
          }
        : {
            verdict: "survey",
            why: "Best small-metal tool in dry dune sand. Depth is shallow. Grid it. Do not wander.",
          }
      : { verdict: "none", why: "A metal detector does not hear bone, ceramic, or fiber." };

  return { sar, lidar, gpr, vhr, mag, pi };
}

export const SENSOR_LABEL: Record<SensorId, string> = {
  sar: "SAR",
  lidar: "LiDAR mesh",
  gpr: "GPR",
  vhr: "VHR photo",
  mag: "Magnetometer",
  pi: "PI metal",
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  none: "Will not show",
  unlikely: "Unlikely here",
  survey: "New survey only",
  proxy: "Landscape proxy",
};
