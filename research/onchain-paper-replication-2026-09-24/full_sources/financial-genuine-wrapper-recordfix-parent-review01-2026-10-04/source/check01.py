import ast,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
import parent01 as P
H=Path(__file__).resolve().parent
checks=[]
def ok(name,value):
 assert value,name
 checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=(H/'original-parent01.py').read_text();s=(H/'parent01.py').read_text();inverse=s
for edit in reversed(json.loads((H/'INVERSE01.json').read_text())['edits']):
 ok('unique inverse '+edit['new'][:60],inverse.count(edit['new'])==1);inverse=inverse.replace(edit['new'],edit['old'])
ok('whole byte inverse',inverse==a);ok('whole AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(a)))
old=H.parent/'financial-genuine-wrapper-parent-preparation03-2026-10-04'
for name in ('supervisor01.py','descendants01.py','owned_io.py','recovery04.py','bounded_git01.py','PROTOCOL_PINS01.json'):
 ok('unchanged helper '+name,sha(H/name)==sha(old/name))
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_text())
for field in ['status','capsule_root','parent_root','identity','expected_phase','source','design_source','registration','proofs','final_review']:
 changed=dict(q);changed[field]='wrong'
 try:P.validate_release(changed)
 except (ValueError,TypeError,KeyError):ok('draft refusal '+field,True)
 else:raise AssertionError(field)
for field in ['source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review']:
 ok('unknown actual authority '+field,q[field] is None)
functions={n.name:n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
pre=ast.get_source_segment(s,functions['preflight']);launch=ast.get_source_segment(s,functions['launch'])
ok('actual admission before command and return',pre.index('job._admitted(args)')<pre.index("job._command(args,'launch')")<pre.index('return parent'))
ok('preflight before intent',launch.index('preflight(q)')<launch.index("directory.mkdir")<launch.index("'intent.json'"))
ok('late imported module reauthentication',pre.index('job._admitted(args)')<pre.index("'post-admission actual package prefix/hash'"))
ok('no native launch in preflight','supervise(' not in pre and '.start(' not in pre and 'mkdir(' not in pre)
job=(H/'original-job.py').read_text();nodes={n.name:n for n in ast.parse(job).body if isinstance(n,ast.FunctionDef)}
proto=json.loads((H/'PROTOCOL_PINS01.json').read_text())
ok('job exact authentic protocol',sha(H/'original-job.py')==proto['tradingagents/research/onchain_replication/job.py'])
ok('resources exact authentic protocol',sha(H/'original-resources.py')==proto['tradingagents/research/onchain_replication/resources.py'])
ad=ast.get_source_segment(job,nodes['_admitted']);ok('genuine admission API calls real admit', 'admit(root=args.root' in ad);ok('exact wrapper admission route', 'financial_wrapper_fixture.admitted(admitted,job)' in ad)
ok('no claim creation in admission function', all(x not in ad for x in ['ResearchRun.start','Owner(','.mkdir(','.write_bytes(','.write_text(']))
# Execute the original command constructor only; no Admission/Owner/Run object.
ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'}
exec(compile(ast.Module(body=[nodes['_command']],type_ignores=[]),'authentic-command','exec'),ns)
args=SimpleNamespace(root=str(P.CAP),registration='UNRELEASED.json',experiment=P.IDENTITY,source='UNRESOLVED')
command=ns['_command'](args,'launch');ok('authentic command fresh CAP',command[command.index('--root')+1]==str(P.CAP));ok('authentic command fresh identity',command[command.index('--experiment')+1]==P.IDENTITY)
ok('no numerical imports',all(n not in sys.modules for n in ['numpy','torch','pandas','scipy']))
ok('unchanged first fatal close', 'finally:R._cleanup((lambda:os.close(fd),))' in s)
ok('unchanged original null terminal',"'actual_parent_exit':None" in s)
ok('unchanged one use',"not os.path.lexists(path)" in pre)
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_admission_calls':0,'native_jobs':0,'numerical_imports':0},indent=2)+'\n')
print('PASS',len(checks))
