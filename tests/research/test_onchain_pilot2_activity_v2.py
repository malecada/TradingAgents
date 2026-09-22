"""Invented activity only; no empirical reconstruction or checker main execution."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'research/onchain-graph-2026-09-16/pilot2/check_activity_v2.py'
spec = importlib.util.spec_from_file_location('pilot2_activity_v2_test', PATH)
correction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(correction)


def producer():
    path = ROOT / 'research/onchain-graph-2026-09-16/prototype/graph_math.py'
    spec = importlib.util.spec_from_file_location('synthetic_activity_producer_v2', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    pairs = {('a', 'b'): 2, ('b', 'a'): 1}
    actual = json.loads(json.dumps(producer().graph_features(pairs)))
    checker = correction.frozen_checker(ROOT)
    expected = checker.prior_checker().static_summary(pairs)
    return actual, expected, checker


def test_exact_annotation_restores_strict_activity_comparison():
    actual, expected, checker = fixture()
    assert actual == expected
    assert actual != {k: v for k, v in expected.items() if k != 'qualification'}
    assert checker.__file__ == str(PATH.resolve())
    assert checker.HERE == PATH.parent


@pytest.mark.parametrize('mutation', ['missing', 'altered', 'extra', 'numeric'])
def test_annotation_or_numeric_mismatch_still_rejected(mutation):
    actual, expected, _ = fixture()
    if mutation == 'missing':
        actual.pop('qualification')
    elif mutation == 'altered':
        actual['qualification'] = 'different qualification'
    elif mutation == 'extra':
        actual['unregistered_annotation'] = 'extra'
    else:
        actual['events'] += 1
    # This is the frozen verify_success comparison, retained without relaxation.
    with pytest.raises(AssertionError):
        assert actual == expected


def test_expected_summary_cannot_silently_replace_existing_annotation():
    with pytest.raises(ValueError, match='unexpectedly contains'):
        correction.annotated_summary({'qualification': 'something else'})


def test_changed_original_binding_rejected_before_import(tmp_path):
    original = tmp_path / correction.ORIGINAL_PATH
    original.parent.mkdir(parents=True)
    original.write_text('raise RuntimeError("must not execute")\n')
    with pytest.raises(ValueError, match='original independent checker binding changed'):
        correction.frozen_checker(tmp_path)


def test_execution_root_stays_frozen_while_report_identifies_wrapper(tmp_path):
    original = tmp_path / correction.ORIGINAL_PATH
    original.parent.mkdir(parents=True)
    original.write_bytes((ROOT / correction.ORIGINAL_PATH).read_bytes())
    checker = correction.frozen_checker(tmp_path)
    assert checker.HERE == original.parent
    assert checker.__file__ == str(PATH.resolve())
    assert checker.HERE != Path(checker.__file__).parent


def test_existing_report_rejected_before_checker_load(tmp_path, monkeypatch):
    report = tmp_path / 'independent-report-v2.json'
    report.write_text('preserved')
    monkeypatch.setattr('sys.argv', [str(PATH), '--root', str(tmp_path), '--source', 'source', '--report', str(report)])
    def unexpected_load(root):
        pytest.fail('checker must not load for an existing report')
    monkeypatch.setattr(correction, 'frozen_checker', unexpected_load)
    with pytest.raises(FileExistsError, match='already exists'):
        correction.main()
    assert report.read_text() == 'preserved'
