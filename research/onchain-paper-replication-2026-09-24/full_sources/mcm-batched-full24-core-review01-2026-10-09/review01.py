import pathlib,json,hashlib,copy
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();D=F/'mcm-batched-pilot-input-templates02-2026-10-09/draft02';C=F/'real-data-pilot-full24-input-binding01-2026-10-09';O=F/'real-data-pilot-final23-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
m=j(D/'MANIFEST.json')
for n,v in m['files'].items():assert h(D/n)==v,n
entry=j(O/'gate03.json')['experiments']['eth-paper-real-data-end-to-end-resource-20261009-23']
def old(role):
 ref=entry['inputs'][role];assert h(ROOT/ref['path'])==ref['sha256'];return j(ROOT/ref['path'])
def draft(role):return j(D/(role+'.template.json'))['template']
assert draft('original_import')==old('original_import') and draft('original_import_stage')==old('original_import_stage')
a=j(D/'ANCESTRY.json')['value'];assert len(a)==26
for row in a:assert h(D/row['preserved_member'])==row['sha256']
for role in ('original_import','original_import_stage','original_claim','original_gate'):assert h(D/'ancestry-metadata'/(role+'.json'))==entry['inputs'][role]['sha256']
science=j(D/'SCIENCE.json')['value'];assert science['dictionary']['size']==32 and science['dictionary']['sample_count']==512
assert science['model_input']['sha256']==entry['inputs']['model']['sha256'] and science['training_input']['sha256']==entry['inputs']['training']['sha256']
graphs=j(D/'GRAPH_BOUNDS.json')['value'];assert len(graphs)==7 and sum(g['cells'] for g in graphs.values())==415968128 and sum(g['groups'] for g in graphs.values())==6352
assert draft('mcm_policy')['numeric']==old('mcm_policy')['numeric']
assert draft('compact_policy')['stage_policy']['pair']==old('compact_policy')['stage_policy']['pair']
assert draft('compact_policy')['stage_policy']['schedule']==old('compact_policy')['stage_policy']['schedule']
p=draft('pilot');original=old('pilot')
for k in original:
 if k not in ('partial_progress','scoring_diagnostic','outputs','cell_id','resource_policy'):assert p[k]==original[k],k
assert 'partial_progress' not in p and 'scoring_diagnostic' not in p and 'diagnostic' not in p['outputs']
core=j(C/'CORE_MANIFEST02.json');assert core['builder_sha256']==h(C/'bind_core02.py')
for ref in core['inputs'].values():assert h(ROOT/ref['path'])==ref['sha256']
for n,v in core['source'].items():assert h(ROOT/n)==v
cm=j(C/'core02/compact_policy.json');mcm=j(C/'core02/mcm_policy.json');typed=j(C/'core02/typed_payload.json');out=j(C/'core02/mcm_output_policy.json')
assert cm==old('compact_policy');assert mcm['batched']['max_checkpoint_bytes']==269114368
assert cm['stage_policy']['schedule']['max_total_checkpoint_bytes']==43058298880 and cm['stage_policy']['schedule']['max_total_checkpoints']==160 and cm['stage_policy']['schedule']['max_checkpoints']==1
expected=draft('mcm_policy');changed={k for k in expected['batched'] if expected['batched'][k]!=mcm['batched'][k]};assert changed=={'max_checkpoint_bytes','max_offload_metadata_bytes','max_offload_entries'}
for k in expected:
 if k!='batched':assert expected[k]==mcm[k]
assert out==draft('mcm_output_policy') and out['schema_version']==1
for key,g in old('typed_payload')['graphs'].items():
 for kind,b in g['kinds'].items():assert typed['graphs'][key]['kinds'][kind]==b
tr=j(C/'TRANSPORT_LIMITS02.json');ot=j(O/'INPUT_DRAFT02.json')['protocol']['transport_limits'];ch=copy.deepcopy(ot['control_history']);ch['success_control_bytes']=16384;assert tr['control_history']==ch
assert ch['full_interval_ms']==1000 and ch['max_callbacks_between_full']==4096
check=j(C/'CORE_CHECK02.json');assert check['status']=='CORE_METADATA_VALIDATED_NOT_RELEASED' and check['batched_one_fatal_save_retention']==269114368 and not check['claim'] and not check['whole_capacity_admitted']
ck=F/'mcm-batched-checkpoint-reconciliation-review01-2026-10-09/SOURCE_REVIEW01.json';assert h(ck)=='27e26c2fbe0c6e66f77b93391f66841c65b7e214220ee38e3916e5ed2d5c196c'
receipt={'decision':'accepted_source_template_core_only','evidence':{str(p.relative_to(ROOT)):h(p) for p in (D/'MANIFEST.json',C/'CORE_MANIFEST02.json',C/'CORE_CHECK02.json',C/'TRANSPORT_LIMITS02.json',C/'CORE_FAILURE01.json',ck)},'checks':['Exact template and core manifests/current validator source pins verified.','26 original ancestry source bodies and four metadata bodies match original declaration hashes; no historical code executed.','Seven graphs415968128 cells,32 motifs512 spent samples,original numeric/pair/schedule/model/training retained; diagnostic stop removed.','Single fatal save retention269114368 replaces draft simultaneous cumulative allowance; original cumulative43058298880/160 and one-checkpoint schedule unchanged.','Legacy typed budgets unchanged; schema6 groups16,total6352,local output1.','Actual prior archive freshness1000ms/4096callbacks restored; only healthy record cap16384 changed within control_history.','Actual installed validation receipt joins exact core outputs; no genuine execution authority follows.'],'limitations':['Remaining physical/current capacity, transport authority, full input/producer descriptor binding and committed registration/source closure are incomplete.','No launch/release/admission or numerical/full-job success claim. Existing source and checkpoint proofs reused; no scientific tests repeated.']}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'decision':receipt['decision'],'sha256':h(R/'SOURCE_REVIEW01.json')}))
