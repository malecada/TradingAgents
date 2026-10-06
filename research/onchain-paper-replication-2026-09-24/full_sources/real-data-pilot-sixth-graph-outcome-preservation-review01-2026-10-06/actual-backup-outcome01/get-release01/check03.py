from pathlib import Path
import json,hashlib,stat,subprocess,types,os,datetime
R=Path.cwd();H=Path(__file__).resolve().parent;F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-sixth-graph-get-duplicates-retirement01-2026-10-06'
def raw(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();t=p.lstat();assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 assert pin is None or hashlib.sha256(b).hexdigest()==pin;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
a=obj(D/'SELECTION01.json','a3290ec188b35530c04e043cb3309400be22442f0bcf3ca1f1aaf39c06d78db2');b=obj(D/'SELECTION02.json','d1b6cb9d76af8b06137c75806b8cd02f98eb74d26f46fd7eb705732aed56000c')
x=obj(D/'BOUND_RELEASE_DRAFT01.json');y=obj(D/'BOUND_RELEASE_DRAFT02.json','4f28a2d46e874a27b6ed63b27a83a569fc3fb79f5d54b34ea96c46aa9415c393')
expected=dict(a);expected['evidence']=dict(a['evidence']);expected['historical_source_mapping']=b['historical_source_mapping'];assert len(b['historical_source_mapping'])==2
for m in b['historical_source_mapping']:
 assert m['actual_git_commit']=='a55823c68668cef70fd7a9909a3ff46420d3d668'
 assert expected['evidence'].pop(m['historical_original_path'])==m['historical_sha256']
 retained=raw(m['retained_body_path'],m['historical_sha256'])
 assert retained==subprocess.check_output(['git','show',m['actual_git_commit']+':'+m['historical_original_path']])
 raw(m['historical_original_path'],m['current_installed_sha256'])
 expected['evidence'][m['retained_body_path']]=m['historical_sha256']
assert expected==b
ex=dict(x);ex['evidence']=dict(b['evidence']);ex['selection']=y['selection'];ex['evidence'][y['selection']['path']]=y['selection']['sha256'];assert ex==y
for p,pin in y['evidence'].items():raw(p,pin)
src=raw(D/'retire01.py',y['entry_sha256']);m=types.ModuleType('review_metadata_only');m.__file__=str(D/'retire01.py');exec(compile(src,m.__file__,'exec'),vars(m));m.selected(R,b);m.recovery(R,b);m.inactive()
for p in b['removed_ledger_paths']:assert not os.path.lexists(R/p)
for n in ('attempt01.json','complete01.json','failed01.json','RELEASE_REVIEW01.json'):assert not os.path.lexists(D/n)
r={'decision':'accepted','correction':'Two historical source references now pin exact retained committed bytes; all scope, caller and controls unchanged.','historical_source_mapping':b['historical_source_mapping'],'selection_sha256':y['selection']['sha256'],'bound_draft_sha256':hashlib.sha256(raw(D/'BOUND_RELEASE_DRAFT02.json')).hexdigest(),'current_ten_stat_joins':True,'no_active_registered_consumer':True,'get_identity_unused':True,'large_payload_reads':0,'evidence_count':len(y['evidence']),'at':datetime.datetime.now(datetime.UTC).isoformat()}
with (H/'CHECK03.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(r))
