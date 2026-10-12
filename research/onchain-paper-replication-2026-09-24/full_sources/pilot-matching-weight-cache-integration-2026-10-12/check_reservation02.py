"""Synthetic entry-seam check with preserved public configuration metadata.

No Admission/Owner/start, empirical array, fitting or external transport. The
candidate modules are installed only in this disposable checker process.
"""
from pathlib import Path
import importlib.util,sys,json,copy,hashlib

P=Path(__file__).resolve().parent;R=P.parents[3]
C=P.parent/'pilot-matching-weight-cache-candidate-2026-10-12'
sys.path.insert(0,str(R));sys.path.insert(0,str(C))
from numeric_harness import policy
PACKAGE='tradingagents.research.onchain_replication'

def load(name):
    spec=importlib.util.spec_from_file_location(PACKAGE+'.'+name,P/(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    setattr(sys.modules[PACKAGE],name,module);spec.loader.exec_module(module)
    return module

batched=load('compact_mcm_batched')
whole=load('batched_pilot_reservations')
D=P.parent/'real-data-pilot-full40-binding-preparation01-2026-10-12/inputs01'
refs=json.loads((D.parent/'ALL_INPUT_REFS01.json').read_bytes())
stage_ref=refs['original_import_stage'];stage_raw=(R/stage_ref['path']).read_bytes()
assert hashlib.sha256(stage_raw).hexdigest()==stage_ref['sha256']
import_stage=json.loads(stage_raw)
names=('compact_policy','original_import','mcm_policy','mcm_output_policy',
       'archive_policy','typed_payload','pair_policy')
objects={name:json.loads((D/(name+'.json')).read_bytes()) for name in names}
typed=objects['typed_payload'];graph_keys=list(typed['graphs'])
pairs=max(g['rows']*32 for g in typed['graphs'].values())

def validate(mcm):
    return whole.validate(objects['compact_policy'],import_stage,
        mcm,objects['mcm_output_policy'],objects['archive_policy'],typed,
        objects['pair_policy'],graph_keys)

original=objects['mcm_policy'];old=validate(original)
selected=copy.deepcopy(original)
selected['batched']['execution']['numeric_kernel_policy']=dict(policy.CACHE_POLICY)
charge=policy.cache_reservation(dict(policy.CACHE_POLICY))
needed=4*pairs+selected['numeric']['max_buffer_bytes']+charge
assert charge==33619968 and needed==784951284
results=[]
for limit in (751331316,needed-1,needed):
    selected['numeric']['max_numeric_bytes']=limit
    for seam,call in (('per_graph',lambda:batched.validate(selected,pairs)),
                      ('whole',lambda:validate(selected))):
        error=None
        try:call()
        except ValueError as failure:error=str(failure)
        assert (error is None)==(limit>=needed),(seam,limit,error)
        results.append(dict(seam=seam,reserved=limit,accepted=error is None,error=error))
assert original['numeric']['max_numeric_bytes']==751331316
record=dict(import_stage_reference=stage_ref,kind='logical-cache-charge-only',baseline_v1_accepted=True,
    baseline_physical_capacity_admitted=old['physical_capacity_admitted'],
    cache_charge=charge,required_numeric_bytes=needed,cases=results,
    public_input_sha256={name:hashlib.sha256((D/(name+'.json')).read_bytes()).hexdigest()
        for name in names},source_sha256={name:hashlib.sha256((P/(name+'.py')).read_bytes()).hexdigest()
        for name in ('compact_mcm_batched','batched_pilot_reservations')},
    claim_created=False,physical_capacity_proven=False)
with (P/'RESERVATION_CHECK02.json').open('x') as out:json.dump(record,out,indent=2,sort_keys=True);out.write('\n')
print(json.dumps({'cases':len(results),'required':needed,'baseline_passed':True}))
