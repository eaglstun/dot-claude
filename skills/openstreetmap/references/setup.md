# Setup, endpoints & usage policy (read this first)

OpenStreetMap data is free; the _servers_ that dish it out are donated, shared
infrastructure with strict fair-use rules. Break them and you get a `403`/`429`
and eventually an IP ban. The skill's scripts already behave; this is the why,
plus how to scale past the toy limits.

## The three rules that get you banned

1. **Send a real User-Agent.** Every OSM service requires a descriptive UA (or
   `Referer`) identifying your app and a contact. The scripts send
   `your-app/1.0 (+you@example.com)` — change it in
   `scripts/_common.py` if you fork this for something public.
2. **Don't hammer.** Nominatim: **≤ 1 request/second, absolute max**. Overpass:
   be gentle, set a `timeout`, don't run parallel heavy queries. Tiles: no bulk
   downloading, no scraping.
3. **Cache and attribute.** Cache results you'll reuse. Show
   "© OpenStreetMap contributors" anywhere you display the data or map.

The full policies (worth a skim once):

- Nominatim: https://operations.osmfoundation.org/policies/nominatim/
- Tile server: https://operations.osmfoundation.org/policies/tiles/
- Overpass: https://dev.overpass-api.de/overpass-doc/en/preface/commons.html

## Public endpoints (defaults the scripts use)

| Service      | Default URL                               | Env override    | Auth |
| ------------ | ----------------------------------------- | --------------- | ---- |
| Nominatim    | `https://nominatim.openstreetmap.org`     | `NOMINATIM_URL` | none |
| Overpass     | `https://overpass-api.de/api/interpreter` | `OVERPASS_URL`  | none |
| OSRM (demo)  | `https://router.project-osrm.org`         | `OSRM_URL`      | none |
| Photon (geo) | `https://photon.komoot.io`                | `PHOTON_URL`    | none |

Keys (only where noted):

- **OpenRouteService** (`isochrone.py`, advanced routing): free key in
  `ORS_API_KEY` — https://openrouteservice.org/dev/#/signup
- **MapTiler / Stadia / Thunderforest** (nice tiles & vector styles for web
  maps): free tier, key per provider — see `web-maps.md`.

## When to stop using the public servers

The free instances are for **light, interactive** use. The moment you're doing
any of these, move to a hosted plan or self-host:

- Bulk/batch geocoding (more than a trickle) → **don't** use public Nominatim.
- A production website hitting tiles at scale → use a tile provider with a key.
- Heavy Overpass extraction → run your own Overpass instance, or use a planet
  extract + a local tool (`osmium`, `osm2pgsql` + PostGIS).

### Self-hosting / paid shortcuts

- **Geocoding at scale:** self-host Nominatim (Docker:
  `mediagis/nominatim`), or use a paid geocoder (LocationIQ, Geocodio, Google).
- **Tiles at scale:** MapTiler, Stadia Maps, Thunderforest, Protomaps
  (`.pmtiles` — serverless, no tile server needed), or self-host with
  `tileserver-gl` / OpenMapTiles.
- **Routing at scale:** self-host OSRM, Valhalla, or GraphHopper from a planet
  PBF, or use OpenRouteService / Mapbox / GraphHopper hosted plans.

## Tooling on this machine

The scripts are pure-stdlib Python 3 — nothing to install. For heavier local
data work you'd want (not required by the skill):

```bash
brew install osmium-tool   # slice/filter/convert .osm.pbf extracts
brew install gdal          # ogr2ogr: convert GeoJSON <-> shapefile, etc.
pip install osmnx          # OSM street networks as NetworkX graphs (research)
```

## Where to get raw OSM data

- **Region extracts:** https://download.geofabrik.de (e.g. Idaho `.osm.pbf`)
- **Small areas, live:** Overpass (see `overpass.md`)
- **Full planet:** https://planet.openstreetmap.org (~80 GB compressed — only if
  you really mean it)
