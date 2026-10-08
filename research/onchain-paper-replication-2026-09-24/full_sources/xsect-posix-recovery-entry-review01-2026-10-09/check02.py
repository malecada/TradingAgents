import ast,hashlib,json,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];A=P.parent/'xsect-posix-recovery-entry01-2026-10-09';raw=(A/'restore.py').read_text();c=json.loads((A/'CONTRACT_DRAFT01.json').read_bytes())
assert hashlib.sha256(raw.encode()).hexdigest()=='f3b1f132a9474c8e3f5df7eb30e885b465bd75e65930a063bfbd634d0da49dad'
added="""    parent = Path(contract['target_root']).parent
    require(parent.resolve(strict=True) == parent and
            parent.stat().st_dev == ROOT.stat().st_dev and
            os.statvfs(parent).f_frsize == contract['allocation_block_bytes'],
            'target filesystem or allocation block differs')
"""
assert raw.count(added)==1
inverse=raw.replace(added,'').replace("        eligibility(contract, remaining)\n        first =", "        first =")
assert hashlib.sha256(inverse.encode()).hexdigest()=='78ca4a2bab44e893efdc6427b5f2f152aee468ff8f083b4950f5e3732aa2c33c'
def require(ok,why):
 if not ok:raise ValueError(why)
t=ast.parse(raw);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='eligibility');code=compile(ast.Module(body=f.body[:2],type_ignores=[]),'actual_fs_seam','exec');env=dict(Path=Path,os=os,ROOT=R,require=require,contract=c);exec(code,env)
wrong=dict(c,allocation_block_bytes=c['allocation_block_bytes']+1)
try:exec(code,dict(env,contract=wrong))
except ValueError as e:assert str(e)=='target filesystem or allocation block differs'
else:raise AssertionError('wrong block accepted')
for ref in c['source_refs'].values():
 q=R/ref['path'];b=q.read_bytes();assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']
parent=Path(c['target_root']).parent
out={'status':'PASS_SOURCE_ONLY','source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'draft_sha256':hashlib.sha256((A/'CONTRACT_DRAFT01.json').read_bytes()).hexdigest(),'literal_inverse_to_prior_reviewed_source':True,'actual_parent_same_device':parent.stat().st_dev==R.stat().st_dev,'actual_parent_block_bytes':os.statvfs(parent).f_frsize,'wrong_block_refused':True,'final_preverification_eligibility_call_added':True,'actual_closure_or_launch_claim':False};(P/'CHECK02.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
