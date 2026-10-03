"""Read-only bounded source census; writes only this investigation's evidence."""
import ast, hashlib, json, stat
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CSC=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03'
WIRE=BASE/'neural-cold-feature-handoff-held-consumer-wiring-preparation01-2026-10-03'
def read(p):
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=4194304
    b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
    return b
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    b=read(p);return {'path':str(p.relative_to(ROOT)),'sha256':sha(b),'bytes':len(b)}
def write(n,v):
    with (HERE/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
inv=json.loads(read(CSC/'source_inventory04.json'));rows={}
for r in inv['source_inventory']:
    b=read(ROOT/r['snapshot']);assert sha(b)==r['sha256'] and len(b)==r['bytes']
    assert r['target'] not in rows
    rows[r['target']]={'target':r['target'],'origin':r['snapshot'],'sha256':sha(b),'bytes':len(b),'change':'unchanged','baseline_sha256':sha(b),'prospective_git_commit':None}
assert len(rows)==195
before=dict(rows)
mapping=json.loads(read(WIRE/'SOURCE_MAP01.json'))
for item in mapping['install_map']:
    r=item.get('candidate',item.get('accepted_unchanged_dependency'));b=read(ROOT/r['path']);assert sha(b)==r['sha256'] and len(b)==r['bytes']
    t=item['target'];old=rows.get(t)
    rows[t]={'target':t,'origin':r['path'],'sha256':sha(b),'bytes':len(b),'change':'replace' if old else 'add','baseline_sha256':old['sha256'] if old else None,'prospective_git_commit':None}
p=ROOT/'tradingagents/research/verify.py';b=read(p);assert sha(b)=='1f14343c7918e3464991b9b57ecdf74425130de5c049a4e401d896116881efce'
t=str(p.relative_to(ROOT));rows[t]={'target':t,'origin':t,'sha256':sha(b),'bytes':len(b),'change':'replace','baseline_sha256':before[t]['sha256'],'prospective_git_commit':None}
# Exact static equivalent of selected job.required_sources over the proposed paths.
def package(t):
    p=Path(t)
    return (p.parent.as_posix() in ('tradingagents/research/onchain_replication','tradingagents/research') and p.suffix=='.py') or t=='tradingagents/__init__.py'
pack={t:r['sha256'] for t,r in rows.items() if package(t)}
assert len(rows)==199 and len(pack)==148
assert sum(r['change']=='replace' for r in rows.values())==3
assert sum(r['change']=='add' for r in rows.values())==4
assert sum(r['change']=='unchanged' for r in rows.values())==192
assert set(pack)=={t for t in rows if t.startswith('tradingagents/')}
for r in rows.values():
    if r['target'].endswith('.py'):ast.parse(read(ROOT/r['origin']))
write('SOURCE_ENTRY_DRAFT01.json',{'schema_version':1,'status':'source-only uninstalled draft; wiring review separate','source_count':199,'package_count':148,'logical_bytes':sum(r['bytes'] for r in rows.values()),'future_execution_commit':None,'future_anchor_commit':None,'entries':[rows[t] for t in sorted(rows)]})
write('PACKAGE_ANCHOR_REQUIREMENTS01.json',{'status':'NOT an admitted numerical_source; commit deliberately absent','required_count':148,'required_files':dict(sorted(pack.items()))})
write('READBACK01.json',{'baseline_inventory':ref(CSC/'source_inventory04.json'),'wiring_map':ref(WIRE/'SOURCE_MAP01.json'),'main_verify':ref(p),'source_count':199,'package_count':148,'unchanged':192,'replaced':3,'added':4,'all_source_bodies_hashed':True,'all_python_bodies_AST_parsed':True,'numerical_imports':0,'actual_capsule_mutations':0,'claims':0})
print('PASS: 195 original bodies; 199 prospective sources / 148 package; 192 unchanged, 3 replaced, 4 added. No installation or authority.')
