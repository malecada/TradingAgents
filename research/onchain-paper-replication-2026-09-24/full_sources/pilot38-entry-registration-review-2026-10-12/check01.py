"""Finite read-only metadata/source seams; no runtime imports, Git or admission."""
import ast, copy, datetime, difflib, hashlib, json
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
F=HERE.parent
OLD=F/'real-data-pilot-full36-entry-preparation01-2026-10-11'
NEW=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
PUBLIC=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
OLD_NAME='eth-paper-real-data-end-to-end-resource-20261011-36'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def refcheck(ref):
    p=ROOT/ref['path']; assert p.resolve()==p and p.is_file() and p.stat().st_nlink==1
    assert sha(p)==ref['sha256'],ref['path']
    if 'bytes' in ref:assert p.stat().st_size==ref['bytes']
def canonical(v):return json.dumps(v,sort_keys=True)

def main():
    result={'scope':'metadata and changed entry source only','findings':[]}
    replacements=[(OLD_NAME,NAME),('full36-binding-preparation01-2026-10-11','full38-binding-preparation01-2026-10-12'),('f95f0bcb1d2fa0d98f681963332fa9710d7a679b4f490454db257d5577f9a20d','16dca252c1d0e8e73070e5a2136e458eecc73c7ae026332cf19ae377452dbc41'),('budget108','budget110'),('preparation36','preparation38'),('!=108','!=110'),("'effective_attempt_budget':108","'effective_attempt_budget':110"),('from preflight36_01 import','from preflight38_01 import')]
    for oldname,newname in [('preflight36_01.py','preflight38_01.py'),('root_io36_01.py','root_io38_01.py')]:
        before=(OLD/oldname).read_text(); after=(NEW/newname).read_text(); expected=before
        for a,b in replacements:expected=expected.replace(a,b)
        assert after==expected
        inverse=after
        for a,b in reversed(replacements):inverse=inverse.replace(b,a)
        assert inverse==before and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(before))
        assert (NEW/(newname+'.diff')).read_text()==''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/oldname),tofile=str(NEW/newname)))
    result['literal_and_ast_inverses']=True
    old=load(OLD/'gate01.json'); gate=load(NEW/'gate01.json'); e=gate['experiments'][NAME]; prior=old['experiments'][OLD_NAME]
    assert len(old['experiments'])==14 and len(gate['experiments'])==15
    assert {k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in old.items() if k!='experiments'}
    assert {k:v for k,v in gate['experiments'].items() if k!=NAME}==old['experiments']
    allowed={'inputs','parent','runtime_hashes','charter','cumulative_budget_extension','question','source_files'}
    assert {k:v for k,v in e.items() if k not in allowed}=={k:v for k,v in prior.items() if k not in allowed}
    result['original_experiment_definitions_preserved']=14
    changes=load(F/'pilot-efficiency-integration-2026-10-12/SOURCE02.json')['changes']
    six={v['path']:v['after_sha256'] for v in changes}
    actual_changed={p:v for p,v in e['source_files'].items() if p in prior['source_files'] and prior['source_files'][p]!=v}
    assert actual_changed==six
    assert set(prior['source_files'])<=set(e['source_files']) and len(e['source_files'])==1036
    for p,d in e['source_files'].items():assert sha(ROOT/p)==d,p
    result['current_source_pins']=len(e['source_files'])
    runtime={p.name:sha(p) for p in sorted((ROOT/'tradingagents/research').glob('*.py'))}
    assert runtime==e['runtime_hashes']
    result['runtime_changed_names']=[k for k,v in runtime.items() if prior['runtime_hashes'].get(k)!=v]
    capacity=load(NEW/'CAPACITY_DECLARATION_ROOT01.json'); oldcap=load(OLD/'CAPACITY_DECLARATION_ROOT01.json')
    pins=load(NEW/'CAPACITY_SOURCE_MAP01.json'); public=load(NEW/'PUBLIC_MANIFEST01.json')
    assert len(pins)==428 and pins==public['source_pins']==capacity['source_body_pins']
    assert {k:v for k,v in pins.items() if oldcap['source_body_pins'][k]!=v}==six
    assert all(e['source_files'][k]==v for k,v in pins.items())
    assert capacity['source_anchor']=='1394d8b03163233df2fcefe658378e0f7b13424d'
    result['capacity_source_body_join']=428
    expected=load(PUBLIC/'ALL_INPUT_REFS01.json'); scratch=load(NEW/'MATCHING_SCRATCH_RESERVATION01.json'); oldscratch=load(OLD/'MATCHING_SCRATCH_RESERVATION01.json')
    assert scratch==dict(oldscratch,experiment=NAME)
    expected['matching_ordered_edge_scratch']={'dataset':'eth','path':str((NEW/'MATCHING_SCRATCH_RESERVATION01.json').relative_to(ROOT)),'sha256':sha(NEW/'MATCHING_SCRATCH_RESERVATION01.json')}
    assert expected==e['inputs'] and len(expected)==73
    binding=load(NEW/'BINDING_DRAFT01.json')
    assert binding['input_refs']=={k:{x:v[x] for x in ('path','sha256')} for k,v in expected.items()}
    for role,v in binding.items():
        if isinstance(v,dict) and {'path','sha256'}<=set(v) and role!='transport':refcheck(v)
    ext=e['cumulative_budget_extension'];assert all(set(v)=={'path','sha256'} for v in ext.values())
    assert binding['budget_review']==ext['review'];refcheck(ext['extension']);refcheck(ext['review'])
    review=load(ROOT/ext['review']['path']);assert review['decision']=='accepted' and review['extension_sha256']==ext['extension']['sha256']
    assert ext['review']['sha256']=='bfbff66065872a67a3b4e57a6bb3e828bcc7e9543df4b6e976b543e4c57083ea'
    result['genuine_110_exact_two_key_join']=True
    job=load(ROOT/e['inputs']['execution_job']['path']); oldjob=load(ROOT/prior['inputs']['execution_job']['path'])
    assert canonical(job['resources'])==canonical(oldjob['resources']).replace(OLD_NAME,NAME)
    observation=load(NEW/'BASELINE_STORAGE_OBSERVATION01.json');assert observation['resources']==job['resources']
    assert observation['source']==capacity['source_anchor'] and observation['experiment']==NAME
    assert datetime.datetime.fromisoformat(observation['at'])<=datetime.datetime.now(datetime.timezone.utc)
    tree=ast.parse((NEW/'preflight38_01.py').read_text()); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    scope={'Path':Path,'ROOT':ROOT,'HERE':NEW,'NAME':NAME,'json':json,'hashlib':hashlib}
    exec(compile(ast.Module(body=[funcs[n] for n in ('need','reference','projected','check')],type_ignores=[]),'review-extracted-preflight','exec'),scope)
    def forbidden(*a,**k):raise AssertionError('subprocess/admission path reached')
    scope['subprocess']=SimpleNamespace(check_output=forbidden);scope['_admitted']=forbidden
    missing=['prior_preservation_complete','prior_recovery_review','binding_review','complete_increment_recovery','new_increment_recovery_review']
    assert all(binding[k] is None for k in missing)
    outcomes={}
    for role in missing:
        candidate=copy.deepcopy(binding)
        for k in missing:candidate[k]={'path':'synthetic-control-only.json','sha256':'0'*64}
        candidate[role]=None
        scope['read_path']=lambda p:json.dumps(candidate).encode()
        try:scope['check']()
        except ValueError as err:assert str(err)=='actual bound reference required';outcomes[role]=str(err)
        else:raise AssertionError('missing ref accepted')
    result['missing_reference_refusals_before_subprocess_or_admission']=outcomes
    fields=['new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','additional_current_metadata_headroom']
    assert all(capacity[k]==oldcap[k] for k in fields)
    assert capacity['full_pilot_capacity_admitted'] is False
    projection=scope['projected'](capacity,observation['storage_observation'],job['resources']['storage_budget']['limits'])
    assert observation['disk_free_bytes']>=projection['new_allocated_growth_bytes']+job['resources']['disk_floor_bytes']
    assert observation['host_mem_available_bytes']>=job['resources']['start_reserve_bytes']
    result['sampled_projection']=projection
    core=load(NEW/'CORE_MANIFEST01.json');mismatch=[]
    for role,ref in core['inputs'].items():
        refcheck(ref)
        if load(ROOT/e['inputs'][role]['path'])!=load(ROOT/ref['path']):mismatch.append(role)
    result['core_equality_mismatch_roles']=mismatch
    if mismatch:result['findings'].append({'priority':'P1','location':'prepare_entry01.py:79','impact':'Copied old36 core mcm_policy differs from actual38 entry selector, so preflight prepared_inputs:200 refuses before entry. Refresh actual38 core refs/builder metadata and dependent pins.'})
    result['snapshot']=[pin(p) for p in sorted(NEW.iterdir()) if p.is_file()]
    result['not_tested']=['Git committed/ancestry join','fresh final storage/runtime/namespace readiness','new recovery or release','native or empirical entry','whole39 capacity']
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
