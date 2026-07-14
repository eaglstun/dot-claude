#!/usr/bin/env python3
"""Isochrones (reachability polygons) via OpenRouteService.

"Where can I get within 15 minutes of this point by car?" ORS returns the
answer as a GeoJSON polygon you can render directly.

Requires a free OpenRouteService API key in ORS_API_KEY
(get one at https://openrouteservice.org/dev/#/signup — generous free tier).
The OSRM demo server does NOT do isochrones; ORS/Valhalla do.

Usage (literal args only):
    isochrone.py -116.2023 43.6150 --minutes 15
    isochrone.py -116.2023 43.6150 --minutes 5,10,15 --profile foot-walking
    isochrone.py -116.2023 43.6150 --km 2 --range-type distance > iso.geojson

profiles: driving-car, foot-walking, cycling-regular (see references/routing.md)
"""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import USER_AGENT, emit, die  # noqa: E402

ORS = "https://api.openrouteservice.org/v2/isochrones"


def main():
    p = argparse.ArgumentParser(description="OpenRouteService isochrones")
    p.add_argument("lon", type=float)
    p.add_argument("lat", type=float)
    p.add_argument("--profile", default="driving-car")
    p.add_argument("--minutes", help="time bands, e.g. 5,10,15")
    p.add_argument("--km", help="distance bands, e.g. 1,2,5 (with --range-type distance)")
    p.add_argument("--range-type", default="time", choices=["time", "distance"])
    args = p.parse_args()

    key = os.environ.get("ORS_API_KEY")
    if not key:
        die("set ORS_API_KEY (free key: https://openrouteservice.org/dev/#/signup)")

    if args.range_type == "time":
        if not args.minutes:
            die("--minutes required for time isochrones")
        ranges = [int(float(x) * 60) for x in args.minutes.split(",")]
    else:
        if not args.km:
            die("--km required for distance isochrones")
        ranges = [int(float(x) * 1000) for x in args.km.split(",")]

    payload = json.dumps({
        "locations": [[args.lon, args.lat]],
        "range": ranges,
        "range_type": args.range_type,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{ORS}/{args.profile}", data=payload,
        headers={"Authorization": key, "Content-Type": "application/json",
                 "Accept": "application/geo+json", "User-Agent": USER_AGENT},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:400]}")

    emit(data, as_json=True)


if __name__ == "__main__":
    main()
