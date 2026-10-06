"""Synthetic metadata only; extract actual candidate helpers, no graph/model inputs."""
import ast
import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
source=(HERE/'candidate/real_pilot_import_caller.py').read_text()
tree=ast.parse(source)
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'require','_read','_archive_namespace'}]
assert len(selected)==3
scope={'__package__':'tradingagents.research.onchain_replication','hashlib':hashlib,'json':json,'FILE_MAX':4*1024**2}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(HERE/'candidate/real_pilot_import_caller.py'),'exec'),scope)
check=scope['_archive_namespace']
cases=[]
with tempfile.TemporaryDirectory(dir=HERE,prefix='synthetic-') as tmp:
    root=Path(tmp)
    ad=SimpleNamespace(root=root,experiment_id='eth-paper-real-data-end-to-end-resource-20261006-05',inputs={})
    s={'compact_archive_transport_input':'transport','compact_archive_input':'archive'}
    p={'schema_version':2,'archive_inputs':{'transport_input':'transport','policy_input':'archive'}}
    def fixture(transport='ethpilot-20261006-05',remote='ethpilot-20261006-05'):
        for name,value in [('transport',{'namespace':transport}),('archive',{'remote_namespace':remote})]:
            raw=json.dumps(value).encode(); (root/(name+'.json')).write_bytes(raw)
            ad.inputs[name]={'path':name+'.json','sha256':hashlib.sha256(raw).hexdigest()}
    def refused(name):
        try:check(ad,s,p,fresh=True)
        except ValueError:cases.append(name)
        else:raise AssertionError(name+' accepted')
    fixture(); check(ad,s,p,fresh=True);cases.append('fresh05 passes')
    fixture('ethpilot-20261006-02','ethpilot-20261006-02');refused('stale02 refuses for fixed05')
    fixture(remote='ethpilot-20261006-04');refused('transport remote mismatch refuses')
    fixture(); (root/'transport.json').write_text('{}');refused('transport hash substitution refuses')
    fixture(); parent=root/'research_artifacts';parent.mkdir()
    reserved=parent/'archive-dispatch-ethpilot-20261006-05';reserved.mkdir()
    refused('reserved directory refuses')
    check(ad,s,p);cases.append('later admission retains own context')
    reserved.rmdir();reserved.symlink_to(parent/'absent')
    refused('dangling symlink refuses');reserved.unlink()
    for legacy in ({'schema_version':1},{'schema_version':2}):
        check(SimpleNamespace(),{},legacy,fresh=True)
    cases.append('legacy and absent archive unchanged')
# Execute the candidate's actual compact-resource routing branch with stand-ins.
job_tree=ast.parse((HERE/'candidate/job.py').read_text())
entry=next(n for n in job_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_admitted')
branch=next(n for n in entry.body if isinstance(n,ast.If) and ast.unparse(n.test)=="job['kind'] == 'compact_resource'")
assert isinstance(branch.body[0],ast.ImportFrom)
branch.body=branch.body[1:]
for selected in (True,False):
    calls=[]
    pilot=SimpleNamespace(selected=lambda job:selected,admitted=lambda *a,**kw:calls.append(('pilot',kw)))
    fixture_route=SimpleNamespace(admitted=lambda *a,**kw:calls.append(('fixture',kw)))
    exec(compile(ast.Module(body=[branch],type_ignores=[]),'actual-entry-branch','exec'),
         {'real_pilot_import_caller':pilot,'resource_fixture':fixture_route,'admitted':object(),'job':{'kind':'compact_resource'}})
    assert calls==[('pilot',{'fresh_archive':True})] if selected else calls==[('fixture',{})]
cases.append('actual entry selects freshness only for pilot; legacy fixture unchanged')
print(json.dumps({'synthetic_only' :True,'checks':cases,'count':len(cases)},indent=2))
