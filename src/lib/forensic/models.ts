export type Ring = { p25: number; p50: number; p75: number; p95: number };

export type SubjectModel = {
  id: string;
  name: string;
  family: "lost" | "abduction";
  ringsMi: Ring | null;
  useOnFleming: "no" | "context";
  behavior: string[];
  caution: string;
};

/**
 * Distances are rounded teaching figures from public descriptions of
 * Koester-style ring models. They are not an ISRID table export.
 * Verify against a current ISRID pull before any real mission.
 */
export const SUBJECT_MODELS: SubjectModel[] = [
  {
    id: "abduction",
    name: "Non-family abduction",
    family: "abduction",
    ringsMi: null,
    useOnFleming: "context",
    behavior: [
      "Distance is set by the other person, usually a vehicle, not by the child's walk",
      "The last-seen point is an IPP for investigation, not the center of a lost-person ring",
      "Roads, causeways, and water matter more than a circle",
    ],
    caution:
      "This is the model class public summaries assign to Keith: he said he would hitchhike, and he did not come home. A hiker ring drawn on that fact is the wrong picture.",
  },
  {
    id: "child-small",
    name: "Lost child, ages 1–3",
    family: "lost",
    ringsMi: { p25: 0.12, p50: 0.19, p75: 0.37, p95: 2.8 },
    useOnFleming: "no",
    behavior: [
      "Often close, low, and sheltered",
      "Public summaries put half of finds inside a few hundred meters",
    ],
    caution: "Keith was 13. Do not brief this ring on his case.",
  },
  {
    id: "child-school",
    name: "Lost child, school age",
    family: "lost",
    ringsMi: { p25: 0.15, p50: 0.5, p75: 1.1, p95: 4 },
    useOnFleming: "no",
    behavior: [
      "Shortcuts, friends' yards, structures",
      "Usually still inside the neighborhood if they are simply lost",
    ],
    caution:
      "A lost school-age ring assumes the child is choosing where to walk. An abduction does not. Shown so the difference is visible.",
  },
  {
    id: "autism",
    name: "Autistic child",
    family: "lost",
    ringsMi: { p25: 0.2, p50: 0.7, p75: 1.6, p95: 5 },
    useOnFleming: "no",
    behavior: ["Attraction to water and familiar special places", "May not answer a searcher"],
    caution: "Not indicated by the public facts of this case. Water attraction is why the category exists, not a reason to apply it here.",
  },
  {
    id: "despondent",
    name: "Despondent",
    family: "lost",
    ringsMi: { p25: 0.2, p50: 0.7, p75: 1.6, p95: 5.5 },
    useOnFleming: "no",
    behavior: ["Often not far, often toward a scenic edge or a secluded spot", "May not be mobile long"],
    caution: "Nothing in the public disappearance narrative supports this category.",
  },
  {
    id: "dementia",
    name: "Dementia, temperate",
    family: "lost",
    ringsMi: { p25: 0.2, p50: 0.6, p75: 1.5, p95: 6 },
    useOnFleming: "no",
    behavior: ["Often found near a road or a path, sometimes only meters off it", "May travel a straight line"],
    caution: "Illustrative adult category, so a planner can see how far the rings move when the subject changes.",
  },
  {
    id: "hiker",
    name: "Day hiker",
    family: "lost",
    ringsMi: { p25: 0.4, p50: 1.3, p75: 2.8, p95: 7 },
    useOnFleming: "no",
    behavior: ["Trail or attempted shortcut", "Terrain bends the ring into a watershed"],
    caution: "The default ring in wilderness apps. It is the wrong default on a barrier-island abduction.",
  },
  {
    id: "waterview",
    name: "Person drawn to water",
    family: "lost",
    ringsMi: { p25: 0.2, p50: 0.6, p75: 1.4, p95: 4 },
    useOnFleming: "no",
    behavior: ["Travel often ends at the water they were already going toward", "Search the edge, not the disk"],
    caution: "He surfed and knew the pier. That is biography. It is not a statistical category assignment.",
  },
];

export type Cache = {
  id: string;
  name: string;
  where: string;
  sar: string;
  lidar: string;
  gpr: string;
  metal: string;
  island: string;
};

