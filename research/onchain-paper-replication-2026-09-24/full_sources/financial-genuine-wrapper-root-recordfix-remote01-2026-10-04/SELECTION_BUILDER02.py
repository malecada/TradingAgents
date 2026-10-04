import hashlib,json,os,stat,subprocess,time
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-recordfix-remote01-2026-10-04';H='2ac9383c2086003e27f28391340832184f9a7221'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==H and not os.path.lexists(D/'SELECTED_BODIES01.json')
closure=['financial-genuine-wrapper-root-recordfix-capture01-2026-10-04','financial-genuine-wrapper-root-recordfix-capture-review-snapshot01-2026-10-04','financial-genuine-wrapper-recordfix-source-admission-review01-2026-10-04','financial-genuine-wrapper-root-recordfix-adoption01-2026-10-04','financial-genuine-wrapper-recordfix-registration-preparation02-2026-10-04','financial-genuine-wrapper-recordfix-registration-review02-2026-10-04','financial-genuine-wrapper-recordfix-remote-preparation01-2026-10-04','financial-genuine-wrapper-recordfix-flat-preparation01-2026-10-04','financial-genuine-wrapper-recordfix-remote-correction02-2026-10-04','financial-genuine-wrapper-recordfix-remote-correction-review02-2026-10-04','financial-genuine-wrapper-root-recordfix-review-snapshot01-2026-10-04','financial-genuine-wrapper-root-recordfix-remote01-2026-10-04','financial-genuine-wrapper-root-recordfix-flat01-2026-10-04','financial-genuine-wrapper-recordfix-outcome-verifier-preparation01-2026-10-04','financial-genuine-wrapper-recordfix-outcome-verifier-review01-2026-10-04']
paths=set()
for name in closure:
 for root,dirs,files in os.walk(B/name,followlinks=False):
  assert not any(n in ('.git','.venv','__pycache__','node_modules') or (Path(root)/n).is_symlink() for n in dirs)
  for n in files:
   p=Path(root)/n;assert stat.S_ISREG(p.lstat().st_mode);paths.add(p.relative_to(M).as_posix())
# Entire large review, including original negative witness link, is in its exact
# opaque archive. Core original decision/check bodies are also directly fetched.
T=B/'financial-genuine-wrapper-recordfix-transport-flat-review01-2026-10-04'
for p in T.iterdir():
 if p.is_file() and not p.is_symlink():paths.add(p.relative_to(M).as_posix())
for p in (B/'financial-genuine-wrapper-recordfix-capture-review01-2026-10-04').iterdir():
 if p.is_file() and not p.is_symlink():paths.add(p.relative_to(M).as_posix())
R=B/'financial-genuine-wrapper-runtime-record-review01-2026-10-04'
for name in ('REVIEW01.json','REVIEW01.md','MANIFEST01.json'):
 p=R/name;assert p.is_file();paths.add(p.relative_to(M).as_posix())
assert 1<=len(paths)<=506
raw_tree=subprocess.check_output(['git','ls-tree','-r','-z',H,'--',*sorted(paths)]);objects={}
for row in raw_tree.split(b'\0')[:-1]:
 left,name=row.split(b'\t',1);mode,kind,oid=left.decode().split();objects[name.decode()]=(mode,kind,oid)
rows=[];modes={};oids=[];begun=time.monotonic()
for name in sorted(paths):
 assert time.monotonic()-begun<120
 p=M/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2
 raw=p.read_bytes();assert subprocess.check_output(['git','show',H+':'+name])==raw
 oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();mode,kind,actual=objects[name];assert mode in ('100644','100755') and kind=='blob' and oid==actual
 rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()});oids.append(oid);modes[name]={'git_mode':mode,'git_object':oid,'original_posix_mode':stat.S_IMODE(s.st_mode)}
assert sum(r['bytes'] for r in rows)<=64*1024**2
value={'remote_commit':H,'rows':rows};body=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
with (D/'SELECTED_BODIES01.json').open('xb') as f:f.write(body)
(D/'SELECTION_READBACK01.json').write_text(json.dumps({'selection_sha256':hashlib.sha256(body).hexdigest(),'remote_commit':H,'count':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'expected_git_operations':11+2*len(rows),'unique_git_oids':len(set(oids)),'modes':modes,'complete_directly_selected_directories':closure,'complete_archived_reviews':['financial-genuine-wrapper-root-recordfix-review-snapshot01-2026-10-04','financial-genuine-wrapper-root-recordfix-capture-review-snapshot01-2026-10-04'],'scope':'Complete current Source325 archive986/713/fullGit/325tracked/324pins, actual capture request/authentication/terminal/Rootactualexit and allcurrent capture/source-admission/adoption/accepted-source02/same-budget18-registration02 preparation and review bodies. Full transport-flat review tree1771/1482+lexicalsymlink and whole original actual-capture review tree are in separate opaque deterministic archives plus original direct decision/core check files. Their lexical links are literal metadata only, never followed or extracted. Exact current source/copy/flat/safe-binder sources and runtime RECORD review decision metadata included. Complete old failed-scope archive remains separately accepted/recovered f1e0a5d3/2eb6546a/ca360ddc, not silently inserted. Installed runtime bodies/empirical stores/POSIX instantiation/full-fit capacity/actual newParent/finalverifier excluded. Full runtime-record negative-witness review bodies are not selected; its original complete Git bytes remain preserved. This Source325 recovery gives no release or paper fit credit.','numerical_or_native_started':False},sort_keys=True,indent=2)+'\n')
print(json.dumps({'selection_sha256':hashlib.sha256(body).hexdigest(),'rows':len(rows),'bytes':sum(r['bytes'] for r in rows),'ops':11+2*len(rows),'oids':len(set(oids))}))
