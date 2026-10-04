from pathlib import Path
import json,hashlib,stat,sys,subprocess,os
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-failed-root-remote02-2026-10-04';A=F/'financial-wrapper-complete100-failed-preservation-tooling02-2026-10-04';C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_bytes());checks=[]
def ok(v,n):assert v,n;checks.append(n)
install=read(T/'ROOT_INSTALLATION_DRAFT01.json');selection=read(T/'SELECTED_BODIES01.json');required=read(C/'REQUIRED_BODIES01.json');commit=selection['remote_commit'];ok(sha((T/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())=='ada25ed8ec68709081d27649d3b8770d6966351623b7e7c92a92a972a494e0e5','actualinstallation pin');ok(sha((T/'SELECTED_BODIES01.json').read_bytes())==install['selection_sha256']=='be615c3631005d3a9aaa93ffdf47e46da4f2c4a50a64a2eb0bc1713e733f6f28','exactselection pin');ok(commit==install['remote_commit']=='e0f6d8709589626ecb8e6185cd403de02160ee4c','actualimmutablecommit')
expected=set(install['helper_pins'])|{'ROOT_INSTALLATION_DRAFT01.json','SELECTED_BODIES01.json'};ok({p.relative_to(T).as_posix()for p in T.rglob('*')if p.is_file()}==expected,'exactinstalled8files')
for name,row in install['helper_pins'].items():
 p=T/name;s=p.lstat();b=p.read_bytes();ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and p.resolve()==p and len(b)==row['bytes']and sha(b)==row['sha256']and b==(A/name).read_bytes(),'actualsix sourceorigin '+name)
review=F/'financial-wrapper-complete100-failed-preservation-review02-2026-10-04';ok(sha((review/'MANIFEST01.json').read_bytes())==install['review_manifest']=='300a3e621020723abeb5eff74399e98c75b9620e53976a1ff62519e5199c2a63','genuine source seal');ok(sha((review/'MACHINE01.json').read_bytes())==install['source_review_machine'],'genuine source decision')
for row in read(review/'MANIFEST01.json')['members']:
 if row['kind']=='file':ok(sha((review/row['path']).read_bytes())==row['sha256'],'source evidence '+row['path'])
sys.path.insert(0,str(T));import recover01 as R
R.validate_fixed_selection(selection);ok(R.encode(selection)==(T/'SELECTED_BODIES01.json').read_bytes(),'canonical exact selection');ok(R.REQUIRED==required and len(required)==35,'exact35 two-prefixrequired');oids=set();calls=[]
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(ROOT),*args],capture_output=True,timeout=15,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});ok(p.returncode==0 and len(p.stdout)<=4*1024**2,'readonly committedGit '+args[0]);calls.append({'args':args,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout)});return p.stdout
entries={}
for record in git(['ls-tree','-r','-z',commit,'--',*sorted(required)]).split(b'\0'):
 if record:
  raw,name=record.split(b'\t');mode,kind,oid=raw.decode().split();entries[name.decode()]=(mode,kind,oid)
for name,row in required.items():
 b=(ROOT/name).read_bytes();mode,kind,oid=entries[name];ok(mode=='100644'and kind=='blob','committed source mode '+name);ok(git(['cat-file','blob',oid])==b and sha(b)==row['sha256']and len(b)==row['bytes'],'actualcurrentcommittedbody '+name);ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual blobOID '+name);oids.add(oid)
ok(len(oids)==29 and 10+len(oids)+2*len(required)==109 and sum(r['bytes']for r in required.values())==16481302,'35rows29OIDs109operations16.48MB')
confirmation=read(H/'REMOTE_CONFIRMATION42.json');ok(confirmation['main_and_actual_remote']==commit and confirmation['actual_ls_remote']['exit']==confirmation['push']['exit']==0 and confirmation['actual_ls_remote']['stdout']==commit+'\t'+R.BRANCH+'\n','genuine Root remote confirmation record')
initial=R.W.census(T);ok(initial['logical_bytes']==sum(p.stat().st_size for p in T.rglob('*')if p.is_file()),'fullinstalled baseline logical');ok(initial['allocated_bytes']==sum(p.stat().st_blocks*512 for p in [T,*T.rglob('*')]),'fullinstalled baseline includes alldirectories allocated')
absent=['fresh-complete100-failed-outcome02-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','attempt','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json']+['flat-'+x+'01'for x in ['capsule01','capsule02','capsule03','capsule04','capsule05','capsule06','capsule07','capsule08','parent','support']]
for name in absent:ok(not os.path.lexists(T/name),'absent fresh namespace '+name)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:argv=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  ok(str(T/'recover01.py').encode()not in argv and str(T/'restore01.py').encode()not in argv,'no currenthelper '+p.name)
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'localGit':calls,'initial_owned_census':initial,'fresh_absent':absent,'installed_draft_actual_receiver_child_fsize_field':'prospective policy only; no actual receiver exists or OS readback is claimed','actual_transfer':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'baseline':initial}))