export const CACHES: Cache[] = [
  {
    id: "soft-case",
    name: "Soft suitcase",
    where: "Luggage, zippered, fabric over a frame",
    sar: "No. Below any civil resolution, and fabric is not a bright target.",
    lidar: "No, once buried. A surface dump can show as a lump for days, not decades.",
    gpr: "A void or a flat reflector only if shallow, dry, and the case still holds shape.",
    metal: "Zippers and a frame can answer a coil. The cloth does not.",
    island: "Possible inland, in a yard or a dune cut. Not on the wet beach.",
  },
  {
    id: "hard-case",
    name: "Hard-shell case",
    where: "Rigid luggage or a small trunk",
    sar: "Still no, unless it is vehicle-sized and the mode is spotlight.",
    lidar: "No underground.",
    gpr: "Best container target: a flat, shallow reflector in dry sand.",
    metal: "Locks and corner hardware. Weak if the shell is plastic.",
    island: "Same places a person can dig quickly beside A1A.",
  },
  {
    id: "textile",
    name: "Duffel or wrap",
    where: "Cloth around cloth",
    sar: "No.",
    lidar: "No.",
    gpr: "Collapses. Rarely a lasting reflection.",
    metal: "Only whatever hardware was inside.",
    island: "The hardest cache to remote-sense. Excavation or a witness, not a satellite.",
  },
  {
    id: "shallow",
    name: "Shallow sand dig",
    where: "A hole measured in feet, backfilled",
    sar: "No direct return. A later photo might show a scar that vegetation then erased.",
    lidar: "A dent, if the fill settled and no one regraded the lot.",
    gpr: "Disturbed bedding can scatter. Salt and shells imitate that scatter.",
    metal: "Only if ferrous or a coil-detectable object went in with the fill.",
    island: "Dunes are easy to dig. They also move. A 1977 surface is not the 2026 surface.",
  },
  {
    id: "dune",
    name: "Dune interior",
    where: "Above the salt wedge, vegetated",
    sar: "Canopy and roughness only.",
    lidar: "Remove vegetation and rootballs, then read residual relief.",
    gpr: "The least-bad GPR ground on this island, if the sand is dry.",
    metal: "Pulse induction on a tight grid.",
    island: "Prefer this over the swash zone for any new geophysics.",
  },
  {
    id: "muck",
    name: "Lagoon margin muck",
    where: "Banana River edge, mangrove, wet organic soil",
    sar: "Smooth dark water against a bright mangrove edge. Change only.",
    lidar: "Poor through mangrove unless leaf-off and carefully classified.",
    gpr: "Conductive muck kills the wave in the first foot.",
    metal: "Depth and conductivity both work against you.",
    island: "Do not task GPR here and call a null result a clearance.",
  },
  {
    id: "water",
    name: "Open water",
    where: "River, canal, or surf",
    sar: "Sees the surface state, not a submerged object of this size.",
    lidar: "Bathymetric lidar only in clear, shallow, calm water. The river is not that.",
    gpr: "Not through salt water.",
    metal: "A towed coil is a different operation, with a survey plan.",
    island: "Both shores are real considerations because the island is thin. They are not findings.",
  },
  {
    id: "structure",
    name: "Structure or crawlspace",
    where: "House, shed, slab, pier building",
    sar: "The building is the bright return. The interior is hidden.",
    lidar: "Roof and slab edge only.",
    gpr: "Slab scans are local and slow, and rebar rings.",
    metal: "Useless inside a building full of nails.",
    island: "A records job: permits, renovations, who owned the lot. Not a waveform job.",
  },
  {
    id: "vehicle",
    name: "Vehicle",
    where: "Car, van, trailer",
    sar: "From the quad-pol decade forward, a vehicle-sized metal body can be a point. In 1977 film, no.",
    lidar: "If it is still on the surface.",
    gpr: "A buried vehicle is a large reflector. Rare, and not subtle.",
    metal: "The whole body is the target.",
    island: "Hitchhiking puts a vehicle in the story. The corridor is A1A and the causeways, which immediately leave this sheet.",
  },
  {
    id: "rootball",
    name: "Rootball cavity",
    where: "Hole left when a tree tips over",
    sar: "A windthrow patch can change backscatter for a season.",
    lidar: "This is the mesh. The rootball is a false hill; the pit is the residual dent.",
    gpr: "The pit fill is disturbed ground. It looks like every other disturbance.",
    metal: "Worth a coil only after the mesh flags the pit.",
    island: "Hurricanes rearrange this island. A dent needs a date, or it is just weather.",
  },
];

export function modelById(id: string): SubjectModel {
  return SUBJECT_MODELS.find((m) => m.id === id) ?? SUBJECT_MODELS[0]!;
}

export function cacheById(id: string): Cache {
  return CACHES.find((c) => c.id === id) ?? CACHES[0]!;
}
