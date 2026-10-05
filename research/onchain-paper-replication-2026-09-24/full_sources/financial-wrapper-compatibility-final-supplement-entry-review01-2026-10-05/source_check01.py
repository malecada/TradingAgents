from pathlib import Path
import ast,copy,hashlib,json,os,stat,sys,types
O=Path(__file__).resolve().parent;F=O.parent;ROOT=F.parents[2];D=F/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05';H=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,h=None):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'bounded regular '+p.name);b=p.read_bytes();ok(s==p.lstat(),'stable '+p.name)
 if h:ok(H(b)==h,'pinned '+p.name)
 return b
manifest=json.loads(read(D/'MANIFEST01.json','f0444630b6c096465c81ded0cf768c7c8ecfe6994cf3087f4ad7ce86e43f62d7'))
for row in manifest['members']:
 p=D/row['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==row['mode'],'original mode '+row['path'])
 if row['kind']=='file':ok(len(read(p,row['sha256']))==row['bytes'],'length '+row['path'])
 else:ok(stat.S_ISDIR(s.st_mode),'directory '+row['path'])
ok({p.relative_to(D).as_posix() for p in D.rglob('*')}=={r['path'] for r in manifest['members']}|{'MANIFEST01.json'},'whole candidate31 namespace')
for row in json.loads(read(D/'INVERSE01.json')):
 old=read(ROOT/row['original_path'],row['original_sha256']).decode();new=read(D/row['file']).decode();ok(old==row['original'] and new==row['new'],'actual full inverse bodies '+row['file'])
 transformed=old
 for a,b in row['changes']:ok(a in transformed,'declared seam');transformed=transformed.replace(a,b)
 ok(transformed==new,'full literal transformation '+row['file']);ok(ast.dump(ast.parse(transformed))==ast.dump(ast.parse(new)),'full AST '+row['file'])
 olddefs={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};newdefs={n.name:ast.dump(n) for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
 exempt={'run'} if row['file']=='restore_bundle01.py' else {'contract','main'}
 for n in olddefs.keys()-exempt:ok(olddefs[n]==newdefs[n],'unchanged '+row['file']+':'+n)
for n,r in json.loads(read(D/'ORIGINS01.json')).items():
 original=read(ROOT/r['path'],r['sha256'])
 if n!='restore_bundle01.py':ok(read(D/n)==original,'exact inherited '+n)
# Load only genuine stdlib preparation helpers; no public run.
sys.path[:0]=[str(D),str(D/'utilities')];import binding01 as B;import restore_bundle01 as S
q=json.loads(read(D/'REQUEST_DRAFT01.json'))
try:B.validate(q)
except (ValueError,TypeError,KeyError):checks.append('actual null draft refuses')
else:raise AssertionError('null draft accepted')
# Exercise new phase and fixed path predicates, no accepted release fabricated.
for filename,phase in [('caller_remote01.py','REMOTE'),('caller_flat01.py','FLAT')]:
 tree=ast.parse(read(D/filename));ns={'Path':Path};nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in {'contract','local','evidence'}]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),filename,'exec'),ns)
 c={'schema_version':1,'status':'ROOT_BOUND_FINAL_SUPPLEMENT_ENTRY','phase':phase,'owned_root':str(ns['D']),'numerical_authority':False,'main_commit':'0'*40,'helpers':{n:'0'*64 for n in ['watch01.py','utilities/owned_io.py','recover01.py','restore_bundle01.py','binding01.py','receipt01.py','cohort01.py','utilities/recovery_pax01.py','utilities/bounded_git01.py']}}
 c['helpers']['utilities/owned_io.py']=ns['IOPIN']
 if phase=='FLAT':c.update({k:{} for k in ['remote_receipt','remote_root_exit','selected_mode_profile','flat_release','request']})
 ok(ns['contract'](c)==phase,'opaque phase predicate '+phase)
 for k,v in [('phase','FLAT' if phase=='REMOTE' else 'REMOTE'),('status','ROOT_BOUND_BASELINE_ENTRY'),('owned_root',str(O)),('numerical_authority',True)]:
  bad=copy.deepcopy(c);bad[k]=v
  try:ns['contract'](bad)
  except AssertionError:checks.append('wrong '+k+' refuses '+phase)
  else:raise AssertionError('predicate accepted '+k)
 if phase=='FLAT':ok(ns['evidence']('selected/x')==S.RECEIVER/'selected/x' and ns['local']('selected/x')!=ns['evidence']('selected/x'),'separate read-only receiver evidence')
# Independently inspect real authored tiny recovery bodies and canonical archive,
# without duplicating archive restoration or modifying its frozen fixtures.
R=S.R;m=json.loads(read(D/'opaque-selected/manifest.json'));meta=json.loads(read(D/'opaque-output/flat-opaque/body-metadata.json'));ok(meta['manifest']==m,'actual original mode metadata')
for row in m['members']:
 if row['kind']=='file':ok(read(D/'opaque-output/flat-opaque'/meta['flat_members'][row['path']],row['sha256'])==read(D/'opaque-original'/row['path']),'actual opaque restored body')
ok(S.RECEIVER==F/'financial-wrapper-compatibility-final-supplement-root02-2026-10-05','fixed receiver root')
result={'assertions':len(checks),'checks':checks,'candidate_manifest_sha256':H((D/'MANIFEST01.json').read_bytes()),'source_only':True,'actual_final_entry_released':False,'public_restore_or_entry':False,'network':False,'numerical_authority':False}
(O/'SOURCE_CHECKS01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'},sort_keys=True))
