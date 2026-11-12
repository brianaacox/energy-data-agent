"""Pull monthly natural gas production and Henry Hub prices from the EIA API
and save the raw responses, untouched, to data/raw/."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("EIA_API_KEY")
if not API_KEY:
    raise SystemExit("EIA_API_KEY is missing from .env")

BASE_URL = "https://api.eia.gov/v2"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
START = "2010-01"
PAGE_SIZE = 5000  # the most rows EIA returns per request

DATASETS = {
    "production": {
        "route": "natural-gas/prod/sum",
        "facets": {
            "duoarea": ["STX", "SPA", "SLA", "SNM", "SOK", "SWV"],
            "process": ["FGW", "VGM"],
        },
    },
    "prices": {
        "route": "natural-gas/pri/fut",
        "facets": {"series": ["RNGWHHD"]},
    },
}


def fetch(route, facets):
    """Download every row for one dataset, one page at a time."""
    params = [
        ("api_key", API_KEY),
        ("frequency", "monthly"),
        ("data[0]", "value"),
        ("start", START),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("length", PAGE_SIZE),
    ]
    for facet, codes in facets.items():
        for code in codes:
            params.append((f"facets[{facet}][]", code))

    rows = []
    while True:
        response = requests.get(
            f"{BASE_URL}/{route}/data/",
            params=params + [("offset", len(rows))],
            timeout=60,
        )
        if response.status_code != 200:
            # Print the error text only, never the URL, which contains the key.
            raise SystemExit(f"EIA returned {response.status_code}: {response.text[:300]}")
        body = response.json()["response"]
        rows.extend(body["data"])
        if not body["data"] or len(rows) >= int(body["total"]):
            return rows


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name, spec in DATASETS.items():
        rows = fetch(spec["route"], spec["facets"])
        output = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "route": spec["route"],
            "facets": spec["facets"],
            "frequency": "monthly",
            "start": START,
            "rows": rows,
        }
        path = RAW_DIR / f"{name}.json"
        path.write_text(json.dumps(output, indent=2))

        periods = sorted(row["period"] for row in rows)
        print(f"\n{name}: {len(rows)} rows, {periods[0]} to {periods[-1]}")
        print(f"saved to {path}")
        series = sorted({
            (row.get("series"), row.get("series-description"), row.get("units"))
            for row in rows
        })
        for code, description, units in series:
            print(f"  {code} | {description} | {units}")


if __name__ == "__main__":
    main()
