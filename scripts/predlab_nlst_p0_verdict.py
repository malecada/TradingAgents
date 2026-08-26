"""nlst P0 verdict — BH-FDR q<0.10 across all 11 pre-named tests (frozen).

Reads {bin,byb,x,dex}_p0_result.json, applies house bh_fdr to the 11 NW
p-values, writes verdicts into gates.json['predlab_nlst']['verdicts'] and
data/predlab/nlst/p0_verdict.json. One-shot semantics: refuses to overwrite
an existing non-empty verdicts block.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_lib import OUT_DIR, bh_fdr, write_result  # noqa: E402

GATES = ROOT / "data" / "predlab" / "gates.json"
CELLS = ("bin", "byb", "x", "dex")


def main() -> None:
    gates = json.loads(GATES.read_text())
    if gates["predlab_nlst"].get("verdicts"):
        raise SystemExit("REFUSED: predlab_nlst verdicts already recorded (one-shot)")
    pvals, stats = {}, {}
    for cell in CELLS:
        payload = json.loads((OUT_DIR / f"{cell}_p0_result.json").read_text())
        for name, st in payload["stats"].items():
            pvals[name] = st["nw_p"]
            stats[name] = st
    assert len(pvals) == 11, f"expected 11 tests, got {len(pvals)}"
    survivors = bh_fdr(pvals, q=0.10)
    verdicts = {}
    for cell in CELLS:
        cell_tests = [k for k in pvals if k.startswith(f"{cell}_")]
        surv = sorted(set(cell_tests) & survivors)
        if surv:
            det = "; ".join(f"{k}: mean={stats[k]['mean']:+.4f} p={pvals[k]:.4g}"
                            for k in surv)
            verdicts[f"nlst_{cell}"] = f"P0 SURVIVOR ({det}) — to P1"
        else:
            best = min(cell_tests, key=lambda k: pvals[k])
            verdicts[f"nlst_{cell}"] = (
                f"FAIL at P0 — 0/{len(cell_tests)} survive BH-FDR q<0.10 "
                f"(min raw p={pvals[best]:.4g} at {best}); cell CLOSED")
    gates["predlab_nlst"]["verdicts"] = verdicts
    GATES.write_text(json.dumps(gates, indent=1))
    write_result("p0_verdict", {"pvals": pvals, "survivors": sorted(survivors),
                                "verdicts": verdicts})
    for k, v in verdicts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
