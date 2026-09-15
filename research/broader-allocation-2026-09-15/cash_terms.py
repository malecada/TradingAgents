"""Fixed retained-evidence cash-term audit; no new requests or financial book."""
import argparse
import hashlib
import json
from pathlib import Path
from tradingagents.research import ResearchRun

HERE = Path(__file__).resolve().parent
EXPERIMENT = 'allocation-cash-terms-20260915'
REGISTRATION = 'research/broader-allocation-2026-09-15/gates-cash-terms.json'
SPEC_HASH = '23e926baafde29ca17db35b7cd5e7b874986ff85ac18c894129657899d29850e'


def evaluate(raw):
    if hashlib.sha256(raw).hexdigest() != SPEC_HASH:
        raise ValueError('unregistered authored cash terms')
    spec = json.loads(raw)
    return {'scope': 'Retained-evidence cash admission; no financial result',
            'implementation_admitted': False, 'financial_run_admitted_by_this_audit': False,
            'conditional_basis': spec['scenario'], 'initial_committed_usd': spec['initial_committed_usd'],
            'absolute_net_profit': None, 'benchmark_relative_value': None,
            'new_requests': 0, 'cells': spec['terms']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=HERE.parents[1], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        run.read_input('ancestry'); run.read_input('spot_result'); run.read_input('dex_result')
        result = evaluate(run.read_input('spec'))
        if len(json.dumps(result, allow_nan=False).encode()) > 1024 * 1024:
            raise ValueError('output bound exceeded')
        run.write_json('cash-terms.json', result)
        run.finish([{k: row[k] for k in ('id', 'status', 'reason') if k in row} for row in result['cells']])


if __name__ == '__main__':
    main()
