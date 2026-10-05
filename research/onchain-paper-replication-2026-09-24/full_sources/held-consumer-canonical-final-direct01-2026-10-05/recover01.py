"""One fixed outcome increment; unchanged accepted receiver mechanics reused."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
HERE = Path(__file__).resolve().parent
BASE = F / 'financial-wrapper-serialized-prediction-final-direct03-2026-10-05'
EXPECTED_PATHS = {
    'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_FINAL_PARENT_READONLY_CHECK01.json',
    'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_RELEASE_FINAL_COPY01.json',
    'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_REQUEST_FINAL_COPY01.json',
    'held-consumer-canonical-final-direct01-2026-10-05/recover01.py',
    'held-consumer-canonical-increment-preservation-review01-2026-10-05/FINAL_BASELINE_RECOVERY_REVIEW01.json',
    'held-consumer-canonical-increment-preservation-review01-2026-10-05/FINAL_PARENT_SOURCE_ENTRY_REVIEW01.json',
    'held-consumer-canonical-increment-preservation-review01-2026-10-05/FULL_CURRENT_RECOVERY_PROOF01.json',
    'held-consumer-canonical-increment-preservation-review01-2026-10-05/RELEASE_EXECUTION_REVIEW01.json',
}

def main():
    for name, pin in {'recover01.py': '001abd3d558cb3ebc4677f1b300219d1355ca394a95fbf8ea7ec8108ac4129c6', 'watch01.py': '8489c36dacc5ef2d4280ad4ed0bf9f5e19e6f452e3ab653838bb6d253764bcbe', 'utilities/owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'}.items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == pin
    # The original receiver authenticates the explicit --selection-sha256 before
    # any operation. This fixed wrapper only narrows its declared path population.
    selection = json.loads((HERE / 'SELECTED_BODIES01.json').read_bytes())
    prefix = 'research/onchain-paper-replication-2026-09-24/full_sources/'
    assert len(selection['rows']) == 8 and {row['path'] for row in selection['rows']} == {prefix + n for n in EXPECTED_PATHS}
    sys.path.insert(0, str(BASE))
    spec = importlib.util.spec_from_file_location('accepted_remote_receiver', BASE / 'recover01.py')
    M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    M.HERE = HERE
    M.REQUIRED = {r['path']: {k: r[k] for k in ('bytes', 'sha256')} for r in selection['rows']}
    M.FINAL_POPULATION_COUNT = 8
    # Original literal final-direct status/qualification remain in the raw helper
    # receipt. Actual declared outcome scope is its exact selection and R4 join;
    # no new scientific authority or reinterpretation of old failures follows.
    M.entry()


if __name__ == '__main__':
    main()
