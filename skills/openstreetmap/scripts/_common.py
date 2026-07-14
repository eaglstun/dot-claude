"""Shared plumbing for the OpenStreetMap skill scripts.

Pure stdlib — no pip deps. Every public OSM service (Nominatim, the tile
server, Overpass) requires a descriptive User-Agent identifying the app and
a contact, and rate-limits anonymous traffic hard. These helpers make sure
every call is a good citizen so we don't get the IP banned.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Identify ourselves on every request. OSM's usage policies REQUIRE a
# descriptive UA with a way to reach the operator; a generic urllib UA is a
# fast track to a 403/429 and eventually a ban.
USER_AGENT = "your-app/1.0 (+you@example.com)"

# Public endpoints. Swap to a self-hosted instance via the matching env var
# for anything beyond light interactive use (see references/setup.md).
import os

NOMINATIM = os.environ.get("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
OVERPASS = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
OSRM = os.environ.get("OSRM_URL", "https://router.project-osrm.org")
PHOTON = os.environ.get("PHOTON_URL", "https://photon.komoot.io")


def http_get(url, params=None, accept_json=True):
    """GET with the required UA. Returns parsed JSON (or raw text)."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    return _request(url, data=None, accept_json=accept_json)


def http_post(url, data, content_type="application/x-www-form-urlencoded",
              accept_json=True):
    """POST raw bytes (used by Overpass, which prefers POST for big queries)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _request(url, data=data, content_type=content_type,
                    accept_json=accept_json)


def _request(url, data=None, content_type=None, accept_json=True):
    headers = {"User-Agent": USER_AGENT}
    if accept_json:
        headers["Accept"] = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:500]
        except Exception:
            pass
        die(f"HTTP {e.code} {e.reason} from {url}\n{detail}")
    except urllib.error.URLError as e:
        die(f"Network error reaching {url}: {e.reason}")
    if not accept_json:
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        die(f"Expected JSON, got:\n{body[:500]}")


def polite_sleep(seconds=1.0):
    """Nominatim's policy is <= 1 request/second. Call between loop iterations."""
    time.sleep(seconds)


def emit(obj, as_json=False):
    """Print a result: pretty JSON when --json, else hand back the object."""
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    return obj


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)
