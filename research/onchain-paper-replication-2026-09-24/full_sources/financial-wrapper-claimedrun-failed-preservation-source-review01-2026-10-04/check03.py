import ast,hashlib,io,json,os,sys
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();source=(T/'restore01.py').read_bytes();assert sha(source)=='1cdfe7bfaf9001ec7a0ea27925f48a3d8e371d290d2da807de6e782aab244440';tree=ast.parse(source)
pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINS'for t in n.targets)));parent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01');checks=[]
for n,h in pins.items():assert sha((parent/n).read_bytes())==h and (parent/n).read_bytes()==(P/n).read_bytes();checks.append('exact original actual Parent primitive '+n)
assert next(i for i,n in enumerate(tree.body)if isinstance(n,ast.For))<next(i for i,n in enumerate(tree.body)if isinstance(n,ast.Import)and n.names[0].name=='recovery04');checks.append('all three body pins checked before import')
for n in ('flat-capsule01','flat-parent01','flat-root01','FLAT_INTENT01.json','FLAT_RECOVERY01.json'):assert not os.path.lexists(T/n);checks.append('fresh original absent '+n)
root=D/'tiny-three-roles';root.mkdir();recovered=[]
for role in ('capsule','parent','root'):
 origin=root/(role+'-origin');origin.mkdir(mode=0o700);(origin/'opaque').write_bytes(('opaque:'+role).encode());manifest=R.scan(origin);archive=root/(role+'.tar.gz');pin=R.pack(origin,manifest,archive);dest=root/(role+'-flat');dest.mkdir(mode=0o700);result=R.restore(archive,pin,manifest,dest)
 assert result['regular_bodies']==1 and not result['research_authority']and not result['instantiated_posix_tree'];checks.append('actual tiny ordinary canonical restore '+role);recovered.append(result)
 try:R.restore(archive,pin,manifest,dest)
 except BaseException as e:checks.append('one-use retained directory refuses '+role+': '+type(e).__name__)
 else:raise AssertionError('reused output')
 bad=dict(pin,sha256='0'*64);fresh=root/(role+'-bad');fresh.mkdir(mode=0o700)
 try:R.restore(archive,bad,manifest,fresh)
 except ValueError as e:checks.append('archive pin refusal '+role+': '+str(e))
 else:raise AssertionError('bad archive pin accepted')
 assert list(fresh.iterdir())==[]
(D/'READBACK03.json').write_bytes(R.encode({'restore_source_sha256':sha(source),'checks':len(checks),'checks_detail':checks,'tiny_actual_opaque_roles':recovered,'actual_root_restore_executed':False,'actual_remote_receipt_not_fabricated':True,'exact_future_receipt_review_still_required':True,'source_limits':{'seconds_sampled':120,'disk_floor_bytes':R.FLOOR,'file_bytes':R.FILE,'baseline_bytes':R.BASE},'schema_qualification':'Remote source selection permits supplemental rows generally; this adapter requires exactly8. Concrete actual committed selection and future receipt must equal the8 pinned REQUIRED bodies; pure helper validators alone do not attest remote origin.'}))
print(json.dumps({'checks':len(checks),'root_restore_executed':False}))
