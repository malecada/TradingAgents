"""One registered six-cell replay with exact recovery overlays and lifecycle guards."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_reeval_common import RunContext, sha256
from tradingagents.predlab import registry

KEY = 'audit_recovered_liq_2026_09_10'


def check_pins(gate):
    pins = dict(gate['original_input_sha256'])
    for path, digest in gate['pinned_auxiliary_inputs'].items():
        if path in pins and pins[path] != digest:
            raise ValueError('contradictory original/documentary hash')
        pins[path] = digest
    for original, replacement in gate['input_overrides'].items():
        if pins.get(original) != replacement['source_sha256']:
            raise ValueError(f'overlay original hash is not pinned: {original}')
        snapshot = replacement['snapshot']
        if snapshot in pins and pins[snapshot] != replacement['snapshot_sha256']:
            raise ValueError('contradictory snapshot hash')
        pins[snapshot] = replacement['snapshot_sha256']
    for path, expected in pins.items():
        if sha256(Path(path)) != expected:
            raise ValueError(f'registered input hash mismatch: {path}')
    return pins


class RecoveredRunContext(RunContext):
    def __init__(self, *, root=None):
        # Verify exact frozen artifacts before an output directory is created.
        gate = registry.get_experiment(KEY)
        pins = check_pins(gate)
        super().__init__('liq_fade', root=root, experiment=KEY)
        # Pin auxiliary receipts and all original inputs for final unchanged checks.
        # track() is intentionally bypassed here: both original and replacement
        # bytes are evidence, while only market reads use the declared overlay.
        for path, expected in pins.items():
            if path in gate['pinned_auxiliary_inputs']:
                # The exact documentary path is separately authorized by its
                # registration; it does not become an allowed market-data root.
                tracked = Path(path).resolve()
                self.hashes[str(tracked)] = sha256(tracked)
            else:
                tracked = super().track(path)
            if self.hashes[str(tracked)] != expected:
                raise ValueError(f'input changed while starting run: {path}')

    def track(self, path):
        original = super().track(path)
        override = self.gate['input_overrides'].get(str(original))
        if override is None:
            return original
        if self.hashes[str(original)] != override['source_sha256']:
            raise ValueError(f'original changed before overlay: {original}')
        snapshot = super().track(override['snapshot'])
        if self.hashes[str(snapshot)] != override['snapshot_sha256']:
            raise ValueError(f'snapshot changed before overlay: {snapshot}')
        return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    if not args.execute:
        print(f'Dry run: {KEY}; no inputs consumed. Use --execute after committed review.')
        return 0
    from scripts.audit_reevaluate_accounting_2026_09_09 import run_family
    print(run_family(RecoveredRunContext(), 'liq_fade'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
