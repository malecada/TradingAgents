"""Stdlib-only actual storage code plus exact AST-extracted identity guards."""
import ast,builtins,copy,hashlib,importlib.util,json,sys,tempfile,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SRC=ROOT/'tradingagents/research/onchain_replication'
OLD='eth-paper-real-data-end-to-end-resource-20261005-01'
NEW='eth-paper-real-data-end-to-end-resource-20261006-02'

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

package=types.ModuleType('_identity_proof');package.__path__=[];sys.modules[package.__name__]=package
workflow=load(SRC/'workflow_storage.py','_identity_proof.workflow_storage')
old=load(SRC/'real_pilot_storage.py','_identity_proof.old')
new=load(HERE/'real_pilot_storage.py','_identity_proof.new')

def refused(action):
    try:action()
    except (ValueError,FileNotFoundError):return
    raise AssertionError('expected refusal')

def guard(path,module,identity,*,native=True):
    tree=ast.parse(path.read_text());hits=[]
    for node in ast.walk(tree):
        if not hasattr(node,'body') or not isinstance(node.body,list):continue
        for i,n in enumerate(node.body):
            if isinstance(n,ast.ImportFrom) and n.module is not None and n.module.endswith('real_pilot_storage') and 'EXPERIMENT' in [a.name for a in n.names]:hits.append((n,node.body[i+1]))
    assert len(hits)==1
    imp,check=hits[0]
    assert isinstance(check,(ast.If,ast.Expr)) and 'EXPERIMENT' in ast.unparse(check)
    def restricted_import(name,*args,**kwargs):
        assert name==imp.module
        return module
    def require(value,message):
        if not value:raise ValueError(message)
    env={'__builtins__':dict(vars(builtins),__import__=restricted_import),'ad':types.SimpleNamespace(experiment_id=identity),'p':{'schema_version':2},'native_unit_limits':{} if native else None,'owner_identity':{'experiment':identity},'require':require}
    exec(compile(ast.Module(body=[imp,check],type_ignores=[]),str(path),'exec'),env)
    assert env['EXPERIMENT']==module.EXPERIMENT
    return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'import_line':imp.lineno,'guard_line':check.lineno}

def run():
    a=(SRC/'real_pilot_storage.py').read_bytes();z=(HERE/'real_pilot_storage.py').read_bytes()
    assert a.count(OLD.encode())==1 and z.replace(NEW.encode(),OLD.encode())==a
    # Confirm the already-reviewed fresh ID from public gate metadata.
    gate=json.loads((HERE.parent.parent/'real-data-pilot-final02-2026-10-06/gate01.json').read_bytes())
    assert NEW in gate['experiments']
    checks=[]
    for leaf in ('job.py','resources.py','real_pilot_import_caller.py'):
        path=SRC/leaf
        refused(lambda:guard(path,old,NEW))
        checks.append(guard(path,new,NEW))
        for identity in (OLD,'foreign-pilot'):
            refused(lambda:guard(path,new,identity))
    refused(lambda:guard(SRC/'resources.py',new,NEW,native=False))
    with tempfile.TemporaryDirectory(prefix='identity02-',dir=HERE) as d:
        root=Path(d).resolve();(root/'research_artifacts').mkdir();(root/'research_runs').mkdir();(root/'research_runs/.lock').touch()
        budget={'schema_version':2,'kind':new.KIND,'authority_root':str(root),'experiment':NEW,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/NEW)],'shared_files':[str(root/'research_runs/.lock')],'limits':{'max_allocated_bytes':20*1024**3,'max_logical_bytes':16*1024**3,'max_entries':1000000,'max_depth':64,'max_scan_seconds':5}}
        refused(lambda:old.validate(budget,root));new.validate(budget,root)
        watch=new.WritableUnion(budget,root);assert watch.target==root/'research_runs'/NEW
        assert all(NEW in str(p) and OLD not in str(p) for p in new.residual_paths(root)['training_and_lifecycle'])
        watch.check();watch.target.mkdir();(watch.target/'tiny').write_bytes(b'new')
        # An old closed sibling remains excluded from lifecycle writer accounting.
        past=root/'research_runs'/OLD;past.mkdir();(past/'retained').write_bytes(b'old retained')
        result=watch.check();assert result['logical_file_bytes']==3
        for identity in (OLD,'foreign-pilot'):
            bad=copy.deepcopy(budget);bad['experiment']=identity;refused(lambda:new.validate(bad,root))
        bad=copy.deepcopy(budget);bad['authority_root']=str(root.parent);refused(lambda:new.validate(bad,root))
        bad=copy.deepcopy(budget);bad['roots'][1]=str(root/'research_runs'/OLD);refused(lambda:new.validate(bad,root))
        bad=copy.deepcopy(budget);bad['shared_files']=[];refused(lambda:new.validate(bad,root))
        bad=copy.deepcopy(budget);bad['limits']['max_scan_seconds']=6;refused(lambda:new.validate(bad,root))
        (root/'research_runs/.lock').unlink();refused(watch.check)
    assert not any(k in sys.modules for k in ('tradingagents','numpy','torch','scipy'))
    return {'status':'PASS','actual_storage_old_RED_new_GREEN':True,'source_exact_inverse':True,'three_exact_import_guard_joins':checks,'refusals':['old identity','foreign identity','missing native guard','authority root mismatch','writer root mismatch','missing shared lock declaration','invalid finite limits','missing lock body'],'residual_and_union_target':NEW,'old_sibling_excluded':True,'caps_and_all_other_code_unchanged':True,'runtime_or_native_or_claim_or_network':False,'qualification':'AST guard checks cover exact identity conditions, not full runtime admission.'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
