"""Opaque source-only controls; no public preflight, admission, native or fake success."""
from pathlib import Path
import ast, copy, hashlib, json, sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import build01 as B
import parent01 as P
checks=[]
def check(name,v):
 if not v:raise AssertionError(name)
 checks.append(name)
def refuses(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):checks.append(name);return
 raise AssertionError(name+' unexpectedly accepted')
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
old=(H/'original_parent01.py').read_bytes();new=(H/'parent01.py').read_bytes();inverse=json.loads((H/'INVERSE01.json').read_bytes())
back=new.decode()
for e in reversed(inverse['edits']):check('unique inverse '+str(len(checks)),back.count(e['new'])==1);back=back.replace(e['new'],e['old'])
check('full original literal inverse',back.encode()==old)
check('full original AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
def functions(b):return {n.name:ast.dump(n) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=functions(old);b=functions(new)
for name in a:
 if name not in ('validate_release','preflight'):check('unchanged AST '+name,a[name]==b[name])
q=json.loads((H/'REQUEST_DRAFT01.json').read_bytes());check('template caller pin',q['caller_sha256']==sha(new));refuses('actual draft release refused',lambda:P.validate_release(q))
oldq=json.loads((Path(str(P.PARENT).replace('continue100-compatibility-root-launch-20261005-01','complete100-compatibility-root-launch-20261004-01'))/'REQUEST_FINAL01.json').read_bytes())
for key in ('source','design_source','registration_sha256','source_files','input_hashes','final_review','proofs'):
 x=copy.deepcopy(oldq);x[key]=None;refuses('null '+key,lambda x=x:P.validate_release(x))
refuses('old genuine spent request cannot release future Parent',lambda:P.validate_release(oldq))
for name,pin in q['helper_hashes'].items():check('helper body '+name,sha((H/name).read_bytes())==pin)
for name in ('supervisor01.py','descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json'):check('original unchanged '+name,q['helper_hashes'][name]==oldq['helper_hashes'][name])
check('exact copied preclaim reuse',q['helper_hashes']['preclaim01.py']=='079df4afd2ad9cc0c303c400df48aca05f22fceba66fe363f0d0147bfe94800c')
draft=json.loads((H/'SOURCE_MANIFEST_DRAFT01.json').read_bytes());refuses('future source manifest null refused',lambda:B.validate_manifest(draft))
refuses('pending builder refuses before any Git call',lambda:B.build({'path':str(H/'SOURCE_MANIFEST_DRAFT01.json'),'sha256':sha((H/'SOURCE_MANIFEST_DRAFT01.json').read_bytes())},{'path':str(H/'proof_reuse_contract01.json'),'sha256':q['helper_hashes']['proof_reuse_contract01.json']}))
for path in ('../gate','a//b','a/./b','/absolute','a\\b','a\nb','a\0b'):refuses('path '+repr(path),lambda path=path:B.relative(path))
for value in (None,'',False,'F'*64,'g'*64,'a'*63):refuses('digest '+repr(value),lambda value=value:B.digest(value,64))
g=json.loads((H/'GATE4_DRAFT01.json').read_bytes());source=g['experiments'][B.ID]['source_files'];B.validate_gate(g,g,source);checks.append('real draft pure schema equality only')
mutations=[('parent',lambda x:x['experiments'][B.ID].update(parent=None)),('budget',lambda x:x['families'][x['experiments'][B.ID]['family']].update(attempt_budget=21)),('role omission',lambda x:x['experiments'][B.ID]['inputs'].pop('historical_state')),('checkpoint pin',lambda x:x['experiments'][B.ID]['inputs']['reference_state'].update(sha256='0'*64)),('extra experiment',lambda x:x['experiments'].update(unrelated={})),('model pin',lambda x:x['experiments'][B.ID]['inputs']['model'].update(sha256='0'*64))]
for name,mutate in mutations:
 x=copy.deepcopy(g);mutate(x);refuses('gate mutation '+name,lambda x=x:B.validate_gate(x,g,source))
c=json.loads((H/'proof_reuse_contract01.json').read_bytes());reader=B.Reads();refuses('absent actual100 recovery refused',lambda:B.validate_reuse(c,c,None,reader))
for key in ('consumer','policy_sha256','anchors','historical_map_sha256','target_map_sha256'):
 x=copy.deepcopy(c);x[key]=None;refuses('reuse immutable '+key,lambda x=x:B.validate_reuse(x,c,None,reader))
reader=B.Reads();raw=reader.read(H/'PROTOCOL_PINS01.json');check('real bounded reader bytes',raw==(H/'PROTOCOL_PINS01.json').read_bytes());reader.finish();check('finish read charged again',reader.charged==2*len(raw))
refuses('wrong actual body pin',lambda:B.Reads().ref({'path':str(H/'PROTOCOL_PINS01.json'),'sha256':'0'*64}))
# Authenticate all four real closed history pairs without invoking research APIs.
history={'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01':('failed.json','4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'),'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01':('failed.json','d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'),'financial-wrapper-classification-eager-complete100-20261003-01':('failed.json','2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57b0a4f943ab864798a4e05224ee530d4117b47f8f032c1'),'financial-wrapper-classification-eager-complete100-compatibility-20261004-01':('complete.json','c6c1106de459a89f9633ae51501959ecabd47c204534d85e9ebcf15671bcd19f','bd54cb0052645e77fa7b0a4f943ab864798a4e05224ee530d4117b47f8f032c1')}
# Exact original failed100 pin from the authenticated inherited caller literal.
history['financial-wrapper-classification-eager-complete100-20261003-01']=('failed.json','2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6')
for identity,(terminal,claimpin,termpin) in history.items():
 for n,pin in (('claim.json',claimpin),(terminal,termpin)):check('actual retained '+identity+'/'+n,sha(P.R.read(B.CAP,'research_runs/'+identity+'/'+n))==pin)
check('no project numerical imports',not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')))
check('no project import',not any(n=='tradingagents' or n.startswith('tradingagents.') for n in sys.modules))
result={'schema_version':1,'controls':len(checks),'passed':checks,'public_preflight_executed':False,'builder_success_path_executed':False,'actual_future_authority':None,'numerical_authority':False}
with (H/'CONTROLS01.json').open('xb') as f:f.write(enc(result))
print(json.dumps({'controls':len(checks),'status':'PASSED_SOURCE_ONLY'}))
