"""Independent finite source/metadata controls; no Run, Owner or real data load."""
import ast
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
OUT = pathlib.Path(__file__).resolve().parent
AUTHOR = F / 'pilot-efficiency-entry-qualification-2026-10-11'
BASE = '86700550a732ddf319d9401c5e472b99b19e2f16'
SOURCE = 'tradingagents/research/onchain_replication/compact_mcm_batched.py'
read = lambda p: json.loads(p.read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()

snap = read(AUTHOR / 'SOURCE_SNAPSHOT01.json')
files = []
for expected in snap['files']:
    data = (ROOT / expected['path']).read_bytes()
    actual = dict(path=expected['path'], bytes=len(data), sha256=sha(data))
    assert actual == expected
    files.append(actual)
source = (ROOT / SOURCE).read_text()
baseline = subprocess.check_output(['git', 'show', BASE + ':' + SOURCE], cwd=ROOT).decode()
recovered = source.replace('import re\n', '', 1)
start = recovered.index("ENTRY_QUALIFICATION = ")
end = recovered.index('\n\n\ndef selected(policy):', start)
recovered = recovered[:start] + recovered[end + 1:]
schema_extension = " | ({'entry_qualification'} if 'entry_qualification' in policy else set())"
assert recovered.count(schema_extension) == 1
recovered = recovered.replace(schema_extension, '', 1)
for seam in ('    _entry_qualification(policy)\n', '        _stop_after_entry(target,policy)\n'):
    assert recovered.count(seam) == 1
    recovered = recovered.replace(seam, '', 1)
assert recovered == baseline, 'Literal inverse differs'
assert ast.dump(ast.parse(recovered)) == ast.dump(ast.parse(baseline))

from tradingagents.research.onchain_replication import compact_mcm_batched as m
from tradingagents.research.onchain_replication import real_pilot_reservations as reservations

qualification = read(AUTHOR / 'QUALIFICATION_MCM_DRAFT01.json')
integration = F / 'pilot-efficiency-integration-2026-10-11'
successor = read(integration / 'SUCCESSOR_MCM_DRAFT01.json')
assert {k: v for k, v in qualification.items() if k != 'entry_qualification'} == successor
typed = read(integration / 'SUCCESSOR_TYPED_DRAFT01.json')
refs = read(F / 'real-data-pilot-full35-entry-preparation01-2026-10-11/BINDING01.json')['input_refs']
inputs = {}
for role in ('compact_policy', 'original_import_stage', 'mcm_output_policy', 'archive_policy', 'pair_policy'):
    ref = refs[role]
    data = (ROOT / ref['path']).read_bytes()
    assert sha(data) == ref['sha256']
    inputs[role] = json.loads(data)
counts = {k: v['rows'] * 32 for k, v in typed['graphs'].items()}
assert qualification['entry_qualification']['graph_hash'] == min(counts) == snap['first_graph']
for count in counts.values():
    m.validate(qualification, count)
    m.validate(successor, count)
accounting = reservations.validate(inputs['compact_policy'], inputs['original_import_stage'], qualification,
    inputs['mcm_output_policy'], inputs['archive_policy'], typed, inputs['pair_policy'], list(counts))
assert accounting['pair_occurrences'] == counts
assert sum(counts.values()) == 415968128

result = dict(status='PASS_SOURCE_AND_PUBLIC_METADATA_ONLY', files=files,
    baseline_commit=BASE, baseline_sha256=sha(baseline.encode()),
    literal_inverse=True, ast_inverse=True, qualification_adds_only_explicit_selector=True,
    exact_first_graph=snap['first_graph'], graph_count=len(counts), whole_cells=sum(counts.values()),
    ordinary_mcm_validation=True, ordinary_reservation_validation=True,
    owner_logical_reservation_bytes=accounting['owner_logical_reservation_bytes'],
    genuine_authority_exercised=False, native_claim=False, physical_capacity_admitted=False)
(OUT / 'CHECK01.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'SOURCE_SNAPSHOT01.json').write_text(json.dumps(dict(files=files, status='INDEPENDENT_SOURCE_AUTHENTICATION_ONLY'), indent=2) + '\n')
print(json.dumps(result, indent=2))
