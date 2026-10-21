# Phone-attached GPR / radar sensor add-on (PROTOTYPE)

**Registry ID: 2020** · **Status: PROTOTYPE / RESEARCH** · No claimed detection results.

Audrey remembers a **phone-attached** GPR or radar sensor (shallow: ~inches, or through concrete). Search findings are in §0. This note is a crawl → walk → run plan using **cited commercial kits and papers only**.

---

## 0. What we found in her accounts (2026-10-21)

| Place | Result |
|---|---|
| **GitHub `midnghtsapphire/Radar`** | **Found.** Public fork of [`user79/Radar`](https://github.com/user79/Radar). Description: “DIY-style ground penetrating radar”. Eagle CAD board (`gpr01.sch` / `.brd`), PDFs, and `GPR progress summer2023.pdf`. It is a **benchtop FMCW PCB** aimed at humanitarian demining, based on MIT OCW radar / UC Davis EEC134 / Ferrara–Chizh–Pietrelli educational GPR — **not** a phone-attached USB/BLE sensor. README says board reflections dominated early tests; summer 2023 hallway person-tracking worked with resolution limits. Link: https://github.com/midnghtsapphire/Radar |
| **GitHub code search** (`walabot`, `acconeer`, `mmwave`, `BGT60`, `IWR6843`, `phone gpr`, `usb radar` under `midnghtsapphire`) | **0 hits** |
| **Other repo names** among 312 repos | Only `Radar` matched gpr/radar/mmwave/uwb/phone-sensor patterns |
| **`/workspace/notebook-sar/`** | No phone/USB radar project. GPR appears only as dielectric / velocity math in `run_county.py` and a mention in `master_unified_sar_bootstrap.py`. Field-equipment note recommends **renting** cart GPR, not a phone sensor: `_pkg/search-system/docs/FIELD_EQUIPMENT.md` |
| **Google Drive** (title search “GPR”; full-text Walabot/mmWave/phone radar) | Field PDFs (calibration log, k9 checklist, vault protocol, tasking report) — **case/field ops, not a phone-sensor product**. No Walabot / Acconeer / mmWave / “phone radar” project files. Walabot/mmWave title+body search returned **empty** |

**Conclusion:** the closest GitHub artifact is the DIY FMCW **Radar** fork. A dedicated **phone-attached** GPR app/hardware project was **not** found on GitHub or Drive from here. It may live only on a phone, Lovable/Replit, or an unlinked private store.

Related shipped code already in this repo: physics model `gpr-wave-model` (500), dielectric mixing / velocity (1120), instrument file input (810).

---

## Crawl — off-the-shelf USB / BLE / phone mmWave & UWB-class boards

Goal: phone (or laptop) reads **raw returns**, aimed at **shallow** concrete rebar / void cues and **very shallow** soil — not burial-depth GPR.

| Hardware | Band / interface | Stated / realistic depth | Price (approx., 2026 lists) | Links |
|---|---|---|---|---|
| **Walabot DIY 2 / DIY 2 M** | Phone app (iOS/Android), Wi‑Fi to sensor, battery | Vendor: **up to 4 in / 10 cm in drywall/plywood**. Vendor: **do not use on concrete, brick, tile, stucco, metal-backed walls**. Third-party tests report only weak cues on concrete | **~$200** | https://walabot.com/products/walabot-diy-2 · https://walabot.com/products/walabot-diy-2-m · support: https://support.walabot.com/hc/en-us/articles/360015452958-What-can-Walabot-DIY-devices-detect |
| **Infineon DEMO BGT60TR13C** (XENSIV 60 GHz) | USB to PC; SPI to MCU; 1 Tx / 3 Rx AiP | Free-space presence / ranging (kit docs: occupancy, ~metre-scale rooms). **60 GHz does not penetrate wet soil or thick concrete** in any useful GPR sense; range resolution example ~0.32 m with 460 MHz chirp bandwidth in AN141319 | Demo kit ~**$190–$220** | https://www.infineon.com/part/BGT60TR13C · demo DEMOBGT60TR13CTOBO1 |
| **TI IWR6843ISK** | USB point cloud; 60–64 GHz, 3 Tx / 4 Rx | Industrial presence / ranging through **plastic/glass/drywall** (TI marketing). Same mmWave physics: **not** a soil/concrete GPR | Module ~**$160–$230** (distributors); starter bundles higher | https://www.ti.com/tool/IWR6843ISK |
| **Acconeer A121** | 57–64 GHz pulsed coherent radar, SPI, tiny AiP | Datasheet: absolute range up to ~20–23 m **in air**, mm accuracy. Material sensing is supported as an app class; **no published soil/concrete penetration depth** — expect surface / through-plastic only at 60 GHz | Chip + XM125/XM126 eval modules (order from Acconeer/distributors; typically low hundreds USD for a module) | Datasheet: https://developer.acconeer.com/download/a121-datasheet/ |

### Honest crawl limits
- **“2 inches”** is plausible for drywall stud/pipe finders (Walabot’s 4 in claim is **drywall only**).
- **“Through concrete”** with 60 GHz phone sensors is **mostly marketing aspiration**. Concrete attenuation at mmWave is severe; Feitor et al. (2011) study concrete **reflection** at 18.7/60 GHz for dielectric extraction, not through-slab imaging ([IEEE LAPC 2011](https://doi.org/10.1109/lapc.2011.6114146)).
- Phone apps that only show a cartoon stud map (no raw IQ / range profile export) are a dead end for SAR integration.

**Crawl next small step:** buy **one** kit that exports raw or range-profile data (prefer Infineon DEMO or TI IWR6843ISK + SDK, or Walabot if Expert Mode raw export is confirmed). Capture: (1) empty drywall, (2) drywall with known pipe, (3) thin concrete paver with known rebar spacing. Log files + photos. No field claims yet.

---

## Walk — low-frequency GPR antenna add-on (power & size)

To see **decimetres to metres** in soil you need **MHz-class** bandwidth and antennas measured in **tens of centimetres**, not a phone dongle.

| Project | Band | Size / power tradeoff | Cost cue | Links |
|---|---|---|---|---|
| **GPRino** (open source) | FMCW **323–910 MHz**, Arduino Mega + custom RF, Vivaldi antennas on A4 FR4 | Antenna boards ~A4; stacked RF+LF boards in a box; not pocketable; onboard LCD or PC | Author: **&lt;$300** components | https://github.com/miricip/GPRino · https://hackaday.io/project/175115-gprino |
| **MIT OCW small radar / UC Davis EEC134** (educational FMCW) | Microwave teaching radars (range/Doppler/SAR labs) | Coax-connected modules, lab PSUs; Audrey’s `Radar` fork followed this path and hit **on-board coupling** | Course materials free; hardware BOM varies | https://ocw.mit.edu/courses/res-ll-003-build-a-small-radar-system-capable-of-sensing-range-doppler-and-synthetic-aperture-radar-imaging-january-iap-2011/ · http://gpradar.eu/onewebmedia/TU1208_GPRforeducationaluse_November2017_FerraraChizhPietrelli.pdf |
| **SDR stepped-frequency GPR** (research) | e.g. USRP N200 + WBX, 1.5 GHz sweep → ~10 cm air resolution (Álvaro et al. 2020) | Needs SDR (~$1k+ class), antennas, switches | Paper: https://doi.org/10.1117/12.2570390 |
| **~100 MHz miniaturized dipole** | Resonates ~104 MHz, 8 MHz BW; board **66.5×22 cm** (still large) | Shows the size floor of low-frequency antennas | Howlader & Sattar (2016) *PIER C* 61:161–170, doi:[10.2528/PIERC15103004](https://doi.org/10.2528/pierc15103004) |
| **Commercial cart GPR** (reality check) | 400–900 MHz carts | Rent **~$1.5k–2.5k/week** with operator — still the field standard (notebook FIELD_EQUIPMENT ladder) | See `FIELD_EQUIPMENT.md` in notebook package |

**Walk next small step:** if crawl proves raw export works, either (a) build/buy a **GPRino-class** 300–900 MHz unit for soil, or (b) rent a commercial 400 MHz cart for one labelled grid and keep the phone sensor for walls only. Do not expect the phone dongle to replace the cart.

---

## Run — tie into the SAR pipeline (1100-series)

Once a sensor produces a time/depth profile:

1. **Velocity / depth:** use `forensic_models.gpr_dielectric` (1120):  
   `eps_eff = (1-θ)[ε_fat(1-f_sap)+ε_soap f_sap] + θ ε_soil`, `v = 0.3/√eps_eff` (m/ns), `depth = v · TWT / 2`.  
   ε_soil from Topp (1010) when θ is known; ε_soap remains user-supplied.
2. **File ingest:** extend `instrument_input` (810) with a `radar_profile` CSV/NPY schema (trace index, time_ns, amplitude) — same pattern as GPR CSV today.
3. **Spatial join:** merge picks into `cameras.timeline` (1913) and/or sector GeoJSON from `run_sectors` (970) with `kind: gpr_pick`.
4. **Anomaly assist (optional):** if you have a dense grid of amplitude/energy maps, Gi* (1110) can flag clusters — same caveats as DEM Gi*.
5. **Phone role:** the phone is the **UI + GNSS stamp + raw capture**, not the deep antenna.

---

## BOM estimate (first crawl build)

| Item | Qty | Est. USD |
|---|---|---|
| Infineon DEMO BGT60TR13C **or** TI IWR6843ISK | 1 | 160–230 |
| USB-C cable / power bank | 1 | 20 |
| Android/iOS phone or laptop for capture | 1 | (have) |
| Known-target kit: drywall scrap, PVC, copper pipe, thin concrete paver, rebar offcuts | 1 | 40–80 |
| Notebook + labels + tape measure | 1 | 20 |
| **Crawl total** | | **~$250–350** (excluding phone) |
| Optional walk upgrade: GPRino-class parts | 1 | ~300 |
| Optional: commercial cart rental (1 week) | 1 | 1,500–2,500 |

---

## Step-by-step first build
1. Clone / bookmark https://github.com/midnghtsapphire/Radar (existing DIY work) so it is not lost; keep it separate from the phone kit.
2. Order **one** raw-capable 60 GHz kit (Infineon or TI).
3. Confirm SDK gives **range profile or IQ**, not only a consumer overlay.
4. Run the three crawl scenes; save files under `case/` (gitignored) with authority/notes.
5. Write a tiny importer that turns one capture format into the 810-style CSV and a unit test with a **synthetic** hyperbola (no field data in git).
6. Depth-label two picks using 1120 with a measured θ (TDR or oven-dry) — report uncertainty, not a single “inches” number.
7. Decide: wall-only product (crawl) vs soil product (walk/rent).

---

## What needs field testing
- Actual centimetres of useful signal in **your** drywall / paver / sandy vs clay soils.
- Whether Walabot Expert Mode (or kit SDK) exports data we can archive with SHA-256 (chain of custody).
- Coupling and ringing on concrete (false “voids”).
- GNSS quality when the phone is against a wall or in a ravine.
- Operator repeatability (two people, same wall).

**Not claimed:** that any phone sensor sees graves, or that 60 GHz replaces 400 MHz cart GPR.
