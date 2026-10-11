"""Narrow corrected18 source/caller and explicit public-roster metadata check."""
import ast,datetime,difflib,hashlib,json,os,resource,signal,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full30increment18';OLD=D.parent/'full30increment17'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(20,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(25)
checks=[];refs={}
def ck(v,n):assert v,n;checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p);assert not {'real_pilot_runtime','keys','apis','.git','.venv'}&set(p.parts) and p.name!='connection.json';assert p.stat().st_size<2*1024**2
    b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
m=js(D/'HELPERS_MANIFEST01.json');prior=js(P/'BINDING_AND_TOOLS17_REVIEW01.json')
ck(prior['binding_decision']=='ACCEPT_ACTUAL_PUBLIC_BINDING67_REFERENCE_JOIN_ONLY' and prior['tools17_decision']=='WITHHOLD_FROZEN17_MISSING_EXPLICIT_HELPERS','actual binding accepted and17refusal retained')
ck(sha(read(OLD/'HELPERS_MANIFEST01.json'))==m['prior_withheld_manifest']['sha256']=='361d13039a4a9081ea445960e9c25480cf9c200ebfdc6868595fb353a8535ee1','unchanged withheld17 manifest')
for name,row in m['files'].items():
    b=read(D/name);ck({'bytes':len(b),'sha256':sha(b)}==row,'frozen18 member '+name)
expected={'select':'c39181cb900ae40d7041987eb49bdfce32c3beea59fb50e28b8da900b3841e43','capture':'fc678dcb7d5e6ea7bf87f2973a13c83c6775e29a82aeac8fa3fa97abe697adf4','recover':'1ed145f27334e4d8889cfb24ff6858f84d02f5237cf49e0a9d28c9f3da8c8198'}
scripts={};patch=[]
for kind in ('select','capture','recover'):
    name=kind+'18.py';body=read(D/name);scripts[kind]=body.decode();ck(sha(body)==expected[kind],'external helper18pin '+kind);ast.parse(body)
    original=R/m['origins'][kind]['path'];oldbody=read(original);ck(sha(oldbody)==m['origins'][kind]['sha256'],'accepted14 source body '+kind)
    patch.extend(difflib.unified_diff(oldbody.decode().splitlines(True),body.decode().splitlines(True),fromfile=str(original.relative_to(R)),tofile=str((D/name).relative_to(R))))
ck(''.join(patch).encode()==read(D/'LITERAL_PATCH01.diff'),'exact14-to18 patch reencoding')
ck(scripts['capture'].replace('18','17')==read(OLD/'capture17.py').decode(),'capture only18namespace change')
recovered=scripts['recover'].replace('18','17').replace("out=D/'fresh-git-recovered-full30increment17.tar'","out=D/'fresh-git-recovered-full29increment14.tar'")
ck(recovered==read(OLD/'recover17.py').decode(),'recover only18namespace and corrected returned basename')
tree=ast.parse(scripts['select']);oldtree=ast.parse(read(OLD/'select17.py'))
def owned(t):return next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='owned' for v in n.targets))
roster=owned(tree);ck(roster==m['owned']==owned(oldtree)+['real-data-pilot-full24-preparation-increment01-2026-10-09/full30increment17'],'exact nine roster keeps withheld17')
explicit=next(ast.literal_eval(n.iter) for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='name' and isinstance(n.iter,ast.Tuple))
ck(explicit==('capture18.py','recover18.py','select18.py','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff') and all((D/name).is_file() for name in explicit),'all exact corrected18 explicit helpers and patch exist')
restored=scripts['select'].replace(repr(roster),repr(owned(oldtree))).replace("('capture18.py', 'recover18.py', 'select18.py', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff')","('capture14.py', 'recover14.py', 'select17.py', 'HELPERS_MANIFEST01.json')").replace('Include nine bounded owned directories (including withheld unexecuted17)','Include eight bounded owned directories').replace('SELECTION18.json','SELECTION17.json')
ck(restored==read(OLD/'select17.py').decode(),'entire17-to18 selector change limited to reported corrections')
for fragment in ["prior = HERE.parent/'outcome16/FRESH_GIT_RECOVERY16.json'","scopes=[]","'.git', '.venv', 'node_modules', 'keys', 'apis'","'connection.json'","not relative.startswith(('research_artifacts/', 'research_runs/'))",'before.st_nlink == 1','before.st_size <= 64*1024**2',"prior.parent/'SELECTION16.json'",'names-excluded-set(reused)']:
    ck(fragment in scripts['select'],'inherited scope/denominator/guard '+fragment)
