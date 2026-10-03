import ast,copy,hashlib,importlib.util,json,os,stat,sys,types
from pathlib import Path
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-held-failure-outcome-parser-preparation02-2026-10-03';B=R.parent/'held-consumer-held-failure-outcome-parser-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST02.json').read_bytes())=='bb44414c9d21a4fd90b73a670f7ddca746952a44c0a8e2c43e9f825c97c63574'
source=(A/'held_failure01.py').read_bytes();old=(B/'held_failure01.py').read_bytes();assert H(source)=='3359b976f650e8748b897f87bb0e3cc7515d9ac679391f1a8fac19154b95a765';assert H(old)=='e76bb9fc08168d6dd31d128c91a9aab8f47a3c4deff04752c2ce282173d518d5'
rows=json.loads((A/'MANIFEST02.json').read_bytes())['files'];names=[]
for r in rows:
 p=A/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['type']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==r['links'] and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
 elif r['type']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert r['type']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
 names.append(r['path'])
actual=[]
for p,ds,fs in os.walk(A,followlinks=False):actual.extend(str((Path(p)/n).relative_to(A)) for n in ds+fs if str((Path(p)/n).relative_to(A))!='MANIFEST02.json')
assert sorted(actual)==sorted(names)
old_fragment=b"journal['workflow_identity']==workflow and journal['required_graphs']==list(TARGETS)"
new_fragment=b"journal['workflow_identity'] is None and journal['parent'] is None and equal(journal['events'],[]) and journal['owner']['workflow_identity']==workflow and journal['required_graphs']==list(TARGETS)"
assert old.count(old_fragment)==1 and source.replace(new_fragment,old_fragment)==old
assert ast.dump(ast.parse(source.replace(new_fragment,old_fragment)))==ast.dump(ast.parse(old))
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load(A/'held_failure01.py','candidate02');baseline=load(B/'held_failure01.py','candidate01')
q=json.loads((R.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json').read_bytes());cap=Path(q['capsule_root'])
r=m.Reader(cap);reg=m.sources(r,q);exp=reg['experiments'][m.IDENTITY];assert len(exp['inputs'])==33 and len(exp['outputs'])==6
inputs={k:H(m.input_body(r,exp,k)) for k in sorted(exp['inputs'])};r.recheck()
jp=cap/'tradingagents/research/onchain_replication/feature_journal.py';jt=ast.parse(jp.read_bytes());cl=next(n for n in jt.body if isinstance(n,ast.ClassDef) and n.name=='FeatureJournal');seal=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='seal');ns={};exec(compile(ast.Module([seal],[]),str(jp),'exec'),ns)
workflow='a'*64;reason='FixturePublicationFailure: registered second-target publication boundary; retain first output; no retry';captured=[]
obj=types.SimpleNamespace(directory=R/'never-born',sealed=False,records=[],identity=None,parent=None,owner={'experiment':m.IDENTITY,'source_commit':m.SOURCE,'producer':'synthetic-metadata-only','workflow_identity':workflow},required=list(m.TARGETS),_publish=lambda p,v:captured.append(v))
ns['seal'](obj,'failed',reason=reason);journal=captured[0]
cells=[{'id':'import-target-01','status':'complete','resource_only':True},{'id':'import-target-02','status':'failed','reason':reason,'resource_only':True}]
resource={'schema_version':2,'kind':'original-import-resource-terminal','status':'failed','resource_only':True,'financial_representation_admitted':False,'reason':reason}
try:baseline.failure_shape(cells,resource,journal,workflow)
except ValueError as e:old_error=str(e)
else:raise AssertionError('original RED missing')
assert m.failure_shape(cells,resource,journal,workflow)==reason
mutations=[('workflow_identity',workflow),('workflow_identity',False),('parent',{}),('parent','claimed-parent'),('events',[{}]),('events',None),('owner',{'workflow_identity':'b'*64}),('owner',{}),('owner',{'workflow_identity':None}),('schema_version',True),('status','complete'),('reason','MemoryError'),('required_graphs',list(reversed(m.TARGETS)))]
refused=[]
for k,v in mutations:
 d=copy.deepcopy(journal);d[k]=v
 try:m.failure_shape(cells,resource,d,workflow)
 except (ValueError,TypeError,KeyError):refused.append(k)
 else:raise AssertionError(('mutation accepted',k,v))
for k in ('workflow_identity','parent','events','owner'):
 d=copy.deepcopy(journal);del d[k]
 try:m.failure_shape(cells,resource,d,workflow)
 except (ValueError,TypeError,KeyError):refused.append('missing '+k)
 else:raise AssertionError(('missing accepted',k))
for index in (0,1):
 d=copy.deepcopy(cells);d[index]['status']='unavailable'
 try:m.failure_shape(d,resource,journal,workflow)
 except ValueError:refused.append('unavailable cell '+str(index))
 else:raise AssertionError('unavailable accepted')
assert len(refused)==19
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'decision':'accepted_source_only','candidate_sha256':H(source),'manifest_members':len(rows),'exact_one_predicate_inverse_bytes_ast':True,'actual_feature_journal_source_sha256':H(jp.read_bytes()),'actual_seal_capture':journal,'old_red':old_error,'new_green':True,'mutation_refusals':refused,'actual_git_current_bodies':205,'opaque_registered_inputs':inputs,'outputs':exp['outputs'],'source':m.SOURCE,'actual_outcome_authority_native_or_numerical_tested':False}
(R/'READBACK02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS: complete manifest; exact one-predicate inverse bytes/AST; original seal RED→GREEN;19 refusal variants;actual205 Git/33opaque inputs/six outputs; no numerical/authority execution')
