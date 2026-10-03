import ast,hashlib,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;B=HERE.parent;NEW=B/'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03';OLD=B/'neural-cold-feature-handoff-outcome-retention-preparation01-2026-10-03'
assert hashlib.sha256((NEW/'MANIFEST02.json').read_bytes()).hexdigest()=='65f6ce8d37edb445ac792adb52e61a3d424129094298bb036fd075bf941fe1c0'
m=json.loads((NEW/'MANIFEST02.json').read_bytes());assert len(m['files'])==25
for r in m['files']:
 b=(NEW/r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
sys.path.insert(0,str(NEW));import archive01 as a;import collector01 as c
checks=[]
with tempfile.TemporaryDirectory(dir=HERE) as d:
 r=Path(d);rows=[{'path':'a'}, {'path':'b/'+'/'.join('é'*100 for _ in range(18))}]
 try:a.pages(r/'oversize',rows)
 except ValueError:pass
 else:raise AssertionError('R1 remains')
 assert all(p.stat().st_size<=8192 for p in (r/'oversize').iterdir());checks.append('postflush-oversize-refused-no-oversized-file')
 rows=[{'path':str(i),'payload':'é'*100} for i in range(61)];refs=a.pages(r/'valid',rows);assert [row for ref in refs for row in json.loads(a.read(r/'valid'/ref['path'],8192))]==rows and all(ref['bytes']<=8192 for ref in refs);checks.append('all-valid-rows-complete-encoded-bounds')
 for name in ('keys/public','apis/manifest','.env','hf_token.txt','.env.local'):
  with patch.object(Path,'resolve',side_effect=AssertionError('resolution reached')),patch.object(a.io,'_opened',side_effect=AssertionError('open reached')):
   try:c.reference({'path':str(r/name),'sha256':'1'*64})
   except ValueError:pass
   else:raise AssertionError('R2 remains')
 checks.append('five-protected-paths-refused-before-resolve-or-open')
 cap=r/'cap';cap.mkdir();q={'reservation_roots':{'materialize':{'wrapper':str(r/'wrapper'),'parent':str(r/'parent')}},'wrappers':{'materialize':None},'wrapper_waits':{'materialize':None}}
 assert c.unattempted_observation(q,cap,'materialize')['all_absent']
 paths=c.capsule_authority_paths(cap,'materialize')+list(c.reservation_paths(q,cap,'materialize').values());assert len(paths)==17
 for p in paths:
  p.parent.mkdir(parents=True,exist_ok=True);p.mkdir();assert not c.unattempted_observation(q,cap,'materialize')['all_absent'];p.rmdir()
 # Namespace parent creation itself can conservatively prevent absence; use independent capsule for dangling proof.
 cap2=r/'cap2';cap2.mkdir();(cap2/'proof_outer').mkdir();(cap2/'proof_outer'/c.IDS['materialize']).symlink_to(r/'does-not-exist');assert c.observed_phase(cap2,'materialize',None)['original_lifecycle_observation']=='unclaimed_partial';checks.append('all17-fixed-planned-paths-and-dangling-proof-born')
 q['wrappers']['materialize']=str(r/'different')
 try:c.reservation_paths(q,cap,'materialize')
 except ValueError:pass
 else:raise AssertionError('planned mismatch accepted')
 checks.append('actual-vs-planned-root-mismatch-refused')
allowed={'archive01.py':{'safe_components','direct','relative','pages'},'collector01.py':{'source_context','capsule_authority_paths','reservation_paths','unattempted_observation','observed_phase','retain_unverified','collect'}}
for name,funcs in allowed.items():
 def reduced(p):
  return [ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if not(isinstance(n,ast.FunctionDef) and n.name in funcs) and not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'AUTHORITY_NAMESPACES','COMPACT_NAMESPACES'} for t in n.targets))]
 assert reduced(OLD/name)==reduced(NEW/name),name
for name in ('closed_comparison01.py','owned_io.py','test_retention01.py','test_archive01.py','closed-context-baseline01.py','closed-auth-baseline01.py'):assert (OLD/name).read_bytes()==(NEW/name).read_bytes()
checks.append('wholeAST-outside-declared-changes-and-six-bodies-identical')
assert not any(n.split('.')[0] in {'numpy','torch','pandas','pyarrow','tradingagents'} for n in sys.modules)
result={'status':'PASS-independent-correction-source-checks','checks':checks,'manifest_files':25,'qualification':'Synthetic metadata/tiny files only, no actual collector/main or authority invocation.'};(HERE/'readback02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
