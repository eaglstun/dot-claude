#!/usr/bin/env python3
"""Run an Overpass QL query against the Overpass API.

Overpass QL is its own little language — see references/overpass.md for the
syntax and a cookbook. This just submits a query and hands back the result.

Usage (literal args only — put real queries in a file to stay shell-safe):
    overpass.py --query-file my_query.overpassql
    overpass.py --query-file q.txt --json
    overpass.py --query-file q.txt --csv name,amenity
    overpass.py --inline "[out:json];node[amenity=cafe](43.6,-116.3,43.7,-116.1);out;"

By default prints a name/type/coords summary of returned elements. --json
dumps the full response; --geojson emits a FeatureCollection you can drop
straight into Leaflet/MapLibre.
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import OVERPASS, http_post, emit, die  # noqa: E402


def to_geojson(data):
    feats = []
    for el in data.get("elements", []):
        if el["type"] == "node":
            lon, lat = el.get("lon"), el.get("lat")
        else:  # way/relation with 'center' (add 'out center;' to your query)
            c = el.get("center")
            if not c:
                continue
            lon, lat = c["lon"], c["lat"]
        if lon is None or lat is None:
            continue
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"osm_type": el["type"], "osm_id": el["id"],
                           **el.get("tags", {})},
        })
    return {"type": "FeatureCollection", "features": feats}


def main():
    p = argparse.ArgumentParser(description="Overpass API client")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--query-file", help="path to a file containing Overpass QL")
    g.add_argument("--inline", help="Overpass QL as a single literal string")
    p.add_argument("--json", action="store_true", help="raw JSON response")
    p.add_argument("--geojson", action="store_true",
                   help="emit a GeoJSON FeatureCollection")
    p.add_argument("--csv", help="comma-separated tag keys for a CSV summary")
    args = p.parse_args()

    if args.query_file:
        with open(args.query_file, encoding="utf-8") as fh:
            ql = fh.read()
    else:
        ql = args.inline

    data = http_post(OVERPASS, data=f"data={ql}")
    if "remark" in data and not data.get("elements"):
        die(f"Overpass remark: {data['remark']}")

    if args.json:
        emit(data, as_json=True)
        return
    if args.geojson:
        emit(to_geojson(data), as_json=True)
        return

    els = data.get("elements", [])
    if args.csv:
        keys = [k.strip() for k in args.csv.split(",")]
        print(",".join(keys))
        for el in els:
            tags = el.get("tags", {})
            print(",".join('"%s"' % str(tags.get(k, "")).replace('"', '""')
                           for k in keys))
        return

    print(f"{len(els)} elements")
    for el in els[:200]:
        tags = el.get("tags", {})
        name = tags.get("name", "(unnamed)")
        coord = ""
        if el["type"] == "node":
            coord = f"{el.get('lat')},{el.get('lon')}"
        elif el.get("center"):
            coord = f"{el['center']['lat']},{el['center']['lon']}"
        print(f"  {el['type']}/{el['id']}  {name}  {coord}")
    if len(els) > 200:
        print(f"  ... {len(els) - 200} more (use --json/--geojson for all)")


if __name__ == "__main__":
    main()
