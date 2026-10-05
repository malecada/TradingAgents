import ast,copy,hashlib,json
from pathlib import Path
from types import SimpleNamespace
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes'); B=M/'research/onchain-paper-replication-2026-09-24'; D=Path(__file__).parent
S=B/'storage/real-pilot-first-graph-preservation-20261006-01'; P=B/'full_sources/real-data-pilot-first-graph-preservation-review02-2026-10-06'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=(S/'entry02.py').read_text(); b=(S/'entry03.py').read_text()
assert h(S/'entry02.py')=='d30eb6f38bec48fec0b310658839d7b7baf201a795ba7400422bcc0f696ea443'
assert h(S/'entry03.py')=='fc733b766a86c176e6572432e20129b2e584a289c59e673bbad599d14ce54b37'
assert h(S/'envelope03.json')=='0ef52a88eeb3fa07d778c8649f6c85e2d5e770a11117c6787b9964e8c7776484'
newblock="""            if claim.is_symlink() or not claim.is_file() or claim.stat().st_size > 4 * 1024**2:
                raise ValueError('active claim metadata is not bounded regular data')
            program = json.loads(claim.read_bytes()).get('program_id')
            if not isinstance(program, str) or not program:
                raise ValueError('active claim program is unknown')
            if program == 'onchain-paper-replication-2026-09-24':
                raise ValueError('another replication claim is active')"""
assert b.count(newblock)==1
inv=b.replace('envelope03.json','envelope02.json').replace('RELEASE_REVIEW03.json','RELEASE_REVIEW02.json').replace('entry03.py','entry02.py').replace(newblock,"            raise ValueError('another research claim is active')")
assert inv==a
old=json.loads((S/'envelope02.json').read_bytes()); new=json.loads((S/'envelope03.json').read_bytes()); inverse=copy.deepcopy(new)
assert inverse['source_files'].pop(str((S/'entry03.py').relative_to(M)))==h(S/'entry03.py')
inverse['source_files'][str((S/'entry02.py').relative_to(M))]=h(S/'entry02.py'); assert inverse==old
launch=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef) and n.name=='launch')
loop=next(n for n in launch.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='claim')
code=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'actual-claim-loop','exec')
class Claim:
    def __init__(self,raw=b'{}',closed=False,symlink=False,regular=True,size=None): self.raw=raw; self.closed=closed; self.symlink=symlink; self.regular=regular; self.size=len(raw) if size is None else size; self.reads=0
    def with_name(self,name): return SimpleNamespace(exists=lambda:self.closed)
    def is_symlink(self): return self.symlink
    def is_file(self): return self.regular
    def stat(self): return SimpleNamespace(st_size=self.size)
    def read_bytes(self): self.reads+=1; return self.raw
class Root:
    def __init__(self,claims): self.claims=claims
    def __truediv__(self,x): assert x=='research_runs'; return self
    def glob(self,x): assert x=='*/claim.json'; return self.claims
cases=[('replication',Claim(b'{"program_id":"onchain-paper-replication-2026-09-24"}'),True),('unrelated',Claim(b'{"program_id":"strategy-search-2026-09-11"}'),False),('missing',Claim(),True),('empty',Claim(b'{"program_id":""}'),True),('null',Claim(b'{"program_id":null}'),True),('numeric',Claim(b'{"program_id":3}'),True),('malformed-json',Claim(b'{'),True),('nonobject',Claim(b'[]'),True),('symlink',Claim(symlink=True),True),('not-regular',Claim(regular=False),True),('oversize',Claim(size=4*1024**2+1),True),('closed-skipped',Claim(b'{',closed=True),False)]
results=[]
for name,claim,expected in cases:
    refused=False
    try: exec(code,{'ROOT':Root([claim]),'json':json})
    except (ValueError,AttributeError): refused=True
    assert refused==expected,name
    if name in ('symlink','not-regular','oversize','closed-skipped'): assert claim.reads==0
    results.append({'name':name,'refused':refused,'body_reads':claim.reads})
# Fresh metadata observation only; does not run entry or reproduce its network/native checks.
observed=[]
for claim in (M/'research_runs').glob('*/claim.json'):
    if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists(): continue
    assert not claim.is_symlink() and claim.is_file() and claim.stat().st_size<=4*1024**2
    raw=claim.read_bytes(); obj=json.loads(raw); assert isinstance(obj.get('program_id'),str) and obj['program_id']
    observed.append({'path':str(claim.relative_to(M)),'sha256':hashlib.sha256(raw).hexdigest(),'program_id':obj['program_id']})
assert all(row['program_id']!='onchain-paper-replication-2026-09-24' for row in observed)
markers=['preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json']
assert not any((S/n).exists() or (S/n).is_symlink() for n in markers)
assert h(P/'RELEASE_REVIEW02.json')=='77c8012da760007e4638423e5c6364b24bb027d1fbe3f72c32a8d08e2d483da2'
assert h(P/'MANIFEST02.json')=='4e34954dbfa0d9080f911e7c1dc37192560020c7480f39fcffb3fbd9a054c5a8'
for path,sha in new['source_files'].items(): assert h(M/path)==sha,path
result={'decision':'accepted-correction03-source','entry_sha256':h(S/'entry03.py'),'envelope_sha256':h(S/'envelope03.json'),'exact_entry_inverse':True,'exact_envelope_inverse':True,'controls':results,'active_claim_metadata_observed':observed,'markers_absent':markers,'qualification':'Discriminator/regular-size validation only, not independent claim admission; existing global native-unit refusal unchanged. No connection/payload read, native or network action.'}
(D/'CHECK03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True))
