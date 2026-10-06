"""Tiny artificial metadata. Opaque sentinels are deliberately not numeric data."""
import ast,copy,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('builder',HERE/'build_inputs01.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
root=HERE/'synthetic02';root.mkdir()
def save(name,value,body=False):
    raw=value if body else b.raw(value);p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return {'path':name,'sha256':b.sha(raw),'bytes':len(raw)}
refs={};graphs={}
evidence=save('counts-evidence.json',{'synthetic':True})
for i,week in enumerate(b.WEEKS):
    start=b.date(week);arrays={k:{'path':k+'.npy','sha256':b.sha((k+week).encode()),'bytes':128} for k in ('node_ids','node_features','edge_index','edge_features','edge_aggregates')}
    value={'graph_hash':b.sha(week.encode()),'arrays':arrays,'metadata':{'asset':'ETH','start_utc':week,'end_utc':b.stamp(start+b.timedelta(days=7)),'available_at':b.stamp(start+b.timedelta(days=8)),'graph_config_hash':b.GRAPH_CONFIG,'source_hashes':[b.sha(('source'+week).encode())]}}
    m=save(f'g{i}.json',value);n=save(f'n{i}.json',{'schema_version':1,'kind':'graph-node-count-metadata-v1','graph_manifest_sha256':m['sha256'],'node_features_sha256':arrays['node_features']['sha256'],'rows':i+1,'method':'retained-header-only','evidence':evidence});graphs[week]={'role':f'graph{i}','manifest':m,'node_count':n}
for name,pin in b.PINS.items():
    refs[name]=save(name+'.opaque',b'UNREAD-SYNTHETIC-SENTINEL',True)|{'sha256':pin}
for name in ('model','training','pair','import_stage','mcm','environment'):refs[name]=save(name+'.opaque',b'UNREAD-SYNTHETIC-CONFIG',True)
original={}
for name in ('dictionary','samples','dictionary_config','matching_config','graph_manifest','claim','terminal','gate','dictionary_intent','sample_intent','dictionary_result'):
    role='original_'+name;refs[role]=save(role+'.opaque',('UNREAD '+role).encode(),True);original[name]={'input':role,'sha256':refs[role]['sha256'],'original_path':'/original/'+name}
limits={'max_allocated_bytes':8*1024**3,'max_logical_bytes':8*1024**3,'max_entries':10000,'max_depth':32,'max_scan_seconds':5}
resources={'memory_max_bytes':6*1024**3,'memory_high_bytes':5*1024**3,'reserve_bytes':3*1024**3,'start_reserve_bytes':9*1024**3,'disk_floor_bytes':10*1024**3,'disk_paths':[str(root)],'wall_seconds':28800,'native_unit_limits':{'file_size_bytes':4*1024**2},'storage_budget':{'schema_version':2,'kind':'real-pilot-writable-union','authority_root':str(root),'experiment':'eth-paper-real-data-end-to-end-resource-20261005-01','roots':[str(root/'research_artifacts'),str(root/'research_runs/eth-paper-real-data-end-to-end-resource-20261005-01')],'shared_files':[str(root/'research_runs/.lock')],'limits':limits}}
outputs={'summary':'summary.json','ledger':'ledger.json','binding':'binding.json','journal':'journal.json'}
pilot={'schema_version':2,'kind':'real-data-import-training-pilot-v1','asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'resource','graph_inputs':{},'indices':None,'decisions':b.DECISIONS,'graph_sequences':[],'population_scope':'resource_pilot_subset','population_plan_input':'population','model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':4*1024**2,'outputs':outputs,'resource_policy':resources,'archive_inputs':{'policy_input':'archive','transport_input':'transport'}}
pop={'schema_version':1,'population_scope':'resource_pilot_subset','financial_fit_complete':False,'fold':'2024','scope_input':'scope','calendar_input':'calendar','price_panel_input':'prices','graphs':{},'outputs':{'resource_population':'population.json','binding':'population-binding.json'}}
selection={'operation':'produce','plan_input':'producer_plan','producer':'original','pair_checkpoint_input':'pair','descriptor':{'arm':'proposed','dictionary_origin':'imported-original-v1','required_graphs':[]},'original_dictionary_input':'dictionary_control','compact_policy_input':'compact','native_backend':b.BACKEND,'original_dictionary_stage_input':'import_stage','compact_mcm_input':'mcm','compact_mcm_output_input':'output','real_pilot_input':'pilot','compact_archive_input':'archive','compact_archive_transport_input':'transport'}
job={'schema_version':1,'kind':'compact_resource','resources':resources,'environment_input':'environment','payload':{'representation_jobs':{'proposed':selection}}}
control={'schema_version':1,'kind':'original-dictionary-import-v1','original_claim':'unchanged-original','original_source':'a'*40,'week':'2021-11-29T00:00:00Z','dictionary_identity':'b'*64,'sample_identity':'c'*64,'seed':11,'sample_count':512,'motif_count':32,'required_graphs':[],'refs':original}
compact={'stage_policy':{'score_chunk_cells':65536,'log':{'max_events':1000,'chunk_events':128}}}
archive={'local_free_floor_bytes':10*1024**3,'max_stage_verifications':1,'max_decoded_transfer_bytes':10**8,'max_remote_payload_bytes':10**8,'max_workflow_metadata_bytes':2*10**6}
templates={'pilot':pilot,'population':pop,'job':job,'producer_plan':{'schema_version':2,'producers':{'original':copy.deepcopy(selection)}},'dictionary':control,'compact':compact,'archive':archive,'output':{'schema_version':1,'backend':b.BACKEND,'max_artifact_bytes':1024**2,'max_workflow_output_bytes':16*1024**2}}
roles={k:('dictionary_control' if k=='dictionary' else k) for k in templates}
for name,value in templates.items():refs[roles[name]]=save(roles[name]+'.json',value)
allocation={kind:{'max_operations':16,'max_preserved_bytes':10**6,'max_recovered_bytes':10**6,'max_chunks':32,'chunk_bytes':(b.LIMIT//width)*width} for kind,width in b.KINDS.items()}
s={'graphs':graphs,'references':refs,'template_roles':roles,'typed_input_role':'typed','typed_allocations':{'chunk_cells':65536,'by_week':{w:copy.deepcopy(allocation) for w in b.WEEKS},'max_control_bytes':10**6},'physical_store':{'baseline_evidence':evidence,'baseline_allocated_bytes':1000,'baseline_logical_bytes':1000,'reserved_growth_bytes':10**6,'reserved_control_bytes':3*10**9},'transport_limits':{'rate_kbit':262144,'max_seconds':28800,'max_payload_bytes':10**9,'max_commands':10000,'max_diagnostic_bytes':3*10**9,'max_control_bytes':6*10**9,'namespace':'synthetic-only','receipt_output':'archive.json','terminal_output':'archive-terminal.json'}}
# Synthetic declaration enlarged together solely to exercise finite schema arithmetic.
s['physical_store']['reserved_control_bytes']=10**10
resources['storage_budget']['limits']['max_allocated_bytes']=32*1024**3;resources['storage_budget']['limits']['max_logical_bytes']=32*1024**3
refs['job']=save('job.json',job);refs['pilot']=save('pilot.json',pilot)
result=b.build(root,s);assert result==b.build(root,s)
p=result['inputs']['pilot'];assert p['indices'] is None and p['decisions']==b.DECISIONS and len(p['graph_sequences'])==16 and all(len(x)==28 for x in p['graph_sequences'])
assert p['graph_sequences'][0][0]==b.sha(b.WEEKS[0].encode()) and p['graph_sequences'][-1][-1]==b.sha(b.WEEKS[-1].encode())
assert result['inputs']['transport']['connection'] is None
assert result['inputs']['producer_plan']['producers']['original']['descriptor']==result['inputs']['job']['payload']['representation_jobs']['proposed']['descriptor']
assert result['inputs']['dictionary_control']['refs']==original
# Original installed pure validators, AST-extracted without importing numerical modules.
def funcs(path,names,ns):
    t=ast.parse(path.read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns
ns={'Path':Path,'GIB':1024**3,'FILE_MAX':b.LIMIT,'KIND':'real-data-import-training-pilot-v1','require':b.need}
funcs(ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py',['validate_plan','_finite_resources'],ns)['validate_plan'](p)
ns={'require':b.need,'SCOPE':'resource_pilot_subset','DECISIONS':b.DECISIONS,'WEEKS':b.WEEKS}
funcs(ROOT/'tradingagents/research/onchain_replication/real_pilot_population.py',['validate_plan'],ns)['validate_plan'](result['inputs']['population'],p)
import re
ns={'require':b.need,'KINDS':b.KINDS,'ASSUMPTION':b.ASSUMPTION,'re':re}
funcs(ROOT/'tradingagents/research/onchain_replication/typed_payload_policy.py',['validate','capacity'],ns)
assert ns['capacity'](result['inputs']['typed'])==result['capacity_lower_bounds']['typed']
refusals=[]
def refused(name,fn):
    try:fn()
    except (ValueError,KeyError) as error:refusals.append({'case':name,'reason':str(error)})
    else:raise AssertionError(name)
bad=copy.deepcopy(s);bad['graphs'][b.WEEKS[1]]['manifest']['path']='missing-manifest.json';refused('missing genuine manifest',lambda:b.build(root,bad))
bad=copy.deepcopy(s);bad['typed_allocations']['by_week'][b.WEEKS[0]]['score-batch-f64']['max_recovered_bytes']=1;refused('underfunded original f64 recovery',lambda:b.build(root,bad))
bad=copy.deepcopy(s);bad['references']['prices']['sha256']='e'*64;refused('substituted frozen price reference',lambda:b.build(root,bad))
refused('price body decode',lambda:b.metadata(root,refs['prices']))
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
(HERE/'SYNTHETIC_SPEC01.json').write_bytes(b.raw(s));(HERE/'SYNTHETIC_DRAFT01.json').write_bytes(b.raw(result));(HERE/'CHECK01.json').write_bytes(b.raw({'status':'passed','pure_installed_validators':3,'deterministic_rebuild':True,'refusals':refusals,'qualification':'artificial metadata and unread sentinel bodies, not genuine graph or authority proof'}));print('PASS deterministic fixed16x28 / caller-population-typed schema joins / 4 refusals; no numerical imports')
