import ast,copy,hashlib,importlib.util,json,os,stat,time
from pathlib import Path
H=Path(__file__).resolve().parent;SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
spec=importlib.util.spec_from_file_location('opaque_compatibility_checker',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[]
def ck(name,truth):
 rows.append({'check':name,'passed':bool(truth)})
 if not truth:raise AssertionError(name)
def refuse(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError):ck(name,True)
 else:ck(name,False)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=sha((H/'operational_source_compatibility.py').read_bytes());target=dict(m.OLD_MAP);target.update(m.CONTROL_TARGETS);target[m.HELPER]=pin
ck('genuine historical denominator194/193',len(m.OLD_MAP)==194 and len(set(m.OLD_MAP.values()))==193)
actual=[]
for p,h in m.OLD_MAP.items():
 raw=(SRC/p).read_bytes();ck('historical body '+p,len(raw)<=4*1024**2 and sha(raw)==h);actual.append({'path':p,'bytes':len(raw),'sha256':h})
ck('target195 and191 original byte equal',len(target)==195 and sum(target.get(p)==h for p,h in m.OLD_MAP.items())==191)
for p,h in m.CONTROL_TARGETS.items():ck('copied control target '+p,sha((H/Path(p).name).read_bytes())==h)
delta=m.validate_maps(m.OLD_MAP,target,pin);ck('four exact explicit path deltas',len(delta)==4)
for p in target:
 wrong=dict(target);wrong[p]='0'*64;refuse('single changed target path '+p,lambda wrong=wrong:m.validate_maps(m.OLD_MAP,wrong,pin))
for label,wrong in [('missing',dict(list(target.items())[1:])),('extra',target|{'unexpected.py':'0'*64}),('reflexive',m.OLD_MAP)]:refuse(label+' target map',lambda wrong=wrong:m.validate_maps(m.OLD_MAP,wrong,pin))
wrong=dict(m.OLD_MAP);a,b=list(wrong)[:2];wrong[a],wrong[b]=wrong[b],wrong[a];refuse('historical same hashset swapped paths',lambda:m.validate_maps(wrong,target,pin))
# Opaque metadata values are not claims, receipts, state tensors or Run objects.
old={'source_commit':m.HISTORICAL_SOURCE,'source_hashes':sorted(set(m.OLD_MAP.values())),'opaque_science':'fixed','cell_id':'opaque-cell'}
new=old|{'source_commit':'1'*40,'source_hashes':sorted(set(target.values()))}
legacy=lambda a,b:{k:v for k,v in a.items() if k!='source_commit'}=={k:v for k,v in b.items() if k!='source_commit'}
ck('original scientific comparison RED for operational source delta',not legacy(old,new));m.validate_relation(m.OLD_MAP,target,old,new);ck('metadata-only exact directional relation GREEN',True)
for label,wrong in [('old-source',new|{'source_commit':m.HISTORICAL_SOURCE}),('null-source',new|{'source_commit':None}),('science',new|{'opaque_science':'changed'}),('missing',{'source_commit':'1'*40}),('rewrite',new|{'source_hashes':old['source_hashes']}),('extra',new|{'extra':1})]:refuse('relation '+label,lambda wrong=wrong:m.validate_relation(m.OLD_MAP,target,old,wrong))
policy={'schema_version':1,'kind':'one-historical-parent-operational-source-edge-v1','historical':{'identity':m.HISTORICAL_ID,'source':m.HISTORICAL_SOURCE,'claim_sha256':m.HISTORICAL_CLAIM_SHA256,'failed_sha256':m.HISTORICAL_FAILED_SHA256,'checkpoint_sha256':m.HISTORICAL_CHECKPOINT_SHA256,'protocol_sha256':m.HISTORICAL_PROTOCOL_SHA256,'installed':m.OLD_MAP,'closure_input':'opaque-old-closure','claim_input':'opaque-claim','failed_input':'opaque-failed','checkpoint_input':'opaque-checkpoint','plan_input':'opaque-plan','job_input':'opaque-job','provenance':old},'target':{'installed':target,'closure_input':'opaque-target-closure'},'allowed_delta':delta,'consumers':{p:{'experiment':'opaque-'+p,'cell_id':'opaque-cell'} for p in ('complete100','continue100','predict')},'proof_roles':list(m.PROOF_ROLES)}
m.validate_contract(policy,pin);ck('opaque policy schema consistent; no authority',True)
for key in policy:
 wrong=copy.deepcopy(policy);del wrong[key];refuse('policy missing '+key,lambda wrong=wrong:m.validate_contract(wrong,pin))
for key in ('identity','source','claim_sha256','failed_sha256','checkpoint_sha256','protocol_sha256'):
 wrong=copy.deepcopy(policy);wrong['historical'][key]='wrong';refuse('historical pin '+key,lambda wrong=wrong:m.validate_contract(wrong,pin))
for key in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input','provenance'):
 wrong=copy.deepcopy(policy);wrong['historical'][key]=None;refuse('unbound historical '+key,lambda wrong=wrong:m.validate_contract(wrong,pin))
for phase in policy['consumers']:
 wrong=copy.deepcopy(policy);wrong['consumers'][phase]['experiment']=None;refuse('unbound consumer '+phase,lambda wrong=wrong:m.validate_contract(wrong,pin))
for label,edit in [('boolschema',lambda p:p.update(schema_version=True)),('deltamissing',lambda p:p['allowed_delta'].pop()),('deltareorder',lambda p:p['allowed_delta'].reverse()),('proofmissing',lambda p:p['proof_roles'].pop()),('proofextra',lambda p:p['proof_roles'].append('fake'))]:
 wrong=copy.deepcopy(policy);edit(wrong);refuse(label,lambda wrong=wrong:m.validate_contract(wrong,pin))
# Freeze literal source inverses and every unaffected AST, including numerical engine.
inv=json.loads((H/'SOURCE_INVERSES02.json').read_text())
for name,allowed in [('training.py',{'_reserve'}),('financial_wrapper_fixture.py',{'authorize','_parent','_reference_state'})]:
 s=(H/name).read_text();orig=(H/('original_'+name)).read_text();back=s
 for row in reversed(inv['changes'][name]):ck('unique inverse '+name+str(len(back)),back.count(row['new'])==1);back=back.replace(row['new'],row['old'])
 ck('full literal inverse '+name,back==orig);a,b=ast.parse(orig),ast.parse(s)
 a.body=[x for x in a.body if getattr(x,'name',None) not in allowed];b.body=[x for x in b.body if getattr(x,'name',None) not in allowed];ck('entire unaffected AST '+name,ast.dump(a)==ast.dump(b))
 for oldrow in inv['changes'][name]:ck('legacy source remains literal '+name,oldrow['old'].strip() in s or name=='training.py')
helper=ast.parse((H/'operational_source_compatibility.py').read_text());func={n.name:n for n in helper.body if isinstance(n,ast.FunctionDef)}
for f in ('_require_parent_under_fit_lock','_parent_predicate','_registered_unlocked','_context'):
 body=ast.unparse(func[f]);ck('held-path no read_input or lock '+f,'.read_input(' not in body and '_lock(' not in body and 'authorize(' not in body)
ck('normal reader retains genuine API','run.read_input(name)' in ast.unparse(func['_registered_normal']))
training=(H/'training.py').read_text();ck('lineage published before genuine fit claim',training.index("_immutable(destination/'operational-source-compatibility.json'")<training.index("_immutable(destination/'claim.json'"))
# Real tiny opaque IO. Retain all files and lexical link witnesses.
owned=H/'owned01';owned.mkdir();body=owned/'body';body.write_bytes(b'opaque registered bytes\x00\xff');budget=lambda:{'begun':time.monotonic(),'bytes':0}
ck('real bounded anchored read',m._read(body,budget())==body.read_bytes());link=owned/'redirect';link.symlink_to(body);refuse('real lexical redirect',lambda:m._read(link,budget()))
refuse('real directory body',lambda:m._read(owned,budget()));refuse('aggregate bytes pre-refusal',lambda:m._read(body,{'begun':time.monotonic(),'bytes':m.TOTAL}));refuse('deadline pre-refusal',lambda:m._read(body,{'begun':time.monotonic()-121,'bytes':0}))
realread=os.read;realclose=os.close
for pi,primary in enumerate((ValueError('opaque primary'),KeyboardInterrupt('opaque primary'),MemoryError('opaque primary'),SystemExit('opaque primary'))):
 for ci,secondary in enumerate((ValueError('opaque close'),KeyboardInterrupt('opaque close'),MemoryError('opaque close'),SystemExit('opaque close'))):
  seen=[];closed=[];once=[False]
  def reading(fd,n):raise primary
  def closing(fd):
   realclose(fd);closed.append(fd)
   if not once[0]:once[0]=True;raise secondary
  m.os.read=reading;m.os.close=closing
  try:
   try:m._read(body,budget())
   except BaseException as error:
    fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
    expected=primary if fatal(primary) else secondary if fatal(secondary) else None
    ok=(error is expected) if expected is not None else isinstance(error,m.CleanupFailure)
    seen.append(error)
   else:ok=False
  finally:m.os.read=realread;m.os.close=realclose
  ck('real IO primary/close precedence '+str((pi,ci)),ok and len(closed)==len(body.parts))
  for fd in closed:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('descriptor retained')
  ck('all actual opened descriptors closed '+str((pi,ci)),True)
# Store exact admitted-source metadata only, not checkpoint bodies/values.
(H/'SOURCE_READBACK01.json').write_text(json.dumps({'actual_historical_source':str(SRC),'actual_rows':actual,'old_map':m.OLD_MAP,'target_map':target,'delta':delta,'candidate_helper_sha256':pin,'qualifier':'source bytes only; historical checkpoint not opened or decoded'},indent=2,sort_keys=True)+'\n')
template=copy.deepcopy(policy)
for c in template['consumers'].values():c['experiment']=None;c['cell_id']=None
for key in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input','provenance'):template['historical'][key]=None
template['target']['closure_input']=None
refuse('actual unfinished Root policy draft refused',lambda:m.validate_contract(template,pin))
(H/'POLICY_DRAFT01.json').write_text(json.dumps(template,indent=2,sort_keys=True)+'\n')
(H/'CHECKS01.json').write_text(json.dumps({'status':'PASS_SOURCE_ONLY','count':len(rows),'rows':rows,'no_runtime_authority_objects':True,'no_numerical_imports':True},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS_SOURCE_ONLY','checks':len(rows),'helper_sha256':pin}))
