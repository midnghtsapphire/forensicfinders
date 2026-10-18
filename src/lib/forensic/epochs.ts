export type Epoch = {
  id: string;
  from: number;
  to: number;
  name: string;
  platform: string;
  band: string;
  wavelengthCm: number;
  resolutionM: number;
  polarization: string;
  calibration: string;
  stripe: number;
  looks: number;
  biasDb: number;
  defects: string[];
  kernel: string[];
  archiveNote: string;
};

export const EPOCHS: Epoch[] = [
  {
    id: "slar-film",
    from: 1960,
    to: 1969,
    name: "Airborne SLAR, film",
    platform: "Real-aperture side-looking airborne radar",
    band: "X / Ka, incoherent",
    wavelengthCm: 3.2,
    resolutionM: 25,
    polarization: "Single, often unrecorded",
    calibration: "None. Gray values on film, not sigma-nought.",
    stripe: 0.85,
    looks: 1,
    biasDb: 4.5,
    defects: [
      "Range compression is optical, not digital",
      "Yaw and altitude wander stretch the near range",
      "No orbit or DEM to terrain-correct against",
    ],
    kernel: [
      "Scan the film at a fixed density curve",
      "Remove range-gain ramp using a smooth across-track fit",
      "Geocode only if the flight line was surveyed",
      "Stop. Do not invent a complex SLC that was never recorded",
    ],
    archiveNote:
      "A 1960s strip can show coastline and large structures. It cannot show a person, a suitcase, or a dent.",
  },
  {
    id: "slar-late",
    from: 1970,
    to: 1977,
    name: "Late film SLAR",
    platform: "Civil and mapping SLAR, still mostly film",
    band: "X-band real aperture",
    wavelengthCm: 3.1,
    resolutionM: 15,
    polarization: "Single",
    calibration: "Relative gray only",
    stripe: 0.7,
    looks: 1,
    biasDb: 3.6,
    defects: [
      "Seasat has not flown yet (1978)",
      "No repeat-pass coherence",
      "Street grid is at or below the resolution cell",
    ],
    kernel: [
      "Density-linearize the film",
      "Destripe along the flight direction",
      "Match the shoreline to a modern coastline and accept tens of meters of error",
      "Hand the sheet to an analyst as context, not as a detection layer",
    ],
    archiveNote:
      "April 1977 has no satellite SAR of a Cocoa Beach street. If a file exists, it is an airplane strip or, more likely, an aerial photo — not a radar cube.",
  },
  {
    id: "seasat-sir",
    from: 1978,
    to: 1990,
    name: "Seasat to SIR",
    platform: "Seasat (1978), SIR-A/B, early airborne SAR",
    band: "Mostly L-band, some airborne C/X",
    wavelengthCm: 23,
    resolutionM: 25,
    polarization: "Single",
    calibration: "Early, unstable",
    stripe: 0.45,
    looks: 2,
    biasDb: 2.4,
    defects: [
      "Seasat lived about 100 days and looked at oceans",
      "SIR swaths are experimental, not a city archive",
      "Long L-band wave washes out small roughness",
    ],
    kernel: [
      "Apply the published sensor gain if the product still has it",
      "Multilook to kill 1-look speckle before any stretch",
      "Do not coregister to a modern street and call the residual a grave",
    ],
    archiveNote:
      "Useful for large shoreline change. Useless for a pendant, a plate, or a shallow cache.",
  },
  {
    id: "ers",
    from: 1991,
    to: 1996,
    name: "ERS-1 era",
    platform: "ERS-1, early ERS-2",
    band: "C-band",
    wavelengthCm: 5.7,
    resolutionM: 30,
    polarization: "VV",
    calibration: "PRI intensity, improving",
    stripe: 0.28,
    looks: 3,
    biasDb: 1.4,
    defects: [
      "30 m cell averages a house with its yard",
      "VV only — no cross-pol vegetation channel",
      "Layover on the dune face if the look is steep",
    ],
    kernel: [
      "Convert digital number with the product calibration constant",
      "Multilook, then speckle-filter lightly",
      "Range-Doppler geocode with a modern DEM",
      "Terrain-correct to gamma-nought, the 2026 anchor",
    ],
    archiveNote:
      "First era where a repeatable coastline backscatter record exists. Still a landscape record.",
  },
  {
    id: "radarsat1",
    from: 1997,
    to: 2006,
    name: "Radarsat-1 / JERS-1",
    platform: "Radarsat-1, JERS-1, ERS-2",
    band: "C or L",
    wavelengthCm: 5.6,
    resolutionM: 12,
    polarization: "Single (HH or VV)",
    calibration: "Beta-nought products common",
    stripe: 0.18,
    looks: 4,
    biasDb: 0.9,
    defects: ["Single polarization", "Incidence swings across the swath", "Speckle still dominates a small bright target"],
    kernel: [
      "Beta-nought to gamma-nought with local incidence from a DEM",
      "Document the filter window. Do not hide it.",
      "Keep the native resolution product beside the pretty one",
    ],
    archiveNote: "Can see a pier, a bridge, a new parking lot. Cannot see bone.",
  },
  {
    id: "polsar",
    from: 2007,
    to: 2013,
    name: "Quad-pol decade",
    platform: "ALOS PALSAR, Radarsat-2, TerraSAR-X",
    band: "L, C, or X",
    wavelengthCm: 5.6,
    resolutionM: 8,
    polarization: "Dual or quad on some modes",
    calibration: "Sigma-nought, often still uncorrected for terrain",
    stripe: 0.1,
    looks: 4,
    biasDb: 0.5,
    defects: ["Mode choice matters more than the year", "Spotlight archives are task-based, not blanket"],
    kernel: [
      "Polarimetric decomposition only if the mode was quad-pol",
      "Otherwise stay with gamma-nought and do not pretend you have entropy",
      "Coregister a stack. Change detection is the actual cold-case use",
    ],
    archiveNote:
      "The honest product of this era is a change map: dune cut, new fill, a lot cleared. Not a material ID.",
  },
  {
    id: "s1",
    from: 2014,
    to: 2023,
    name: "Sentinel-1 standard",
    platform: "Sentinel-1 IW, plus commercial tasking",
    band: "C-band",
    wavelengthCm: 5.5,
    resolutionM: 20,
    polarization: "VV+VH typical",
    calibration: "Radiometric terrain correction is now ordinary",
    stripe: 0.04,
    looks: 5,
    biasDb: 0.2,
    defects: ["IW burst seams if mosaicked badly", "20 m still cannot hold a cache"],
    kernel: [
      "Apply orbit file, thermal noise removal, calibration, terrain correction",
      "Output gamma-nought, 10 m posting, both polarizations",
      "This is the current civil standard the older years are being pulled toward",
    ],
    archiveNote: "Free, repeatable, and still the wrong tool for a dental plate.",
  },
  {
    id: "now",
    from: 2024,
    to: 2026,
    name: "Current standard",
    platform: "Sentinel-1C, NISAR-class L/S, commercial X-band spotlight",
    band: "L / S / C / X depending on task",
    wavelengthCm: 3.1,
    resolutionM: 1,
    polarization: "As tasked",
    calibration: "Gamma-nought, geocoded, documented looks",
    stripe: 0,
    looks: 6,
    biasDb: 0,
    defects: ["A 1 m spotlight is tasked, not archived everywhere", "Even 0.25 m does not resolve a horn or a tooth"],
    kernel: [
      "You are already on the standard. Reprocessing means: document RTC, looks, and DEM",
      "Fuse with a new GPR or metal survey instead of stretching the radar harder",
    ],
    archiveNote:
      "Best radar the island can be given today. Still a map of roughness and structures, not of remains.",
  },
];

export function epochForYear(year: number): Epoch {
  const y = Math.min(2026, Math.max(1960, Math.round(year)));
  return EPOCHS.find((e) => y >= e.from && y <= e.to) ?? EPOCHS[EPOCHS.length - 1]!;
}

export const YEAR_PRESETS = [
  { year: 1964, label: "1964 film" },
  { year: 1977, label: "1977 case" },
  { year: 1992, label: "1992 ERS-1" },
  { year: 2017, label: "2017 S1" },
  { year: 2025, label: "2025 spot" },
] as const;
