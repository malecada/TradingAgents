"""Source-only exact diagnostic guard; no import of target or authority."""
import ast,hashlib,json,pathlib,stat
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
old=BASE/'held-consumer-canonical-successor-preparation01-2026-10-03/original_dictionary.py'
before=old.read_bytes();H=lambda b:hashlib.sha256(b).hexdigest()
assert H(before)=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88'
red=json.loads((HERE/'RED01.json').read_bytes());assert red['failures']==1 and red['errors']==0 and not red['passed']
needle="                else:primary.add_note('post-callback evidence/authority check failed: '+type(error).__name__)\n"
replacement="""                else:
                    # Diagnostic failure participates after the selected error;
                    # it must never replace an earlier actual fatal.
                    try:primary.add_note('post-callback evidence/authority check failed: '+type(error).__name__)
                    except BaseException as diagnostic:
                        if fatal(diagnostic) and not fatal(primary):primary=diagnostic
"""
text=before.decode();assert text.count(needle)==1;after=text.replace(needle,replacement).encode()
assert after.decode().count(replacement)==1 and after.decode().replace(replacement,needle).encode()==before
for name,body in [('baseline93c.py',before),('original_dictionary.py',after)]:
 with (HERE/name).open('xb') as f:f.write(body)
inverse={'schema_version':1,'before_sha256':H(before),'after_sha256':H(after),'old_text':needle,'new_text':replacement,'full_byte_inverse':True}
original=ast.parse(before);candidate=ast.parse(after)
def method(tree):
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImportedOriginal')
 return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='with_evidence')
om,nm=method(original),method(candidate)
oi=next(n for n in ast.walk(om) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None')
ni=next(n for n in ast.walk(nm) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None')
# Restore only the else-suite of the existing elif, not the entire method.
assert isinstance(oi.orelse[0],ast.If) and isinstance(ni.orelse[0],ast.If)
ni.orelse[0].orelse=oi.orelse[0].orelse
assert ast.dump(candidate,include_attributes=False)==ast.dump(original,include_attributes=False)
inverse['whole_other_AST_inverse']=True
with (HERE/'INVERSE01.json').open('x') as f:json.dump(inverse,f,sort_keys=True,indent=2);f.write('\n')
refs=[old,BASE/'held-consumer-canonical-successor-preparation01-2026-10-03/baseline.py',BASE/'held-consumer-canonical-successor-preparation01-2026-10-03/MANIFEST01.json',BASE/'held-consumer-canonical-successor-review01-2026-10-03/REVIEW01.md',BASE/'held-consumer-canonical-successor-review01-2026-10-03/LIMITATIONS01.json',BASE/'held-consumer-canonical-successor-review01-2026-10-03/MANIFEST01.json',pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source/tradingagents/research/onchain_replication/owned_io.py')]
rows=[]
for p in refs:
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
 b=p.read_bytes();rows.append({'path':str(p),'bytes':len(b),'sha256':H(b),'mode':stat.S_IMODE(s.st_mode)})
with (HERE/'ORIGINS01.json').open('x') as f:json.dump({'schema_version':1,'source_only':True,'references':rows},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'source_sha256':H(after),'full_byte_and_other_AST_inverse':True}))
