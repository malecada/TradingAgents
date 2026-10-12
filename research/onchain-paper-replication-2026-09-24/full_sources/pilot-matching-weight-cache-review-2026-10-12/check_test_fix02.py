from pathlib import Path
import ast,json,hashlib,difflib
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';I=F/'pilot-matching-weight-cache-integration-2026-10-12';D=F/'pilot-matching-weight-cache-review-2026-10-12';J=F/'pilot-matching-cleanup-test-investigation-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(I/'TEST_FIX02.json')=='28135679b3496e0cc36c28ae6b835588e3f6170036d717d6c6c9269042b82f3c'
v=json.loads((I/'TEST_FIX02.json').read_bytes());a=(I/'FINAL_test_compact_mcm.py').read_text();b=(I/'FINAL02_test_compact_mcm.py').read_text()
assert h(I/'FINAL_test_compact_mcm.py')==v['old_test_sha256'] and h(I/'FINAL02_test_compact_mcm.py')==v['candidate_sha256']
x=a
for old,new in v['literal_changes']:
 assert x.count(old)==1;x=x.replace(old,new)
assert x==b
x=b
for old,new in reversed(v['literal_changes']):assert x.count(new)==1;x=x.replace(new,old)
assert x==a
# All preexisting assertions except the three superseded cause/type expectations remain unchanged.
original=ast.parse((I/'BASELINE_test_compact_mcm.py').read_text());final=ast.parse(b)
old_functions={n.name:n for n in original.body if isinstance(n,ast.FunctionDef)};new_functions={n.name:n for n in final.body if isinstance(n,ast.FunctionDef)}
changed={'test_nested_cleanup_uncertainty_remains_fatal_through_producer','test_final_producer_descriptor_close_is_fatal_and_releases_lock','test_fatal_log_terminal_cleanup_cannot_be_downgraded_to_primary_error'}
for name,n in old_functions.items():
 if name not in changed:assert ast.dump(n)==ast.dump(new_functions[name]),name
for name in changed:
 old_assertions=[ast.dump(n) for n in ast.walk(old_functions[name]) if isinstance(n,ast.Assert) and '__cause__' not in ast.unparse(n)]
 new_assertions=[ast.dump(n) for n in ast.walk(new_functions[name]) if isinstance(n,ast.Assert)]
 for assertion in old_assertions:assert assertion in new_assertions,name
fn=new_functions['_assert_cleanup_group'];ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-cleanup-assertion','exec'),ns)
class Fatal(BaseException):pass
primary=RuntimeError('primary');cleanup=OSError('cleanup')
def error(leaves):
 e=Fatal('outer');e.failures=leaves;e.__cause__=BaseExceptionGroup('leaves',leaves);return e
ns['_assert_cleanup_group'](error((primary,cleanup)),primary,cleanup,Fatal)
for leaves in ((RuntimeError('primary'),OSError('cleanup')),(cleanup,primary),(primary,OSError('cleanup'))):
 try:ns['_assert_cleanup_group'](error(leaves),primary,cleanup,Fatal)
 except AssertionError:pass
 else:raise AssertionError('fabricated/reordered leaves accepted')
class WrongFatal(Fatal):pass
e=WrongFatal();e.failures=(primary,cleanup);e.__cause__=BaseExceptionGroup('leaves',e.failures)
try:ns['_assert_cleanup_group'](e,primary,cleanup,Fatal)
except AssertionError:pass
else:raise AssertionError('wrong outer class accepted')
# Separate unchanged production cleanup and exact installed reanchor.
manifest=json.loads((J/'MANIFEST01.json').read_bytes())
for row in manifest['files']:
 if row['path'].startswith('tradingagents/'):assert h(R/row['path'])==row['sha256']
pin=json.loads((I/'PIN_INTEGRATION01.json').read_bytes());assert h(R/pin['target'])==pin['installed_sha256']=='3925510198ea32dd35be55b2a46a45d72e12b239f213f799f026ad06a12b785a'
assert pin['review_sha256']==h(D/'PIN_FIX_REVIEW01.json')
t=json.loads((I/'TEST_FIX01.json').read_bytes())['targets'][1];p=R/t['target'];assert h(p)==t['installed_sha256']
base=(I/'BASELINE_test_batched_continuation.py').read_text();new=(I/'FINAL_test_batched_continuation.py').read_text();assert p.read_text()==new
assert (R/t['diff']).read_text().splitlines(True)[2:]==list(difflib.unified_diff(base.splitlines(True),new.splitlines(True)))[2:]
print(json.dumps({'result':'PASS','literal_inverse':True,'unrelated_test_functions_unchanged':True,'poison_marker_fd_lock_assertions_preserved':True,'actual_helper_rejects_fabricated_reordered_leaves_and_wrong_outer_class':True,'installed_pin_join':True,'cleanup_production_hashes_unchanged':True,'default_v1_v2_constructor_binding_diff_reviewed':True,'numerical_execution':False},indent=2))
