# Overpass API — querying OSM data

Overpass is a read-only database query engine over the live OSM dataset. You
ask "give me every X in area Y" in **Overpass QL** and get back nodes, ways, and
relations. It's the power tool of OSM — and it has its own query language.

Script: `scripts/overpass.py` (put real queries in a file — they have braces,
brackets, and semicolons that wreck shell quoting).

```bash
overpass.py --query-file q.overpassql            # summary
overpass.py --query-file q.overpassql --geojson  # FeatureCollection for maps
overpass.py --query-file q.overpassql --csv name,amenity,opening_hours
```

Test/iterate queries visually first at **https://overpass-turbo.eu** — write,
run, see results on a map, then save the query to a file for the script.

## The data model

- **node** — a point (lat/lon). A cafe, a tree, a bench.
- **way** — an ordered list of nodes. A road, a building outline, a river.
- **relation** — a group of elements. A bus route, a multipolygon (lake with
  islands), an administrative boundary.

Everything carries **tags** (`key=value`): `amenity=cafe`, `name=Flying M`,
`highway=residential`. Tags are how you find things — see `tags.md`.

## Anatomy of a query

```overpassql
[out:json][timeout:25];
// find the area "Boise" and store it as searchArea
area[name="Boise"][admin_level=8]->.searchArea;
// all cafes within that area
node[amenity=cafe](area.searchArea);
// print results
out body;
```

1. **Settings** — `[out:json]` (or `out:csv`, `out:xml`), `[timeout:25]`,
   optional `[bbox:...]`.
2. **Statements** — selectors that build sets of elements, ending in `;`.
3. **Output** — `out body;` / `out center;` / `out geom;` etc.

## Filtering by location (4 ways)

```overpassql
node[amenity=cafe](43.61,-116.22,43.63,-116.19);   // bbox: S,W,N,E (lat,lon!)
node[amenity=cafe](around:500,43.6150,-116.2023);   // within 500 m of a point
node[amenity=cafe](area.searchArea);                // inside a named area
node[amenity=cafe](poly:"43.6 -116.2 43.7 -116.2 43.7 -116.1"); // polygon
```

⚠️ **bbox order is `south,west,north,east` = `minlat,minlon,maxlat,maxlon`** —
the opposite axis order from Nominatim's `viewbox` and from GeoJSON. The single
most common Overpass mistake.

## Tag selectors

```overpassql
node[amenity=cafe];                 // exact match
node[amenity];                      // has the key, any value
node[!amenity];                     // does NOT have the key
node[name~"Coffee",i];              // regex, case-insensitive
node[amenity~"cafe|restaurant"];    // regex value
node[amenity=cafe][wifi=yes];       // AND (chain selectors)
nwr[amenity=cafe];                  // nodes+ways+relations in one go
```

## Output modes (pick the right `out`)

| `out ...`     | Use when                                                       |
| ------------- | -------------------------------------------------------------- |
| `out body;`   | nodes (you get coords for free)                                |
| `out center;` | ways/relations and you only need a single representative point |
| `out geom;`   | you need full geometry (polygons, lines) inline                |
| `out tags;`   | tags only, no geometry (counts, attribute analysis)            |
| `out count;`  | just the number of matching elements                           |
| `out skel;`   | minimal (ids + refs)                                           |

For `--geojson` of ways/relations to work in `overpass.py`, add `out center;`
so each element has a `center`. For true polygons, use `out geom;` and convert
with a heavier tool.

## The union + recurse pattern (get cafes AND their geometry)

```overpassql
[out:json][timeout:25];
area[name="Boise"][admin_level=8]->.a;
(
  node[amenity=cafe](area.a);
  way[amenity=cafe](area.a);
  relation[amenity=cafe](area.a);
);
out center;
```

`( ... );` is a **union**. `nwr[...]` is shorthand for the same three lines.
`>;` after a set recurses **down** (way → its nodes); `<;` recurses **up**.

## Cookbook (drop into a file, run with overpass.py)

**Every coffee shop in Boise, as GeoJSON:**

```overpassql
[out:json][timeout:60];
area[name="Boise"][admin_level=8]->.a;
nwr[amenity=cafe](area.a);
out center;
```

**Trailheads within 20 km of downtown Boise:**

```overpassql
[out:json][timeout:60];
node[highway=trailhead](around:20000,43.6150,-116.2023);
out body;
```

**All parks (green space) in a bbox:**

```overpassql
[out:json][timeout:60];
nwr[leisure=park](43.55,-116.35,43.75,-116.10);
out center;
```

**Count restaurants by cuisine in an area (CSV):**

```overpassql
[out:csv(cuisine; true; ",")][timeout:60];
area[name="Boise"][admin_level=8]->.a;
nwr[amenity=restaurant](area.a);
out tags;
```

**EV charging stations in a county:**

```overpassql
[out:json][timeout:60];
area[name="Ada County"][admin_level=6]->.a;
nwr[amenity=charging_station](area.a);
out center;
```

**Drinking fountains near a point (handy for a trail app):**

```overpassql
[out:json][timeout:25];
node[amenity=drinking_water](around:1500,43.6150,-116.2023);
out body;
```

## Performance & manners

- Always set `[timeout:N]` and an `[out:...]`. Big areas → bigger timeout.
- Prefer `area`/`around`/bbox to global queries; never query the whole planet.
- `out center;` instead of `out geom;` when you don't need full polygons —
  vastly smaller responses.
- Don't run queries in a tight loop against the public server. If you're doing
  that, self-host Overpass (`setup.md`).
- 429/`runtime error: Query timed out` → narrow the area or raise the timeout,
  not retry-spam.

## Finding the right tags

You can't query what you can't name. `tags.md` has the common keys; the
authoritative source is the wiki (https://wiki.openstreetmap.org/wiki/Map_features)
and **https://taginfo.openstreetmap.org** to see how often a tag is actually
used in the wild.
