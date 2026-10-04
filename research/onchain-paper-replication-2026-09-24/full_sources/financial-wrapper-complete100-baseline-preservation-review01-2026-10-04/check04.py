from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent;F=D.parent;C=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';ROOT=F.parents[2];checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
p=C/'ORIGINAL_ROOT_RECEIPT_MODES01.json';raw=p.read_bytes();q=json.loads(raw);old=json.loads((D/'MODE_FINDING01.json').read_bytes())['rows']
ok(sha(raw)=='17b9baf9e9a37c3b98943e7c9d46ffa85d2771eb8d7bd7cc76530017372450da','exact additive mode sidecar')
ok(q['capture_sha256']==sha((C/'CAPTURE01.json').read_bytes())=='7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176','original capture unchanged')
ok(len(q['members'])==len(old)==7,'seven modes exact complete')
for row,original in zip(q['members'],old):
 a=Path(row['original_absolute_path']);b=C/'support-snapshot'/row['support_snapshot_path']
 ok(str(a)==original['original']and str(b)==original['snapshot']and a.resolve()==a,'exact original canonical path mapping')
 ok(stat.S_IMODE(a.stat().st_mode)==row['original_current_mode']==original['original_mode']==0o664,'original0664')
 ok(stat.S_IMODE(b.stat().st_mode)==row['captured_private_mode']==original['snapshot_archive_mode']==0o600,'actual private0600')
 ok(a.read_bytes()==b.read_bytes()and sha(a.read_bytes())==row['sha256']==original['sha256']and len(a.read_bytes())==row['bytes']==original['bytes'],'original opaque byte equality')
first=json.loads((C/'REQUIRED_BODIES01.json').read_bytes());second=json.loads((C/'REQUIRED_BODIES02.json').read_bytes());new=str(p.relative_to(ROOT))
ok(len(first)==16 and len(second)==17 and set(second)-set(first)=={new}and all(second[k]==v for k,v in first.items()),'exact17 body successor adds only sidecar')
for name,row in second.items():
 b=(ROOT/name).read_bytes();ok(len(b)==row['bytes']<=4*1024**2 and sha(b)==row['sha256'],'actual required body '+name)
cap=json.loads((C/'CAPTURE01.json').read_bytes());ok(all(v['free_bytes']>=10*1024**3 for v in cap['disk_floor_observations']),'all recorded disk floors >=10GiB')
result={'checks':len(checks),'checks_detail':checks,'mode_sidecar_sha256':sha(raw),'required02_sha256':sha((C/'REQUIRED_BODIES02.json').read_bytes()),'required02_count':len(second),'required02_bytes':sum(v['bytes']for v in second.values()),'scope':'local original-byte preservation with explicit0664-to0600 mode metadata mapping; no POSIX restoration or actual external proof'}
(D/'READBACK04.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
