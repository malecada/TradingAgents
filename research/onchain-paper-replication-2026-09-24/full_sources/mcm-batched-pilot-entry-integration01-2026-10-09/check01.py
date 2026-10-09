"""Focused metadata validator checks; no Run, authority or scientific inputs."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys

resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024**2,)*2)
signal.alarm(60)
os.sched_setaffinity(0, set(sorted(os.sched_getaffinity(0))[:2]))
os.nice(10)
ROOT=Path.cwd(); HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
PKG='tradingagents.research.onchain_replication'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module
def read(path):return json.loads(path.read_bytes())
gate=read(HERE.parent/'real-data-pilot-final23-2026-10-09/gate03.json')
entry=list(gate['experiments'].values())[-1]
def role(name):
    ref=entry['inputs'][name];path=ROOT/ref['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256']
    return read(path)
args=[role(n) for n in ('compact_policy','original_import_stage','mcm_policy',
                      'mcm_output_policy','archive_policy','typed_payload','pair_policy')]
keys=tuple(args[5]['graphs']);args.append(keys)
original=load(PKG+'.original_reservation_sourcecheck',ROOT/'tradingagents/research/onchain_replication/real_pilot_reservations.py')
helper=load(PKG+'.batched_pilot_reservations',HERE/'batched_pilot_reservations.py')
candidate=load(PKG+'.candidate_reservation_sourcecheck',HERE/'real_pilot_reservations.py')
checks=[]
# Actual legacy RED from the newly enlarged shared kind roster; not fabricated.
try:original.validate(*args)
except KeyError as exc:
    assert exc.args==('mcm-batched-bundle-v3',);checks.append('original_legacy_extra_kind_RED')
else:raise AssertionError('expected original legacy refusal missing')
legacy=candidate.validate(*args);assert sum(legacy['pair_occurrences'].values())==415968128
checks.append('candidate_legacy_original_denominator_GREEN')
n=max(legacy['pair_occurrences'].values());batch=4096;count=(n+batch-1)//batch
mcm=copy.deepcopy(args[2]);mcm.pop('durability');mcm['schema_version']=5
mcm['batched']={'format':'ordered-mcm-batch-closure-v2',
 'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':batch,
 'max_body_bytes':8192,'max_journal_bytes':53*n+count*(2*8192+92),
 'max_closure_token_bytes':168*count,'max_checkpoint_bytes':512*1024**2,
 'retention':'typed-recover-before-retire-v2','max_spool_bytes':4*n,
 'max_offload_metadata_bytes':2*1024**3,'max_offload_entries':4000000,
 'max_offload_anchor_bytes':32*count,
 'execution':{'route':'immutable-input-session+exact-byte-reuse-v1',
  'max_entries':4096,'max_retained_bytes':64*1024**2,'max_key_bytes':8*1024**2,
  'max_origin_bytes':9*n,'max_summary_bytes':8192*count}}
output=copy.deepcopy(args[3]);output.pop('payload_archive_input');output['schema_version']=1
typed=copy.deepcopy(args[5]);typed.update(schema_version=2,format='typed-payload-budget-v2',batched_parent='actual-active-mcm-stage-v1')
for g in typed['graphs'].values():
    cells=g['rows']*32;blocks=(cells+batch-1)//batch
    g['kinds']['mcm-batched-bundle-v3']={'max_operations':2*blocks,'max_chunks':3*blocks,
     'chunk_bytes':4*1024**2,'max_preserved_bytes':blocks*4*1024**2,
     'max_recovered_bytes':2*blocks*4*1024**2}
selected=[args[0],args[1],mcm,output,args[4],typed,args[6],keys]
value=candidate.validate(*selected)
assert value['batched_schema']==5 and value['physical_capacity_admitted'] is False
assert value['pair_occurrences']==legacy['pair_occurrences']
checks.append('actual_schema5_validator_full_counts_no_capacity_credit')
for name,change in (
 ('missing_graph',lambda a:a[5]['graphs'].pop(keys[0])),
 ('legacy_typed',lambda a:a.__setitem__(5,copy.deepcopy(args[5]))),
 ('wrong_output',lambda a:a.__setitem__(3,copy.deepcopy(args[3]))),
 ('origin_short',lambda a:a[2]['batched']['execution'].__setitem__('max_origin_bytes',1)),
 ('summary_short',lambda a:a[2]['batched']['execution'].__setitem__('max_summary_bytes',1)),
 ('chunk_short',lambda a:a[5]['graphs'][keys[0]]['kinds']['mcm-batched-bundle-v3'].__setitem__('max_chunks',1)),
 ('operations_short',lambda a:a[5]['graphs'][keys[0]]['kinds']['mcm-batched-bundle-v3'].__setitem__('max_operations',1)),
 ('recover_short',lambda a:a[5]['graphs'][keys[0]]['kinds']['mcm-batched-bundle-v3'].__setitem__('max_recovered_bytes',1)),
):
    bad=copy.deepcopy(selected);change(bad)
    try:candidate.validate(*bad)
    except ValueError:checks.append(name+'_refused')
    else:raise AssertionError(name+' accepted')
# Complete inverse of the old reservation source except intentional legacy fix.
text=(HERE/'real_pilot_reservations.py').read_text()
start=text.index('    if type(mcm) is dict');stop=text.index('    typed_payload_policy.validate(typed)',start)
inverse=text[:start]+text[stop:]
inverse=inverse.replace('typed_payload_policy.LEGACY_KINDS.items()','typed_payload_policy.KINDS.items()')
assert inverse==(ROOT/'tradingagents/research/onchain_replication/real_pilot_reservations.py').read_text()
checks.append('exact_legacy_source_inverse')
result={'decision':'PASS','checks':checks,'scientific_arrays':False,'genuine_authority':False,
        'claim':False,'capacity_admitted':False,'fixture_bounds_not_registration':True}
(HERE/'TEST01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':'PASS','checks':len(checks)}))
