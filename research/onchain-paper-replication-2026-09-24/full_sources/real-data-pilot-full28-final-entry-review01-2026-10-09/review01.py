import pathlib,json,hashlib,copy,subprocess,stat,os,resource,signal,ast
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();E=F/'real-data-pilot-full28-entry01-2026-10-09';P=F/'real-data-pilot-full28-input-draft01-2026-10-09';T=F/'real-data-pilot-full28-transport-binding01-2026-10-09';O=F/'real-data-pilot-full27-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-28';oldname=name[:-2]+'27'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();norm=lambda d:{k:{q:v[q] for q in ('path','sha256')} for k,v in d.items()}
def move(v):
 if type(v) is dict:return {move(k):move(x) for k,x in v.items()}
 if type(v) is list:return [move(x) for x in v]
 if type(v) is str:return v.replace(oldname,name).replace('real-eth-seven-graph-joint-update-resource27','real-eth-seven-graph-joint-update-resource28').replace('ethpilot-20261009-27','ethpilot-20261009-28')
 return v
b=j(E/'BINDING_DRAFT04.json');gate=j(E/'gate01.json');entry=gate['experiments'][name];oldgate=j(O/'gate01.json');oldentry=oldgate['experiments'][oldname];oldb=j(O/'BINDING01.json');evidence={}
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
s=(E/'preflight28_01.py').read_text();assert s.replace('20261009-28','20261009-27').replace('!=99','!=98').replace("'effective_attempt_budget':99","'effective_attempt_budget':98")==(O/'preflight27_01.py').read_text()
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
changed={p for p,v in pair['numerical_source']['files'].items() if oldpair['numerical_source']['files'][p]!=v};expected_changed={'tradingagents/research/onchain_replication/'+n for n in ('batched_driver.py','batched_numeric_reuse.py')};assert changed==expected_changed
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
for p in [E/'preflight28_01.py',E/'root_io28_01.py',E/'BINDING_DRAFT04.json',P/'prepare02.py',P/'PREPARATION02.json',P/'MANIFEST02.json',T/'bind_actual01.py',T/'BINDING_CHECK01.json',T/'REQUEST01.json',T/'ALL_INPUT_REFS01.json',F/'real-data-pilot-numerical-source-preflight-review01-2026-10-09/SOURCE_REVIEW01.json',F/'real-data-pilot-full27-final-entry-review01-2026-10-09/BINDING_REVIEW01.json',F/'real-data-pilot-full27-final-entry-review01-2026-10-09/SOURCE_REVIEW01.json']:add(p)
for ref in capacity['basis'].values():pin(ref)
tree=ast.parse((E/'preflight28_01.py').read_bytes());constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('INDEX_CAPACITY','BINDER','EXPECTED_RESOURCES')}
for k in ('INDEX_CAPACITY','BINDER'):pin(constants[k])
assert bound['inputs']['execution_job']['resources']==constants['EXPECTED_RESOURCES']
for q in ('pilot-batched-pair-policy-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-admission-dedup-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-batched-authority-poll-review01-2026-10-09/SOURCE_REVIEW01.json','pilot-preparation-eager-sweep-removal-review01-2026-10-09/SOURCE_REVIEW01.json'):add(F/q)
assert [p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
assert not (ROOT/'research_runs'/name).exists()

assert len(entry['source_files'])==416 and set(oldentry['source_files'])<=set(entry['source_files'])
assert {p for p,v in oldentry['source_files'].items() if entry['source_files'][p]!=v}==changed
for n in range(23,28):
 ident='eth-paper-real-data-end-to-end-resource-20261009-'+str(n)
 assert gate['experiments'][ident]==oldgate['experiments'][ident]
assert (T/'bind_actual01.py').read_text().replace('full28-input-draft01','full27-input-binding01').replace('20261009-28','20261009-27')==(F/'real-data-pilot-full27-transport-binding01-2026-10-09/bind_actual01.py').read_text()
assert len(bound['inputs'])==11 and len(core['inputs'])==4
immutable_roles=[k for k in refs if refs[k]==oldb['input_refs'][k]];assert len(immutable_roles)==51
# 52 non-bound-public/non-private roles includes the fresh scratch declaration; 51 literal original refs.
assert len(set(refs)-set(bound['inputs'])-{'archive_transport'})==52
for role,pref in public['public_inputs'].items():
 pin(pref)
assert len(public['public_inputs'])==12
for role in ('token_source_review','timing_source_review'):
 reviewed=j(ROOT/b[role]['path']);assert reviewed['decision'].startswith('accepted')
add(E/'ENTRY_CORRECTION01.json');add(E/'ENTRY_CORRECTION02.json')
ad=j(E/'ADMISSION_CHECK01.json');add(E/'ADMISSION_CHECK01.json')
for ext in ('stdout','stderr'):
 p=E/('ADMISSION_CHECK01.'+ext);assert h(p)==ad[ext+'_sha256'];add(p)
assert ad['exit_code']==0
r={'decision':'accepted','identity':name,'input_refs':refs,'evidence':evidence,'scope':'Corrected DRAFT04 changed source/input/caller binding only; conditional on exact final binding, current committed admission, actual final preparation external recovery and fresh preflight/native eligibility. No claim or launch granted.'}
(R/'BINDING_REVIEW01.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
v={'decision':'accepted_changed_entry_only','identity':name,'binding_review_sha256':h(R/'BINDING_REVIEW01.json'),'source_count':416,'input_count':64,'evidence_count':len(evidence),'anchor':capacity['source_anchor'],'changed_numerical_source_pins':{p:entry['source_files'][p] for p in sorted(changed)},'checks':['All193 numeric pins,365 public pins and366 union authenticate actual anchor bytes and local files. Prior406 gate source membership preserved with exactly two accepted replacements plus10 entry refs.','Wrapper inverse only identity and enforced/reported99; RootIO import only; binder inverse input directory and identity only.','12 public templates,11 bound public documents, sole opaque private reference.52 remaining roles consist51 unchanged refs plus namespace-renamed scratch262144.','Exact public/prepared/bound inverse; four core bodies and full7graphs32motifs512samples/original model/training/tolerances unchanged.','Historical23–27 experiment definitions literal unchanged; genuine99 extension/allocation/review pins and exact review object joined.','Capacity terms13551374941allocated/10988852301logical unchanged; currentness and remote samples are observations, not future-success promises.','Prior27 partial4096 and FAILED dispositions remain unchanged; actual outcome11 recoveryc9f reused.'],'corrected_findings':['Original375 gate omitted batched_pilot_reservations membership; corrected416 restores prior full406 plus10.','Reported effective_attempt_budget98 corrected99; enforcement was99 throughout.','Draft03 budget_review extra bytes removed in04 to satisfy exact gate equality.'],'preserved_harness_failures':['CHECK01 source membership refusal','CHECK02 wrong expected timing-module filename in reviewer adaptation','CHECK03 concurrent gate correction invalidated old draft ref','CHECK04 reviewer cell-rename identity typo','CHECK05 exact budget-review object refusal'],'admission_qualification':'Actual ADMISSION_CHECK01 sourcec5cc passed metadata only for predecessor375 configuration; it is retained historical evidence, not an assertion that corrected416 committed admission has occurred.','private_qualification':'Only current28 opaque private file hash/stat checked; no connection body or credentials decoded.','limitations':'No numerical imports/empirical array reads/Run/Owner/network; no complete scientific result, current capacity, full preparation recovery or launch authority.'}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'binding':h(R/'BINDING_REVIEW01.json'),'source':h(R/'SOURCE_REVIEW01.json'),'evidence':len(evidence)}))
