#!/usr/bin/env python3
"""Forward geocode: place name / address -> coordinates, via Nominatim.

Usage (literal args only — no $VARS, pipes, or redirects):
    geocode.py "Boise State University"
    geocode.py "1910 University Dr, Boise, ID" --limit 1
    geocode.py "cafe near Hyde Park Boise" --country us --json
    geocode.py --structured --city Boise --state Idaho --country us

Output: a compact table by default (name, lat, lon, type); full JSON with --json.
Respects Nominatim's policy: one request, descriptive User-Agent. For bulk
work, self-host or use a paid provider — see references/setup.md.
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import NOMINATIM, http_get, emit, die  # noqa: E402


def main():
    p = argparse.ArgumentParser(description="Nominatim forward geocoder")
    p.add_argument("query", nargs="?", help="free-form place/address text")
    p.add_argument("--limit", type=int, default=5, help="max results (default 5)")
    p.add_argument("--country", help="ISO 3166-1 alpha-2 filter, e.g. us")
    p.add_argument("--viewbox", help="bias to bbox: minlon,minlat,maxlon,maxlat")
    p.add_argument("--bounded", action="store_true",
                   help="restrict strictly to --viewbox")
    p.add_argument("--addressdetails", action="store_true",
                   help="include a parsed address breakdown")
    p.add_argument("--json", action="store_true", help="raw JSON output")
    # structured-query fields (mutually exclusive with free-form query)
    p.add_argument("--structured", action="store_true",
                   help="use the structured-query fields below")
    for f in ("street", "city", "county", "state", "postalcode"):
        p.add_argument(f"--{f}")
    args = p.parse_args()

    params = {"format": "jsonv2", "limit": args.limit}
    if args.structured:
        for f in ("street", "city", "county", "state", "postalcode"):
            v = getattr(args, f)
            if v:
                params[f] = v
        if getattr(args, "country"):
            params["country"] = args.country
        if len(params) <= 2:
            die("--structured needs at least one of --street/--city/--state/...")
    else:
        if not args.query:
            die("provide a query string, or use --structured with fields")
        params["q"] = args.query
        if args.country:
            params["countrycodes"] = args.country
    if args.viewbox:
        params["viewbox"] = args.viewbox
    if args.bounded:
        params["bounded"] = 1
    if args.addressdetails:
        params["addressdetails"] = 1

    results = http_get(f"{NOMINATIM}/search", params)
    if not results:
        die("no matches")
    if args.json:
        emit(results, as_json=True)
        return
    for r in results:
        name = r.get("display_name", "?")
        print(f"{r['lat']:>12} {r['lon']:>12}  [{r.get('type','?')}]  {name}")


if __name__ == "__main__":
    main()
