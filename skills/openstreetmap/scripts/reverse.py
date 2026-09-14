#!/usr/bin/env python3
"""Reverse geocode: coordinates -> nearest address, via Nominatim.

Usage (literal args only):
    reverse.py 43.6150 -116.2023
    reverse.py 43.6150 -116.2023 --zoom 16
    reverse.py 43.6150 -116.2023 --json

--zoom controls detail level: 3=country, 10=city, 16=street, 18=building.
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import NOMINATIM, http_get, emit, die  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Nominatim reverse geocoder")
    p.add_argument("lat", type=float)
    p.add_argument("lon", type=float)
    p.add_argument("--zoom", type=int, default=18,
                   help="detail 3=country .. 18=building (default 18)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    params = {
        "format": "jsonv2",
        "lat": args.lat,
        "lon": args.lon,
        "zoom": args.zoom,
        "addressdetails": 1,
    }
    r = http_get(f"{NOMINATIM}/reverse", params)
    if "error" in r:
        die(str(r["error"]))
    if args.json:
        emit(r, as_json=True)
        return
    print(r.get("display_name", "?"))


if __name__ == "__main__":
    main()
