"""Snapshot the DefiLlama emissions store for unlock_xs_t1.

DefiLlama serves the *current* unlock schedule and amends it silently
(data-source audit 2026-07-30), so the snapshot is stamped with a vintage
record at fetch time: per-file sha256 + byte size, the protocol-list hash,
and fetched_utc. P0 in scripts/unlock_xs_dev.py reads the stamp offline —
the same no-live-network-at-probe-time contract value_xs_t1 settled on
after two fix rounds.

Also snapshots the CoinGecko /coins/list mapping (gecko_id -> ticker),
needed to intersect emissions protocols with the 799-symbol perp store.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "xsect" / "emissions"
VINTAGE_FILE = ROOT / "data" / "xsect" / "emissions_vintage.json"
GECKO_LIST_FILE = ROOT / "data" / "xsect" / "coingecko_coins_list.json"

LIST_URL = "https://defillama-datasets.llama.fi/emissionsProtocolsList"
EMISSIONS_URL = "https://defillama-datasets.llama.fi/emissions/{slug}"
GECKO_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"


def _get(url: str, retries: int = 4, timeout: float = 30.0) -> requests.Response:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                time.sleep(15 * (i + 1))
                continue
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed after {retries} tries: {url}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-existing", action="store_true",
                   help="do not re-download files already on disk (resume only; "
                        "a mixed-vintage store is disclosed in the stamp)")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fetched_utc = datetime.now(timezone.utc).isoformat()

    raw_list = _get(LIST_URL).content
    slugs = json.loads(raw_list)
    list_sha = hashlib.sha256(raw_list).hexdigest()
    print(f"protocol list: {len(slugs)} slugs sha256={list_sha[:12]}")

    if not GECKO_LIST_FILE.exists():
        GECKO_LIST_FILE.write_bytes(_get(GECKO_LIST_URL).content)
        print("coingecko coins list snapshotted")

    files, failed, skipped = {}, [], 0
    for i, slug in enumerate(sorted(slugs)):
        dest = OUT_DIR / f"{slug}.json"
        if args.skip_existing and dest.exists():
            body = dest.read_bytes()
            skipped += 1
        else:
            try:
                body = _get(EMISSIONS_URL.format(slug=slug)).content
                json.loads(body)  # refuse to store non-JSON error pages
            except (RuntimeError, json.JSONDecodeError) as e:
                failed.append({"slug": slug, "error": str(e)[:200]})
                continue
            dest.write_bytes(body)
        files[slug] = {"sha256": hashlib.sha256(body).hexdigest(),
                       "bytes": len(body)}
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(slugs)} fetched")

    stamp = {
        "fetched_utc": fetched_utc,
        "source": EMISSIONS_URL,
        "protocol_list_sha256": list_sha,
        "n_slugs": len(slugs),
        "n_ok": len(files),
        "n_failed": len(failed),
        "n_skipped_existing": skipped,
        "failed": failed,
        "hazard_note": ("DefiLlama serves the CURRENT schedule and amends "
                        "silently; this stamp proves what was on disk at "
                        "fetch time, it cannot recover pre-amendment "
                        "history. P0 (silent restatement) quantifies the "
                        "residual risk."),
        "files": files,
    }
    VINTAGE_FILE.write_text(json.dumps(stamp, indent=1))
    print(f"snapshot: {len(files)} ok, {len(failed)} failed, "
          f"{skipped} skipped-existing -> {VINTAGE_FILE}")
    if failed:
        for f in failed[:10]:
            print("  FAIL", f["slug"], f["error"][:80])
    sys.exit(0 if len(files) >= 0.95 * len(slugs) else 1)


if __name__ == "__main__":
    main()