for fragment in ["S=D/'SELECTION18.json'","D/'full30-preparation-increment18.tar'","D/'CAPTURE18.json'",'before.st_nlink==1','tarfile.PAX_FORMAT','m.isfile()']:
    ck(fragment in scripts['capture'],'capture exact18/readback '+fragment)
for fragment in ['real-pilot-full30-preparation-20261011-18.git',"D/'CAPTURE18.json'","D/'FRESH_GIT_RECOVERY18.json'","out=D/'fresh-git-recovered-full30increment18.tar'",'assert remotehead==source','sha(returned)==a[\'sha256\']']:
    ck(fragment in scripts['recover'],'recovery exact18/source/blob join '+fragment)
metadata=[];blocked=[];missing=[]
for name in roster:
    root=F/name
    if not root.exists():missing.append(name);continue
    ck(root.is_dir() and not root.is_symlink(),'explicit root type '+name)
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name2 in list(dirs):
            if name2 in {'.git','.venv','keys','apis','node_modules'}:blocked.append(str(Path(parent)/name2));dirs.remove(name2)
        for name2 in files:
            p=Path(parent)/name2;relative=str(p.relative_to(R));s=p.lstat();metadata.append({'path':relative,'bytes':s.st_size})
            if name2 in {'.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273'} or not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>64*1024**2:blocked.append(relative)
ck(not blocked,'no current explicit-roster secret/type/nlink/64MiB refusals')
for name in ['SELECTION18.json','CAPTURE18.json','full30-preparation-increment18.tar','FRESH_GIT_RECOVERY18.json','fresh-git-recovered-full30increment18.tar','GIT_OPERATIONS18.json']:
    ck(not (D/name).exists(),'fresh18 output absent '+name)
ck(not (R.parent/'onchain-pilot-recovery/real-pilot-full30-preparation-20261011-18.git').exists(),'fresh18 bare destination absent (metadata only)')
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'RELEASE_EXACT_INCREMENT18_SEQUENTIAL_ROOT_CALLER','checks':checks,'references':refs,'manifest18_sha256':sha(read(D/'HELPERS_MANIFEST01.json')),'metadata_entries':len(metadata),'metadata_bytes':sum(x['bytes'] for x in metadata),'current_missing_owned_directories':missing,'current_metadata_refusals':blocked,'baseline':'actual16 source41b55367bd226c7292c1f4a802c200cc5cd1f841 through authenticated prior returned review','no_selector_capture_recover_git_network_native_execution':True,'no_private_body_or_target_metadata_inspection':True,'conditions':['Finish and freeze all nine owned directories and selected public writers before actual selection; missing-at-review directories must be present or explicitly resolved by Root.','Actual Git-derived delta roster is outside reviewer tool authority; Root checks no unexpected raw/private/runtime/secret path and preserves refusal.','Exact local sequential18 helpers only; Root commits/pushes capture then recovers; preserve partial failures and do not overwrite/retry.','Actual returned archive typed/body denominator requires later independent readback; source review does not establish preservation.'],'limits':['64MiB is per-member storage bound only; capture/recover still hold full aggregate archive bodies.','Accepted16 aliases/subtree omissions remain in prior evidence; no old store/alias recopy or new alias admission.']}
with (P/'TOOLS18_REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references','conditions','limits')}));print('checks',len(checks))
