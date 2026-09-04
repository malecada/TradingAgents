"""nlst4 screening continuation (charter docs/superpowers/specs/2026-09-04-nlst4-charter.md).

Replays the closed family's seeded screening order (seed 7) with the quota
raised to 600 KEEP per quarter and fetches the 16-day event windows for the
new KEEP pools. The closed script predlab_nlst_dex_fetch.py is imported, not
edited; every phase is append-only and resumable (re-run = resume).

  cd TradingAgents-predlab
  nohup python scripts/predlab_nlst4_screen.py >> data/predlab/nlst/nlst4_screen.log 2>&1 &
  echo $! > data/predlab/nlst/nlst4_screen.pid
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import predlab_nlst_dex_fetch as fetch  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402

KEEP_PER_Q = 600
SNAPSHOT = fetch.RAW / "screened_nlst3_snapshot.jsonl"
STATE = fetch.RAW.parent / "nlst4_screen_state.json"


def main() -> None:
    gates = registry.load_gates()
    assert "predlab_nlst4" in gates, "register first (scripts/predlab_register_nlst4.py)"
    screened = fetch.RAW / "screened.jsonl"
    if not SNAPSHOT.exists():
        shutil.copyfile(screened, SNAPSHOT)
        sha = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
        n = sum(1 for _ in SNAPSHOT.open())
        STATE.write_text(json.dumps({"snapshot_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                     "snapshot_rows": n, "snapshot_sha256": sha, "keep_per_q": KEEP_PER_Q}, indent=1))
        print(f"snapshot {SNAPSHOT} rows={n} sha256={sha[:16]}", flush=True)
    fetch.KEEP_PER_Q = KEEP_PER_Q
    t0 = time.time()
    pairs = fetch.phase_a()
    print(f"A done: {len(pairs)} PairCreated events ({time.time()-t0:.0f}s)", flush=True)
    kept = fetch.phase_b(pairs)
    print(f"B done: {len(kept)} kept pools total ({time.time()-t0:.0f}s)", flush=True)
    fetch.phase_c(kept)
    print(f"C done ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
