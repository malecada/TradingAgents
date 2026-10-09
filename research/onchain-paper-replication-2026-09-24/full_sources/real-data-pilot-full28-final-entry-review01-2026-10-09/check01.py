import pathlib,json,hashlib,copy,subprocess,stat,os,resource,signal,ast
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();E=F/'real-data-pilot-full28-entry01-2026-10-09';P=F/'real-data-pilot-full28-input-draft01-2026-10-09';T=F/'real-data-pilot-full28-transport-binding01-2026-10-09';O=F/'real-data-pilot-full27-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-28';oldname=name[:-2]+'27'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();norm=lambda d:{k:{q:v[q] for q in ('path','sha256')} for k,v in d.items()}
def move(v):
 if type(v) is dict:return {move(k):move(x) for k,x in v.items()}
 if type(v) is list:return [move(x) for x in v]
 if type(v) is str:return v.replace(oldname,name).replace('real-eth-seven-graph-joint-update-resource28','real-eth-seven-graph-joint-update-resource28').replace('ethpilot-20261009-27','ethpilot-20261009-28')
 return v
b=j(E/'BINDING_DRAFT01.json');gate=j(E/'gate01.json');entry=gate['experiments'][name];oldgate=j(O/'gate01.json');oldentry=oldgate['experiments'][oldname];oldb=j(O/'BINDING01.json');evidence={}
def pin(ref):
 p=ROOT/ref['path'];assert p.resolve()==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2,ref['path'];assert h(p)==ref['sha256'],ref['path'];evidence[ref['path']]=ref['sha256']
 if 'bytes' in ref:assert p.stat().st_size==ref['bytes']
