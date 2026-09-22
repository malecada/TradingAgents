"""Read-only correction of the frozen independent checker's annotation schema.

All original checks and source bindings remain in force. Only the expected
activity annotation is added; no numerical values or actual output are changed.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path

ORIGINAL_PATH = 'research/onchain-graph-2026-09-16/pilot2/check_independent.py'
ORIGINAL_SHA256 = '3809fbe4b0b7605c265076b7b41466b9b164df79f233eeec0d2d0c1a465735ac'
QUALIFICATION = ('Static count-weighted top-level address graph; no entity labels, '
                 'monetary weights, temporal motifs or economic interpretation.')


def annotated_summary(summary):
    if 'qualification' in summary:
        raise ValueError('frozen independent summary unexpectedly contains qualification')
    return dict(summary, qualification=QUALIFICATION)


def frozen_checker(root):
    path = Path(root).resolve() / ORIGINAL_PATH
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != ORIGINAL_SHA256:
        raise ValueError('original independent checker binding changed')
    spec = importlib.util.spec_from_file_location('pilot2_frozen_review_activity_v2', path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    original_factory = checker.prior_checker
    def corrected_factory():
        reviewer = original_factory()
        original_summary = reviewer.static_summary
        def corrected_summary(pairs):
            return annotated_summary(original_summary(pairs))
        reviewer.static_summary = corrected_summary
        return reviewer
    checker.prior_checker = corrected_factory
    # The original main hashes __file__ into the report; identify the actual
    # executed correction wrapper, while its original gate checks remain intact.
    checker.__file__ = str(Path(__file__).resolve())
    return checker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', '--report', dest='output', required=True)
    args = parser.parse_args()
    report = Path(args.output)
    if report.exists() or report.is_symlink():
        raise FileExistsError('independent correction report already exists')
    # Frozen main re-parses the same CLI and performs every original check,
    # including terminal/HEAD/claim/registration/input identity and exclusive write.
    frozen_checker(args.root).main()


if __name__ == '__main__':
    main()
