from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;F=H.parent
B=F/'real-data-pilot-may30-ledger-continuation-handoff01-2026-10-06/candidate/graph_ledger_continuation.py'
s=B.read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1;s=s.replace(a,b);edits.append({'before':a,'after':b})
a="def plan_check(p):\n";b=a+"""    if type(p) is dict and p.get('schema_version')==2:
        need(set(p)=={'schema_version','mode','asset','week','end_utc','predecessor','graph_config_input','ledger','recovery_review_input','original_inputs','new_experiment_id','relocation_receipt_input','relocation_review_input'},'exact cross-volume fields')
        need(p['new_experiment_id']=='eth-paper-real-pilot-may30-ledger-continuation-20261006-01','fixed cross-volume identity required')
        roles=[p[k] for k in ('recovery_review_input','relocation_receipt_input','relocation_review_input')]
        need(all(type(r) is str and r and r not in FIXED for r in roles) and len(set(roles))==3,'distinct registered relocation roles required')
        legacy={k:v for k,v in p.items() if k not in ('relocation_receipt_input','relocation_review_input')};legacy['schema_version']=1
        plan_check(legacy)
        return p
""";edit(a,b)
a='def produce(run,plan_input):\n'
b='''DATA_ROOT=Path('/home/malecada/Data')
EXTERNAL=DATA_ROOT/'onchain-pilot-retained-ledgers'/OLD/'ledger.sqlite'
DATA_DEVICE=66307
DATA_RESERVE=64*1024**2

def relocation_metadata(p,receipt_raw,review_raw):
    """Registered independent copy/recovery/retirement proof, never a grant."""
    r=json.loads(receipt_raw);review=json.loads(review_raw)
    need(type(r) is dict and set(r)=={'schema_version','kind','identity','predecessor','original_claim_sha256','original_source','original','target','copy_readback_verified','external_byte_recovery_verified','original_retired','retirement_evidence'},'exact relocation receipt fields')
    need(r['schema_version']==1 and r['kind']=='closed-ledger-cross-volume-relocation' and r['identity']==p['new_experiment_id'] and r['predecessor']==OLD and r['original_claim_sha256']==FIXED['old_claim']['sha256'] and r['original_source']=='14414c1637256dd286eafbe92391129dee3d29bf' and r['original']==p['ledger'],'original relocation ancestry differs')
    t=r['target'];need(type(t) is dict and set(t)=={'path','device','bytes','sha256','stat_identity'},'exact relocated body descriptor')
    need(t['path']==str(EXTERNAL) and t['device']==DATA_DEVICE and t['bytes']==p['ledger']['bytes'] and t['sha256']==p['ledger']['sha256'],'fixed external body differs')
    need(type(t['stat_identity']) is list and len(t['stat_identity'])==7 and all(type(n) is int for n in t['stat_identity']) and t['stat_identity'][0]==DATA_DEVICE and t['stat_identity'][2]==1 and t['stat_identity'][3]==p['ledger']['bytes'],'exact relocated inode/extent required')
    need(r['copy_readback_verified'] is True and r['external_byte_recovery_verified'] is True and r['original_retired'] is True,'verified copy/recovery/retirement required')
    proof=r['retirement_evidence'];need(type(proof) is dict and set(proof)=={'path','sha256'} and type(proof['path']) is str and not Path(proof['path']).is_absolute() and '..' not in Path(proof['path']).parts and type(proof['sha256']) is str and len(proof['sha256'])==64,'retirement evidence reference required')
    need(review.get('decision')=='accepted' and review.get('identity')==p['new_experiment_id'] and review.get('predecessor')==OLD and review.get('relocation_receipt_sha256')==sha(receipt_raw) and review.get('complete_copy_recovery_and_retirement') is True and review.get('evidence',{}).get(proof['path'])==proof['sha256'],'independent complete relocation acceptance required')
    return r

def relocated_path(root,p,read):
    if p['schema_version']==1:return root/LEDGER
    r=relocation_metadata(p,read(p['relocation_receipt_input']),read(p['relocation_review_input']))
    # Consume the independently reviewed retirement body, not just its hash text.
    proof=r['retirement_evidence'];q=root/proof['path']
    need(q.resolve(strict=True)==q and q.is_file() and q.stat().st_nlink==1 and q.stat().st_size<=2*1024**2,'bounded original retirement evidence required')
    need(sha(q.read_bytes())==proof['sha256'],'original retirement evidence bytes differ')
    need(not os.path.lexists(root/LEDGER),'historical original path must be genuinely retired, never linked')
    need(DATA_ROOT.resolve(strict=True)==DATA_ROOT and DATA_ROOT.stat().st_dev==DATA_DEVICE and root.stat().st_dev!=DATA_DEVICE,'fixed distinct Data volume required')
    need(EXTERNAL.resolve(strict=True)==EXTERNAL and set(x.name for x in EXTERNAL.parent.iterdir())=={'ledger.sqlite'},'exact sole external retained body namespace required')
    before=EXTERNAL.lstat();need(stat.S_ISREG(before.st_mode) and list(_sig(before))==r['target']['stat_identity'],'relocated body identity differs')
    from .workflow_storage import StorageWatch
    observation=StorageWatch(root=EXTERNAL.parent,limits={'max_logical_bytes':p['ledger']['bytes']+DATA_RESERVE,'max_allocated_bytes':p['ledger']['bytes']+DATA_RESERVE,'max_entries':2,'max_depth':1,'max_scan_seconds':5}).check()
    need(observation['root_device']==DATA_DEVICE,'retained store census device differs')
    return EXTERNAL

'''+a
edit(a,b)
edit("required_paths=[root],wall_seconds=", "required_paths=[root]+([DATA_ROOT] if p['schema_version']==2 else []),wall_seconds=")
edit("    path=root/LEDGER;before=path.lstat()", "    path=relocated_path(root,p,run.read_input);before=path.lstat()")
edit("        need(file_hash(path)==p['ledger']['sha256'] and _sig(path.lstat())==_sig(before),'original ledger changed during continuation')", "        need(file_hash(path)==p['ledger']['sha256'] and _sig(path.lstat())==_sig(before),'original ledger changed during continuation')\n        need(relocated_path(root,p,run.read_input)==path,'retained location changed during continuation')")
(H/'graph_ledger_continuation.py').write_text(s)
inv={'graph_ledger_continuation.py':{'baseline':str(B),'before_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(s.encode()).hexdigest(),'edits':edits}}
(H/'INVERSE01.json').write_text(json.dumps(inv,indent=2)+'\n')
(H/'graph_ledger_continuation.patch').write_text(''.join(difflib.unified_diff(B.read_text().splitlines(True),s.splitlines(True),fromfile=str(B),tofile='graph_ledger_continuation.py')))
