# openstreetmap

Claude Code skill for working with **OpenStreetMap** data and maps across its
four main surfaces: geocoding (Nominatim), feature queries (Overpass QL),
routing & isochrones (OSRM / OpenRouteService), and embedding maps in web pages
(Leaflet / MapLibre). Ships runnable pure-stdlib Python scripts — no pip, no API
key for geocoding, Overpass, and car routing — plus copy-paste web-map examples.

Built around being a good citizen on OSM's donated, rate-limited public servers:
every script sends a descriptive User-Agent and paces itself. See
`references/setup.md` before any heavy/repeated use.

## Scripts at a glance

```bash
scripts/geocode.py "Boise State University"          # text → coordinates
scripts/reverse.py 43.6150 -116.2023                 # coordinates → address
scripts/overpass.py --query-file q.overpassql --geojson   # OSM features → GeoJSON
scripts/route.py -116.2023,43.6150 -116.1937,43.6629 # directions (car)
scripts/isochrone.py -116.2023 43.6150 --minutes 15  # drive-time polygon (needs ORS_API_KEY)
```

All support `--json`. Coordinates are `lon,lat` for routing/Overpass/GeoJSON and
`lat lon` for Nominatim — the skill's #1 footgun.

## Docs

`SKILL.md` is the entry point; load the reference matching the task:

| Task                                           | Doc                                                  |
| ---------------------------------------------- | ---------------------------------------------------- |
| Geocoding (forward / reverse / autocomplete)   | [`references/geocoding.md`](references/geocoding.md) |
| Overpass QL queries + cookbook                 | [`references/overpass.md`](references/overpass.md)   |
| Routing, isochrones, matrices                  | [`references/routing.md`](references/routing.md)     |
| Maps in web pages (Leaflet / MapLibre)         | [`references/web-maps.md`](references/web-maps.md)   |
| Self-hosted vector tiles (Protomaps / PMTiles) | [`references/protomaps.md`](references/protomaps.md) |
| OSM tag cheat sheet                            | [`references/tags.md`](references/tags.md)           |
| Endpoints, keys, fair-use, self-hosting        | [`references/setup.md`](references/setup.md)         |

Web-map starting points: [`examples/leaflet.html`](examples/leaflet.html),
[`examples/maplibre.html`](examples/maplibre.html).
