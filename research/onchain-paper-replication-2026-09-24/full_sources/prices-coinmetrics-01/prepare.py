"""Freeze prospective exact source contracts; this script never retrieves data."""
from pathlib import Path
import copy
import json
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from tradingagents.research.onchain_replication.coinmetrics_prices import price_policy
from tradingagents.research.onchain_replication.job import required_sources, job_schema
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash, canonical_bytes


def save(path, value):
    with path.open('xb') as out: out.write(canonical_bytes(value))


def main():
    destination = Path('/tmp/onchain-paper-coinmetrics-checkout-20260924-01')
    common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, text=True).strip()
    save(HERE/'workspace.json', {'root':str(destination), 'ledger':str((ROOT/'research_runs').resolve()),
        'artifacts':str((ROOT/'research_artifacts').resolve()), 'git_common':str((ROOT/common).resolve())})
    save(HERE/'environment.json', inventory(ROOT, include_torch=False))
    gate = copy.deepcopy(json.loads((HERE.parent/'prices-01/gate-v3.json').read_bytes()))
    old = gate['experiments']; gate['experiments'] = {}
    charter = HERE/'CHARTER.md'
    with charter.open('x') as out:
        out.write((HERE/'PROTOCOL-AMENDMENT.proposed.md').read_text())
        out.write('''
## Frozen finite capture and process contract

Per asset: one HTTPS request to the pinned Coin Metrics GitHub CSV,30seconds,
32MiB maximum response plus one sentinel byte; no retry, redirect, proxy,
credentials, query override, alternative metric or alternate URL. Persist intent
before requesting, retain response/prefix and failure. Each source has3289cells:
one capture and3288required2016–2024 dates. Full archive rows outside that window
are raw exposure only and excluded from model inputs; no fresh-confirmation claim.
Strict UTF8/CSV, unique nonempty headers, exactly one time and PriceUSD column,
at most512columns/10000rows, unique increasing canonical ISO dates and positive
finite prices. Missing PriceUSD remains unavailable. Invalid schema rejects the
entire panel; HTTP completion is separate from daily data acceptance.

All old gates and attempts remain unchanged. The exact physical shared ledger,
lock and artifact store are bound in workspace.json. The isolated source checkout
must match the committed gate and all60transitive source files. BTC then ETH
execute sequentially once each, after independent review and admission. Budget
allocation is an input; family51/17prior is identical to all prior claims.

Bounds per job:512MiB memory maximum,384MiB high,zero swap,two CPUs,3GiB host
reserve,3.5GiB startup availability,20GiB free disk,300seconds total wall time.
Immutable supervisor/monitor ownership, cgroup limit and death proof, complete
cell ledger, outputs and all raw hashes are required. Terminal identities cannot
restart. No fit, transaction capture, contact, payment, trading or deployment.
''')
    freeze_files = [HERE/'PROTOCOL-AMENDMENT.proposed.md', HERE/'budget-allocation.proposed.json',
        STUDY/'config/calendar-coinmetrics-v5.json', charter]
    freeze = STUDY/'protocol-freeze-v5.json'
    save(freeze, {'schema_version':5, 'parent_sha256':file_hash(STUDY/'protocol-freeze-v4.json'),
        'reason':'prospective explicit price provider amendment after two closed Yahoo HTTP429 attempts; before any real financial fitting',
        'config_overrides':{'calendar':'config/calendar-coinmetrics-v5.json'},
        'files':{str(p.relative_to(STUDY)):file_hash(p) for p in freeze_files}})
    for asset in ('BTC','ETH'):
        experiment = copy.deepcopy(old['paper-prices-'+asset.lower()+'-20260924'])
        gate['datasets'][asset.lower()]['identity'] = asset.lower()+'-usd-coinmetrics-priceusd-'+price_policy(asset)['revision']
        experiment['question'] = 'Capture pinned Coin Metrics '+asset+' daily PriceUSD for2016–2024; retain every required date and explicit provider deviation, no fitting'
        experiment['source_files'] = {p:file_hash(ROOT/p) for p in sorted(required_sources())}
        experiment['charter'] = {'path':str(charter.relative_to(ROOT)), 'sha256':file_hash(charter)}
        limits = {'memory_max_bytes':512*1024**2, 'memory_high_bytes':384*1024**2,
            'reserve_bytes':3*1024**3, 'start_reserve_bytes':3584*1024**2,
            'disk_floor_bytes':20*1024**3, 'disk_paths':[str(destination)], 'wall_seconds':300}
        job = {'schema_version':1, 'kind':'coinmetrics_prices', 'resources':limits,
            'environment_input':'environment', 'payload':{'asset':asset}}
        job_schema(job)
        save(HERE/(asset+'-job.json'), job); save(HERE/(asset+'-policy.json'), price_policy(asset))
        bindings = {'budget_allocation':HERE/'budget-allocation.proposed.json',
            'calendar':STUDY/'config/calendar-coinmetrics-v5.json', 'environment':HERE/'environment.json',
            'execution_job':HERE/(asset+'-job.json'), 'execution_workspace':HERE/'workspace.json',
            'price_policy':HERE/(asset+'-policy.json'), 'protocol_amendment':HERE/'PROTOCOL-AMENDMENT.proposed.md',
            'protocol_freeze':freeze}
        for name,path in bindings.items():
            experiment['inputs'][name] = {'path':str(path.relative_to(ROOT)), 'sha256':file_hash(path), 'dataset':asset.lower()}
        gate['experiments']['paper-prices-coinmetrics-'+asset.lower()+'-20260924'] = experiment
    save(HERE/'gate.json', gate)
    print(json.dumps({'gate_sha256':file_hash(HERE/'gate.json'), 'sources':len(experiment['source_files']),
        'inputs_per_asset':len(experiment['inputs']), 'destination':str(destination)}))


if __name__ == '__main__': main()
