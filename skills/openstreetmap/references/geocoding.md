# Geocoding — Nominatim (and Photon)

Turning text into coordinates and back. Two free engines on OSM data:

- **Nominatim** — the canonical geocoder. Best for full addresses & places.
- **Photon** — Komoot's geocoder, built for **autocomplete / fuzzy search**
  (type-ahead). Faster, typo-tolerant, weaker on structured addresses.

Both obey the same fair-use spirit (`setup.md`). Scripts:
`scripts/geocode.py`, `scripts/reverse.py`.

## Forward geocoding (text → coords)

```bash
geocode.py "Boise State University"
geocode.py "1910 University Dr, Boise, ID" --limit 1 --json
geocode.py "trailhead" --viewbox -116.3,43.55,-116.1,43.75 --bounded
```

Structured query (more precise than free-form when you have the parts):

```bash
geocode.py --structured --street "1910 University Dr" --city Boise --state Idaho --country us
```

### Raw API

`GET https://nominatim.openstreetmap.org/search`

| Param                                         | Meaning                                                  |
| --------------------------------------------- | -------------------------------------------------------- |
| `q`                                           | free-form query (don't combine with structured fields)   |
| `street/city/county/state/country/postalcode` | structured query fields                                  |
| `format`                                      | `jsonv2` (recommended), `geojson`, `geocodejson`, `xml`  |
| `limit`                                       | max results (default 10)                                 |
| `countrycodes`                                | comma list of ISO alpha-2, e.g. `us,ca`                  |
| `viewbox`                                     | `minlon,minlat,maxlon,maxlat` — bias results to this box |
| `bounded=1`                                   | hard-restrict to `viewbox`                               |
| `addressdetails=1`                            | include a parsed `address{}` object                      |
| `extratags=1`                                 | include extra OSM tags (website, opening_hours, ...)     |
| `dedupe=1`                                    | drop near-duplicate results (default on)                 |

```bash
curl -s 'https://nominatim.openstreetmap.org/search?q=Hyde+Park+Boise&format=jsonv2&limit=1' \
  -H 'User-Agent: my-app/1.0 (me@example.com)'
```

Key fields in each result: `lat`, `lon`, `display_name`, `type`, `class`,
`importance`, `boundingbox` (`[minlat,maxlat,minlon,maxlon]`), `osm_type`/`osm_id`.

## Reverse geocoding (coords → address)

```bash
reverse.py 43.6150 -116.2023            # building-level
reverse.py 43.6150 -116.2023 --zoom 10  # city-level
```

`GET .../reverse?lat=..&lon=..&format=jsonv2&zoom=18&addressdetails=1`

`zoom` controls the address granularity returned:

| zoom | level              |
| ---- | ------------------ |
| 3    | country            |
| 5    | state              |
| 10   | city               |
| 14   | suburb             |
| 16   | major street       |
| 18   | building (default) |

## Gotchas

- **lat,lon vs lon,lat:** Nominatim takes `lat`/`lon` as named params and
  returns `lat`,`lon` strings. GeoJSON, Overpass `out center`, and routing use
  `[lon, lat]`. Mixing these up puts you in the ocean — double-check order.
- **Coverage = whatever's mapped.** Rural/new addresses may be missing; fall
  back to nearest-street reverse, or interpolation results (`type=house`,
  `class=place`).
- **Rate limit is real:** loop with `polite_sleep()` (≥1 s). For more than a
  handful, self-host or use a paid geocoder (`setup.md`).
- **`importance`** ranks results 0–1; the first result isn't always the one you
  want — inspect `type`/`class` (e.g. `boundary`/`administrative` for a whole
  city vs `place`/`city` for the point).

## Photon (autocomplete)

No script (it's a one-liner), but handy for type-ahead UIs:

```bash
curl -s 'https://photon.komoot.io/api/?q=boise+st&limit=5&lat=43.6&lon=-116.2'
```

Returns GeoJSON features. `lat`/`lon` bias toward a location; `bbox` restricts;
`osm_tag` filters (e.g. `osm_tag=place:city`). Great paired with a debounced
input box in a web map.
