"""Independent tiny synthetic caller-shape probe; never starts a research run."""
from pathlib import Path
from tradingagents.research.onchain_replication import phase_timing
from tests.research.onchain_replication.test_pilot_efficiency_selection import test_complete_compute_retains_commits_and_joins_numeric_score_bodies
root=Path(__file__).parent/'open-phase-fixture'
root.mkdir()
collector=phase_timing.PhaseTotals()
try:
    with phase_timing.activate(collector), phase_timing.measure('entry'):
        test_complete_compute_retains_commits_and_joins_numeric_score_bodies(root)
except BaseException as error:
    import traceback
    traceback.print_exc()
    print('retained_first_score_complete', (root/'matching/00000000.complete.json').exists())
    print('retained_first_prefix_commit', (root/'matching/00000000.prefix.json').exists())
    print('retained_numeric_summary', (root/'stream/numeric-batches/000000000000.json').exists())
    raise
