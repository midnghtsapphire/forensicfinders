/** A635 Holmfirth Road sight study, 17 Oct 2026.
 * Copernicus GLO-30, 25 m grid, British National Grid.
 * Hidden means a point on the ground is not visible to a 1.7 m eye on the road.
 * It is not a grave, a cache, or a detection.
 */

export const ROAD_RUN = {
  place: "Saddleworth Moor",
  road: "A635 Holmfirth Road",
  elevation:
    "Copernicus GLO-30, a 30 m surface model resampled to a 25 m grid. It includes walls, buildings, and dam faces. It shows which ground the road cannot see. It does not show grave-scale features.",
  eyeM: 1.7,
  targetM: 0,
  viewshedM: 500,
  capM: 300,
  observers: 92,
  stepM: 100,
  withinM2: 5_655_625,
  hiddenM2: 1_120_625,
} as const;

export const QGIS_POINTS = [
  {
    id: "1",
    name: "Script point 1, Greenfield side",
    easting: 400821,
    northing: 404561,
    elevM: 255.0,
    nearestRoadM: 31.2,
    withinM2: 282_500,
    hiddenM2: 130_000,
    visibleWithin500Pct: 32.8,
  },
  {
    id: "2",
    name: "Script point 2, central moor",
    easting: 404100,
    northing: 404050,
    elevM: 485.0,
    nearestRoadM: 509.8,
    withinM2: 280_000,
    hiddenM2: 165_000,
    visibleWithin500Pct: 28.6,
  },
  {
    id: "3",
    name: "Script point 3",
    easting: 405550,
    northing: 403810,
    elevM: 508.1,
    nearestRoadM: 865.5,
    withinM2: 283_750,
    hiddenM2: 85_000,
    visibleWithin500Pct: 42.7,
  },
] as const;

export function hiddenShare(hidden: number, within: number) {
  if (within <= 0) return 0;
  return hidden / within;
}

export const REFUSED = [
  "No cell on this map is a burial, a cache, or a recovery.",
  "The Fleming drop centered 0.25 mile and 1 mile rings on a residence. Those radii were chosen, not checked against a printed page. The elevation grid filled 362,315 empty cells, which invents terrain. Those depressions are not shown.",
  "Scored grids, Garmin tracks, and drone waypoint files from that drop are not loaded. A number written into a waypoint is not a sensor return.",
  "City permit pulls, river gages, rain multipliers, and highway-camera harvests are not a case file and are not on this desk.",
] as const;
