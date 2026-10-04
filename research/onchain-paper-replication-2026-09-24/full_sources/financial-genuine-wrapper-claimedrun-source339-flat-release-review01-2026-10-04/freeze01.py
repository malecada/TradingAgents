import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# Exact Source339 flat request release

Accepted only the original proposal3e56dfac for the fixed installed Source339 flat namespace, actual remote02 receipt9e6d7dd7 and genuine independent actual-remote review6dcb03cf. RELEASE01.json is the genuine reviewer-authored five-field contract required by the unchanged validate_request. It excludes only the release reference from request hashing. Root's original proposal remains null and unchanged; no adapter run, restore or Root namespace reservation was performed by this review.

All six installed helper/pin bodies match accepted strict03 preparation; source review manifestdacd234b independently qualifies strict1,024 ancestry states and preserves prior fixed-scope/generic-bound findings. Actual received archive/manifest/capture pins join the195-body remote receipt and accepted actual-remote proof. The whole current Source remains identical to the captured1,029-member/747-body manifest. A fresh observed disk floor exceeds10 GiB; this is not a future continuous-capacity guarantee.

The original null proposal and missing fields refuse. Noncanonical manifest tails, altered capture cardinality/spent-history/native/Parent scope fields and wrong remote receipt hashes refuse in pure source checks. After authenticating all prerequisites, the real review release is accepted by the original pure validator; source, remote root/receipt, review and release-reference tampering refuse. No fake valid release, Claim, Owner, Binding or Run was constructed. Full source restoration and Git ancestry decoding remain the next actual operation, not outcomes of these controls.

The adapter requires full747 flat regular bodies plus metadata748 private files; authenticates original1,029 modes/names, current Git339/selected338/eight roles,194 implementation149 package,251 runtime RECORD metadata and original failed claim/hash/absence of replacement or new claim. Accepted bounded Git helper walks actual recovered ancestry and joins the original genuine claim; a successful actual seven-commit result remains to be observed and reviewed. Metadata modes do not instantiate an original POSIX/Git tree. Installed runtime bodies, empirical stores, final Parent/caller/review recovery, resource capacity and numerical eligibility remain excluded.

Root may bind only this real release into a separately retained final request and perform one fresh fixed flat operation. Any original failure/partial namespace must be preserved and cannot be replayed. The actual result must receive independent full-body/ancestry/outcome review before any later empirical work.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['RELEASE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
