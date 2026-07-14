# Protomaps — self-hosted vector tiles, no tile server

Protomaps is the best "host your own tiles" story for a static/Hugo + CDN setup
like the user's. The whole basemap is **one file** (`.pmtiles`) you drop on object
storage or a plain web server. No tile server, no per-tile API bill, no
running process — the browser pulls only the bytes it needs via HTTP **range
requests**.

Three parts: the **PMTiles format** (single-file tile archive), the **`pmtiles`
CLI** (build/slice/serve), and a ready-made **OSM basemap** (daily planet build,
ODbL).

> **Use MapLibre GL JS, not Leaflet, for Protomaps.** The `protomaps-leaflet`
> library is in **maintenance mode** — the official docs say to use it only for
> legacy Leaflet projects. For anything new, render PMTiles with MapLibre GL JS
> (vector, smooth, restyleable). Leaflet can only show Protomaps as flat _raster_
> tiles via `leafletRasterLayer`, which throws away the whole point of vector
> tiles. So: **MapLibre over protomaps-leaflet.** See `web-maps.md` for the
> raster-Leaflet fallback if you're truly stuck on Leaflet.

## Why this fits the user's stack

- A `.pmtiles` file is just a static asset → drop it on the droplet's
  `cdn.example.com`, or on DigitalOcean Spaces. nginx supports range
  requests out of the box; you only need to add a CORS header (§4 has both,
  ready to paste).
- No tile API key, no usage cap, no surprise bill. Compared to per-tile
  providers, "70%+ storage savings and avoids millions of API requests."
- Regional cutout instead of the planet keeps it small enough to host anywhere.

## 1. Get a basemap `.pmtiles`

The Protomaps OSM basemap is built daily.

- **Daily builds:** `https://maps.protomaps.com/builds/` (current is the v4
  basemap; URLs can change — don't hotlink in production, copy to your own
  storage).
- **Full planet** is ~**120 GB** (z0–15). You almost never want the whole thing.

**Slice out just the region you need** with the CLI — and `extract` works
against the _remote_ archive, so you download only your cutout, not the planet:

```bash
# Idaho-ish bbox, from the latest remote daily build, limited to z0–13
pmtiles extract https://maps.protomaps.com/builds/20260601.pmtiles idaho.pmtiles \
  --bbox=-117.24,41.99,-111.04,49.00 --maxzoom=13
```

Each extra zoom level roughly doubles size — cap `--maxzoom` to what your map
actually shows (z12–14 is plenty for a regional site).

## 2. The `pmtiles` CLI

Single static binary, no deps. Grab it from
https://github.com/protomaps/go-pmtiles/releases (or `protomaps/go-pmtiles`
Docker image). On a Mac: `brew install protomaps/tap/pmtiles` if available, else
download the release binary.

```bash
pmtiles show idaho.pmtiles                 # header + metadata summary
pmtiles show idaho.pmtiles --metadata      # full tilejson-ish metadata
pmtiles verify idaho.pmtiles               # integrity check

# Slice a region (bbox or a GeoJSON polygon), optionally cap zoom
pmtiles extract IN.pmtiles OUT.pmtiles --bbox=MINLON,MINLAT,MAXLON,MAXLAT
pmtiles extract IN.pmtiles OUT.pmtiles --region=area.geojson --maxzoom=14

# Convert a legacy MBTiles (e.g. from tippecanoe) to PMTiles
pmtiles convert tiles.mbtiles tiles.pmtiles

# Serve locally as a z/x/y endpoint for quick testing
pmtiles serve . --port=8080
# → http://localhost:8080/idaho/{z}/{x}/{y}.mvt
```

Building your _own_ vector tiles from GeoJSON/OSM (instead of the OSM basemap):
make MBTiles with **tippecanoe**, then `pmtiles convert`.

## 3. Render with MapLibre GL JS

Two pieces: the `pmtiles` package registers the `pmtiles://` protocol, and
`@protomaps/basemaps` generates the cartography (style layers) for the OSM
basemap.

```html
<link
  href="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.css"
  rel="stylesheet"
/>
<script src="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/pmtiles@4/dist/pmtiles.js"></script>
<script
  src="https://unpkg.com/@protomaps/basemaps@5/dist/basemaps.js"
  crossorigin="anonymous"
></script>
<div id="map" style="height:100vh"></div>
<script>
  // Register the pmtiles:// protocol once.
  const protocol = new pmtiles.Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);

  const map = new maplibregl.Map({
    container: "map",
    center: [-116.2023, 43.615], // lon, lat
    zoom: 11,
    style: {
      version: 8,
      glyphs:
        "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
      sprite: "https://protomaps.github.io/basemaps-assets/sprites/v4/light",
      sources: {
        protomaps: {
          type: "vector",
          // your self-hosted file — note the pmtiles:// prefix
          url: "pmtiles://https://cdn.example.com/idaho.pmtiles",
          attribution:
            '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> · <a href="https://protomaps.com">Protomaps</a>',
        },
      },
      // basemaps.layers(source, flavor, opts) builds the cartography
      layers: basemaps.layers("protomaps", basemaps.namedFlavor("light"), {
        lang: "en",
      }),
    },
  });
  map.addControl(new maplibregl.NavigationControl());
</script>
```

