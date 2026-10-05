"""Fresh opaque recovery of all nineteen actual outcome shards; accepted R4 unchanged."""
from pathlib import Path
import hashlib,importlib.util,json,resource,shutil,time
ROOT=Path.cwd();F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
TOOL=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation03-2026-10-05'
OUT=F/'financial-wrapper-serialized-continuation-outcome-flat01-2026-10-05'
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05'
COMMIT='91cc2c13417e04f7af0b8b78d9dff9c67b1e7516'
PINS=('1fac541136d807b18ace86699af215a1b6910fdc8d16796547ac48747df1a85a','01c306ff43940e746bacfa9ab2fff0128f7c954100f557c2599dfbce10be98a0','99354625986874a41414e7725c6980e35ccc740f8d27497b36fb91270b11e66a')
assert hashlib.sha256((TOOL/'capture01.py').read_bytes()).hexdigest()=='d8b61b8bc45e69da0df50bfa4694c0c0d103aaa5dce6668fccd0686c275958bb'
for n,h in {'recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():assert hashlib.sha256((TOOL/'utilities'/n).read_bytes()).hexdigest()==h
spec=importlib.util.spec_from_file_location('accepted_opaque_sharder',TOOL/'capture01.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S);R=S.R
resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE));start=time.monotonic();assert not OUT.exists();S.boundary(start,128*1024**2)
refs={};receipts=[]
for lane,pin in enumerate(PINS,1):
 remote=F/f'financial-wrapper-serialized-continuation-outcome-remote-lane{lane:02d}-2026-10-05';raw=R.read(remote,'SELECTED_BODIES01.json');assert R.digest(raw)==pin
 selected=json.loads(raw);assert selected['remote_commit']==COMMIT
 recraw=R.read(remote,'REMOTE_RECOVERY01.json');rec=json.loads(recraw);assert rec['selection_sha256']==pin and rec['remote_commit']==COMMIT and rec['selected_count']==len(selected['rows']) and rec['selected_logical_bytes']==sum(v['bytes'] for v in selected['rows']) and rec['expected_operations']==len(rec['operations'])
 assert json.loads(R.read(remote,'ACTUAL_ROOT_EXIT01.json'))['actual_root_exit']==0
 assert all(v['exit']==0 and v['actual_reaped_exit']==0 and v['cleanup_failures']==[] and v['actual_child_limits']=={'pid':v['pid'],'fsize':[R.FILE,R.FILE]} for v in rec['operations'])
 assert rec['selected_blobs']==[dict(r,git_mode=v['git_mode'],git_object=v['git_object']) for r,v in zip(selected['rows'],rec['selected_blobs'],strict=True)]
 for row in rec['selected_blobs']:
  n=row['path'];assert n not in refs;p=remote/'selected'/n;b=R.read(p.parent,p.name);assert len(b)==row['bytes'] and R.digest(b)==row['sha256'];refs[n]=(p,row)
 receipts.append({'path':str(remote/'REMOTE_RECOVERY01.json'),'sha256':R.digest(recraw),'actual_root_exit':0})
descriptor,descrow=refs[PREFIX+'/shards/CAPTURE01.json'];descraw=R.read(descriptor.parent,descriptor.name);assert R.digest(descraw)=='b1bcc9afbc3ce2516eaec8f182d726e975de90b1ee0e96f050846e32d14713fb';desc=json.loads(descraw)
assert len(desc['pieces'])==19 and [p['id'] for p in desc['pieces']]==list(range(19)) and len(desc['originals']['increment']['manifest']['members'])==400
OUT.mkdir(mode=0o700);results=[];count=0
for piece in desc['pieces']:
 S.boundary(start,128*1024**2);archive=refs[PREFIX+'/shards/'+piece['archive']][0];manifest=refs[PREFIX+'/shards/'+piece['manifest']][0];m=json.loads(R.read(manifest.parent,manifest.name))
 dest=OUT/f"piece-{piece['id']:03d}";dest.mkdir(mode=0o700);result=R.restore(archive,piece['archive_pin'],m,dest);count+=result['regular_bodies'];results.append({'id':piece['id'],'archive':str(archive),'manifest':str(manifest),'primitive':result})
assert count==400;S.boundary(start,128*1024**2)
R.put(OUT/'RECOVERY01.json',{'schema_version':1,'status':'ACTUAL_COMPLETE_SERIALIZED_CONTINUATION_INCREMENT_FRESH_FLAT_BYTE_RECOVERY','remote_commit':COMMIT,'receiver_receipts':receipts,'capture_sha256':R.digest(descraw),'pieces':results,'regular_bodies':count,'new_original_bodies':399,'all99_opaque_checkpoint_states_included':True,'numerical_or_paper_fit_authority':False,'installed_runtime_body_recovery':False,'POSIX_reconstruction':False,'immutable_writer_exclusion':False,'qualification':'Every fresh shard restored once from actual externally retrieved bytes through accepted unchanged R4 framing/mode/hash/re-encoding checks. Complete current CAP/Git/Parent outcome scope additionally joins accepted immutable current/final/historical bases; independent original-path joins remain required.'})
print(json.dumps({'status':'ACTUAL_NEW_OUTCOME_INCREMENT_BYTE_RECOVERED','pieces':19,'regular_bodies':count,'recovery_sha256':R.digest(R.read(OUT,'RECOVERY01.json'))}))
