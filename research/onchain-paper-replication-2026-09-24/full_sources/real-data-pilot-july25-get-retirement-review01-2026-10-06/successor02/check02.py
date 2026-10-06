"""Independent delta-only check; invented metadata, no payload operations."""
from pathlib import Path
import ast,copy,hashlib,json,types
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;REVIEW=HERE.parent;F=REVIEW.parent
OLD=F/'real-data-pilot-july25-get-retirement-preparation01-2026-10-06';NEW=F/'real-data-pilot-july25-get-retirement-preparation02-2026-10-06'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(NEW/'MANIFEST02.json')=='e22f2199a6663808a6b5af839f26854e8418c67562f8c206060a008f7150a65e'
assert sha(NEW/'retire01.py')=='05512665226937ca46ab9bdaf5578de9de53e46b5778e859b885854d48ea5f8e'
for n,info in json.loads((NEW/'MANIFEST02.json').read_text())['files'].items():assert sha(NEW/n)==info['sha256'],n
change=json.loads((NEW/'SUCCESSOR_DELTA02.json').read_text());actual=(NEW/'retire01.py').read_text();inverse=actual
for r in reversed(change['retire_ordered_replacements']):assert inverse.count(r['after'])==1;inverse=inverse.replace(r['after'],r['before'])
assert inverse==(OLD/'retire01.py').read_text();assert ast.dump(ast.parse(inverse))==ast.dump(ast.parse((OLD/'retire01.py').read_text()))
assert (OLD/'recovery01.py').read_bytes()==(NEW/'recovery01.py').read_bytes()
for n,h in change['all_parent_files'].items():assert sha(OLD/n)==h,n
for n in ('SELECTION_TEMPLATE01.json','RELEASE_TEMPLATE01.json','RELOCATION_OUTCOME_REQUIRED01.json'):assert (NEW/n).read_bytes()==(OLD/n).read_bytes()
oldpins=json.loads((OLD/'SOURCE_PINS01.json').read_text());newpins=json.loads((NEW/'SOURCE_PINS01.json').read_text());adjusted=copy.deepcopy(newpins)
adjusted['recovery']['path']=adjusted['recovery']['path'].replace(NEW.name,OLD.name);assert adjusted==oldpins

def load(p):
 m=types.ModuleType('independent_delta');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),vars(m));return m
fixture=load(OLD/'check01.py');r=load(NEW/'retire01.py');m=load(NEW/'recovery01.py');c,docs=fixture.Check().gate_fixture()
# Only supply genuine-schema fields missing from the old synthetic fixture.
docs[c['relocation']['relocation_receipt']['path']]['identity']=r.RELOCATION
docs[c['relocation']['retire_outer']['path']]['cleanup_verified']=None

def invoke(d):
 with patch.object(m,'recovery'),patch.object(m,'current'),patch.object(m,'metadata',side_effect=lambda root,p,pin:json.dumps(d[p]).encode()),patch.object(r,'retained'),patch.object(r.os.path,'lexists',return_value=False),patch.object(Path,'exists',return_value=False):return r.validate(m,c)
invoke(docs);witnesses={}
for name,role,key,value in [('R1','retire_outer','cleanup_verified',True),('R2','relocation_receipt','identity','unrelated-maintenance')]:
 bad=copy.deepcopy(docs);bad[c['relocation'][role]['path']][key]=value
 try:invoke(bad)
 except ValueError as e:witnesses[name]={'refused':True,'message':str(e)}
 else:raise AssertionError(name+' original RED still accepts')
prior=json.loads((REVIEW/'MANIFEST01.json').read_text())
for n,h in prior['files'].items():assert sha(REVIEW/n)==h,n
result={'status':'PASS','exact_byte_AST_inverse':True,'unchanged_recovery_and_templates':True,'dependency_delta':'recovery path only; body unchanged','accepted_positive_fixture':True,'original_RED_refusals':witnesses,'prior_withheld_review_preserved':sha(REVIEW/'MANIFEST01.json'),'prior_unchanged_fatal_and_retirement_checks_reused':True,'actual_payload_or_native_operations':False}
(HERE/'CHECK02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