**Flavors** (`namedFlavor("...")`): `light`, `dark`, `white`, `black`,
`grayscale`. Options: `{ lang: "en" }` for label language, `{ labelsOnly: true }`
for a labels-only overlay.

ESM/bundler form:

```js
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";
import { layers, namedFlavor } from "@protomaps/basemaps";
const protocol = new Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);
// ...style.layers = layers("protomaps", namedFlavor("dark"), { lang: "en" })
```

In React, call `addProtocol` once in a root `useEffect` and `removeProtocol` on
cleanup.

> **Version drift:** the `@protomaps/basemaps` package (major **5**), the sprite
> asset path (`/v4/`), and the basemap _build_ (v4) carry independent version
> numbers and move over time. The snippet above is the current shape; if labels
> or sprites render wrong, check the matching versions at docs.protomaps.com.

## 4. Host the `.pmtiles` file — two options for the user's setup

The browser just needs HTTP **range requests** + permissive **CORS**. Both
options below give you that. Decision rule:

- **Small/medium regional cutout (≲ ~1 GB), one or two sites** → put it on the
  **droplet's `cdn.example.com`**. Simplest; the wildcard cert already
  covers it; zero new infra.
- **Large file, or you want it off the droplet's disk/bandwidth** → **DO
  Spaces** (object storage + built-in CDN edge, already in your DO account).

> **Won't this kill the 1 GB droplet?** No. nginx serves a `.pmtiles` via byte
> ranges straight from the page cache — it never loads the whole file into RAM,
> so it behaves like any other static read (cheap on that box, per the
> `digitalocean` skill). The real constraint is **disk**, not RAM: keep the
> cutout modest with `--bbox` + `--maxzoom` (Idaho at z13 is a few hundred MB).
> A planet-scale file would blow the disk — don't put that here; use Spaces.

### Option A — the droplet (`cdn.example.com`)

1. **Upload** the file as `eric` (who owns `/var/www/cdn.example.com`):
   ```bash
   rsync -avz --progress idaho.pmtiles user@your-server.example.com:/var/www/cdn.example.com/
   ```
2. **Add a `.pmtiles` location** to that vhost
   (`/etc/nginx/sites-available/cdn.example.com`, edit with sudo). The
   site's `/` returns 204, but file requests serve fine — this block just adds
   CORS + cache and disables gzip for the format:
   ```nginx
   location ~ \.pmtiles$ {
       add_header Access-Control-Allow-Origin  "*"            always;
       add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS" always;
       add_header Access-Control-Allow-Headers "Range"        always;
       add_header Access-Control-Expose-Headers "Content-Length, Content-Range" always;
       add_header Cache-Control "public, max-age=86400";
       gzip off;          # never gzip pmtiles — it breaks range requests
       # byte-range support is on by default in nginx
   }
   ```
3. **Reload** (needs the sudo password — keep the user in the loop):
   ```bash
   ssh user@your-server.example.com 'sudo nginx -t && sudo systemctl reload nginx'
   ```
4. Your source URL becomes
   `pmtiles://https://cdn.example.com/idaho.pmtiles`.

### Option B — DigitalOcean Spaces (+ CDN)

S3-compatible; use `s3cmd`/`aws` CLI or the DO control panel. Spaces has an
optional CDN edge — enable it and serve from the `*.cdn.digitaloceanspaces.com`
hostname so range requests hit the edge, not origin.

```bash
# with s3cmd configured for the DO Spaces endpoint (nyc3 example)
s3cmd put idaho.pmtiles s3://my-space/idaho.pmtiles --acl-public \
  --add-header="Cache-Control:public, max-age=86400"
```

Then set a **CORS rule** on the Space (control panel → Settings → CORS, or via
the API) allowing origin `https://*.pinecone.website` (or `*`), methods
`GET, HEAD`, and the `Range` request header. Source URL:
`pmtiles://https://my-space.nyc3.cdn.digitaloceanspaces.com/idaho.pmtiles`.

Choose Spaces when the cutout is large, traffic is heavy, or you'd rather not
spend the droplet's modest disk/bandwidth on map tiles.

### Sanity checks after deploy (either option)

```bash
pmtiles show https://cdn.example.com/idaho.pmtiles   # reads over HTTP via range reqs
curl -sI -H 'Range: bytes=0-99' https://cdn.example.com/idaho.pmtiles \
  | grep -i 'content-range\|access-control'
```

You want a **`206 Partial Content`** and an `Access-Control-Allow-Origin` header
back. No 206 → range requests blocked (gzip or a proxy stripping ranges). No
CORS header → the map silently fails cross-origin.

## Inspect / debug

- **https://pmtiles.io** — drag-and-drop viewer: open a local or remote
  `.pmtiles`, inspect tiles, check it renders before wiring up the site.
- `pmtiles show --metadata` to confirm the layer names your style references
  actually exist in the archive.

## Attribution (required)

The Protomaps basemap is OSM data under ODbL. Always show **© OpenStreetMap
contributors** (the `attribution` field above does this); crediting Protomaps
too is polite.
