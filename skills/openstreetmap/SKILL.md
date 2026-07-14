---
name: openstreetmap
version: 1.0.0
public: true
description: >-
  Work with OpenStreetMap data and maps — geocode addresses ↔ coordinates (Nominatim),
  query features by tag/area (Overpass QL), get directions and drive/walk-time isochrones
  (OSRM/OpenRouteService), and embed interactive or static maps (Leaflet/MapLibre, tile
  providers). Use when the user wants coordinates for a place, what's at a location, OSM
  features ("all cafes/trails/parks in X"), routes or reachability areas, a map on a site,
  or asks about OSM/Nominatim/Overpass/Leaflet/MapLibre/tiles.
semantic_id: "XXlvLDq53fvHXeSdo59K7kR5yNKKwAAF"
related_ids:
  - "DnvnaKG83eW1tLd7GVw6emSYqTIK8AAN"
topic_id: "v2:FKBP"
topic_path: "site-tools/visual-maps"
---

# OpenStreetMap

OSM is free geodata; the public servers that serve it are donated, shared, and
rate-limited. The scripts here are good citizens by default (descriptive
User-Agent, polite pacing). **Read [`references/setup.md`](references/setup.md)
before any non-trivial or repeated use** — it's the difference between "works"
and "IP banned." Always show "© OpenStreetMap contributors" when you display the
data or a map.

This file is an index — load the one reference for your task; each is
self-contained.

## Pick a doc

| Task                                                      | Reference                                            |
| --------------------------------------------------------- | ---------------------------------------------------- |
| Address ↔ coordinates (geocode / reverse / autocomplete)  | [`references/geocoding.md`](references/geocoding.md) |
| Query OSM features by tag/area (Overpass QL + cookbook)   | [`references/overpass.md`](references/overpass.md)   |
| Directions, isochrones, travel-time matrices              | [`references/routing.md`](references/routing.md)     |
| Maps in web pages (Leaflet / MapLibre, tiles, static)     | [`references/web-maps.md`](references/web-maps.md)   |
| Self-hosted vector tiles (Protomaps / PMTiles + MapLibre) | [`references/protomaps.md`](references/protomaps.md) |
| Tag cheat sheet (what to put in an Overpass query)        | [`references/tags.md`](references/tags.md)           |
| Endpoints, keys, fair-use policy, self-hosting, data      | [`references/setup.md`](references/setup.md)         |

## Scripts at a glance

Pure-stdlib Python 3 (no pip installs). No API key needed except `isochrone.py`.
Every script supports `--json`. Pass **literal args only** (no `$VARS`, pipes, or
redirects into the script) so calls stay permission-friendly; put Overpass
queries in a file.

```bash
# Geocoding (Nominatim) — no key
scripts/geocode.py "Boise State University"            # text → coords
scripts/geocode.py --structured --city Boise --state Idaho --country us
scripts/reverse.py 43.6150 -116.2023                   # coords → address

# Data queries (Overpass) — no key. Iterate visually at overpass-turbo.eu first.
scripts/overpass.py --query-file q.overpassql --geojson > cafes.geojson
scripts/overpass.py --query-file q.overpassql --csv name,amenity

# Routing (OSRM demo, car only) — no key
scripts/route.py -116.2023,43.6150 -116.1937,43.6629   # coords are lon,lat!
scripts/route.py -116.20,43.61 -116.19,43.66 --steps --geojson

# Isochrones (OpenRouteService) — needs free ORS_API_KEY
scripts/isochrone.py -116.2023 43.6150 --minutes 5,10,15 > iso.geojson
```

## Web-map examples

Openable HTML starting points — drop into a page or a Hugo shortcode:

- [`examples/leaflet.html`](examples/leaflet.html) — raster tiles, simplest, default for a site.
- [`examples/maplibre.html`](examples/maplibre.html) — vector tiles, smooth/restyleable.

Both show loading `overpass.py --geojson` / `route.py --geojson` output directly.

## The one gotcha that bites everyone: coordinate order

| Where                                                     | Order                                                   |
| --------------------------------------------------------- | ------------------------------------------------------- |
| Nominatim params / Leaflet `setView`/`marker`             | **lat, lon**                                            |
| GeoJSON, Overpass `out center`, routing engines, MapLibre | **lon, lat**                                            |
| Overpass **bbox** filter                                  | **south,west,north,east** (minlat,minlon,maxlat,maxlon) |

When a result lands in the ocean off West Africa (0,0) or the wrong hemisphere,
it's almost always this.
