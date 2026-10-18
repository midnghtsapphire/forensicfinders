export const CASE = {
  name: "Keith Dean Fleming",
  short: "KDF-1977",
  missing: "28 April 1977",
  from: "Cocoa Beach, Brevard County, Florida",
  born: "18 September 1963",
  age: "13",
  stature: "About 5'0\", with public pages listing roughly 90–110 lb",
  class: "Non-family abduction. Foul play is suspected in public summaries.",
  numbers: [
    { label: "NCMEC", value: "601296" },
    { label: "Police", value: "77099132" },
    { label: "NCIC", value: "M-080547943" },
  ],
  contacts: [
    { name: "Cocoa Beach Police", phone: "(321) 868-3251" },
    { name: "Florida Missing Person Unit", phone: "1-888-356-4774" },
    { name: "NCMEC", phone: "1-800-843-5678" },
  ],
  narrative: [
    "Last seen on his way home from a girlfriend's house, north of his own, after school. He was expected for dinner.",
    "They rode her bicycle to the end of Osceola Street at State Road A1A. He got off and said he would hitchhike the rest of the way, which public accounts describe as common on the island then.",
    "Her mother drove back to pick him up. He was already gone. He did not arrive home and has not been seen since.",
    "Public summaries say he surfed and spent time at the Cocoa Beach Pier. That is a place people knew him, not a location of recovery.",
  ],
  body: [
    "Blond or strawberry-blond hair, brown eyes. Hair had been trimmed shorter than in earlier photos.",
    "A partial upper plate: two front teeth had been lost in an accident.",
    "A prior fracture of the left leg.",
  ],
  worn: [
    "Public pages do not fully agree on the shirt. One summary specifies a green T-shirt with the words Thirsty Turtle.",
    "Jeans, and thong sandals or flip-flops.",
    "A gold chain with an Italian horn.",
    "Treat the list as unconfirmed until the agency of record says otherwise.",
  ],
  suspect:
    "Public case pages name John Rodney McRae as the person investigators have treated as the prime suspect. This desk does not score that, and it does not assemble a prosecution file.",
} as const;

export const LANES = [
  {
    id: "epochs",
    title: "Year kernels, 1960 to now",
    gap: "Archives still hold film SLAR and early ERS. Almost nobody sells a kernel that says what that year physically was, and what reprocessing is allowed to do to it.",
    who: "State archives, mapping libraries, SAR shops that inherit old strips.",
    here: "The year slider is that kernel. 1977 is film-era. It is not pulled toward a fake complex image.",
  },
  {
    id: "switch",
    title: "Abduction switch",
    gap: "Wilderness apps brief a lost-hiker ring on every pin. On a hitchhiking disappearance that ring hides the road.",
    who: "Cold-case units and volunteer search managers who inherited a child case.",
    here: "The default model on this file refuses the lost-child ring and draws the stated direction instead.",
  },
  {
    id: "cards",
    title: "Artifact return cards",
    gap: "Teams task SAR to 'look for the necklace.' The physics says no. A card that says so saves a season.",
    who: "Anyone about to rent a sensor.",
    here: "Gold horn, dental plate, possible rivets, bone, and cloth each get a verdict per sensor and per wetness.",
  },
  {
    id: "chromalock",
    title: "Chromalock inversion",
    gap: "Inverting a scene to see dents also inverts the one thing you were trying to keep. Analysts lose the target hue.",
    who: "Training programs and photo interpreters.",
    here: "Invert the island. The reticle, and the synthetic phantom, keep their color.",
  },
  {
    id: "rootball",
    title: "Rootball residual mesh",
    gap: "Forestry clouds already subtract tipped-tree rootballs. Cold-case LiDAR rarely borrows that move to see the pit and any smaller dent left in it.",
    who: "Drone LiDAR vendors and reconstruction teams.",
    here: "The mesh view lifts the rootball off and leaves the residual.",
  },
  {
    id: "cache",
    title: "Suitcase and cache matrix",
    gap: "Container cases get briefed as if every sensor could see luggage. Soft cloth, hard shell, muck, and open water are different problems.",
    who: "Homicide units working concealment, not wilderness rescue.",
    here: "Ten caches, including a rootball cavity, matched to this island's sand and salt.",
  },
  {
    id: "now",
    title: "What to task in 2026",
    gap: "The missing product is not another heatmap. It is a refusal: which archive cannot answer, and which new line might.",
    who: "The detective who has one budget line left.",
    here: "Dry dune, pulse-induction grid, high-frequency GPR off the salt wedge, LiDAR for dated dents. Not a 1977 radar cube.",
  },
] as const;
