"""Independent finite metadata arithmetic; no project imports or runtime claims."""
import hashlib
import json
import struct
from pathlib import Path

P = Path(__file__).resolve().parent
F = P.parent
R = F.parents[2]
pins = {}
def read(relative):
    path = R / relative
    raw = path.read_bytes()
    pins[relative] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return raw
def load(name):
    return json.loads(read(str((F/name).relative_to(R))))
def ceil(n, unit):
    return -(-n//unit)*unit

w = load('pilot37-continuation-capacity-2026-10-11/CAPACITY01.json')
for name, pin in w['source_pins'].items():
    read(name)
    assert pins[name] == pin, name
for name in ('calculate01.py', 'REPORT.md'):
    read(str((F/'pilot37-continuation-capacity-2026-10-11'/name).relative_to(R)))
t = load('real-data-pilot-full36-binding-preparation01-2026-10-11/inputs01/typed_payload.json')
m = load('real-data-pilot-full36-binding-preparation01-2026-10-11/inputs01/mcm_policy.json')['batched']
old = load('mcm-batched-grouped-capacity01-2026-10-09/CAPACITY01.json')
d35 = load('real-data-pilot-full35-entry-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json')
d36 = load('real-data-pilot-full36-entry-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json')
keys = ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','directory_allocated_bound_bytes','other_writer_reserved_bytes','new_entries')
assert all(d35[k] == d36[k] for k in keys)
assert m['continuation']['manifest_input'] is None and m['continuation']['graph_manifest_inputs'] == {}
assert m['batch_cells'] == 4096 and m['group_batches'] == 16 and m['max_body_bytes'] == 4096
header = struct.calcsize('>8sIQQ32s32s')
record = struct.calcsize('>Q32sdIB')
assert (header, record) == (92,53)
rows = []
for g,v in t['graphs'].items():
    c = 32*v['rows']
    assert v['rows'] == old['graphs'][g]['rows']
    assert c*4 == v['kinds']['mcm-output-f32']['max_preserved_bytes']
    b = ceil(c,4096)//4096
    groups = ceil(b,16)//16
    # Independent aggregation by full groups plus at most one trailing group.
    def group_extent(cells, cap):
        sizes = []
        while cells:
            n = min(cells,4096)
            sizes.extend((cap,header+record*n,cap))
            cells -= n
        return ceil(1024+sum(512+ceil(n,512) for n in sizes),10240)
    full, tail = divmod(c,65536)
    tar = {cap:full*group_extent(65536,cap)+(group_extent(tail,cap) if tail else 0) for cap in (1024,4096)}
    budget = v['kinds']['mcm-batched-bundle-v3']
    assert tar[4096] == budget['max_preserved_bytes']
    assert 2*tar[4096] == budget['max_recovered_bytes']
    assert 2*groups == budget['max_operations'] and 3*groups == budget['max_chunks']
    assert group_extent(65536,4096) <= budget['chunk_bytes'] <= 4*1024**2
    assert b*4096 <= m['continuation']['max_commit_bytes']
    assert b*8192 <= m['execution']['max_summary_bytes']
    assert c*9 <= m['execution']['max_origin_bytes']
    actual = next(x for x in w['graphs'] if x['graph']==g)
    assert (c,b,groups,tar[1024],tar[4096]) == tuple(actual[k] for k in ('cells','batches','groups','old_tar_cap','new_tar_cap'))
    rows.append({'graph':g,'rows':v['rows'],'cells':c,'batches':b,'groups':groups,'tail_cells':tail,'prefix_bytes':b*4096,'tar_bytes':tar[4096]})
totals = {k:sum(x[k] for x in rows) for k in ('cells','batches','groups','prefix_bytes')}
assert totals == dict(cells=415968128,batches=101559,groups=6352,prefix_bytes=415985664)
live = {cap:16*(2*cap+header+record*4096) for cap in (1024,4096)}
allocated = {cap:16*(2*ceil(cap,4096)+ceil(header+record*4096,4096)) for cap in live}
assert live[4096]-live[1024] == 98304 and allocated[4096] == allocated[1024] == 3670016
# Recover-before-retire holds original and extracted journal concurrently.
# Inherited capacity conservatively sums seven original groups, plus one scratch
# journal; source is serial and aborts on failure, so at most two coexist.
old_journal_aggregate = old['totals']['live_original_journal_payload_upper'] if 'totals' in old else next(v['live_original_journal_payload_upper'] for v in old.values() if isinstance(v,dict) and v.get('cells')==415968128)
assert old_journal_aggregate == 7*live[1024]
old_journal_envelope = old_journal_aggregate + old['group_scratch_source_bound']['live_journal_payload_upper']
assert 2*live[4096] < old_journal_envelope
delta = totals['prefix_bytes'] + live[4096]-live[1024]
projection = {k:w['inherited36_projection'][k]+(totals['batches'] if k=='entries' else delta) for k in ('logical_file_bytes','allocated_bytes','entries')}
assert projection == w['whole37_projection_with_unchanged_declared_directory_other_writer_allowances']
assert w['remaining_margin'] == {k:w['fixed_caps'][k]-projection[k] for k in projection}
out = dict(status='ACCEPTED_STATIC_PROSPECTIVE_ARITHMETIC_ONLY',graphs=rows,totals=totals,additional_logical_and_conservative_allocated_bytes=delta,projection=projection,margin=w['remaining_margin'],live_journal_logical=live,live_journal_alloc4096=allocated,original_plus_semantic_recovery_peak=2*live[4096],inherited_original_plus_recovery_journal_envelope=old_journal_envelope,source_pins=pins,limitations=['No current baseline/free-space/inode/directory measurement.','No whole37 declaration/admission/release.','Current36 mandatory stop remains selected; whole37 requires its own reviewed registration.','Only null continuation inputs; no recovered-parent import/copy allowance.','No numerical execution, runtime import, network, credentials, Git or claim.'])
(P/'CHECK01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('status','totals','projection','margin','original_plus_semantic_recovery_peak','inherited_original_plus_recovery_journal_envelope')},indent=2))
