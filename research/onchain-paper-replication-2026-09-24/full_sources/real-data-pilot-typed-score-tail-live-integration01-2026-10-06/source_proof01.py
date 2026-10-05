"""Candidate-only metadata sealing preparation; no Git or numerical imports."""
from pathlib import Path
import ast,difflib,hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3];F=D.parent;P=Path('tradingagents/research/onchain_replication')
def sha(raw):return hashlib.sha256(raw).hexdigest()
baselines={name:R/P/name for name in ('compact_stage.py','archived_stage.py','archive_owner_operations.py','archive_owner_seal.py','compact_owner.py')}
baselines['archive_dispatch.py']=F/'real-data-pilot-preimport-archive-owner-seam01-2026-10-06/candidate'/P/'archive_dispatch.py'
baselines['mcm_score_stream.py']=F/'real-data-pilot-main-functional-composition02-2026-10-06/candidate'/P/'mcm_score_stream.py'
baselines['typed_tail_binding.py']=F/'real-data-pilot-typed-tail-binding01-2026-10-06/typed_tail_binding.py'
modules=set(baselines)|{'typed_payload_policy.py','typed_payload_operations.py','typed_score_store.py','score_tail_archive.py','score_tail_semantics.py'}
result={};patch=[]
for name in sorted(modules):
 new=(D/name).read_bytes();ast.parse(new);baseline=baselines.get(name);old=None if baseline is None else baseline.read_bytes();edits=[]
 if old is not None:
  a=old.decode().splitlines(True);b=new.decode().splitlines(True)
  for op,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
   if op!='equal':edits.append(dict(new_start=k,new_end=l,old=a[i:j],new=b[k:l]))
  restored=b[:]
  for e in reversed(edits):
   assert restored[e['new_start']:e['new_end']]==e['new'];restored[e['new_start']:e['new_end']]=e['old']
  assert ''.join(restored).encode()==old
  assert ast.dump(ast.parse(''.join(restored)))==ast.dump(ast.parse(old))
 result[name]=dict(target=str(P/name),candidate_sha256=sha(new),bytes=len(new),baseline=None if baseline is None else str(baseline),baseline_sha256=None if old is None else sha(old),literal_inverse=old is not None,edits=edits)
 patch.extend(difflib.unified_diff([] if old is None else old.decode().splitlines(True),new.decode().splitlines(True),fromfile='/dev/null' if old is None else 'a/'+str(P/name),tofile='b/'+str(P/name)))
for name in ('score_tail_archive.py','score_tail_semantics.py'):
 baseline=F/'real-data-pilot-typed-tail-binding01-2026-10-06'/name
 assert (D/name).read_bytes()==baseline.read_bytes();result[name]['unchanged_banked_source']=str(baseline)
(D/'SOURCE_DELTA01.json').write_text(json.dumps(result,indent=2)+'\n');(D/'integration.patch').write_text(''.join(patch))
print(json.dumps({'modules':len(modules),'literal_and_ast_inverses':len(baselines),'unchanged_banked_helpers':2,'numerical_imports':False}))
