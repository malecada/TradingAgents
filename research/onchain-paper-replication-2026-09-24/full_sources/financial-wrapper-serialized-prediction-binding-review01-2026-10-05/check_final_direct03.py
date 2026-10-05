from pathlib import Path
import ast,hashlib,json,os,stat
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;R=F/'financial-wrapper-serialized-prediction-final-direct01-2026-10-05';B=F/'financial-wrapper-serialized-storage-final-direct01-2026-10-05'
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(name,obj):
 p=D/name
 with p.open('x') as h:h.write(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
 p.chmod(0o444)
old=(B/'recover01.py').read_text();new=(R/'recover02.py').read_text();assert sha(old.encode())=='d1317d86400d649c6e3281b5ac4b9b86a41272b01d7ba9ac267065c921421e11';assert sha(new.encode())=='a7a6c0168a336bfcba455ee60ba2663d2a08ecf10f69a56ec3e78530934d1126'
def assignment(t,key):return [n for n in ast.parse(t).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id==key][-1]
a=assignment(old,'REQUIRED');b=assignment(new,'REQUIRED');required=ast.literal_eval(b.value)
lines=new.splitlines(True);lines[b.lineno-1:b.end_lineno]=old.splitlines(True)[a.lineno-1:a.end_lineno]
inverse=''.join(lines).replace('FINAL_POPULATION_COUNT = 23','FINAL_POPULATION_COUNT = 20').replace('fresh-serialized-prediction-final-direct01.git','fresh-serialized-storage-final-direct01.git').replace('fresh-actual-serialized-prediction-final-direct01-recovered','fresh-actual-remote-compatibility-final-bundle01-supervised-recovered');assert inverse==old
for name,pin in [('watch01.py','121a443011f6a95f6e5ec84fedd6a06c51e328d1d317cdf445b77ef192b20795'),('utilities/owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb')]:assert (R/name).read_bytes()==(B/name).read_bytes() and sha((R/name).read_bytes())==pin
s=json.loads((R/'SELECTED_BODIES_DRAFT02.json').read_bytes());assert s['remote_commit'] is None and len(s['rows'])==23 and sum(x['bytes'] for x in s['rows'])==583271
assert required=={x['path']:{k:v for k,v in x.items() if k!='path'} for x in s['rows']}
rows={x['path']:x for x in s['rows']};bodies={}
for path,row in rows.items():
 p=M/path;raw=p.read_bytes();st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and len(raw)==row['bytes'] and sha(raw)==row['sha256'] and len(raw)<=4194304;bodies[path]=raw
scope=json.loads((R/'FINAL_TYPED_SCOPE02.json').read_bytes());assert len(scope['original_regular_files'])==23
mapping=scope['actual_parent_delta_body_mapping'];assert len(mapping)==2
for row in scope['original_regular_files']:
 p=Path(row['path']);rel=mapping.get(str(p),str(p.relative_to(M)) if p.is_relative_to(M) else None);assert rel in rows
 raw=bodies[rel];st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==row['mode'] and len(raw)==row['bytes'] and sha(raw)==row['sha256'];assert p.read_bytes()==raw
P=Path(next(iter(mapping))).parent;assert sorted(x.name for x in P.iterdir() if x.is_file()) and len([x for x in P.rglob('*') if x.is_file()])==13
q=json.loads((P/'REQUEST_FINAL01.json').read_bytes());candidate=json.loads((P/'REQUEST_RELEASE_CANDIDATE01.json').read_bytes());assert q['final_review']==ref(D/'FINAL_PARENT_REVIEW01.json');qq=dict(q);qq['final_review']=None;assert qq==candidate
review=json.loads((D/'FINAL_PARENT_REVIEW01.json').read_bytes());qq=dict(q);qq.pop('final_review');assert sha((json.dumps(qq,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())==review['contract_sha256'];assert sha((P/'REQUEST_FINAL01.json').read_bytes())=='a1bb2267b835a36117f67422a3451da99e0b740e8e41911d2fc63a8e8e270bc2'
assert scope['accepted_current_proof']==ref(D/'FULL_CURRENT_RECOVERY_PROOF01.json')
absent=['fresh-serialized-prediction-final-direct01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','ACTUAL_ROOT_EXIT01.json'];assert all(not os.path.lexists(R/n) for n in absent)
finding={'schema_version':1,'decision':'withheld-unexecuted-incomplete22-body-final-scope','source':ref(R/'recover01.py'),'selection':ref(R/'SELECTED_BODIES_DRAFT01.json'),'scope':ref(R/'FINAL_TYPED_SCOPE01.json'),'missing_actual_original':str(P/'REQUEST_RELEASE_CANDIDATE01.json'),'impact':'Declared complete Parent13 was not recoverable from prior11 and selected final body. Descriptor did not contain missing candidate bytes.','resolution':'Corrected recover02 fixed23 includes exact candidate copy and original-to-copy mapping; initial22 remains unexecuted.','unselected_local_checker_sources':['check_capture02.py','check_current_flat01.py','check_final_candidate01.py']}
save('FINAL_DIRECT_FINDING01.json',finding)
check={'schema_version':1,'decision':'accepted-exact-final-direct-source-and23-body-draft','source':ref(R/'recover02.py'),'baseline_source':ref(B/'recover01.py'),'selection_draft':ref(R/'SELECTED_BODIES_DRAFT02.json'),'typed_scope':ref(R/'FINAL_TYPED_SCOPE02.json'),'watch':ref(R/'watch01.py'),'owned_io':ref(R/'utilities/owned_io.py'),'literal_inverse_exact':True,'selected_count':23,'selected_bytes':583271,'unique_blobs':len(set(x['sha256'] for x in s['rows'])),'expected_operations':10+len(set(x['sha256'] for x in s['rows']))+2*len(s['rows']),'parent_count':13,'parent_baseline_count':11,'actual_parent_delta_body_mapping':mapping,'final_request':ref(P/'REQUEST_FINAL01.json'),'final_review':ref(D/'FINAL_PARENT_REVIEW01.json'),'full_current_basis':ref(D/'FULL_CURRENT_RECOVERY_PROOF01.json'),'finding':ref(D/'FINAL_DIRECT_FINDING01.json'),'unchanged_limits':{'whole_seconds':600,'Git_seconds':60,'logical':67108864,'allocated':100663296,'file':4194304,'floor':10737418240},'qualification':'Exact23 original path-mode rows map to22 unique selected bodies plus typed scope23rd body. Current Parent11/CAP/Git inherited from actual accepted fullcurrent basis. Local checker sources and later self-referential closure excluded. No actual remote or preflight/numerical release; exact actual selection/commit confirmation required before one-use receiver entry.'}
save('FINAL_DIRECT_SOURCE_CHECK02.json',check)
print(json.dumps({'check':ref(D/'FINAL_DIRECT_SOURCE_CHECK02.json'),'finding':ref(D/'FINAL_DIRECT_FINDING01.json'),'operations':check['expected_operations']}))
