import ast,atexit,copy,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;P=H/'predecessor01';rows=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(n,v):
 rows.append({'check':n,'passed':bool(v)})
 assert v,n
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):ck(n,True)
 else:ck(n,False)
def save(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
atexit.register(lambda:save('CHECK02_PROGRESS.json',rows))
spec=importlib.util.spec_from_file_location('opaque_new_policy_bridge',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
newpin=sha((H/'operational_source_compatibility.py').read_bytes());target=dict(m.OLD_MAP);target.update(m.CONTROL_TARGETS);target[m.HELPER]=newpin
policy=json.loads((P/'POLICY_DRAFT01.json').read_text());policy['target']['installed']=target;policy['allowed_delta']=m.validate_maps(m.OLD_MAP,target,newpin)
for key in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input'):policy['historical'][key]='opaque-'+key
policy['historical']['provenance']={'source_commit':m.HISTORICAL_SOURCE,'source_hashes':sorted(set(m.OLD_MAP.values())),'opaque_science':'fixed','cell_id':'opaque-cell'};policy['target']['closure_input']='opaque-current-closure'
for phase,c in policy['consumers'].items():c.update(experiment='opaque-'+phase,cell_id='opaque-cell')
other=copy.deepcopy(policy);other['consumers']['predict']['experiment']='opaque-alternate-predict'
m.validate_contract(policy,newpin);m.validate_contract(other,newpin);pa=m.sha(m.canonical(policy));pb=m.sha(m.canonical(other));ck('two valid pure policies share195 map but differ hash',pa!=pb and policy['target']['installed']==other['target']['installed'])
# Exact OLD production comparison, taken directly from predecessor wrapper AST.
parent=next(n for n in ast.parse((P/'financial_wrapper_fixture.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_parent');branch=next(n for n in parent.body if isinstance(n,ast.If) and 'require_parent_compatibility' in ast.unparse(n));expr=next(n for n in ast.walk(branch.orelse[0]) if isinstance(n,ast.Compare) and isinstance(n.left,ast.DictComp))
oldprov={'source_commit':'1'*40,'source_hashes':sorted(set(target.values())),'opaque_science':'fixed','cell_id':'opaque-cell'};newprov=oldprov|{'source_commit':'2'*40}
ck('original exact prediction policy gap RED',eval(compile(ast.Expression(expr),'original-extracted-comparison','eval'),{}, {'value':{'provenance':oldprov},'prov':newprov}) is True)
# Only pure metadata components are supplied. No Run/Owner/Admission/claim or
# actual lifecycle receipt is manufactured or exercised.
closure='a'*64;inputs={m.ROLE:{'sha256':pa},policy['target']['closure_input']:{'sha256':closure}};identity=policy['consumers']['continue100']['experiment'];cells=['opaque-cell']
refuse('new GREEN refuses actual witnessed differing policy hash',lambda:m.validate_prediction_parent(other,pb,closure,identity,inputs,target,cells))
result=m.validate_prediction_parent(policy,pa,closure,identity,inputs,target,cells);ck('same-policy exact metadata edge',result['policy_sha256']==pa and result['target_map_sha256']==m.sha(m.canonical(target)))
for label,bad in [('absent-role',{k:v for k,v in inputs.items() if k!=m.ROLE}),('wrong-policy',inputs|{m.ROLE:{'sha256':pb}}),('null-policy',inputs|{m.ROLE:{'sha256':None}}),('missing-hash',inputs|{m.ROLE:{}}),('missing-closure',{m.ROLE:inputs[m.ROLE]}),('wrong-closure',inputs|{policy['target']['closure_input']:{'sha256':'b'*64}})]:refuse(label,lambda bad=bad:m.validate_prediction_parent(policy,pa,closure,identity,bad,target,cells))
for label,badid,badcells in [('wrong-consumer','other',cells),('parent-is-predict',policy['consumers']['predict']['experiment'],cells),('old-failed-parent',m.HISTORICAL_ID,cells),('wrong-cell',identity,['other']),('extra-cell',identity,cells+['other']),('missing-cell',identity,[])]:refuse(label,lambda badid=badid,badcells=badcells:m.validate_prediction_parent(policy,pa,closure,badid,inputs,target,badcells))
for p in target:
 wrong=dict(target);wrong[p]='0'*64;refuse('parent full target body '+p,lambda wrong=wrong:m.validate_prediction_parent(policy,pa,closure,identity,inputs,wrong,cells))
for bad in (None,'',False,'A'*64,'0'*63):refuse('bad currentpolicy '+str(bad),lambda bad=bad:m.validate_prediction_parent(policy,bad,closure,identity,inputs,target,cells))
# Actual wrapper order: verified claim+COMPLETE terminal+old scientific equality
# precede new guarded prediction join; original checkpoint/member work follows.
s=(H/'financial_wrapper_fixture.py').read_text();node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='_parent');newbranch=next(n for n in node.body if isinstance(n,ast.If) and any(isinstance(q,ast.Name) and q.id=='require_prediction_policy' for q in ast.walk(n)))
ck('dedicated optional policy + predict branch',ast.unparse(newbranch.test)=="'operational_source_compatibility' in run.admission.inputs and p['phase'] == 'predict'")
text=ast.unparse(node);ck('genuine verify and lifecycle/strict comparison before new join',text.index('claim = verify_claim(directory)')<text.index('actual prior lifecycle status differs')<text.index('prior scientific provenance differs')<text.index('require_prediction_policy(run, claim)')<text.index("info = run.admission.inputs[value['checkpoint_input']]"))
ck('legacy absent-role comparison preserved literal',ast.unparse(expr) in text)
inv=json.loads((H/'SUCCESSOR_INVERSE01.json').read_text())
for n,changes in inv['changes'].items():
 back=(H/n).read_text()
 for change in reversed(changes):
  if change.get('operation')=='append':ck('one exact appended helper tail',back.endswith(change['new']));back=back[:-len(change['new'])]
  else:ck('one exact source substitution '+n,back.count(change['new'])==1);back=back.replace(change['new'],change['old'])
 ck('full literal predecessor inverse '+n,back==(P/n).read_text());ck('full AST predecessor inverse '+n,ast.dump(ast.parse(back))==ast.dump(ast.parse((P/n).read_text())))
for n in ('training.py','workflow_storage.py'):ck('unchanged exact '+n,(H/n).read_bytes()==(P/n).read_bytes())
# Re-run the exact506 inherited controls in fresh owned paths, bound to02 source.
replay=H/'replay03';replay.mkdir()
for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py','training.py','workflow_storage.py','original_financial_wrapper_fixture.py','original_training.py','SOURCE_INVERSES02.json'):(replay/n).write_bytes((H/n).read_bytes())
for n in ('check02.py','check03.py'):
 (replay/n).write_bytes((P/n).read_bytes());run=subprocess.run([sys.executable,'-B',str(replay/n)],capture_output=True,timeout=60);(replay/(n+'.stdout')).write_bytes(run.stdout);(replay/(n+'.stderr')).write_bytes(run.stderr);save('REPLAY2_'+n+'.json',{'exit':run.returncode});ck('inherited raw control '+n,run.returncode==0)
priorrows=json.loads((replay/'CHECKS01.json').read_text())['count']+json.loads((replay/'CHECKS03.json').read_text())['count'];ck('all506 inherited plus2 new inverse-control rows',priorrows==508)
for n in ('POLICY_DRAFT01.json','SOURCE_CLOSURE_DRAFT01.json','PROOF_ROLES_DRAFT01.json','SOURCE_READBACK01.json'):(H/n).write_bytes((replay/n).read_bytes())
witness={'finding':'OPC-PREDICT-POLICY-01','predecessor_manifest':sha((P/'MANIFEST01.json').read_bytes()),'actual_review_witness_sha256':sha((H/'independent_finding01/WITNESS01.json').read_bytes()),'old_exact_comparison_accepted':True,'new_same_policy_predicate_refused':True,'policy_a':pa,'policy_b':pb,'same_target_map':True,'genuine_runtime_objects_created':False,'qualification':'Opaque components only; actual production branch and pure predicate tested, no outcomes or authority fabricated.'};save('RED_GREEN01.json',witness)
save('CHECKS01.json',{'status':'PASS_SOURCE_ONLY','new_controls':len(rows),'inherited_final_controls':priorrows,'rows':rows});print(json.dumps({'status':'PASS_SOURCE_ONLY','new_controls':len(rows),'inherited_controls':priorrows}))
