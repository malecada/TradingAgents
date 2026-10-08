"""Exact authorized startup predicate diff, reused worker tests and own refusals."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json
H=Path(__file__).resolve().parent;R=H.parents[4];D=H.parent.parent/'real-data-pilot-startup-reserve-correction01-2026-10-08';evidence={}
def raw(p):
 b=p.read_bytes();assert p.resolve(strict=True)==p and p.stat().st_size==len(b)<2*1024**2;evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
manifest=read(D/'MANIFEST01.json');assert ref(D/'MANIFEST01.json')['sha256']=='e56deb77c0bdaeefcd6d42b2216de5af72283648f3a1f5f3802567d2ebbd0a50'
for n,v in manifest['files'].items():assert hashlib.sha256(raw(D/n)).hexdigest()==v['sha256'] and len(raw(D/n))==v['bytes']
changes={
'resources.py':[
("if start_reserve_bytes < memory_max_bytes + reserve_bytes:\n        raise ValueError('startup reserve must cover memory.max plus host reserve')", "if start_reserve_bytes < reserve_bytes:\n        raise ValueError('explicit startup reserve must cover host runtime reserve')"),
('minimum_reserve=3*GIB\n','minimum_reserve=3*GIB\n    minimum_start=memory_max_bytes+live[\'reserve_bytes\']\n'),
("minimum_reserve=policy['reserve_bytes']\n", "minimum_reserve=policy['reserve_bytes']\n        minimum_start=policy['start_reserve_bytes']\n"),
("if live['start_reserve_bytes']<memory_max_bytes+live['reserve_bytes']:","if live['start_reserve_bytes']<minimum_start:")],
'job.py':[("or value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']:", "or (not amended and value['start_reserve_bytes'] < value['memory_max_bytes']+value['reserve_bytes']):")],
'real_pilot_import_caller.py':[
("'reserve_bytes':5*GIB//2,'start_reserve_bytes':17*GIB//2,", "'reserve_bytes':5*GIB//2,"),
("return (all(type(p.get(k)) is int and p[k]==v for k,v in expected.items())\n", "return (all(type(p.get(k)) is int and p[k]==v for k,v in expected.items())\n            and type(p.get('start_reserve_bytes')) is int\n            and p['start_reserve_bytes'] in (5*GIB//2,17*GIB//2)\n"),
("and p['start_reserve_bytes']>=p['memory_max_bytes']+p['reserve_bytes'],", "and (p['start_reserve_bytes']>=p['memory_max_bytes']+p['reserve_bytes'] or _amended_host_reserve(p)),")]
}
for name,edits in changes.items():
 before=raw(D/'baseline'/name);after=raw(D/name);assert raw(R/'tradingagents/research/onchain_replication'/name)==before
 expected=before.decode()
 for old,new in edits:assert expected.count(old)==1;expected=expected.replace(old,new)
 assert expected.encode()==after
 inverse=after.decode()
 for old,new in reversed(edits):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
 assert inverse.encode()==before;compile(after,str(D/name),'exec')
 b=ast.parse(before);a=ast.parse(after);assert len(a.body)==len(b.body)
 for x,y in zip(b.body,a.body):
  if ast.dump(x)!=ast.dump(y):assert isinstance(x,ast.FunctionDef) and isinstance(y,ast.FunctionDef) and x.name==y.name and ast.dump(x.args)==ast.dump(y.args)
# Both exact patch documents are independent byte reconstructions.
for filename,reverse in [('FORWARD01.patch',False),('INVERSE01.patch',True)]:
 body=''
 for name in changes:
  a=raw(D/'baseline'/name).decode();b=raw(D/name).decode();target='tradingagents/research/onchain_replication/'+name
  if reverse:a,b=b,a
  body+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+target,tofile='b/'+target))
 assert body.encode()==raw(D/filename)
assert '24 passed' in raw(D/'GREEN02.log').decode()
assert '18 passed' in raw(H/'BOUNDARIES01.stdout').decode() and raw(H/'BOUNDARIES01.stderr')==b''
for n in ['run_boundaries01.py','test_boundaries01.py','review01.py']:raw(H/n)
source_refs={n:ref(D/n) for n in changes}
result={'schema_version':1,'decision':'accepted-source-adoption-only','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_candidates':source_refs,'manifest':ref(D/'MANIFEST01.json'),'evidence':dict(sorted(evidence.items())),
'authorized_new_startup_bytes':2684354560,'prior_startup_bytes_retained':9126805504,'runtime_reserve_bytes_unchanged':2684354560,'memory_max_bytes_unchanged':6442450944,'memory_high_bytes_unchanged':5368709120,'swap_bytes_unchanged':0,'disk_floor_bytes_unchanged':10737418240,
'exact_forward_inverse':True,'all_signatures_defaults_unchanged':True,'outside_enumerated_predicates_byte_identical':True,'worker24_focused_tests_reused':True,'independent18_authentication_cases_passed':True,
'independent_checks':['For both exact2.5GiB and retained8.5GiB tuples, refuse wrong owner source, wrong owner experiment, live/admitted startup mismatch, runtime reserve mismatch and nonzero swap','For both tuples, genuine synthetic non-ready Admission cannot authorize amended resource policy','For both tuples, neighboring cap/high/disk tuples do not acquire amended authority'],
'authority':'Generic guarded_run now deliberately allows an explicit startup>=runtime reserve; omitted startup remains cap+reserve. Authenticated job and worker routes allow the lower sum-floor exception only for the exact2.5runtime reserve/6cap5high/10floor/schema2 tuple with startup2.5 or8.5, ready original Admission and matching hash-authenticated execution/plan/live-owner/source. Legacy job/worker minimum remains cap+reserve.',
'qualification':'Accept only the three exact source files for the explicit user-authorized startup amendment. Full native containment, FSIZE/CPU/wall/swap, host runtime-reserve kill, disk enforcement, source/input authentication and scientific algorithms remain unchanged. Worker original entry/setup/runtime pressure refusals and default/legacy cases reused; independent18 cases target authentication equality at the changed branch. No real native unit/claim/Owner/scientific input or numerical import was executed. New registered configuration and exact entry release must join the approved tuple before any launch.',
'not_tested':['No original full preflight/admission replay, private transport/runtime or scientific body reads, numerical execution, new host-memory measurements or capacity proof.','Current available RAM and future successful startup remain unproved by synthetic predicates.','Proposed90 accounting reviews and import/strict19 source acceptances remain separate immutable evidence; this review alone does not release19.']}
out=H/'SOURCE_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':result['decision'],'review':ref(out)}))
