"""Exact old helper RED and strengthened helper GREEN, opaque metadata only."""
import ast,copy,hashlib,importlib.util,json,os
from pathlib import Path
import prepare01 as P
import rebind01 as B
from manifest02 import collect
H=Path(__file__).resolve().parent;checks=[];red={}
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuses(n,fn):
 try:fn()
 except (ValueError,AssertionError):checks.append(n)
 else:raise AssertionError(n)
def load(name):
 spec=importlib.util.spec_from_file_location(name,H/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('baseline-rebind01.py');oldprep=load('baseline-prepare01.py');case='success'
for path in ['/',str(P.CAP.parent)]:
 d,_=old.rebind(case,path);ok('RR1 RED unsafe root accepted',d['capsule_root']==path)
red['RR1']=['/',str(P.CAP.parent)]
e=P.expectations();before=copy.deepcopy(e['baseline']);after=copy.deepcopy(e['candidate']);key=next(k for k in before if k!=P.CHANGE);before.pop(key);after.pop(key);oldprep.one_change(before,after);red['RR2']={'accepted_equal_reduced_maps':len(before)}
refuses('RR2 GREEN missing same path bothmaps',lambda:P.one_change(before,after));P.one_change(e['baseline'],e['candidate']);checks.append('complete199/148 source maps accepted')
a=copy.deepcopy(e['baseline']);b=copy.deepcopy(e['candidate']);a['extra.py']='0'*64;b['extra.py']='0'*64;refuses('extra both source maps refused',lambda:P.one_change(a,b))
drafts=json.loads(P.read(H/'generated01/DRAFT_CASES01.json'));mutated=copy.deepcopy(drafts);mutated[case]['roles']['extra']=None;mutated[case]['experiment']['source_files'].pop(key)
original_read=old.read
old.read=lambda path:P.encode(mutated) if str(path).endswith('DRAFT_CASES01.json') else original_read(path)
bad,_=old.rebind(case);old.read=original_read
ok('RR3 RED emits199 from198 and16roles',bad['candidate_implementation_count']==199 and len(bad['experiment']['source_files'])==198 and len(bad['roles'])==16)
red['RR3']={'actual_sources':198,'reported_sources':bad['candidate_implementation_count'],'roles':16}
refuses('RR3 GREEN mutated helper draft refused',lambda:B.validate_draft(mutated[case],case))
for label,mutate in [('missing role',lambda d:d['roles'].pop('runtime')),('missing input',lambda d:d['experiment']['inputs'].pop('original_samples')),('extra input',lambda d:d['experiment']['inputs'].update(extra={})),('missing output',lambda d:d['experiment']['outputs'].pop()),('inputhash drift',lambda d:d['experiment']['inputs']['original_samples'].update(sha256='0'*64)),('invented authority',lambda d:d.update(fresh_identity='fabricated'))]:
 d=copy.deepcopy(drafts[case]);mutate(d);refuses(label,lambda d=d:B.validate_draft(d,case))
unsafe=['/',str(P.CAP),str(P.CAP.parent),str(P.CAP.parent.parent),str(P.CAP/'nested/source'),str(P.CAP.parent/'other/source'),'/tmp/future-unit/source','relative','/home/malecada/master_thesis/onchain-financial-isolation/future-unit/source',str(P.CAP.parent.parent/'keys/source')]
for value in unsafe:refuses('unsafe path '+value,lambda value=value:B.fresh_capsule(value))
fresh=str(P.CAP.parent.parent/'canonical-review-uncreated-20261004-02/source');ok('no fixture unit created',not os.path.lexists(Path(fresh).parent));ok('fresh authorized disjoint future unit accepted',str(B.fresh_capsule(fresh))==fresh)
for case in P.CASES:
 d,b=B.rebind(case);ok(case+' unchanged valid null draft',d==json.loads(P.read(H/'DRAFT_CASES02.json'))[case])
 bound,_=B.rebind(case,fresh);ok(case+' fresh root metadata only',bound['capsule_root']==fresh and bound['fresh_identity'] is None);refuses(case+' release remains refused',lambda:P.release(bound))
# RR4 exact original inventory omission, then complete current collection.
original=H.parent/'held-consumer-canonical-root-recipe01-2026-10-04';m=json.loads((original/'MANIFEST01.json').read_bytes());declared={r['path'] for r in m['entries']};actual={str(p.relative_to(original)) for p in original.rglob('*') if p!=original/'MANIFEST01.json'};missing=sorted(actual-declared)
ok('RR4 RED exactly three nested manifests omitted',len(missing)==3 and all(Path(n).name=='MANIFEST01.json' for n in missing));red['RR4']={'missing':missing,'original_actual_members':len(actual),'original_declared_members':len(declared)}
current=collect(H);paths={r['path'] for r in current};ok('RR4 GREEN all three included',all(n in paths for n in missing));ok('old root manifest also included','MANIFEST01.json' in paths)

# RR5 actual owned opaque job file, no outside reads or writes.
opaque=H/'opaque-absolute-job03.json';opaque.write_bytes(P.read(H/'generated01/input-draft'/drafts['success']['experiment']['inputs']['execution_job']['path']))
mutated=copy.deepcopy(drafts);mutated['success']['experiment']['inputs']['execution_job']['path']=str(opaque)
original_read=old.read
old.read=lambda path:P.encode(mutated) if str(path).endswith('DRAFT_CASES01.json') else original_read(path)
absdraft,absbodies=old.rebind('success');old.read=original_read
ok('RR5 RED actual absolute owned path accepted',str(opaque) in absbodies)
red['RR5']={'absolute_owned_job_path':str(opaque),'old_returned_absolute_key':str(opaque) in absbodies,'outside_helper_scope_io':False}
refuses('RR5 GREEN absolute descriptor refused',lambda:B.validate_draft(mutated['success'],'success'))
for badpath in ['../escape.json','fixture_inputs/../escape.json','/etc/passwd','fixture_inputs/.env','fixture_inputs/keys/payload.json']:
 value=copy.deepcopy(drafts['success']);value['experiment']['inputs']['execution_job']['path']=badpath
 refuses('malformed input descriptor '+badpath,lambda value=value:B.validate_draft(value,'success'))

# Full byte/AST inverse of helper changes.
i=json.loads((H/'INVERSE02.json').read_bytes());raw=(H/'rebind01.py').read_text();restored=raw.replace(i['inserted_helper'],'').replace(i['inserted_validator'],'').replace(i['validation_call'],'').replace(i['replace_new'],i['replace_old']);baseline=(H/'baseline-rebind01.py').read_text();ok('full rebind byte inverse',restored==baseline);ok('full rebind AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(baseline)))
i=json.loads((H/'PREPARE_INVERSE02.json').read_bytes());raw=(H/'prepare01.py').read_text();restored=raw.replace(i['new'],i['old']);baseline=(H/'baseline-prepare01.py').read_text();ok('full preparation byte inverse',restored==baseline);ok('full preparation AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(baseline)))
for name,value in [('RED03.json',red),('CHECKS03.json',{'count':len(checks),'checks':checks,'numerical_imports':False,'native_execution':False,'metadata_only':True})]:
 with (H/name).open('xb') as f:f.write(P.encode(value))
print(len(checks),'checks passed')
