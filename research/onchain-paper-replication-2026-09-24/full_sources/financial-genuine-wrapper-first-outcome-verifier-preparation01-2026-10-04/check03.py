import copy,itertools,json,os,shutil
from pathlib import Path
import verifier01 as V
root=Path(__file__).resolve().parent;owned=root/'opaque_controls03';owned.mkdir();checks=[]
def check(name,predicate):
 assert predicate,name;checks.append(name)
def refuse(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError,NotADirectoryError,OSError):checks.append(name)
 else:raise AssertionError(name)
for values in itertools.product((False,True),repeat=4):
 got=V.classify(**dict(zip(('claim_present','planned_bytes','cleanup_proved','predispatch_proved'),values)))
 expected='CLEANUP_UNCERTAIN' if not values[2] else ('PLANNED_FAILED_SPENT_INTERRUPT1_BYTES' if values[1] else 'UNEXPECTED_FAILURE_SPENT') if values[0] else 'NO_CLAIM_PREDISPATCH_REFUSAL' if values[3] else 'UNEXPECTED_FAILURE_NO_CLAIM'
 check('four-state-'+str(values),got==expected)
for i in range(4):
 x=dict(zip(('claim_present','planned_bytes','cleanup_proved','predispatch_proved'),(False,)*4));x[list(x)[i]]=1;refuse('bool-not-int-'+str(i),lambda:V.classify(**x))
prov={'opaque':'metadata é, not an actual checkpoint'};body=b'opaque synthetic bytes, never torch';key=V.sha(V.canonical({'provenance':prov,'epoch':1,'batch':0}));m={'schema_version':1,'key':key,'provenance':prov,'members':{'state.pt':{'sha256':V.sha(body),'size':len(body)}}}
check('opaque-checkpoint-metadata',V.cursor_manifest(m,prov,body)==key)
for field,replacements in {'schema_version':[True,0,2,None], 'key':['0'*64,None], 'provenance':[{},None], 'members':[{}, {'state.pt':{'sha256':'0'*64,'size':len(body)}}]}.items():
 for index,value in enumerate(replacements):
  n=copy.deepcopy(m);n[field]=value;refuse('checkpoint-'+field+str(index),lambda:V.cursor_manifest(n,prov,body))
refuse('checkpoint-body-corruption',lambda:V.cursor_manifest(m,prov,body+b'!'))
for text in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}') :refuse('strict-json-'+str(text),lambda:V.decoded(text))
tiny=owned/'tree';tiny.mkdir();(tiny/'empty').mkdir();(tiny/'file').write_bytes(body);t=V.Tree(tiny);check('inventory-denominator',len(t.rows)==2);check('exact-opaque-body',t.raw('file')==body);t.close_check()
refuse('missing-file',lambda:t.raw('absent'));refuse('wrong-hash',lambda:t.raw('file','0'*64))
for path in ('../outside','/tmp/x','a/../b','.env','keys/a') :refuse('path-'+path,lambda:V.R.path_name(path))
(tiny/'file').write_bytes(body+b'changed');refuse('body-changed',lambda:t.raw('file'));refuse('tree-changed',t.close_check)
for name,target in [('dangling','missing'),('ancestor','empty')]:
 p=owned/name;p.mkdir();(p/'link').symlink_to(target);refuse('symlink-'+name,lambda:V.inventory(p))
p=owned/'hardlink';p.mkdir();(p/'a').write_bytes(b'x');os.link(p/'a',p/'b');refuse('hardlink',lambda:V.inventory(p))
p=root/'opaque_controls01'/'oversized';refuse('retained-4MiB-ceiling-witness',lambda:V.inventory(p))
# Full authenticated STATIC source route, no Run/Owner/claim or outcome fabricated.
parent=owned/'static_parent';shutil.copytree(root/'baseline/parent',parent);shutil.copyfile(root/'REQUEST_FINAL03.json',parent/'REQUEST_FINAL03.json');cap=root/'baseline/capsule'
c=V.Tree(cap);p=V.Tree(parent);q=V.decoded((root/'REQUEST_FINAL03.json').read_bytes());context={'schema_version':1,'kind':'root-financial-first-outcome-observation-v1','identity':q['identity'],'capsule_inventory_sha256':V.sha(V.canonical(c.inventory)),'parent_inventory_sha256':V.sha(V.canonical(p.inventory)),'actual_parent_exit':None,'process_observation':None,'source_claim_review':None};raw=V.canonical(context)
result=V.verify(cap,parent,raw,V.sha(raw));check('static-only-no-claim',result['disposition']=='CLEANUP_UNCERTAIN' and not result['claim_present'] and result['paper_financial_fit_credit']==0 and not result['release_authorized'])
(owned/'static-inspection.json').write_bytes(V.R.encode(result))
for key,value in [('identity','wrong'),('schema_version',True),('capsule_inventory_sha256','0'*64),('parent_inventory_sha256','0'*64),('actual_parent_exit',True),('process_observation',{})]:
 bad=copy.deepcopy(context);bad[key]=value;b=V.canonical(bad);refuse('context-'+key,lambda:V.external_context(b,V.sha(b),c,p,q['identity']))
refuse('context-external-pin',lambda:V.external_context(raw,'0'*64,c,p,q['identity']))
print(json.dumps({'checks':len(checks),'names':checks,'scope':'stdlib opaque/source-only; no genuine outcome or claim instantiated'},sort_keys=True))
