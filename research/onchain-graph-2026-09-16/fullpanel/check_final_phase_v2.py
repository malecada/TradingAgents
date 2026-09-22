"""Narrow phase-byte reconstruction correction around the frozen final checker.

Fresh source activity histograms originally had integer degree keys. Their
initial sorted JSON used numeric key order; parsing converts those keys to
strings. Reused sources already had string keys before initial serialization.
Restore only these two fresh-source maps on a copy. All values, other keys,
evidence comparisons, admission criteria and original checker identity remain.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

BASE = 'research/onchain-graph-2026-09-16/fullpanel'
ORIGINAL_SHA256 = '214ca8e0312b8cc832a4a46e7f518364f61681aad9553121758f5e6d5e96905f'
HISTOGRAMS = ('in_degree_histogram', 'out_degree_histogram')


def json_bytes(phase):
    """Reconstruct the producer's exact sorted phase JSON without mutation."""
    if type(phase.get('source_reused')) is not bool:
        raise ValueError('phase source_reused must be boolean')
    value = copy.deepcopy(phase)
    activity = value['source']['activity']
    for name in HISTOGRAMS:
        histogram = activity[name]
        if not isinstance(histogram, dict):
            raise ValueError('degree histogram must be a mapping')
        # Parsed JSON keys must have one canonical representation. Rejecting
        # aliases prevents key collapse while reconstructing the integer map.
        if any(not isinstance(key, str) or re.fullmatch(r'0|[1-9][0-9]*', key) is None for key in histogram):
            raise ValueError('degree histogram key must be canonical nonnegative decimal text')
        if not value['source_reused']:
            activity[name] = {int(key): count for key, count in histogram.items()}
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def wrap_publication(checker, metadata):
    """Add correction provenance while retaining the original report publisher."""
    original_day_module = checker.day_module
    def day_module():
        module = original_day_module()
        publish = module.publish_report
        def publish_report(path, result):
            if 'phase_serialization_correction' in result:
                raise ValueError('correction metadata already present')
            return publish(path, dict(result, phase_serialization_correction=dict(metadata)))
        module.publish_report = publish_report
        return module
    checker.day_module = day_module


def load_original(root):
    """Execute hash-verified original bytes with its original __file__ intact."""
    root = Path(root).resolve()
    path = root / BASE / 'check_final.py'
    path.resolve().relative_to(root)
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError('original checker path contains a symlink')
        if part == root:
            break
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('original checker source hash mismatch')
    spec = importlib.util.spec_from_file_location('fullpanel_frozen_final_phase_v2', path)
    checker = importlib.util.module_from_spec(spec)
    # Execute the bytes just verified, rather than letting a loader reread them.
    exec(compile(raw, str(path), 'exec'), checker.__dict__)
    checker.json_bytes = json_bytes
    wrapper = Path(__file__).resolve()
    metadata = dict(wrapper_path=str(wrapper), wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        original_checker_path=str(path), original_checker_sha256=ORIGINAL_SHA256,
        scope='Only source.activity.in_degree_histogram and out_degree_histogram keys are restored to integers for fresh-source phase serialization; reused sources retain string key sorting. No values or admission criteria change.')
    wrap_publication(checker, metadata)
    return checker


def main():
    parser = argparse.ArgumentParser()
    for key in ('root', 'source', 'report'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    # Original main reparses the unchanged CLI and performs all terminal, source,
    # gate, audit, resource, bucket and report-publication checks itself.
    return load_original(args.root).main()


if __name__ == '__main__':
    main()
