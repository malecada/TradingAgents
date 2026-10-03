import ast,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;P=F/'held-consumer-local-case-metadata-preparation01-2026-10-03';PAY=P/'capsule_payload';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');sha=lambda b:hashlib.sha256(b).hexdigest();doc=lambda p:json.loads(p.read_bytes())
m=doc(P/'MANIFEST01.json');actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()};assert actual=={r['path'] for r in m['files']}|{'MANIFEST01.json'}
for r in m['files']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
def body(r):
 n=r['path'];p=PAY/n if (PAY/n).exists() else S/n
 assert Path(n).as_posix()==n and not Path(n).is_absolute() and '..' not in Path(n).parts and p.resolve()==p and p.stat().st_nlink==1
 b=p.read_bytes();assert sha(b)==r['sha256'] and ('bytes' not in r or len(b)==r['bytes']);return b
source=doc(F/'held-consumer-actual-source-runtime-role-readback02-2026-10-03/ACTUAL_SOURCE_PLAN02.json');code=source['source_files'];pkg=source['package_files'];assert len(code)==199 and len(pkg)==148
for n,pin in code.items():assert sha((S/n).read_bytes())==pin
# Execute only installed pure metadata generator definitions, never numerical generation.
t=ast.parse((S/'fixture_tools/generate_inputs01.py').read_bytes());wanted={'canonical','sha','require','_held_ref','render_held_auxiliary_declaration','held_auxiliary_metadata','held_input_plan','HELD_ROLES','AUXILIARY_ROLES'}
nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in wanted or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in n.targets)]
ns={'Path':Path,'json':json,'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-pure-held-generators','exec'),ns)
gate=doc(PAY/'held-fixture-registration01.json');expected_runtime={p.name:sha(p.read_bytes()) for p in sorted((S/'tradingagents/research').glob('*.py'))}
oldids={p.name for p in (S/'research_runs').iterdir()};assert len(oldids)==4
for n in oldids:assert gate['experiments'][n]==doc(S/'research_runs'/n/'claim.json')['experiment']
base=gate['experiments']['original-import-native-success-20261003-04'];summary=[];findings=[]
for short,case in [('success','success'),('failure','second_target_publication_failure')]:
 refs=doc(P/(short+'-roles01.json'));assert set(refs)==set(ns['HELD_ROLES']) and len(refs)==15
 roles={k:{'reference':r,'document':body(r).decode() if k=='charter' else json.loads(body(r))} for k,r in refs.items()}
 plan=ns['held_input_plan'](roles,source);assert plan==doc(P/(short+'-input-plan01.json'))
 contract=roles['case_contract']['document'];eid=contract['experiment_id'];exp=gate['experiments'][eid]
 assert exp['parent'] is None and exp['cells']==['import-target-01','import-target-02'] and exp['stage']=='development' and exp['reuse']=='exploratory' and exp['selection'] is None
 assert exp['windows']==base['windows'] and exp['family']==base['family']
 assert len(exp['inputs'])==33 and len(exp['source_files'])==204 and len(exp['outputs'])==len(set(exp['outputs']))==6
 for n,pin in exp['source_files'].items():assert sha((PAY/n if (PAY/n).exists() else S/n).read_bytes())==pin
 for n,r in exp['inputs'].items():body(r)
 for k in ['budget_extension','budget_allocation','budget_review']:assert roles[k]['reference']['sha256'] in ['b1d56965524c870c3233e828cc94f28402c4d9b0cffe82f4d87bf090cbe3ce1c','7f882018f3d34bbd98a4ac1c1498e25fc3f4d577309832c87a98455e229c7120','e317a6e59b79036376dc055c8aa42db6366bf230b151b1cd66404576752e58f7']
 def inp(n):return json.loads(body(exp['inputs'][n]))
 job=inp(contract['job_input']);producer=inp(contract['plan_input'])['producers'][contract['producer']];selected=job['payload']['representation_jobs'][contract['representation']];descriptor=selected['descriptor']
 assert {k:v for k,v in producer.items() if k not in ('binding_output','journal_output')}==selected
 assert producer['held_score_consumer_input']==selected['held_score_consumer_input']==contract['held_policy_input']
 assert descriptor['resource_fixture']['case']==case and descriptor['required_graphs']==[r['graph_hash'] for r in roles['target_catalog']['document']['targets']]
 assert descriptor['configs']['matching']==roles['matching']['document']
 pair=inp('pair_policy');assert pair['numerical_source']=={'commit':source['anchor'],'files':pkg} and descriptor['pair_execution']['policy_sha256']==exp['inputs']['pair_policy']['sha256']
 for d,n in [('original_dictionary_import','original_import'),('original_dictionary_stage','original_import_stage')]:assert descriptor[d]=={'input':n,'sha256':exp['inputs'][n]['sha256']}
 assert descriptor['compact_execution']['policy_sha256']==exp['inputs']['compact_policy']['sha256']
 assert inp('compact_policy')['stage_policy']['score_chunk_cells']==64 and inp('mcm_policy')['numeric']['edge_chunk']==4096
 assert job['resources']==roles['native_policy']['document'] and job['resources']['disk_paths']==[str(S)] and job['resources']['storage_budget']['root']==str(S)
 assert inp(job['environment_input'])==roles['software_environment']['document']
 policy=inp('held_score_policy');assert body(exp['inputs']['held_score_policy'])==plan['rendered_metadata']['held_score_policy']['raw_utf8'].encode();assert policy['max_read_bytes']==768
 assert set(exp['outputs'])=={producer['binding_output'],producer['journal_output'],'cell-ledger.json','resource-summary.json',*contract['readback_outputs'].values()}
 er=roles['original_evidence']['document']['control_reference'];missing=not (PAY/er['path']).exists() and not (S/er['path']).exists();assert missing
 findings.append({'id':'HLM1','case':short,'dangling_control_reference':er,'actual_registered_control':exp['inputs']['original_import']})
 delta={n:{'registered':exp['runtime_hashes'].get(n),'actual':expected_runtime.get(n)} for n in set(exp['runtime_hashes'])|set(expected_runtime) if exp['runtime_hashes'].get(n)!=expected_runtime.get(n)};assert set(delta)=={'verify.py'}
 findings.append({'id':'HLM2','case':short,'runtime_hashes_delta':delta})
 summary.append({'identity':eid,'case':case,'roles':15,'inputs':33,'sources':204,'outputs':6,'parent':None,'package_anchor':source['anchor'],'windows':exp['windows']})
assert not any(n.split('.')[0] in ('numpy','torch','scipy') for n in sys.modules)
(H/'READBACK01.json').write_text(json.dumps({'manifest_sha256':sha((P/'MANIFEST01.json').read_bytes()),'members':len(m['files']),'payload_files':len(list(PAY.rglob('*')))-sum(p.is_dir() for p in PAY.rglob('*')),'cases':summary,'findings':findings,'historical_experiments_unchanged':4,'authority_executed':False,'numerical_imports':False},indent=2)+'\n')
print('PASS fullmanifest/pureplans15roles33inputs204pins6outputs;fouractualolddefsunchanged;currentpolicy64/4096/148anchor; REPRODUCED HLM1 missingcontrol/HLM2 staleverify bothcases; noauthority')