def add(p):pin({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
refs=norm(entry['inputs']);assert len(refs)==64 and refs==b['input_refs']==norm(j(T/'ALL_INPUT_REFS01.json'))
assert {k:v['dataset'] for k,v in entry['inputs'].items()}=={k:v['dataset'] for k,v in oldentry['inputs'].items()}
for p,v in entry['source_files'].items():pin({'path':p,'sha256':v})
for ref in refs.values():pin(ref)
for ref in b.values():
 if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():pin(ref)
# Accepted wrapper logic exactly preserved after fixed identity/budget/import changes.
s=(E/'preflight28_01.py').read_text();assert s.replace('20261009-28','20261009-27').replace('!=99','!=98')==(O/'preflight27_01.py').read_text()
assert (E/'root_io28_01.py').read_text().replace('from preflight28_01 import check','from preflight27_01 import check')==(O/'root_io27_01.py').read_text()
for p in (oldname,oldentry['parent']):assert gate['experiments'][p]==j(ROOT/'research_runs'/p/'claim.json')['experiment']
for k in ('families','datasets','program_id'):assert gate[k]==oldgate[k]
for k in ('family','stage','windows','reuse','selection','runtime_hashes','outputs'):assert entry[k]==oldentry[k],k
assert entry['parent']==oldname and entry['cells']==['real-eth-seven-graph-joint-update-resource28']
prepared=j(T/'PREPARED01.json');bound=j(T/'BOUND01.json');public=j(ROOT/b['public_manifest']['path']);core=j(ROOT/b['core_manifest']['path']);prior=j(ROOT/b['public_refs']['path']);capacity=j(ROOT/b['capacity_observation']['path']);oldprepared=j(ROOT/oldb['preparation']['path'])
assert prepared['preparation_origin']['public_manifest']==b['public_manifest'] and bound['source_request']['prepared']==b['preparation'] and bound['source_request']['archive_policy']==b['unbound_archive'] and prepared['builder03_spec']['references']['archive_policy']==b['unbound_archive']
for role,body in bound['inputs'].items():assert j(ROOT/refs[role]['path'])==body
for role,ref in core['inputs'].items():pin(ref);assert j(ROOT/refs[role]['path'])==j(ROOT/ref['path'])
for role in set(prior)-set(bound['inputs'])-{'archive_transport','matching_ordered_edge_scratch'}:assert refs[role]['sha256']==prior[role]['sha256']
old=move(oldprepared['builder03_result']['inputs']);actual=copy.deepcopy(prepared['builder03_result']['inputs']);pair=actual['pair_policy'];oldpair=old['pair_policy'];assert {k:v for k,v in pair.items() if k!='numerical_source'}=={k:v for k,v in oldpair.items() if k!='numerical_source'}
package=ROOT/'tradingagents/research/onchain_replication';required={'tradingagents/research/onchain_replication/'+p.name for p in package.glob('*.py')}|{'tradingagents/research/'+p.name for p in package.parent.glob('*.py')}|{'tradingagents/__init__.py'}
assert len(required)==193 and set(pair['numerical_source']['files'])==required and all(entry['source_files'].get(p)==v for p,v in pair['numerical_source']['files'].items())
assert len(oldpair['numerical_source']['files'])==193 and set(required)==set(oldpair['numerical_source']['files'])
changed={p for p,v in pair['numerical_source']['files'].items() if oldpair['numerical_source']['files'][p]!=v};expected_changed={'tradingagents/research/onchain_replication/'+n for n in ('batched_driver.py','batched_numeric_execution.py')};assert changed==expected_changed
actual['pair_policy']=oldpair
for val,ov in ((actual['execution_job']['payload']['representation_jobs']['original32'],old['execution_job']['payload']['representation_jobs']['original32']),(actual['producer_plan']['producers']['original32'],old['producer_plan']['producers']['original32'])):
 for key in ('pair_execution','compact_execution','compact_archive_execution'):val['descriptor'][key]['policy_sha256']=ov['descriptor'][key]['policy_sha256']
assert actual==old
for val in (bound['inputs']['execution_job']['payload']['representation_jobs']['original32'],bound['inputs']['producer_plan']['producers']['original32']):
 d=val['descriptor'];assert d['configs']['dictionary']['size']==32 and d['configs']['dictionary']['sample_count']==512 and len(d['required_graphs'])==7
 for key,role in (('pair_execution','pair_policy'),('compact_execution','compact_policy'),('compact_archive_execution','archive_policy')):assert d[key]['policy_sha256']==refs[role]['sha256']
 for key in ('original_dictionary_import','original_dictionary_stage'):assert d[key]['sha256']==refs[d[key]['input']]['sha256']
# Bound-vs-prepared inverse: only archive identity/descriptor, no connection decoding.
a=copy.deepcopy(bound['inputs']);ar=a.pop('archive_policy');unbound=j(ROOT/b['unbound_archive']['path']);ar['transport_identity']=None;assert ar==unbound
for val in (a['execution_job']['payload']['representation_jobs']['original32'],a['producer_plan']['producers']['original32']):val['descriptor']['compact_archive_execution']['policy_sha256']=bound['binding']['prior_descriptor_policy_sha256']
a['archive_transport']=prepared['builder03_result']['inputs']['archive_transport'];assert a==prepared['builder03_result']['inputs']
assert bound['private_input']=={'archive_transport':b['transport']};opaque=ROOT/b['transport']['path'];assert stat.S_IMODE(opaque.stat().st_mode)==0o600 and stat.S_IMODE(opaque.parent.stat().st_mode)==0o700 and h(opaque)==b['transport']['sha256']
assert capacity['source_body_pins']==public['source_pins'] and len(public['source_pins'])==365 and all(entry['source_files'].get(p)==v for p,v in public['source_pins'].items())
oldcap=move(j(ROOT/oldb['capacity_observation']['path']));c=copy.deepcopy(capacity)
for k in ('at','source_anchor','source_body_pins','qualification','basis','decision_scope'):c[k]=oldcap[k]
assert c==oldcap and capacity['new_allocated_growth_bytes']==13551374941 and capacity['new_logical_growth_bytes']==10988852301
assert capacity['source_anchor']==pair['numerical_source']['commit'] and capacity['source_anchor'].startswith('1d23956e')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert subprocess.run(['git','merge-base','--is-ancestor',capacity['source_anchor'],head]).returncode==0
combined_pins=dict(public['source_pins']);combined_pins.update(pair['numerical_source']['files']);assert len(combined_pins)==366
paths=list(combined_pins);raw=subprocess.check_output(['git','-c','core.packedGitWindowSize=1m','-c','core.packedGitLimit=16m','cat-file','--batch'],input=('\n'.join(capacity['source_anchor']+':'+p for p in paths)+'\n').encode());pos=0
for p in paths:
 end=raw.index(b'\n',pos);header=raw[pos:end].split();assert len(header)==3 and header[1]==b'blob';n=int(header[2]);pos=end+1;assert hashlib.sha256(raw[pos:pos+n]).hexdigest()==combined_pins[p];pos+=n+1
assert pos==len(raw)
scratch=j(ROOT/refs['matching_ordered_edge_scratch']['path']);assert scratch==move(j(ROOT/oldb['input_refs']['matching_ordered_edge_scratch']['path']))
assert scratch['experiment']==name and scratch['incremental_explicit_numeric_scratch_bytes']==262144
pin(entry['charter']);extref=entry['cumulative_budget_extension']['extension'];pin(extref);ext=j(ROOT/extref['path']);pin(ext['allocation']);assert entry['cumulative_budget_extension']['review']==b['budget_review'];br=j(ROOT/b['budget_review']['path']);assert br['decision']=='accepted' and br['extension_sha256']==extref['sha256'] and ext['cumulative_ceiling']==99 and ext['consumed_before']==67
for ref in (extref,ext['allocation'],b['budget_review']):assert entry['source_files'].get(ref['path'])==ref['sha256'],'Missing cumulative97 source pin '+ref['path']
for p in [E/'preflight28_01.py',E/'root_io28_01.py',E/'BINDING_DRAFT01.json',P/'prepare02.py',P/'PREPARATION02.json',P/'MANIFEST02.json',T/'bind_actual01.py',T/'BINDING_CHECK01.json',T/'REQUEST01.json',T/'ALL_INPUT_REFS01.json',F/'real-data-pilot-numerical-source-preflight-review01-2026-10-09/SOURCE_REVIEW01.json',F/'real-data-pilot-full27-final-entry-review01-2026-10-09/BINDING_REVIEW01.json',F/'real-data-pilot-full27-final-entry-review01-2026-10-09/SOURCE_REVIEW01.json']:add(p)
for ref in capacity['basis'].values():pin(ref)
tree=ast.parse((E/'preflight28_01.py').read_bytes());constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('INDEX_CAPACITY','BINDER','EXPECTED_RESOURCES')}
for k in ('INDEX_CAPACITY','BINDER'):pin(constants[k])
assert bound['inputs']['execution_job']['resources']==constants['EXPECTED_RESOURCES']
for q in ('pilot-batched-pair-policy-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-admission-dedup-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-batched-authority-poll-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-preparation-eager-sweep-removal-review01-2026-10-09/SOURCE_REVIEW01.json'):add(F/q)
assert [p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
assert not (ROOT/'research_runs'/name).exists()
print('REMAINING_JOIN_CHECKS_PASSED',len(evidence))
