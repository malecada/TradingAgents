from pathlib import Path
import ast,hashlib,json,types
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];C=F/'real-data-pilot-monitor-lease-diagnostics-candidate01-2026-10-06';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((C/'MANIFEST01.json').read_bytes());assert h(C/'MANIFEST01.json').startswith('5cee83c7')
for name,pin in manifest['files'].items():assert h(C/name)==pin
inv=json.loads((C/'INVERSE01.json').read_bytes());old=(M/inv['baseline']).read_text();new=(C/'resources.py').read_text();assert h(M/inv['baseline'])==inv['before_sha256'] and h(C/'resources.py')==inv['after_sha256']
s=new
for e in reversed(inv['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'])
assert s==old
# Check retained author's five refusal receipts and unchanged successful body, no rerun.
for name in ('stale','future','missing_key','malformed','absent'):
 a=json.loads((C/('old-'+name)/'child_exit.json').read_bytes());b=json.loads((C/('new-'+name)/'child_exit.json').read_bytes());detail=b.pop('lease_rejection');assert a==b and b['exit_code']==125
 assert len(json.dumps(detail,allow_nan=False))<1024
 if name in ('malformed','absent'):assert detail['sampled_monotonic_seconds'] is detail['parsed_monotonic_seconds'] is detail['observed_age_seconds'] is None
assert (C/'old-valid/child_exit.json').read_bytes()==(C/'new-valid/child_exit.json').read_bytes()
# Independently execute just the actual nested predicate at inclusive boundaries
# and nonfinite JSON timestamp. There is no native child or authority fixture.
def predicate(source,body):
 tree=ast.parse(source);child=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_child_legacy');fresh=next(n for n in child.body if isinstance(n,ast.FunctionDef) and n.name=='fresh')
 outer=ast.parse('def probe():\n lease_rejection=None\n result=fresh()\n return result,lease_rejection\n').body[0];outer.body.insert(1,fresh);reads=[];clocks=[]
 class Receipt:
  def __truediv__(self,key):assert key=='live.json';return self
  def read_text(self):reads.append(1);return body
 def now():clocks.append(1);return 100.
 ns={'json':json,'receipt':Receipt(),'time':types.SimpleNamespace(monotonic=now),'lease_seconds':15.}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[outer],type_ignores=[])),'actual-nested-fresh','exec'),ns)
 result=ns['probe']();assert len(reads)==len(clocks)==1;return result
results=[]
for label,body,want in [('age_zero','{"monotonic_seconds":100}',True),('age_limit','{"monotonic_seconds":85}',True),('nan','{"monotonic_seconds":NaN}',False)]:
 a=predicate(old,body);b=predicate(new,body);assert a[0]==b[0]==want
 if want:assert b[1] is None
 else:assert b[1]['category']=='unordered_age' and b[1]['parsed_monotonic_seconds'] is b[1]['observed_age_seconds'] is None and b[1]['sampled_monotonic_seconds']==100.;json.dumps(b[1],allow_nan=False)
 results.append({'case':label,'accepted':b[0],'diagnostic':b[1]})
result={'decision':'pass-source-only','exact_three_edit_inverse':True,'retained_five_refusal_receipts_match_prior_decisions':True,'retained_valid_receipt_byte_identical':True,'independent_predicate_cases':results,'single_read_and_single_clock_sample':True,'no_native_processes_or_authority':True,'candidate_manifest_sha256':h(C/'MANIFEST01.json'),'resources_sha256':h(C/'resources.py')}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
