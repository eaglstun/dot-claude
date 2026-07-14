#!/usr/bin/env python3
"""Routing (directions) via the public OSRM demo server.

OSRM's demo (router.project-osrm.org) serves the CAR profile only and is
strictly best-effort/no-SLA — fine for a quick distance/ETA, not for
production. For walking/cycling profiles, isochrones, or a matrix, see
references/routing.md (OpenRouteService / Valhalla / GraphHopper).

Coordinates are lon,lat (GeoJSON order), NOT lat,lon. Pass two or more.

Usage (literal args only):
    route.py -116.2023,43.6150 -116.1937,43.6629
    route.py -116.20,43.61 -116.19,43.66 --steps
    route.py -116.20,43.61 -116.19,43.66 --geojson > route.geojson
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import OSRM, http_get, emit, die  # noqa: E402


def fmt_dist(m):
    return f"{m/1000:.2f} km ({m*0.000621371:.2f} mi)"


def fmt_dur(s):
    m = int(s // 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m" if h else f"{m} min"


def main():
    p = argparse.ArgumentParser(description="OSRM directions (car profile)")
    p.add_argument("coords", nargs="+", metavar="lon,lat",
                   help="two or more 'lon,lat' waypoints")
    p.add_argument("--profile", default="driving",
                   help="OSRM demo only supports 'driving'")
    p.add_argument("--steps", action="store_true", help="print turn-by-turn")
    p.add_argument("--geojson", action="store_true",
                   help="emit the route line as GeoJSON")
    p.add_argument("--json", action="store_true", help="raw OSRM JSON")
    args = p.parse_args()

    if len(args.coords) < 2:
        die("need at least two 'lon,lat' waypoints")
    coord_str = ";".join(args.coords)
    params = {"overview": "full", "geometries": "geojson"}
    if args.steps:
        params["steps"] = "true"
    url = f"{OSRM}/route/v1/{args.profile}/{coord_str}"
    data = http_get(url, params)
    if data.get("code") != "Ok":
        die(f"OSRM: {data.get('code')} — {data.get('message','')}")

    route = data["routes"][0]
    if args.json:
        emit(data, as_json=True)
        return
    if args.geojson:
        emit({"type": "Feature", "geometry": route["geometry"],
              "properties": {"distance_m": route["distance"],
                             "duration_s": route["duration"]}}, as_json=True)
        return

    print(f"Distance: {fmt_dist(route['distance'])}")
    print(f"Duration: {fmt_dur(route['duration'])}")
    if args.steps:
        print("\nTurn-by-turn:")
        for leg in route.get("legs", []):
            for st in leg.get("steps", []):
                man = st["maneuver"]
                road = st.get("name", "")
                print(f"  {man['type']:>12} {man.get('modifier',''):>10}"
                      f"  {road}  ({fmt_dist(st['distance'])})")


if __name__ == "__main__":
    main()
