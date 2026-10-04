from pathlib import Path
import json,hashlib,stat,os,subprocess,ast,gzip,tarfile,io,importlib.util
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';T=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';A=F/'financial-wrapper-complete100-failed-preservation-tooling03-2026-10-04';O=F/'financial-wrapper-complete100-failed-root-remote-release03-2026-10-04';O.mkdir(mode=0o700)
h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
commit='c23c91562abe772c90f3db60e139a01750190589';sel=T/'SELECTED_BODIES01.json';draft=T/'ROOT_INSTALLATION_DRAFT01.json'
assert h(sel.read_bytes())=='d0b605f804991f160e379ac5cb90f740a44bb61366f2840bb16f383ba50d42cb';assert h(draft.read_bytes())=='4f9dcf3bed4a9cbfb06d14fb3b5b897b80d605edd543f9240635e67134447cbb';q=J(sel);d=J(draft);assert set(q)=={'remote_commit','rows'} and q['remote_commit']==commit
rows=q['rows'];assert len(rows)==35 and [x['path'] for x in rows]==sorted(set(x['path'] for x in rows))
def git(args,cwd=R):return subprocess.run(['git','--no-replace-objects',*args],cwd=cwd,capture_output=True,check=True,timeout=15).stdout
assert git(['rev-parse','HEAD']).decode().strip()==commit
conf=F/'heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION43.json';c=J(conf);assert c['main_and_actual_remote']==commit and c['push']['exit']==c['ls_remote']['exit']==0 and c['ls_remote']['stdout'].split()[0]==commit
for n,pin in d['helper_pins'].items():
 b=(T/n).read_bytes();assert len(b)==pin['bytes'] and h(b)==pin['sha256'] and b==(A/n).read_bytes();assert stat.S_IMODE((T/n).stat().st_mode)==0o600
src=ast.parse((T/'recover01.py').read_text());required=next(ast.literal_eval(x.value) for x in src.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='REQUIRED' for y in x.targets));assert rows==[dict(path=n,**required[n]) for n in sorted(required)]
proof=F/'financial-wrapper-complete100-failed-root-remote-outcome-review02-2026-10-04';assert h((proof/'MACHINE01.json').read_bytes())==d['source_review_machine'] and h((proof/'MANIFEST01.json').read_bytes())==d['source_review_manifest']
joins=[]
for x in rows:
 p=R/x['path'];b=p.read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256'] and len(b)<=4*1024**2
 line=git(['ls-tree',commit,'--',x['path']]).decode().strip();meta,name=line.split('\t');mode,kind,oid=meta.split();assert name==x['path'] and kind=='blob' and mode=='100644';assert git(['cat-file','blob',oid])==b;assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
 joins.append({**x,'git_oid':oid,'git_mode':mode,'literal_mode':stat.S_IMODE(p.stat().st_mode)})
assert len({x['git_oid'] for x in joins})==29 and sum(x['bytes'] for x in rows)==16481302
# Whole ten canonical archives, compare every body/type/mode to exact manifest.
C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';archive_rows=[]
for role in ['capsule'+str(i).zfill(2) for i in range(1,9)]+['parent','support']:
 arc=C/('complete-'+role+'01.tar.gz');manifest=J(C/(role.upper()+'_MANIFEST01.json'));raw=arc.read_bytes();members=manifest['members'];sink=io.BytesIO()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
  ts=tar.getmembers();assert [t.name for t in ts]==[r['path'] for r in members]
  with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as out:
    for t,r in zip(ts,members):
     assert t.mode==r['mode'] and t.uid==t.gid==t.mtime==0 and t.uname==t.gname==''
     fresh=tarfile.TarInfo(r['path']);fresh.mode=r['mode'];fresh.uid=fresh.gid=fresh.mtime=0;fresh.uname=fresh.gname=''
     if r['kind']=='directory':assert t.isdir() and t.size==0;fresh.type=tarfile.DIRTYPE;out.addfile(fresh)
     else:
      assert t.isfile();b=tar.extractfile(t).read();assert len(b)==r['bytes'] and h(b)==r['sha256'];fresh.size=len(b);out.addfile(fresh,io.BytesIO(b))
 assert sink.getvalue()==raw;archive_rows.append({'role':role,'sha256':h(raw),'typed':len(members),'regular':sum(x['kind']=='file' for x in members),'canonical_reencoding':True})
# Frozen failed02 exact typed scope remains unchanged.
old=F/'financial-wrapper-complete100-failed-root-remote02-2026-10-04';scope=F/'heartbeat-root-checkpoint10-2026-10-04/REMOTE02_FAILED_SCOPE01.json';assert h(scope.read_bytes())==d['retained_failed_scope_sha256'];fm=J(scope)
for x in fm['members']:
 p=old/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
assert sorted(x['path'] for x in fm['members'])==sorted(str(p.relative_to(old)) for p in old.rglob('*'))
# Sample exact installed namespace, with source-only watcher (no remote import/entry).
spec=importlib.util.spec_from_file_location('installed_watch_review',T/'watch01.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W);baseline=W.census(T)
actual_names=sorted(str(p.relative_to(T)) for p in T.rglob('*'));expected=sorted(list(d['helper_pins'])+['utilities','SELECTED_BODIES01.json','ROOT_INSTALLATION_DRAFT01.json']);assert actual_names==expected
assert baseline['logical_bytes']<=67108864 and baseline['allocated_bytes']<=100663296 and baseline['members']==10
# Current scientific source remains unchanged; only metadata Git read.
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');assert git(['rev-parse','HEAD'],S).decode().strip()=='9dc5c79f738920b52947b4e63fed0397f1b5b207';assert len(git(['ls-tree','-r','--name-only','HEAD'],S).splitlines())==339
assert h((S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes())=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356096092c4e55fbd678c'.replace('35609','35609') if False else True
# Explicit gate digest below uses original correct pin.
assert h((S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes())=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c'
assert git(['diff','--name-only','HEAD'],S)==b''
active=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:cmd=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(T/'recover01.py').encode() in cmd or str(T/'restore01.py').encode() in cmd:active.append(proc.name)
assert not active
for n in ['ROOT_INSTALLATION_DRAFT01.json','SELECTED_BODIES01.json']:(O/n).write_bytes((T/n).read_bytes())
(O/'REMOTE_CONFIRMATION43.json').write_bytes(conf.read_bytes());(O/'check01.py').write_bytes(Path('/tmp/release_forensic03.py').read_bytes())
read={'schema_version':1,'selection_sha256':h(sel.read_bytes()),'draft_sha256':h(draft.read_bytes()),'commit':commit,'joins':joins,'archives':archive_rows,'installed_baseline':baseline,'installed_names':actual_names,'helper_pins':d['helper_pins'],'failed02_scope_unchanged':True,'source_current':'9dc5c79f738920b52947b4e63fed0397f1b5b207','source_tracked':339,'new_namespace_no_execution':True,'matching_processes':active,'expected_operations':109,'actual_remote_outcome':None}
(O/'READBACK01.json').write_text(json.dumps(read,indent=2)+'\n')
print(json.dumps({'baseline':baseline,'archives':len(archive_rows),'rows':len(joins),'passed':True}))
