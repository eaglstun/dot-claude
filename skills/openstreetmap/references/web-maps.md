# Maps in web pages — Leaflet & MapLibre

Two ways to put an OSM map on a page. Pick by tile type:

- **Leaflet** — raster tiles (pre-rendered `.png` images). Tiny, dead simple,
  works everywhere. Best for markers, popups, GeoJSON overlays. **Default choice
  for a Hugo site.**
- **MapLibre GL JS** — vector tiles rendered in the browser via WebGL. Smooth
  zoom/rotate/tilt, restyleable, 3D. Heavier; needs a vector tile source + style.

Runnable starting points: `examples/leaflet.html`, `examples/maplibre.html`.
Open them straight in a browser.

> **For Protomaps / self-hosted vector tiles, use MapLibre — not Leaflet.** The
> `protomaps-leaflet` binding is in maintenance mode, and Leaflet can only show
> PMTiles as flat raster, defeating the point of vector tiles. New self-hosted
> map → MapLibre + Protomaps. See [`protomaps.md`](protomaps.md).

## Tiles & the attribution rule

OSM's raster tile server (`tile.openstreetmap.org`) is for **light/personal**
use only — no heavy traffic, and you **must** show attribution. For any real
site, use a provider's tiles (free tiers below). **Always** display
"© OpenStreetMap contributors" (providers add their own credit too).

| Provider      | Type              | Free tier | Notes                                                                                                     |
| ------------- | ----------------- | --------- | --------------------------------------------------------------------------------------------------------- |
| OSM standard  | raster            | light use | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` — don't ship at scale                                    |
| Carto         | raster            | yes       | clean "Positron"/"Dark Matter" styles                                                                     |
| Stadia Maps   | raster + vector   | yes (key) | Stamen styles (Toner/Watercolor) live here now                                                            |
| Thunderforest | raster            | yes (key) | outdoors/transport/cycle styles                                                                           |
| MapTiler      | raster + vector   | yes (key) | full vector styles + the easiest MapLibre setup                                                           |
| Protomaps     | vector (.pmtiles) | self-host | single-file tiles, **no tile server** — great for static/Hugo. Full guide: [`protomaps.md`](protomaps.md) |

## Leaflet — minimum viable map

```html
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="map" style="height:400px"></div>
<script>
  const map = L.map("map").setView([43.615, -116.2023], 13); // lat, lon
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  L.marker([43.615, -116.2023])
    .addTo(map)
    .bindPopup("Downtown Boise")
    .openPopup();
</script>
```

⚠️ Leaflet uses **`[lat, lon]`**. GeoJSON uses `[lon, lat]`. Leaflet's
`L.geoJSON()` handles the GeoJSON order for you — but your hand-written
`setView`/`marker` calls are lat,lon. Mind the flip.

### Drop in OSM data you queried

`overpass.py --geojson` and `route.py --geojson` produce GeoJSON that goes
straight in:

```js
fetch("cafes.geojson")
  .then((r) => r.json())
  .then((gj) => {
    L.geoJSON(gj, {
      onEachFeature: (f, layer) => layer.bindPopup(f.properties.name || "cafe"),
    }).addTo(map);
  });
```

Common Leaflet bits: `L.circle`, `L.polygon`, `L.polyline`, `L.layerGroup`,
`map.fitBounds(layer.getBounds())`, marker clustering via the
`leaflet.markercluster` plugin (for hundreds+ of points).

## MapLibre — vector map

```html
<link
  href="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.css"
  rel="stylesheet"
/>
<script src="https://unpkg.com/maplibre-gl@4/dist/maplibre-gl.js"></script>
<div id="map" style="height:400px"></div>
<script>
  const map = new maplibregl.Map({
    container: "map",
    // free demo style; swap for MapTiler/Protomaps with your own key/url
    style: "https://demotiles.maplibre.org/style.json",
    center: [-116.2023, 43.615], // lon, lat (note the order!)
    zoom: 12,
  });
  map.addControl(new maplibregl.NavigationControl());
  map.on("load", () => {
    new maplibregl.Marker()
      .setLngLat([-116.2023, 43.615])
      .setPopup(new maplibregl.Popup().setText("Downtown Boise"))
      .addTo(map);
  });
</script>
```

For real styling use MapTiler (`style: 'https://api.maptiler.com/maps/streets-v2/style.json?key=YOUR_KEY'`)
or self-host Protomaps `.pmtiles` (one file on your CDN — fits the
`pinecone-cdn` / Hugo setup nicely; full guide in [`protomaps.md`](protomaps.md)).
Add a GeoJSON layer:

```js
map.on("load", () => {
  map.addSource("cafes", { type: "geojson", data: "cafes.geojson" });
  map.addLayer({
    id: "cafes",
    type: "circle",
    source: "cafes",
    paint: { "circle-radius": 5, "circle-color": "#c0392b" },
  });
});
```

## Static maps (an image, no JS)

For a thumbnail or an email/PDF you want a plain image, not an interactive map.
The OSM foundation has no static-map API; use a provider:

- **MapTiler static maps:** `https://api.maptiler.com/maps/streets-v2/static/{lon},{lat},{zoom}/{w}x{h}.png?key=KEY&markers=...`
- **Geoapify / Stadia** also offer static-map endpoints (free tier, key).

Self-host option: render a Leaflet/MapLibre map headless and screenshot it
(you have Chrome automation + the Draw Things/Pollinations skills are unrelated;
for screenshots use the `claude-in-chrome` tools).

## Picking for a Hugo site

- A few markers, simple basemap, minimal weight → **Leaflet + Carto tiles**.
  Add it as a shortcode; load Leaflet from CDN only on pages that need it.
- Branded, smooth, custom-styled basemap → **MapLibre + MapTiler** (or
  Protomaps `.pmtiles` served from your CDN to avoid per-tile API costs).
- Just an image → a provider static-map URL in an `<img>`.

Always: lazy-load the library, set an explicit map height, and keep the
attribution visible.
