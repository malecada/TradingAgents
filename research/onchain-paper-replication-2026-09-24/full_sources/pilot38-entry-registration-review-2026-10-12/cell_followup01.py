"""Exact cell identity correction only, without importing the admission route."""
import ast, copy, difflib, hashlib, json, re
from pathlib import Path
from types import SimpleNamespace
from check01 import ROOT,HERE,F,NEW,NAME,load,sha,pin,refcheck

prior=load(HERE/'ENTRY_REGISTRATION_REVIEW01.json')['evidence']
text=(NEW/'CELL_ID_CORRECTION_INVERSE01.diff').read_text();lines=text.splitlines(True);i=0;restored={}
while i<len(lines):
    assert lines[i].startswith('--- ')
    name=lines[i][4:].strip().removesuffix('.before').removesuffix('.after');i+=2
    body=(NEW/name).read_text().splitlines(True);out=[];pos=0
    while i<len(lines) and not lines[i].startswith('--- '):
        m=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',lines[i]);assert m
        start=int(m[1])-1;out.extend(body[pos:start]);pos=start;i+=1
        while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
            line=lines[i];i+=1
            if line[0] in ' -':assert body[pos]==line[1:];pos+=1
            if line[0] in ' +':out.append(line[1:])
    out.extend(body[pos:]);raw=''.join(out)
    assert hashlib.sha256(raw.encode()).hexdigest()==prior[str((NEW/name).relative_to(ROOT))]
    restored[name]=json.loads(raw)
gate=load(NEW/'gate01.json');before=restored['gate01.json'];e=gate['experiments'][NAME]
job=load(ROOT/e['inputs']['execution_job']['path']);selected=next(iter(job['payload']['representation_jobs'].values()))
pilot=load(ROOT/e['inputs'][selected['real_pilot_input']]['path']);assert e['cells']==[pilot['cell_id']]==['real-eth-first-graph-entry-preparation-resource38']
helper=(NEW/'prepare_entry01.py').read_text()
addition="    selected=next(iter(job['payload']['representation_jobs'].values()))\n    experiment['cells']=[load(ROOT/inputs[selected['real_pilot_input']]['path'])['cell_id']]\n"
assert helper.count(addition)==1;oldhelper=helper.replace(addition,'')
assert hashlib.sha256(oldhelper.encode()).hexdigest()==prior[str((NEW/'prepare_entry01.py').relative_to(ROOT))]
assert (NEW/'CELL_ID_GENERATOR_CORRECTION01.diff').read_text()==''.join(difflib.unified_diff(oldhelper.splitlines(True),helper.splitlines(True),fromfile='prepare_entry01.before',tofile='prepare_entry01.after'))
oldast=ast.parse(oldhelper);newast=ast.parse(helper);main=next(n for n in newast.body if isinstance(n,ast.FunctionDef) and n.name=='main')
insertion=ast.parse(addition.strip().replace('\n    ','\n')).body
indices=[i for i,n in enumerate(main.body) if ast.dump(n)==ast.dump(insertion[0])];assert len(indices)==1
i=indices[0];assert ast.dump(main.body[i+1])==ast.dump(insertion[1]);del main.body[i:i+2]
assert ast.dump(oldast)==ast.dump(newast)
ref=str((NEW/'prepare_entry01.py').relative_to(ROOT));assert e['source_files'][ref]==sha(NEW/'prepare_entry01.py')
inverse=copy.deepcopy(gate);inverse['experiments'][NAME]['cells']=before['experiments'][NAME]['cells'];inverse['experiments'][NAME]['source_files'][ref]=before['experiments'][NAME]['source_files'][ref]
assert inverse==before
binding=load(NEW/'BINDING_DRAFT01.json');oldbinding=restored['BINDING_DRAFT01.json'];refcheck(binding['gate']);oldbinding['gate']=binding['gate'];assert binding==oldbinding
reg=load(NEW/'REGISTRATION_DRAFT01.json');oldreg=restored['REGISTRATION_DRAFT01.json'];refcheck(reg['new_gate']);oldreg.update(new_gate=reg['new_gate'],fresh_registered_cell_identity=e['cells']);assert reg==oldreg
for name in ('binding_review','complete_increment_recovery','new_increment_recovery_review','prior_preservation_complete','prior_recovery_review'):assert binding[name] is None
# Execute only the actual plain boolean expression that rejected Root's metadata check.
source=ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py';tree=ast.parse(source.read_text())
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='separate one-cell resource pilot admission required'];assert len(calls)==1
expr=compile(ast.Expression(calls[0].args[0]),str(source),'eval')
family={'mechanism_id':'celik-sefer-transaction-graph-full-neural-replication'}
assert eval(expr,{'ad':SimpleNamespace(family=family,experiment=before['experiments'][NAME]),'p':pilot}) is False
assert eval(expr,{'ad':SimpleNamespace(family=family,experiment=e),'p':pilot}) is True
changed={str((NEW/n).relative_to(ROOT)) for n in ('gate01.json','BINDING_DRAFT01.json','REGISTRATION_DRAFT01.json','prepare_entry01.py')}
for path,digest in prior.items():
    if str(NEW.relative_to(ROOT))+'/' in path and path not in changed:assert sha(ROOT/path)==digest,path
result={'decision':'accepted','scope':'Corrected cell identity/source/dependent draft reference delta only; no release','predicate_before':False,'predicate_after':True,'original_metadata_and_generator_hashes_restored':True,'literal_and_ast_generator_inverse':True,'unchanged_prior_experiments_and_scientific_native_configuration':True,'recovery_and_release_pending':True,'snapshot':[pin(NEW/n) for n in ('gate01.json','BINDING_DRAFT01.json','REGISTRATION_DRAFT01.json','prepare_entry01.py','CELL_ID_CORRECTION01.json','CELL_ID_CORRECTION01.diff','CELL_ID_CORRECTION_INVERSE01.diff','CELL_ID_GENERATOR_CORRECTION01.diff')],'predicate_source':pin(source)}
print(json.dumps(result,indent=2,sort_keys=True))
