from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,types
R=Path(__file__).resolve().parent
A=R.parent/'held-consumer-final-composition-root-preparation01-2026-10-03'
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
P=C.parent.parent/'held-score-consumer-root-launch-20261003-01'
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda p:json.loads(p.read_bytes())
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1')
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
proposal=J(A/'NATIVE_CONTRACT_PROPOSAL01.json');actual=J(P/'release-unreleased01.json')
assert H((A/'NATIVE_CONTRACT_PROPOSAL01.json').read_bytes())=='2d80c20b409f55ecd3e61141d8a962b43ba2d105326248f40fb6bfffea906b8c'
assert H((P/'launch_success01.py').read_bytes())=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc'
assert H((P/'held_outcome02.py').read_bytes())=='95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
proofs=('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
contract=H(canonical({k:v for k,v in proposal.items() if k not in proofs}))
assert contract=='17e513bb0fa4ae667c822d80118578ae487138a3c6ad1cdd1123b7d68c435110'
assert actual['status']=='UNRELEASED-investigation-template' and all(proposal[k] is None for k in proofs)
assert {k:v for k,v in actual.items() if k not in ('status','remaining')}=={k:v for k,v in proposal.items() if k not in ('status','remaining')}
m=load(P/'held_outcome02.py','native_contract_semantic');reader=m.Reader(C);reg=m.sources(reader,proposal)
assert len(proposal['source_files'])==204 and len([p for p in proposal['source_files'] if p.startswith('tradingagents/')])==148
case_rows={};G=1024**3
for case,entry in proposal['cases'].items():
 exp=reg['experiments'][entry['identity']];assert exp==entry['experiment'] and reg['families'][exp['family']]==proposal['family']
 assert exp['parent'] is None and len(exp['inputs'])==33 and exp['outputs']==['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json','held-target-01.json','held-target-02.json']
 for name in exp['inputs']:m.input_body(reader,exp,name)
 job=json.loads(m.input_body(reader,exp,'execution_job'));p=job['resources'];assert p==entry['job_resources']
 assert job['kind']=='compact_resource' and p['memory_max_bytes']==p['memory_high_bytes']==3*G and p['wall_seconds']==1800 and p['reserve_bytes']==3*G and p['start_reserve_bytes']==6*G
 assert p['disk_floor_bytes']==10*G and p['native_unit_limits']=={'file_size_bytes':4194304} and p['disk_paths']==[str(C)]
 assert p['storage_budget']=={'root':str(C),'limits':{'max_allocated_bytes':G,'max_logical_bytes':G,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}
 assert 'physical_policy' not in p
 ext=exp['cumulative_budget_extension'];body=reader.body(ext['extension']['path']);review=reader.body(ext['review']['path'])
 assert H(body)==ext['extension']['sha256']=='b1d56965524c870c3233e828cc94f28402c4d9b0cffe82f4d87bf090cbe3ce1c'
 assert H(review)==ext['review']['sha256']=='e317a6e59b79036376dc055c8aa42db6366bf230b151b1cd66404576752e58f7'
 extension=json.loads(body);budget_review=json.loads(review);assert budget_review['decision']=='accepted' and budget_review['extension_sha256']==H(body)
 selected=next(iter(job['payload']['representation_jobs'].values()));plan=json.loads(m.input_body(reader,exp,selected['plan_input']));item=plan['producers'][selected['producer']]
 assert all(item[k]==v for k,v in selected.items())
 policy=json.loads(m.input_body(reader,exp,selected['compact_policy_input']));held=json.loads(m.input_body(reader,exp,selected['held_score_consumer_input']))
 assert policy['stage_policy']['score_chunk_cells']==64 and len(held['targets'])==2 and held['max_read_bytes']==768
 for b in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/b/entry['identity'])
 case_rows[case]={'identity':entry['identity'],'inputs':33,'outputs':6,'parent':None,'budget_extension':extension,'policy':policy,'held_policy':held}
assert proposal['family']['attempt_budget']==2 and proposal['family']['prior_attempts']==0
source=C/'tradingagents/research/onchain_replication';jobraw=(source/'job.py').read_text();tree=ast.parse(jobraw);nodes={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'}
exec(compile(ast.Module([nodes['_command']],type_ignores=[]),str(source/'job.py'),'exec'),ns)
args=types.SimpleNamespace(root=str(C),registration=proposal['registration'],experiment=proposal['cases']['success']['identity'],source=proposal['capsule_commit'])
vectors={mode:ns['_command'](args,mode) for mode in ('launch','monitor','worker')}
for mode,v in vectors.items():assert v==[sys.executable,'-B','-m',ns['MODULE'],'--mode',mode,'--root',str(C),'--registration',args.registration,'--experiment',args.experiment,'--source',args.source]
worker=ast.get_source_segment(jobraw,nodes['worker']);assert worker.index('resources.assert_guarded_worker(')<worker.index('_resource_limit_receipt(')<worker.index('with ResearchRun.start(')<worker.index('resource_fixture.execute(')
fixture=(source/'resource_fixture.py').read_text();ft=ast.parse(fixture);execute=ast.get_source_segment(fixture,next(n for n in ft.body if isinstance(n,ast.FunctionDef) and n.name=='execute'))
assert execute.index('preflight(')<execute.index('resource_binding.open_first(')<execute.index('original_import_stage.attach(')<execute.index('compact_mcm.produce_imported(')
rtpath=C/'fixture_tools/runtime_gate01.py';assert H(rtpath.read_bytes())==proposal['source_files']['fixture_tools/runtime_gate01.py'];runtime=load(rtpath,'native_contract_runtime');os.chdir(C);rr=runtime.check(C,proposal['runtime']);os.chdir(R)
reader.recheck();assert len(proposal['runtime']['distribution_records'])==251 and not any(n in sys.modules for n in ('numpy','torch','scipy'))
assert not os.path.lexists(P/'attempt')
refs={str(p):H(p.read_bytes()) for p in [A/'NATIVE_CONTRACT_PROPOSAL01.json',P/'launch_success01.py',P/'held_outcome02.py',P/'release-unreleased01.json',P/'request-unreleased01.json',source/'job.py',source/'resource_fixture.py',source/'matching_owner.py',source/'resource_binding.py',source/'resources.py',source/'compact_mcm.py',source/'held_score_consumer.py',C/'fixture_tools/outer_controller01.py',rtpath]}
out={'schema_version':1,'scope':'source contract and actual readonly metadata; not release authority','contract_sha256':contract,'references':refs,'current_git_registration_sources':205,'package_sources':148,'cases':case_rows,'command_vectors':vectors,'actual_runtime_metadata':rr,'runtime_records':251,'numerical_imports':False,'actual_claims_started':0,'actual_units_launched':0,'three_release_proof_fields':None,'genuine_source_order_static_only':True}
(R/'READBACK02.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print('PASS: actual205Git/source+both33opaque inputs/six outputs/148package; exact two cases, budget refs, limits; real251 runtime metadata; extracted command vectors and static guarded claim ordering; no numerical imports, claims, native units or release decision.')
