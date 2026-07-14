# Routing, isochrones & matrices

OSM has no single routing API — several engines consume OSM data and expose
HTTP routing. Pick by what you need and whether you can self-host.

| Engine               | Hosted free option             | Profiles (hosted)                    | Isochrones | Matrix | Key       |
| -------------------- | ------------------------------ | ------------------------------------ | ---------- | ------ | --------- |
| **OSRM**             | `router.project-osrm.org` demo | car only (demo)                      | no         | yes¹   | none      |
| **OpenRouteService** | api.openrouteservice.org       | car, bike, foot, wheelchair, hgv     | **yes**    | yes    | free      |
| **Valhalla**         | (no official public)           | car, bike, foot, transit, multimodal | yes        | yes    | —         |
| **GraphHopper**      | hosted plan / demo             | car, bike, foot, ...                 | yes        | yes    | free tier |

¹ OSRM `/table` matrix works on the demo too but is best-effort.

**Rule of thumb:** quick car distance/ETA → OSRM (`route.py`, no key).
Walking/cycling, isochrones, or anything user-facing → OpenRouteService
(`isochrone.py`, free key). Heavy/production → self-host OSRM or Valhalla.

⚠️ All routing engines take coordinates as **`lon,lat`** (GeoJSON order).

## OSRM — directions (script: `route.py`)

```bash
route.py -116.2023,43.6150 -116.1937,43.6629           # A → B, car
route.py -116.20,43.61 -116.19,43.66 -116.21,43.62      # multi-stop
route.py -116.20,43.61 -116.19,43.66 --steps            # turn-by-turn
route.py -116.20,43.61 -116.19,43.66 --geojson > r.geojson
```

Raw API:

```
GET https://router.project-osrm.org/route/v1/driving/{lon,lat};{lon,lat}?overview=full&geometries=geojson&steps=true
```

Response: `routes[0].distance` (m), `.duration` (s), `.geometry` (GeoJSON
LineString), `.legs[].steps[]` (maneuvers). Other services on the same engine:
`/table` (matrix), `/nearest`, `/match` (GPS trace → road), `/trip` (TSP).

## OpenRouteService — the Swiss-army option

Free key: https://openrouteservice.org/dev/#/signup → `export ORS_API_KEY=...`

**Directions** (more profiles than OSRM demo):

```bash
curl -s -X POST 'https://api.openrouteservice.org/v2/directions/cycling-regular/geojson' \
  -H "Authorization: $ORS_API_KEY" -H 'Content-Type: application/json' \
  -d '{"coordinates":[[-116.2023,43.6150],[-116.1937,43.6629]]}'
```

Profiles: `driving-car`, `driving-hgv`, `cycling-regular`, `cycling-road`,
`cycling-mountain`, `foot-walking`, `foot-hiking`, `wheelchair`.

**Isochrones** (script: `isochrone.py`) — reachability polygons:

```bash
isochrone.py -116.2023 43.6150 --minutes 5,10,15                  # drive-time bands
isochrone.py -116.2023 43.6150 --minutes 15 --profile foot-walking
isochrone.py -116.2023 43.6150 --km 2 --range-type distance > iso.geojson
```

Output is a GeoJSON `FeatureCollection` of nested polygons (one per band) —
render directly in Leaflet/MapLibre (`web-maps.md`). Classic uses: "what's
within a 15-min drive of this house", store catchment areas, "walkable from
here" overlays.

**Matrix** (durations/distances between many points):

```
POST https://api.openrouteservice.org/v2/matrix/driving-car
{"locations":[[lon,lat],...],"metrics":["duration","distance"]}
```

ORS free tier (per key): ~2000 directions/day, ~500 isochrone & matrix/day.
Plenty for dev; check current limits in the dashboard.

## Self-hosting (when free tiers aren't enough)

All consume a region `.osm.pbf` from Geofabrik (`setup.md`):

- **OSRM** — fastest for car routing at scale. Docker:
  `osrm/osrm-backend` (extract → partition/contract → routed).
- **Valhalla** — most flexible (multimodal, time-based, dynamic costing).
  Docker: `valhalla/valhalla`.
- **GraphHopper** — Java, easy to run, good defaults.

Point the scripts at a self-hosted OSRM by setting `OSRM_URL`.

## Picking for the user's likely cases

- "How far / how long by car between two points" → `route.py`.
- "Draw the 10-minute-walk area around this trailhead/house" → `isochrone.py`
  with `foot-walking`.
- "Best route hitting these N stops" → OSRM `/trip` (optimization) or ORS
  optimization endpoint.
- A web map with live directions → ORS directions + render the GeoJSON line
  (see `web-maps.md`).
