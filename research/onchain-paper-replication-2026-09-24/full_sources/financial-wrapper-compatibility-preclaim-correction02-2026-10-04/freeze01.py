from pathlib import Path
import hashlib,json,os,stat
P=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-preclaim-correction02-2026-10-04');F=P.parent;A=F/'financial-wrapper-compatibility-preclaim-source01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
assert not (P/'MANIFEST01.json').exists()
counts=[]
for k in (1,2,5):
 a=json.loads((P/f'CHECKS{k:02d}.json').read_bytes());assert all(r['passed'] for r in a['rows']);assert (P/f'CHECK{k:02d}.err').read_bytes()==b'';counts.append(a['count'])
assert counts==[136,214,53]
assert sha((P/'preclaim01.py').read_bytes())=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'
assert sha((P/'ORIGINAL_preclaim01.py').read_bytes())=='24b6c2a51759bf992fb0da479f46ba6d582b0e24f1c5c40c5055a34f859de71e'
(P/'INTERFACE01.md').write_bytes((A/'INTERFACE01.md').read_bytes()+b'\nSuccessor02 qualification: Reader.finish rehashes every cached body, closes every actual read descriptor, then performs one finite final canonical-path/type/dev/inode/mode/nlink/size/mtime/ctime sample for every cached path. Each signature must equal the last exact verified byte sample recorded before descriptor cleanup. This rejects the observed PC1 later-close mutation; it establishes sampled currentness only, with no writer exclusion, atomicity or ABA guarantee. All exact entry/source/policy/role/Parent joins and caps remain unchanged. This helper is not installed or released.\n')
(P/'REPORT01.md').write_text('''Successor02 is ready for independent source review. Only Reader.__init__, _physical and finish change by three exact literal edits; the full inverse returns original source24b6c2a. The final metadata join occurs after all actual measurement descriptor cleanup and compares each path against its last verified byte-read signature. Original public class/role/source/policy/history/proof/Parent predicates and fixed4MiB/8MiB/120s bounds remain unchanged. No scientific or installed source, gate, registration, Parent or spent identity changed.

The original350 source/opaque controls passed against the successor, including actual original FAILED claim and checkpoint metadata through genuine read-only verify_claim, all195 current source readbacks, missing recovery/COMPLETE refusals and24 real nested first-fatal/secondary-close matrices.53 additional controls reproduce five actual later-cleanup mutations: bytes with explicit mtime advance, mode, inode replacement, lexical symlink and disappearance. Each original returns while current evidence is stale; the successor refuses. Both original and successor retain the original final deadline refusal. Intact two-file reads pass and every acquired descriptor closes. All bodies remain opaque; no Admission, Run, Owner, future recovery or COMPLETE authority was synthesized.

Two Root check harness failures are retained. CHECK03 incorrectly required descriptor numbers to remain unique across sequential reads, although the OS can reuse already-closed numbers. CHECK04 incorrectly expected the original to accept an expired final deadline; it already has a final tick. Separately named CHECK05 corrected only these harness expectations and passed. Both prior scripts, errors, partial rows and owned files remain immutable.

This is a finite sampled metadata rejoin, not continuous writer exclusion or an atomic launch. Metadata ABA and changes after a path sample remain outside the claim. The own byte budget does not cover original verify_claim internal source transport. Actual full public-entry success, whole Parent capacity, installed currentness, complete external recovery, a genuine final registration/admission/caller and one-use release remain absent. No numerical package was imported, checkpoint decoded, claim spent or original source01 disposition erased.
''')
put('MACHINE01.json',{'schema_version':1,'decision':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW','source_sha256':sha((P/'preclaim01.py').read_bytes()),'original_source_sha256':sha((P/'ORIGINAL_preclaim01.py').read_bytes()),'original_review_machine_sha256':sha((P/'ORIGINAL_PC1_MACHINE01.json').read_bytes()),'original_PC1_witness_sha256':sha((P/'ORIGINAL_PC1_WITNESS01.json').read_bytes()),'complete_literal_inverse_sha256':sha((P/'SOURCE_INVERSE01.json').read_bytes()),'checks':{'original_replay':350,'additional':53,'total':403,'actual_late_cleanup_RED_GREEN_pairs':5,'unchanged_deadline_both_refuse':True,'real_FD_matrices':24},'public_entry_genuine_success_tested':False,'actual_recovery_proof':None,'actual_final_parent_release':None,'source_adopted':False,'genuine_claim_or_num':False,'caps':{'file':4194304,'own_total':8388608,'sampled_seconds':120},'preserved_harness_failures':['CHECK03.err','CHECK04.err'],'limitations':['Finite sampled metadata rejoin only; no writer exclusion, atomicity or ABA guarantee.','Original verify_claim read transport remains outside own counter.','No future authority or successful genuine public entry is fabricated.'],'report_sha256':sha((P/'REPORT01.md').read_bytes())})
rows=[];exclude={'MANIFEST01.json','FREEZE01.out','FREEZE01.err'}
for root,dirs,files in os.walk(P,followlinks=False):
 for n in dirs+files:
  p=Path(root)/n;rel=p.relative_to(P).as_posix()
  if rel in exclude:continue
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode),'links':s.st_nlink}
  if stat.S_ISREG(s.st_mode):assert s.st_size<=4194304;r.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
  elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
  else:raise AssertionError(rel)
  rows.append(r)
rows.sort(key=lambda r:r['path']);put('MANIFEST01.json',{'schema_version':1,'status':'SOURCE_ONLY_READY_FOR_INDEPENDENT_REVIEW','excluded':sorted(exclude),'members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows)})
print(json.dumps({n:sha((P/n).read_bytes()) for n in ('MANIFEST01.json','MACHINE01.json','REPORT01.md')}));print('members',len(rows))
