"""Read-only consumed v2/v1 history proof; never admits a research claim."""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tradingagents.research.verify import _blob, verify_claim, verify_run
from tradingagents.research_spread.verify_v2_snapshot import check
from tradingagents.research_spread.admission import runtime_hashes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    directory = ROOT / 'research_runs/dated-mark-20260911'
    claim = verify_claim(directory)
    structural = verify_run(directory)
    assert structural['status'] == 'complete'
    registered = json.loads(_blob(ROOT, claim['source'], claim['registration']))
    check(directory, claim, registered, _blob)
    certificate_ref = claim['experiment']['budget_extension']
    certificate = json.loads((ROOT / certificate_ref['path']).read_bytes())
    repair_ref = certificate['consumed_amendment']['certificate']
    repair = json.loads((ROOT / repair_ref['path']).read_bytes())
    inventory = {}
    for path in sorted(directory.parent.iterdir()):
        if path.name.startswith('.'):
            continue
        other = verify_claim(path)
        if other['family']['mechanism_id'] != claim['family']['mechanism_id']:
            continue
        assert other['program_id'] == claim['program_id']
        terminal = verify_run(path)
        filename = 'complete.json' if terminal['status'] == 'complete' else 'failed.json'
        inventory[path.name] = {'claim_sha256': sha(path / 'claim.json'),
                                'terminal': filename, 'terminal_sha256': sha(path / filename),
                                'started_at': other['started_at']}
    assert set(inventory) == set(certificate['prior_claims']) | {claim['experiment_id']}
    assert len(inventory) == 5 and len(certificate['prior_claims']) == 4 and len(repair['prior_claims']) == 3
    assert all(datetime.fromisoformat(item['started_at']) <= datetime.fromisoformat(claim['started_at'])
               for item in inventory.values())
    result = {'status': 'PASS', 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'script_sha256': sha(Path(__file__)), 'source': claim['source'],
              'parent': claim['experiment_id'], 'parent_structural_verification': structural,
              'runtime_hashes': runtime_hashes(), 'certificate': certificate_ref,
              'nested_repair_certificate': repair_ref, 'current_same_mechanism_inventory': inventory,
              'closed_v2_prior_inventory': certificate['prior_claims'],
              'closed_v1_prior_inventory': repair['prior_claims'],
              'cpu_affinity_count': len(os.sched_getaffinity(0)),
              'scope': 'Actual consumed v2 certificate checked at its closed four-prior inventory, including independent nested v1 closed three-prior verification; current five-claim inventory and latest completed parent checked. Structural hashes and preservation only; no financial arithmetic or claim admission.',
              'limitation': 'Frozen v1/v2 live-ledger verifiers are not represented as valid after later descendants. A prospective seventh grant still needs its separate full live-inventory admission and review.'}
    assert result['cpu_affinity_count'] <= 2
    destination = Path(__file__).with_name('dated-v2-actual-snapshot-result.json')
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'result': str(destination)}))


if __name__ == '__main__':
    main()
