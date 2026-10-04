import sys,json,hashlib,ast,importlib.util
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D));import binding01 as B
n=0
def yes(x):
 global n
 assert x;n+=1
def refuses(f):
 try:f()
 except (ValueError,KeyError,TypeError):yes(True)
 else:raise AssertionError('accepted malformed or missing field')
r={'path':B.PREFIX+'opaque-fixture/a.json','bytes':1,'sha256':'1'*64}
q={'round':'BASELINE',**{k:dict(r,path=B.PREFIX+'opaque-fixture/'+k+'.json') for k in B.COMMON},**{k:None for k in B.FINAL}}
f,rows=B.evidence(q);yes(len(rows)==5);yes(f==B.COMMON)
for k in B.COMMON:
 t=dict(q);t[k]=None;refuses(lambda:B.evidence(t))
for k in B.FINAL:
 t=dict(q);t[k]=r;refuses(lambda:B.evidence(t))
for kind in [None,'FINAL','baseline',True]:
 t=dict(q,round=kind);refuses(lambda:B.evidence(t))
t=dict(q,round='FINAL_SUPPLEMENT');refuses(lambda:B.evidence(t))
for k in B.FINAL:t[k]=dict(r,path=B.PREFIX+'opaque-fixture/'+k+'.json')
t['complete_three_proofs']=[dict(r,path=B.PREFIX+'opaque-fixture/proof'+str(i)) for i in range(3)]
f,rows=B.evidence(t);yes(len(rows)==12)
for k in B.FINAL:
 bad=dict(t);bad[k]=None;refuses(lambda:B.evidence(bad))
for values in [[],[r],[r]*3]:
 bad=dict(t,complete_three_proofs=values);refuses(lambda:B.evidence(bad))
for kind in B.ROUNDS:
 draft=json.loads((D/kind/'REQUEST_DRAFT01.json').read_text());refuses(lambda:B.validate(draft));yes(draft['actual_main_commit'] is None)
# Entire unchanged operational helpers; literal inverse per-round orchestration.
A=D.parent/'financial-wrapper-compatibility-final-bundle-transport-preparation01-2026-10-04'
for p in (A/'utilities').rglob('*'):
 if p.is_file():
  for target in [D,D/'BASELINE',D/'FINAL_SUPPLEMENT']:yes((target/'utilities'/p.relative_to(A/'utilities')).read_bytes()==p.read_bytes())
for kind,suffix in B.ROUNDS.items():
 for name in ['watch01.py','cohort01.py','recover.template01.py']:yes((D/kind/name).read_bytes()==(A/name).read_bytes())
 s=(D/kind/'restore_bundle01.py').read_text().replace('compatibility-'+suffix,'compatibility-final-bundle01').replace(";R.require(q['round']=="+repr(kind)+",'exact installed round')",'').replace(repr('ACCEPTED_EXACT_'+kind+'_BUNDLE_FLAT'),"'ACCEPTED_EXACT_FINAL_BUNDLE_FLAT'").replace(repr(kind+'_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW'),"'FINAL_BUNDLE_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW'")
 yes(s==(A/'restore_bundle01.py').read_text());yes(ast.dump(ast.parse(s))==ast.dump(ast.parse((A/'restore_bundle01.py').read_text())))
 yes((D/kind/'receipt01.py').read_text().replace('compatibility-'+suffix,'compatibility-final-bundle01')==(A/'receipt01.py').read_text())
# Original exact population loops remain; no runtime authority fixture or release is constructed.
for name in ['hexpin','ref','body']:
 def node(p):return ast.dump(next(x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name))
 yes(node(D/'binding01.py')==node(A/'binding01.py'))
print(json.dumps({'checks':n,'metadata_only':True,'actual_network':False,'actual_recovery':False}))
