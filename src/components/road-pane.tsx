import { horizonM } from "@/lib/forensic/physics";
import { QGIS_POINTS, REFUSED, ROAD_RUN, hiddenShare } from "@/lib/forensic/road";

function km2(m2: number) {
  return (m2 / 1_000_000).toFixed(2);
}

function pct(hidden: number, within: number) {
  return `${(hiddenShare(hidden, within) * 100).toFixed(1)}%`;
}

export function RoadPane() {
  const geometricKm = horizonM(ROAD_RUN.eyeM) / 1000;
  const refractedKm = horizonM(ROAD_RUN.eyeM, 4 / 3) / 1000;
  return (
    <section className="grid gap-4 lg:grid-cols-5">
      <div className="panel p-3 lg:col-span-3">
        <p className="eyebrow mb-2">Road sight · 17 Oct 2026</p>
        <img
          src="/a635-hidden-ground.png"
          alt="Elevation of Saddleworth Moor. The A635 is a black line. Red cells are within 300 metres of the road and hidden from a 1.7 metre eye on it. Blue cells are within 300 metres and visible. Three triangles sit off the road."
          className="w-full rounded-md bg-fg"
        />
        <p className="mt-2 text-sm text-muted">
          Red is ground the road cannot see. Blue is ground it can. Neither color is a find.
        </p>
      </div>

      <div className="flex flex-col gap-4 lg:col-span-2">
        <article className="panel flex flex-col gap-3 p-4">
          <p className="eyebrow">{ROAD_RUN.place}</p>
          <h2 className="display text-2xl">What the {ROAD_RUN.road} cannot see</h2>
          <p className="text-sm text-muted">{ROAD_RUN.elevation}</p>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-md bg-surface-2 p-3">
              <dt className="text-muted">Observers on the road</dt>
              <dd className="display text-2xl">
                {ROAD_RUN.observers}
                <span className="ml-1 text-sm text-muted">every {ROAD_RUN.stepM} m</span>
              </dd>
            </div>
            <div className="rounded-md bg-surface-2 p-3">
              <dt className="text-muted">Eye / target</dt>
              <dd className="display text-2xl">
                {ROAD_RUN.eyeM} m
                <span className="ml-1 text-sm text-muted">to the ground</span>
              </dd>
            </div>
            <div className="rounded-md bg-surface-2 p-3">
              <dt className="text-muted">Within {ROAD_RUN.capM} m</dt>
              <dd className="display text-2xl">{km2(ROAD_RUN.withinM2)} km²</dd>
            </div>
            <div className="rounded-md bg-surface-2 p-3">
              <dt className="text-muted">Hidden from the road</dt>
              <dd className="display text-2xl">
                {km2(ROAD_RUN.hiddenM2)} km²
                <span className="ml-1 text-sm text-muted">
                  {pct(ROAD_RUN.hiddenM2, ROAD_RUN.withinM2)}
                </span>
              </dd>
            </div>
          </dl>
          <p className="text-sm text-muted">
            Viewshed stops at {ROAD_RUN.viewshedM} m. A smooth-earth horizon for this eye is{" "}
            {geometricKm.toFixed(2)} km, or {refractedKm.toFixed(2)} km with the 4/3-earth refraction allowance.
            Both sit far outside the viewshed, so red cells are relief, not the curve of the earth. A red cell
            is shielded ground. It does not mean anything was put there.
          </p>
        </article>

        <article className="panel flex flex-col gap-2 p-4">
          <p className="eyebrow">Three script points</p>
          <p className="text-sm">
            The triangles are the three points written in the QGIS script. They are not the {ROAD_RUN.observers}{" "}
            observers on Holmfirth Road. Nearest line in the roads file came back unnamed.
          </p>
          <ul className="flex flex-col gap-2">
            {QGIS_POINTS.map((p) => (
              <li key={p.id} className="rounded-md bg-surface-2 p-3 text-sm">
                <p className="text-fg">{p.name}</p>
                <p className="text-muted">
                  {p.elevM} m elevation · nearest line {p.nearestRoadM} m · hidden{" "}
                  {pct(p.hiddenM2, p.withinM2)} of the {ROAD_RUN.capM} m circle · {p.visibleWithin500Pct}% of
                  the {ROAD_RUN.viewshedM} m circle is visible
                </p>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel flex flex-col gap-2 p-4">
          <p className="eyebrow">Left out of this drop</p>
          <ul className="list-disc pl-4 text-sm text-muted">
            {REFUSED.map((line) => (
              <li key={line} className="mt-1">
                {line}
              </li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
