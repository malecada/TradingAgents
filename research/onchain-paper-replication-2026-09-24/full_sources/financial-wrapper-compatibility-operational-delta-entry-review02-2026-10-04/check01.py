from pathlib import Path
import json,hashlib,stat,os,subprocess,importlib.util,sys
O=Path(__file__).resolve().parent;F=O.parent;R=F.parents[2];T=F/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());d=J(T/'ROOT_INSTALLATION_DRAFT01.json');q=J(T/'SELECTED_BODIES01.json')
assert h((T/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())=='e47a2f70c812399c051600f426fc60452c979f7b38f36336ad2711c47a3643ee';assert h((T/'SELECTED_BODIES01.json').read_bytes())=='55532ac9b8ea0d92f8a75f202a6733b43124cb9367dccca2c4fabfd175b7f791';assert q['remote_commit']==d['source_main_commit']=='0e65d12400e9c63b0eaf1f93bea2c81b10a82743'
assert (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()==(T/'SELECTED_BODIES01.json').read_bytes();assert T.resolve()==T and stat.S_IMODE(T.stat().st_mode)==0o700
installed=[]
for n,x in d['helpers_and_selection'].items():
 p=T/n;s=p.lstat();b=p.read_bytes();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(b)==x['bytes'] and h(b)==x['sha256'];installed.append(dict(path=n,mode=stat.S_IMODE(s.st_mode),**x))
assert h(Path(d['source_review']['path']).read_bytes())==d['source_review']['sha256']=='4605c1f6dc5af27d3abe4d03de0f6adc203ab01d88bbdcadeca26f5ba399c895'
SR=Path(d['source_review']['path']).parent;assert h((SR/'MANIFEST01.json').read_bytes())=='f5149fb8f06d400982324ceca7e8afdc64205c2f692320ccbd440041444e59c2'
required=J(F/'financial-wrapper-compatibility-operational-delta-tooling01-2026-10-04/REQUIRED_BODIES01.json');assert q['rows']==[dict(path=n,**x) for n,x in sorted(required.items())] and len(q['rows'])==10 and sum(x['bytes'] for x in q['rows'])==451691

def git(args):return subprocess.run(['git','--no-replace-objects',*args],cwd=R,capture_output=True,check=True,timeout=20).stdout
joined=[]
for x in q['rows']:
 b=(R/x['path']).read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256'];line=git(['ls-tree','-z',q['remote_commit'],'--',x['path']]);meta,n=line[:-1].split(b'\t');mode,kind,oid=meta.split();assert n.decode()==x['path'] and mode==b'100644' and kind==b'blob';assert git(['cat-file','blob',oid.decode()])==b;assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode();joined.append(dict(x,git_mode=mode.decode(),git_oid=oid.decode(),literal_mode=stat.S_IMODE((R/x['path']).stat().st_mode)))
# No actual transfer status inferred from local objects. Root remote confirmation remains operational evidence.
absent=['fresh-operational-source-policy01.git','selected','flat-operational-delta01','REMOTE_RECOVERY01.json','FAILED01.json','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','FLAT_POSTWRITE_OBSERVATION01.json','attempt','attempt.json','INTENT01.json']
for n in absent:assert not os.path.lexists(T/n)
assert {p.relative_to(T).as_posix() for p in T.rglob('*')}==set(d['helpers_and_selection'])|{'utilities','ROOT_INSTALLATION_DRAFT01.json'}
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  argv=(p/'cmdline').read_bytes().split(b'\0');cwd=(p/'cwd').resolve()
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if cwd==T or str(T/'recover01.py').encode() in argv or str(T/'restore01.py').encode() in argv:active.append(p.name)
assert not active
sys.path.insert(0,str(T));spec=importlib.util.spec_from_file_location('entry_watch',T/'watch01.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W);baseline=W.census(T)
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');assert subprocess.run(['git','rev-parse','HEAD'],cwd=S,capture_output=True,check=True,timeout=20).stdout.decode().strip()=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
prior=Path(d['prior_unreleased_definition']['root']);assert not (prior/'selected').exists() and not (prior/'REMOTE_RECOVERY01.json').exists() and not (prior/'fresh-operational-source-policy01.git').exists()
read={'schema_version':1,'draft_sha256':h((T/'ROOT_INSTALLATION_DRAFT01.json').read_bytes()),'selection_sha256':h((T/'SELECTED_BODIES01.json').read_bytes()),'commit':q['remote_commit'],'installed':installed,'joined_rows':joined,'unique_oids':len({x['git_oid'] for x in joined}),'expected_operations':10+len({x['git_oid'] for x in joined})+20,'initial_owned_sample':baseline,'fixed_policy':W.POLICY,'absent_names':absent,'current_matching_processes':active,'prior_unreleased_definition':d['prior_unreleased_definition'],'actual_remote_receipt':None};(O/'READBACK01.json').write_text(json.dumps(read,indent=2)+'\n');print('PASS exact installed closure/current+commit ten bodies/fresh namespace/current sample')
