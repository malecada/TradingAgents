import hashlib,json,os,shutil,sys,time
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04'
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
scopes={
 'preparation02':('financial-genuine-wrapper-claimedrun-source-recovery-preparation02-2026-10-04','MANIFEST02.json','bb6db7b928c92b1a310bbbf759dfcd212b92c8ed031d360069c1c5b91df9a3be'),
 'review02':('financial-genuine-wrapper-claimedrun-source-recovery-review02-2026-10-04','MANIFEST01.json','ee1e4aa23cc0d37f4db3c6607638db27a29ff1285b8cc4943089efd390687c47'),
 'preparation03':('financial-genuine-wrapper-claimedrun-source-recovery-preparation03-2026-10-04','MANIFEST01.json','8ae5ecff843ea2bec4960d88ed9314f8cbd06cfe5c32efb11b430079cc0ecf79'),
 'review03':('financial-genuine-wrapper-claimedrun-source-recovery-review03-2026-10-04','MANIFEST01.json','dacd234b5c16579039d0da8d1654b4a982260873904b15bf91fc126507977980'),
}
assert not os.path.lexists(D) and shutil.disk_usage(B).free>=R.FLOOR
for role,(name,leaf,pin)in scopes.items():assert R.digest(R.read(B/name,leaf))==pin
D.mkdir(mode=0o700);(D/'CAPTURE01.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic();records={};pid=os.getpid();ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]
for role,(name,leaf,pin)in scopes.items():
 root=B/name;m=R.scan(root);R.validate(m);a=R.pack(root,m,D/(role+'.tar.gz'));R.put(D/(role+'-manifest.json'),m)
 records[role]={'original_root':str(root),'archive':a,'members':len(m['members']),'regular_bodies':sum(x['kind']=='file'for x in m['members']),'original_seal':{'path':leaf,'sha256':pin}}
 assert shutil.disk_usage(D).free>=R.FLOOR
R.put(D/'CAPTURE01.json',{'status':'ACTUAL_COMPLETE_CLOSED_RECOVERY_SOURCE_AND_REVIEW_BYTE_CAPTURE','records':records,'observed_pid':pid,'observed_start_ticks':ticks,'elapsed_seconds':time.monotonic()-start,'disk_free_after_bytes':shutil.disk_usage(D).free,'original02_accepted_fixed_seven_commit_scope':True,'original01_withheld_preserved_elsewhere':True,'strict03_source_only_accepted':True,'actual_external_recovery':False,'actual_source339_flat':False,'new_claim_or_native':False,'scope':'Complete ordinary byte/mode/path captures of immutable accepted-narrow02, strict03 and all their actual generic boundary/semantic reviewer witnesses. No Source339 restore, numerical authority or generic research claims.'})
print(json.dumps({'roles':len(records),'archives':{k:v['archive']for k,v in records.items()},'observed_pid':pid,'native':False}))
