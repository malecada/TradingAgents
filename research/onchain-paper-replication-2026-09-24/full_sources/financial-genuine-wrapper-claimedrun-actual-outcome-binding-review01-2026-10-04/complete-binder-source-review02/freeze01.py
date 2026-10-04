import hashlib,json,os,shutil,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-genuine-wrapper-claimedrun-outcome-binding-preparation02-2026-10-04';W=B/'financial-genuine-wrapper-claimedrun-claim-window-review01-2026-10-04'
def digest(b):return hashlib.sha256(b).hexdigest()
def put(n,o):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(o,sort_keys=True,indent=2)+'\n')
shutil.copytree(P,H/'frozen-preparation02',symlinks=True)
shutil.copytree(W,H/'full-original-window-review01',symlinks=True)
report='''Accepted for the exact source-only binder and window correction. No material blocker was found in the reviewed delta. This is a different-author review of binder b5af0ffe3688144ab6f5f691ad92f188441d90dd620090fca34be5485c60fd4f and complete author MANIFEST02 2241ec9be76510da07c06b8cea389d6f2782e25c1fc6fbeec0237b69e41ac80c. The full author tree and full original claim-window investigation, including raw metadata and witness sources, are copied beneath this review without following lexical links.

Independent check01 completed 348 checks; the supplement completed three further checks. These counts include body/mode inventory checks and are not independent experiments. The original guard rejects actual immutable claim4c54. The corrected exact fragment accepts that same genuine historical metadata, retaining availability and every original window field. Every changed/missing field, extra/duplicate/empty row and schema/binding mutation tested refuses. The two ordered expansion assignments are AST-identical to genuine verify.py lines261–264 after local-name normalization; original and successor produce identical exploratory/exposed and confirmation/spent expected metadata. Ordered prior exposures are compared exactly, so historical exposures are neither dropped nor treated as fresh confirmation. Only expected administrative metadata was evaluated; no future claim or authority was created.

The single added rewrite pair at bind01.py:16 reverses byte-for-byte and by AST to binder01. The full in-memory verifier transformation reverses all seven declared edits to original f662: three bindings, three accounting changes, and the one window correction. Accounting retains prior0, requires effective19 for the future claim, exactly the old failed identity plus new identity, original claim4c54/failed3515 hashes, and absence of original COMPLETE. This does not reopen the checkpointless failure or change its actual ceiling18. All functions/classes outside the narrowly changed verify function retain identical AST, including native failure classification, final empty/subset CPU census, early ready/release requirements and fatal cleanup. Original VF1/VF2 and all earlier evidence remain historical.

Actual Source0a2/gate3a20/338pins/eight inputs/f4ea/251 runtime metadata and actual Parent5d5 draftb108 mappings were joined read-only. bind01.py:27–35 and52–66 require the exact accepted installed Parent, six helper bodies, source/design/identity, genuine proof bytes, final request and accepted release before emission. Both fixed(actual_draft) and genuine Parent.validate_release(actual_draft) refuse. Full recovery and final review remain null in that pinned draft. Pure rewrite was exercised only in memory using an explicitly test-only request hash; no verifier was emitted and no actual outcome was classified.

Remaining prerequisites are genuine final full-recovery evidence, actual Parent final review and RELEASED_ONE_USE request, actual exact binder execution and independent generated-body binding review, then Root's complete caller/review preservation and separate native eligibility/release. No actual recovery, native execution, tensor/checkpoint semantics, resource feasibility, fees/funding, PnL/return convention or financial strategy was tested here. All1,420 paper fits remain outside this source review; this verdict grants no numerical capacity or release. No Source, Parent, gate, ledger or registered identity was changed.
'''
with (H/'REPORT01.md').open('x') as f:f.write(report)
put('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','author_reviewed':'outcome_archive','decision':'ACCEPTED_SOURCE_ONLY_BINDER_AND_WINDOW_CORRECTION','candidate_sha256':digest((P/'bind01.py').read_bytes()),'candidate_manifest_sha256':digest((P/'MANIFEST02.json').read_bytes()),'checks':351,'check01_sha256':digest((H/'READBACK01.json').read_bytes()),'supplement_sha256':digest((H/'SUPPLEMENT01.json').read_bytes()),'actual_source':'0a2e7639b42b9423b90743feadcda4078aa21816','actual_parent_sha256':'5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','actual_draft_sha256':'b1087b980a44fcc4cd920cdcbd472f092ba17223d0a329cbc74b52a8e0236c98','actual_generated_verifier':None,'actual_final_request':None,'actual_full_recovery':None,'outcome_classified':False,'numerical_release':False,'new_claim_created':False,'material_findings':[],'remaining_requirements':['genuine final full recovery and accepted Parent request/release','actual binding and independent generated-body review','complete caller/review preservation and separate native release'],'original_failed_claim_preserved':True})
rows=[]
def scan(root):
 for p in sorted(root.iterdir(),key=lambda x:x.name):
  s=p.lstat();r={'path':p.relative_to(H).as_posix(),'mode':oct(stat.S_IMODE(s.st_mode))}
  if stat.S_ISREG(s.st_mode):raw=p.read_bytes();r.update(kind='file',bytes=len(raw),sha256=digest(raw))
  elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
  else:raise ValueError('unexpected kind')
  rows.append(r)
  if r['kind']=='directory':scan(p)
scan(H);rows.sort(key=lambda x:x['path']);put('MANIFEST01.json',{'schema_version':1,'scope':'complete independent binder02 review; excludes only this manifest','members':rows,'counts':{k:sum(r['kind']==k for r in rows) for k in ('file','directory','symlink')},'member_count':len(rows)})
for n in ('REPORT01.md','VERDICT01.json','READBACK01.json','SUPPLEMENT01.json','MANIFEST01.json'):print(n,digest((H/n).read_bytes()))
print('members',len(rows))
