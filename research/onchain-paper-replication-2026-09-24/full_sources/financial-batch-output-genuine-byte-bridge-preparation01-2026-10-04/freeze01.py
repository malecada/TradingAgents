import ast,hashlib,json,os,stat
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    with (P/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
protocol=json.loads((P/'PROTOCOL01.json').read_bytes())
for name,digest in protocol['sources'].items():assert sha((P/name).read_bytes())==digest
checks=[json.loads((P/('CHECKS%02d.json'%i)).read_bytes()) for i in (1,2,3)]
assert sum(c['count'] for c in checks)==448
for i in (1,2,3):assert (P/('CHECK%02d.err'%i)).read_bytes()==b''
assert b'CleanupFailure' in (P/'IO_RED01.err').read_bytes()
for name in ('held_score_consumer','completed_f32'):
    a=(P/(name+'.original.py')).read_bytes();b=(P/(name+'.py')).read_bytes();assert b.startswith(a)
    t=ast.parse(b);assert ast.dump(ast.Module(body=t.body[:-1],type_ignores=[]),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
declared=[{'path':n,'sha256':h,'definitions':[{'name':getattr(d,'name',None),'line':d.lineno,'end_line':d.end_lineno} for d in ast.parse((P/n).read_bytes()).body if isinstance(d,(ast.FunctionDef,ast.ClassDef))]} for n,h in protocol['sources'].items()]
save('MACHINE01.json',{'status':'SOURCE_PREPARATION_COMPLETE_UNINSTALLED_NOT_INDEPENDENTLY_REVIEWED','checks':448,'source':protocol['sources'],'declared_definitions':declared,'protocol_sha256':sha((P/'PROTOCOL01.json').read_bytes()),'report_sha256':sha((P/'REPORT01.md').read_bytes()),'original_inverses':'exact predecessor prefix and all old AST preserved; only one new explicit entrypoint in each consumer','harnesses':[{'name':'CHECK%02d'%i,'result_sha256':sha((P/('CHECKS%02d.json'%i)).read_bytes())} for i in (1,2,3)],'retained_red':'R4 context-manager misuse, exact old source and raw failure preserved; corrected real FD controls passed','genuine_run_handles_constructed':False,'numerical_imports':False,'actual_source_adopted':None,'actual_gate_grant':None,'actual_whole_storage_admission':None,'actual_byte_transport':None,'actual_retirement':None})
rows=[]
for p in sorted(P.rglob('*')):
    s=p.lstat();r={'path':p.relative_to(P).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
    if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
    elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
    elif stat.S_ISREG(s.st_mode):
        assert s.st_size<=4*1024**2
        r.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
    else:raise AssertionError('unselected own type')
    rows.append(r)
save('MANIFEST01.json',{'schema_version':1,'kind':'complete-source-preparation-with-raw-controls','self_excluded':'MANIFEST01.json','members':rows,'count':len(rows),'regular_files':sum(x['kind']=='file' for x in rows),'literal_links':sum(x['kind']=='symlink' for x in rows),'regular_bytes':sum(x.get('bytes',0) for x in rows)})
print(json.dumps({'manifest_sha256':sha((P/'MANIFEST01.json').read_bytes()),'machine_sha256':sha((P/'MACHINE01.json').read_bytes()),'source_sha256':protocol['sources']['byte_bridge01.py'],'members':len(rows),'files':sum(x['kind']=='file' for x in rows),'bytes':sum(x.get('bytes',0) for x in rows)}))
