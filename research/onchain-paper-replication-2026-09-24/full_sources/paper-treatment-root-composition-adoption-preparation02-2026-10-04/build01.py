"""One-use source-only assembly into this owned preparation directory."""
from pathlib import Path
import ast,hashlib,json,os,shutil,stat,subprocess
D=Path(__file__).resolve().parent;ROOT=D.parents[3];FS=D.parent
PROD=FS/'paper-treatment-production-preparation03-2026-10-04';CONS=FS/'paper-treatment-fit-admission-preparation03-2026-10-04'
PKG='tradingagents/research/onchain_replication/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def oid(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def write(n,v):(D/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
paths=sorted({str(p.relative_to(ROOT)) for p in (ROOT/PKG).glob('*.py')}|{str(p.relative_to(ROOT)) for p in (ROOT/'tradingagents/research').glob('*.py')}|{'tradingagents/__init__.py'})
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=10).strip()
rawtree=subprocess.check_output(['git','ls-tree','-z',head,'--',*paths],cwd=ROOT,timeout=10)
git={}
for row in rawtree.split(b'\0'):
 if row:
  info,path=row.split(b'\t',1);mode,kind,objectid=info.decode().split();assert kind=='blob';git[path.decode()]={'git_mode':mode,'git_blob_oid':objectid}
assert set(git)==set(paths)
baseline={}
for rel in paths:
 p=ROOT/rel;st=p.lstat();raw=p.read_bytes();assert p.resolve()==p and stat.S_ISREG(st.st_mode) and len(raw)<=4*1024**2 and oid(raw)==git[rel]['git_blob_oid']
 baseline[rel]={'sha256':sha(raw),'bytes':len(raw),'mode':stat.S_IMODE(st.st_mode),**git[rel]}
 for kind in ('baseline','candidate'):
  out=D/kind/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
changes=[]
for name,origin in [('job.py',PROD),('treatment_contract.py',PROD),('treatment_production.py',PROD),('population_assembly.py',CONS),('run.py',CONS),('evaluation.py',CONS),('treatment_admission.py',CONS)]:
 rel=PKG+name;p=origin/'overlay'/rel;raw=p.read_bytes();out=D/'candidate'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
 if name=='job.py':assert (ROOT/rel).read_bytes()==(PROD/'baseline-job.py').read_bytes()
 elif name in ('population_assembly.py','run.py','evaluation.py'):assert (ROOT/rel).read_bytes()==(CONS/'origins'/name).read_bytes()
 changes.append({'path':rel,'origin':str(p),'origin_sha256':sha(raw),'kind':'modified' if rel in baseline else 'new'})
allpaths=sorted(p.relative_to(D/'candidate').as_posix() for p in (D/'candidate').rglob('*.py'))
selfpath=PKG+'treatment_admission.py';pins={rel:sha((D/'candidate'/rel).read_bytes()) for rel in allpaths if rel!=selfpath}
p=D/'candidate'/selfpath;original=p.read_text();edits=[]
def replace(old,new):
 global original
 assert original.count(old)==1;original=original.replace(old,new);edits.append({'old':old,'new':new})
replace('PRODUCER_SOURCE_PINS = None','PRODUCER_SOURCE_PINS = '+repr(pins))
replace("    require(run.admission.experiment['source_files'].get(str(source_path.relative_to(run.admission.root))) == file_hash(source_path), 'treatment verifier source is not admitted')", "    self_relative = str(source_path.relative_to(run.admission.root))\n    self_hash = file_hash(source_path)\n    require(run.admission.experiment['source_files'].get(self_relative) == self_hash, 'treatment verifier source is not admitted')\n    # Fixed other-source pins plus the current admitted verifier close the map\n    # without embedding this file's own hash into its body.\n    producer_pins = {**PRODUCER_SOURCE_PINS, self_relative: self_hash}")
replace("for k, v in PRODUCER_SOURCE_PINS.items()), 'unreviewed producer source closure')", "for k, v in producer_pins.items()), 'unreviewed producer source closure')")
p.write_text(original);ast.parse(original)
inverse=original
for e in reversed(edits):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
assert inverse.encode()==(CONS/'overlay'/selfpath).read_bytes()
closure={}
for rel in allpaths:
 p=D/'candidate'/rel;raw=p.read_bytes();ast.parse(raw);closure[rel]={'sha256':sha(raw),'bytes':len(raw),'mode':stat.S_IMODE(p.stat().st_mode),'git_blob_oid':oid(raw),'git_mode':('100755' if p.stat().st_mode&0o111 else '100644')}
assert len(baseline)==135 and len(closure)==138 and len(pins)==137
assert set(closure)-set(baseline)=={PKG+n for n in ('treatment_contract.py','treatment_production.py','treatment_admission.py')}
write('BASELINE01.json',{'root':str(ROOT),'head':head,'source_count':len(baseline),'sources':baseline})
write('CLOSURE01.json',{'source_count':len(closure),'onchain_module_count':sum(r.startswith(PKG) for r in closure),'sources':closure,'producer_static_pins':pins,'producer_dynamic_self_path':selfpath,'new_source_commit':None,'scope':'actual candidate bodies and computed Git blob OIDs; no candidate commit exists'})
write('COMPOSITION_INVERSE01.json',{'origin':str(CONS/'overlay'/selfpath),'origin_sha256':sha((CONS/'overlay'/selfpath).read_bytes()),'candidate_sha256':closure[selfpath]['sha256'],'edits':edits,'full_byte_inverse':True,'full_ast_inverse':ast.dump(ast.parse(inverse))==ast.dump(ast.parse((CONS/'overlay'/selfpath).read_bytes()))})
write('ADOPTION_DELTAS01.json',changes)
for label,origin,manifest,pin in [('producer',PROD,'MANIFEST04.json','80fa83c9cd36e2742a580a743122133314f79cd8654cb23c2e92d7932329fc3b'),('consumer',CONS,'MANIFEST03.json','8f5e7ac08046c3e63b1237ed62f57e24ee9e9d046bb8cf07224bb013fa1a1d38')]:
 assert sha((origin/manifest).read_bytes())==pin
 for name in ([manifest,'TP3_INVERSE01.json','CORRECTION_INVERSE02.json','JOB_INVERSE01.json'] if label=='producer' else [manifest,'DA4_INVERSE01.json','CORRECTION_INVERSE01.json','DELTA_INVERSE01.json']):
  target=D/'origin-evidence'/label/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin/name,target)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=10).strip()==head
print(json.dumps({'baseline':len(baseline),'final':len(closure),'onchain':sum(r.startswith(PKG) for r in closure),'self_sha256':closure[selfpath]['sha256'],'head':head}))
