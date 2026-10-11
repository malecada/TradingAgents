"""One focused missing-recovery followup; syntactic references only, no receipts."""
import ast,copy,hashlib,json,pathlib,types
ROOT=pathlib.Path(__file__).resolve().parents[4];F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent;E=F/'real-data-pilot-full36-entry-preparation01-2026-10-11'
old=(OUT/'PRE_FIX_PREFLIGHT01.py').read_text();current=(E/'preflight36_01.py').read_text()
before="'unbound_archive','budget_review')";after="'unbound_archive','budget_review','complete_increment_recovery','new_increment_recovery_review')"
assert old.count(before)==1 and current==old.replace(before,after,1)
assert hashlib.sha256(current.encode()).hexdigest()=='b00449135a348f5393afef09acadda02bab0cc2c60cf00f5abaa75f92ae72138'
assert ast.dump(ast.parse(current.replace(after,before,1)))==ast.dump(ast.parse(old))
draft=json.loads((E/'BINDING_DRAFT01.json').read_text());assert 'final_review' not in draft and draft['complete_increment_recovery'] is draft['new_increment_recovery_review'] is None
nodes=[n for n in ast.parse(current).body if isinstance(n,ast.FunctionDef) and n.name in {'need','reference','check'}]
called=[]
class BlockedLookup(Exception):pass
def never_run(*a,**k):called.append('blocked_source_lookup');raise BlockedLookup
ns={'Path':pathlib.Path,'ROOT':ROOT,'HERE':E,'NAME':draft['identity'],'GATE':str((E/'gate01.json').relative_to(ROOT)),'json':json,'subprocess':types.SimpleNamespace(check_output=never_run)}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'focused_recovery_prefix','exec'),ns)
base=copy.deepcopy(draft)
# These deliberately nonexistent reference shapes are never read or saved as receipts.
for key in ('binding_review','complete_increment_recovery','new_increment_recovery_review'):base[key]={'path':'synthetic-never-read/'+key+'.json','sha256':'0'*64}
cases=[]
for missing in ('complete_increment_recovery','new_increment_recovery_review'):
    for kind in ('null','absent'):
        b=copy.deepcopy(base)
        if kind=='null':b[missing]=None
        else:del b[missing]
        ns['read_path']=lambda p,b=b:json.dumps(b).encode()
        try:ns['check']()
        except ValueError as error:assert kind=='null' and str(error)=='actual bound reference required'
        except KeyError as error:assert kind=='absent' and error.args==(missing,)
        else:raise AssertionError('missing recovery passed')
        assert called==[];cases.append({'missing':missing,'form':kind,'refused_before_source_lookup':True})
ns['read_path']=lambda p:json.dumps(base).encode()
try:ns['check']()
except BlockedLookup:pass
else:raise AssertionError('unexpected prefix route')
assert called==['blocked_source_lookup']
assert not (E/'BINDING01.json').exists() and not (E/'RELEASE_REVIEW01.json').exists()
gate=json.loads((E/'gate01.json').read_text());experiment=gate['experiments'][draft['identity']]
assert experiment['source_files'][str((E/'preflight36_01.py').relative_to(ROOT))]==hashlib.sha256(current.encode()).hexdigest()
result={'status':'PASS_FOCUSED_CHANGED_FIX_ONLY','source_sha256':hashlib.sha256(current.encode()).hexdigest(),'literal_inverse':True,'ast_inverse':True,'negative_controls':cases,'positive_prefix_ends_at_blocked_lookup':True,'genuine_recovery_bodies_created':False,'admission_called':False,'native_called':False,'claim_called':False,'fixed_source_committed_by_review':False,'release':False,'gate_sha256':hashlib.sha256((E/'gate01.json').read_bytes()).hexdigest()}
with (OUT/'FIX_FOLLOWUP02.json').open('x') as h:json.dump(result,h,indent=2);h.write('\n')
print(json.dumps(result,indent=2))
