import ast,hashlib,json,sys,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import byte_bridge01 as B
checks=[]
def check(v,n):
    if not v:raise AssertionError(n)
    checks.append(n)
def refuse(fn,n):
    try:fn()
    except ValueError:checks.append(n);return
    raise AssertionError(n)
B.original_cardinality({'sample_count':512,'motif_count':32});check(True,'exact original spent512/motifs32')
for key in ('sample_count','motif_count'):
    for value in (None,True,False,0,1,31,33,511,513,'512'):
        d={'sample_count':512,'motif_count':32};d[key]=value
        refuse(lambda:B.original_cardinality(d),'cardinality refuses '+key+' '+repr(value))
old=ast.parse((P/'byte_bridge01.draft02.py').read_bytes());new=ast.parse((P/'byte_bridge01.py').read_bytes())
changed={'original_cardinality','_authority','_snapshot'}
for node in old.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name not in changed:
        n=next(n for n in new.body if getattr(n,'name',None)==node.name)
        check(ast.dump(node,include_attributes=False)==ast.dump(n,include_attributes=False),'previous utility/IO controls exact AST '+node.name)
for name,extra in [('held_score_consumer','encode_codec_held'),('completed_f32','encode_codec_completed')]:
    a=(P/(name+'.original.py')).read_bytes();b=(P/(name+'.py')).read_bytes();check(b.startswith(a),'literal full original inverse '+name)
    tree=ast.parse(b);check(tree.body[-1].name==extra,'only explicit new source entrypoint '+name)
    check(ast.dump(ast.parse(a),include_attributes=False)==ast.dump(ast.Module(body=tree.body[:-1],type_ignores=[]),include_attributes=False),'all inherited original AST unchanged '+name)
    check(b[:len(a)]==a,'byte inverse '+name)
for draft in ('byte_bridge01.draft01.py','byte_bridge01.draft02.py'):
    (P/(draft+'.patch')).write_text(''.join(difflib.unified_diff((P/draft).read_text().splitlines(True),(P/'byte_bridge01.py').read_text().splitlines(True),fromfile=draft,tofile='byte_bridge01.py')))
SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source/tradingagents/research/onchain_replication')
api={}
for name in ('original_import_preparation.py','original_dictionary.py','original_import_stage.py','compact_mcm_publication.py'):
    path=SRC/name;raw=path.read_bytes();ast.parse(raw);api[name]={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'source':raw.decode()}
check("p['sample_count']<=512" in api['original_dictionary.py']['source'],'original ceiling differs from bridge exact512 requirement')
check('self._input=input_name' in api['original_import_preparation.py']['source'] and 'self._cap=cap' in api['original_import_preparation.py']['source'],'actual prepared policy access')
check("receipt.json" in api['compact_mcm_publication.py']['source'],'actual raw publication receipt member')
for name,obj in [('API_SOURCE_READBACK01.json',api),('CHECKS03.json',{'count':len(checks),'checks':checks,'candidate_sha256':hashlib.sha256((P/'byte_bridge01.py').read_bytes()).hexdigest(),'genuine_execution':None})]:
    with (P/name).open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'candidate_sha256':hashlib.sha256((P/'byte_bridge01.py').read_bytes()).hexdigest()}))
