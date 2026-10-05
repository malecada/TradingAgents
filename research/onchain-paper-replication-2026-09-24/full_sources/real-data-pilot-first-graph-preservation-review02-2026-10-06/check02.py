import ast, copy, hashlib, json
from pathlib import Path
from types import SimpleNamespace
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
D=Path(__file__).parent
B=M/'research/onchain-paper-replication-2026-09-24'
S=B/'storage/real-pilot-first-graph-preservation-20261006-01'
P=B/'full_sources/real-data-pilot-first-graph-preservation-review01-2026-10-06'
h=lambda b: hashlib.sha256(b).hexdigest()
a=(S/'entry01.py').read_text(); b=(S/'entry02.py').read_text()
assert h(a.encode())=='26a17ccea0acd693b95148773eced123b50fbc3ad900ee0cd25ec86eeea35af8'
assert h(b.encode())=='d30eb6f38bec48fec0b310658839d7b7baf201a795ba7400422bcc0f696ea443'
inv=b.replace('envelope02.json','envelope01.json').replace('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json').replace('entry02.py','entry01.py')
inv=inv.replace("if (envelope['identity'] != ID\n            or envelope['local_only_evidence'] != [envelope['connection']['path']]\n            or envelope['connection']['path'] in envelope['source_files']):\n        raise ValueError('fixed identity/local-only connection binding differs')", "if envelope['identity'] != ID:\n        raise ValueError('fixed operation identity differs')")
inv=inv.replace("        if path not in envelope['local_only_evidence']:\n            if hashlib.sha256(subprocess.check_output(['git', 'show', head + ':' + path], cwd=ROOT)).hexdigest() != sha:\n                raise ValueError('released evidence not committed: ' + path)", "        if hashlib.sha256(subprocess.check_output(['git', 'show', head + ':' + path], cwd=ROOT)).hexdigest() != sha:\n            raise ValueError('released evidence not committed: ' + path)")
assert inv==a
old=json.loads((S/'envelope01.json').read_bytes()); new=json.loads((S/'envelope02.json').read_bytes())
rest=copy.deepcopy(new); rest.pop('local_only_evidence')
oldpath=str((S/'entry01.py').relative_to(M)); newpath=str((S/'entry02.py').relative_to(M))
assert rest['source_files'].pop(newpath)==h(b.encode()); rest['source_files'][oldpath]=h(a.encode()); assert rest==old
connection=new['connection']['path']
assert new['local_only_evidence']==[connection]
assert new['connection']['sha256']=='d79023381eb9f2788709a7a4c043046d8998c30bb4abab678cb41caaf4dc70ef'
tree=ast.parse(b); funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
condition=next(n for n in funcs['frozen'].body if isinstance(n,ast.If))
code=compile(ast.fix_missing_locations(ast.Module(body=[condition],type_ignores=[])),'actual-condition','exec')
def valid(e):
    exec(code,{'envelope':e,'ID':new['identity']})
valid(new)
refusals=[]
for name,values in [('extra',['extra',connection]),('duplicate',[connection,connection]),('source-only',[newpath]),('empty',[])]:
    e=copy.deepcopy(new); e['local_only_evidence']=values
    try: valid(e)
    except ValueError: refusals.append(name)
    else: raise AssertionError(name)
e=copy.deepcopy(new); e['source_files'][connection]=e['connection']['sha256']
try: valid(e)
except ValueError: refusals.append('connection-as-executable-source')
else: raise AssertionError('source bypass')
loop=next(n for n in funcs['launch'].body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple))
loopcode=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'actual-loop','exec')
raws={'code.py':b'code','evidence.json':b'evidence','local-connection.json':b'offline-placeholder'}
e={'source_files':{'code.py':h(raws['code.py'])},'local_only_evidence':['local-connection.json']}
r={'evidence':{k:h(v) for k,v in raws.items() if k!='code.py'}}
def run(corrupt_git=None,corrupt_local=None):
    git=[]; local=[]
    def output(args,**kw):
        path=args[2].split(':',1)[1]; git.append(path)
        return b'corrupt' if path==corrupt_git else raws[path]
    def body(ref):
        local.append(ref['path']); value=b'corrupt' if ref['path']==corrupt_local else raws[ref['path']]
        if h(value)!=ref['sha256']: raise ValueError('body mismatch')
    exec(loopcode,{'envelope':e,'release':r,'hashlib':hashlib,'subprocess':SimpleNamespace(check_output=output),'head':'fixed','ROOT':M,'body':body})
    return git,local
assert run()==(['code.py','evidence.json'],['code.py','evidence.json','local-connection.json'])
for kind,path in [('git','code.py'),('git','evidence.json'),('local','local-connection.json')]:
    try: run(**{'corrupt_'+kind:path})
    except ValueError: refusals.append(kind+'-changed-'+path)
    else: raise AssertionError((kind,path))
# Authenticate only compact/source prior evidence; never open local connection or payloads.
prior=json.loads((P/'RELEASE_REVIEW01.json').read_bytes())
assert h((P/'RELEASE_REVIEW01.json').read_bytes())=='dfe998a3f42114733a7e3383909fded23035cb5f014b8a861edda26b1c6778a4'
assert h((P/'MANIFEST01.json').read_bytes())=='1eebdda02f9a151865acbbb3ecac3927082e80bf735ee9ae82af340d3ee5e230'
for path,sha in prior['evidence'].items():
    if path==connection: continue
    assert h((M/path).read_bytes())==sha,path
for path,sha in new['source_files'].items(): assert h((M/path).read_bytes())==sha,path
refusal=json.loads((S/'READ_ONLY_REFUSAL01.json').read_bytes())
assert refusal['actual_tool']=='a48c8a' and refusal['actual_exit_code']==1
assert not any(refusal[k] for k in ('attempt_exists','intent_exists','native_guard_exists'))
markers=('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json')
assert not any((S/n).exists() or (S/n).is_symlink() for n in markers)
result={'decision':'accepted-correction-only','entry_sha256':h(b.encode()),'envelope_sha256':h((S/'envelope02.json').read_bytes()),'old_entry_exact_inverse':True,'old_envelope_exact_inverse':True,'refusal_controls':refusals,'actual_refusal_sha256':h((S/'READ_ONLY_REFUSAL01.json').read_bytes()),'markers_absent':list(markers),'connection_contents_read':False,'payloads_read':False,'network_native_execution':False,'qualification':'Actual AST condition/loop exercised with offline bytes; original source/protocol reused, entry must enforce fresh commit/remote/resource checks.'}
(D/'CHECK02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
