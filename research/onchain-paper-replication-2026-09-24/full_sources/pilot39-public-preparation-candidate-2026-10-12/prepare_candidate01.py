"""Source-only finite candidate generation. Does not invoke any public builder."""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
D37=F/'real-data-pilot-full37-binding-preparation01-2026-10-11';D38=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
before=(D37/'build_public01.py').read_text();s=before
for a,b in [('pilot37','pilot39'),('20261011-37','20261012-39'),('full37','full39'),('resource37','resource39'),('Fixed37','Fixed39'),('real-data-pilot-full39-binding-preparation01-2026-10-11','real-data-pilot-full39-binding-preparation01-2026-10-12')]:s=s.replace(a,b)
s=s.replace("'Accepted and externally recovered genuine36 entry component required before execution'","'Actual closed38 component qualification, accepted outcome, fresh recovery and current whole39 capacity required before execution'")
s=s.replace("STOP=F/'pilot-efficiency-entry-qualification-2026-10-11'","ACCEPTED38=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'")
# Pin only accepted public metadata/source declaration, never active outcome or runtime envelope.
publicpins={n:sha(D38/n) for n in ['public01/mcm_policy.json','public01/pair_policy.json','public01/typed_payload.json','public01/pilot.json','public01/execution_job.json','EXPECTED_CODE_POLICY01.json']}
s=s.replace("def main(anchor):", "ACCEPTED38_PINS="+repr(publicpins)+"\n\ndef main(anchor):")
needle="    assert ref(OLD/'MANIFEST01.json')['sha256']==BASE_MANIFEST"
s=s.replace(needle,"    for name,digest in ACCEPTED38_PINS.items():assert ref(ACCEPTED38/name)['sha256']==digest\n"+needle)
needle="    queries='\\n'.join(anchor+':'+p for p in files)+'\\n'"
s=s.replace(needle,"    assert files==load(ACCEPTED38/'public01/pair_policy.json')['numerical_source']['files'], 'accepted38 source bodies changed'\n"+needle)
needle="    assert docs['mcm_policy']['schema_version']==6"
s=s.replace(needle,needle+"\n    accepted_mcm=load(ACCEPTED38/'public01/mcm_policy.json')\n    qualification=accepted_mcm.pop('entry_qualification')\n    assert qualification['experiment_id']=='eth-paper-real-data-end-to-end-resource-20261012-38'\n    assert docs['mcm_policy']==accepted_mcm, 'full route changes beyond removing entry qualification'\n    assert docs['mcm_policy']['batched']['continuation']['manifest_input'] is None\n    assert docs['mcm_policy']['batched']['continuation']['graph_manifest_inputs']=={}")
needle="    docs['typed_payload']=load(EFF/'SUCCESSOR_TYPED_DRAFT01.json')"
s=s.replace(needle,needle+"\n    assert docs['typed_payload']==load(ACCEPTED38/'public01/typed_payload.json')\n    assert len(docs['typed_payload']['graphs'])==7\n    assert sum(v['rows']*32 for v in docs['typed_payload']['graphs'].values())==415968128")
needle="    save(HERE/'EXPECTED_CODE_POLICY01.json',ast.literal_eval(expected))"
s=s.replace(needle,"    assert ast.literal_eval(expected)==load(ACCEPTED38/'EXPECTED_CODE_POLICY01.json')\n"+needle)
needle="    (HERE/'public01').mkdir()"
s=s.replace(needle,"    accepted_resources=load(ACCEPTED38/'public01/execution_job.json')['resources']\n    accepted_resources['storage_budget']['experiment']=NAME\n    accepted_resources['storage_budget']['roots'][1]=str(ROOT/'research_runs'/NAME)\n    assert docs['execution_job']['resources']==accepted_resources\n"+needle)
s=s.replace("'physical_caps_changed':False,", "'physical_caps_changed':False,'prior38_outcome':None,'prior38_recovery':None,'prior38_component_qualification':None,'current_whole39_capacity':None,'final_release':None,")
ast.parse(s);(P/'build_public01.py').write_text(s)
for baseline,label in [(D37/'build_public01.py','37'),(D38/'build_public01.py','38')]:
 b=baseline.read_text()
 (P/('BUILDER_FROM'+label+'_PATCH01.diff')).write_text(''.join(difflib.unified_diff(b.splitlines(True),s.splitlines(True),fromfile=str(baseline.relative_to(R)),tofile='full39/build_public01.py')))
 (P/('BUILDER_FROM'+label+'_INVERSE01.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),b.splitlines(True),fromfile='full39/build_public01.py',tofile=str(baseline.relative_to(R)))))
# Read-only metadata model of the intended delta; no builder invocation or data access.
old=json.loads((D38/'public01/mcm_policy.json').read_bytes());new=dict(old);removed=new.pop('entry_qualification')
policy={'identity':'eth-paper-real-data-end-to-end-resource-20261012-39','status':'UNEXECUTED_PUBLIC_BUILDER_CANDIDATE','full_route_mcm_removed_only':{'entry_qualification':removed},'mcm_remaining_equal':new==json.loads((D37/'public01/mcm_policy.json').read_bytes()),'graphs':7,'whole_cells':415968128,'cell_id':'real-eth-whole-seven-graph-joint-pilot-resource39','actual_joint_update_required':True,'continuation':new['batched']['continuation'],'prior38_outcome':None,'prior38_recovery':None,'prior38_component_qualification':None,'current_whole39_capacity':None,'final_release':None,'builder_executed':False,'binder_executed':False,'claim':False,'accepted38_public_pins':publicpins}
assert policy['mcm_remaining_equal'];(P/'CONFIG_DELTA01.json').write_text(json.dumps(policy,indent=2)+'\n')
sources=['tradingagents/research/admission.py']+['tradingagents/research/onchain_replication/'+n+'.py' for n in ['compact_mcm','imported_authority_lease','imported_mcm_identity','job','streamed_gat']]
(P/'SOURCE_MANIFEST01.json').write_text(json.dumps({'baselines':[ref(D37/'build_public01.py'),ref(D38/'build_public01.py')],'accepted_six_source_bodies':{n:sha(R/n) for n in sources},'accepted38_numerical_source_declaration':ref(D38/'public01/pair_policy.json'),'builder':ref(P/'build_public01.py'),'no_actual_git_or_builder_execution':True},indent=2)+'\n')
print(json.dumps({'builder_sha256':sha(P/'build_public01.py'),'mcm_remaining_equal':policy['mcm_remaining_equal'],'executed':False}))
