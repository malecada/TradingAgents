from pathlib import Path
import ast,hashlib,importlib.util,json,sys
H=Path(__file__).resolve().parent;B=H.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
spec=importlib.util.spec_from_file_location('additional_preclaim',H/'preclaim01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows=[]
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError):ck(n,True)
 else:ck(n,False)
I=B/'financial-wrapper-operational-provenance-compatibility-investigation01-2026-10-04';req=json.loads((I/'PARENT_INPUT_REQUIREMENTS01.json').read_bytes());cp=next(r for r in req['rows'] if r['descriptor_field']=='checkpoint_input');state=next(r for r in req['rows'] if r['descriptor_field']=='checkpoint_member:state.pt')
registered={'actual_cp':{k:cp[k] for k in ('path','sha256')}|{'dataset':'synthetic'},'actual_state':{k:state[k] for k in ('path','sha256')}|{'dataset':'synthetic'}};inputs=m.Inputs(S,registered,m.Reader());original=inputs.json('actual_cp');fit=(S/cp['path']).parents[2]
m._checkpoint(inputs,'actual_cp',original['provenance'],fit,m.Reader());ck('actual old manifest pure schema/member validator',True)
for key,value in [('schema_version',True),('key','0'*64),('provenance',{}),('members',{}),('members',{'state.pt':{'size':True,'sha256':state['sha256']}}),('members',{'state.pt':{'size':state['bytes'],'sha256':'0'*64}})]:
 bad=dict(original);bad[key]=value;inputs.bodies['actual_cp']=json.dumps(bad).encode();refuse('pure altered original manifest '+key+str(len(rows)),lambda:m._checkpoint(inputs,'actual_cp',original['provenance'],fit,m.Reader()))
inputs.bodies['actual_cp']=json.dumps(original|{'extra':1}).encode();refuse('generic manifest extra key refuses',lambda:m._checkpoint(inputs,'actual_cp',original['provenance'],fit,m.Reader()))
inputs.bodies['actual_cp']=m.encoded(original)
# Exact unchanged original admitted() function establishes the RED scope.
old=B/'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/source-old/tradingagents/research/onchain_replication/financial_wrapper_fixture.py';current=S/m.PREFIX/'financial_wrapper_fixture.py'
def named(p,name):return next(n for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name==name)
ck('admitted original0a2 AST is still exact',ast.dump(named(old,'admitted'))==ast.dump(named(current,'admitted')))
# The additive helper cannot alter original scientific source. Record exact
# target maps/current source bytes after all source/opaque component checks.
policy=json.loads((B/'financial-wrapper-compatibility-root-policy01-2026-10-04/POLICY01.json').read_bytes());pins=[]
for path,pin in policy['target']['installed'].items():
 raw=(S/path).read_bytes();ck('actual195 source remains unchanged '+path,m.sha(raw)==pin);pins.append({'path':path,'sha256':pin,'bytes':len(raw)})
# Nongenuine object refuses at exact class gate; no Admission/Run is constructed.
sys.path.insert(0,str(S));refuse('nongenuine object rejected by public entry',lambda:m.validate_preclaim(object(),{}, {},{}))
ck('no scientific packages imported',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
# Original exact Parent contract normalization uses sorted indented JSON+LF.
oldparent=B/'financial-genuine-wrapper-claimedrun-parent-preparation01-2026-10-04'
source=(oldparent/'recovery04.py').read_text();ck('original Parent normalization retained',"json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\\n'" in source)
ours=ast.parse((H/'preclaim01.py').read_text());release=next(n for n in ours.body if isinstance(n,ast.FunctionDef) and n.name=='_parent_release');text=ast.unparse(release)
for item in ('accepted-exact-one-use-financial-parent','contract_sha256','proof_sha256','caller_sha256','compatibility_preclaim_external_refs','full_recovery'):
 ck('concrete required Parent predicate '+item,item in text)
ck('own preclaim sources include no output write/Run start',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('write_bytes','write_text','mkdir','start','start_new','save_checkpoint','load_checkpoint') for n in ast.walk(ours)))
(H/'SOURCE_READBACK01.json').write_text(json.dumps(pins,indent=2)+'\n');(H/'CHECKS02.json').write_text(json.dumps({'count':len(rows),'rows':rows,'genuine_Admission_created':False,'public_Green_path_untested':True,'qualification':'Pure malformed-original metadata controls; no fabricated COMPLETE/recovery body or scientific state.'},indent=2)+'\n')
for label,path in [('original-admission.py',S/'tradingagents/research/admission.py'),('original-job.py',S/m.PREFIX/'job.py'),('current-financial_wrapper_fixture.py',current),('original-verify.py',S/'tradingagents/research/verify.py'),('original-parent01.py',oldparent/'parent01.py')]: (H/label).write_bytes(path.read_bytes())
print(json.dumps({'status':'PASS_ADDITIONAL_SOURCE_ONLY','checks':len(rows)}))
