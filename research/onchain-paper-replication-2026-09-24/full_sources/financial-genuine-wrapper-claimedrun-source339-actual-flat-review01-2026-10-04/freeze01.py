import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text())
(O/'REPORT01.md').write_text('''# Complete actual Source339 byte-union acceptance

Accepted complete actual Source339 archival recovery from the separately authenticated external195-body scope. All747 original regular bodies match their current originals, received canonical archive and actual0600 single-link flat files. Metadata completes748 private files and preserves all1,029 original paths/types/modes. No extra or missing flat body exists. The full archive reconstructed from actual flat bodies is byte-identical to b5b6aad2; the complete original Source remains unchanged before and after review.

An independent stdlib loose-Git decoder bounded and authenticated every380 actual recovered object by compressed framing/type/size/OID. It followed the complete seven-commit ancestry (current commit plus six predecessors), independently parsed current339 tracked tree/blob/mode joins and historical649's325-body tree, matched every338 current pin/eight input/194 implementation149 package body, and verified251 runtime RECORD metadata rows are present as metadata only. Exact original claim4c54/failed3515, source=design649,324 original claim source pins/eight inputs and budget18 join recovered historical Git bytes. The original failure remains one global spent identity; no replacement COMPLETE or new claimedrun claim exists. Actual receipt semantic counts match these independent results.

Root's final request differs from the reviewed proposal only by genuine release62606. Original same-exec observation, intent, receiptf9b3a0c7, stdout/empty stderr and terminal bind actual session74472/start e43a2f/completion75eb7a exit0. Original PID458640/start ticks15965707/group/session458637 are currently absent. All four actual disk-floor observations exceed10 GiB. This is actual archival outcome evidence, not a fabricated native or scientific outcome.

The original lower-level archival receipt flags remain unchanged, including research_authority=false, recovered_tree_git_join=false and no POSIX instantiation. This independent report separately verifies semantic Git joins using recovered bytes; it does not rewrite those original fields. Remote scope is bound to original9e6d7dd7 and accepted independent a747c2ad; all unchanged opaque witness archives retain that closed external lineage.

No restore replay, Git repository reconstruction, network, admission, numerical module import, array decode, claim or Source mutation was performed. This proof can serve only the Parent's Source full_recovery role. It does not recover the new Parent/caller/final-review union, installed runtime package bodies or empirical stores; it establishes no runtime numerical API equality, POSIX tree, memory/capacity sufficiency or numerical release. Those predicates remain separate before any empirical work.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'])
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
