"""Bounded independent source-seam tests. Never runs a preservation helper main."""
import ast, datetime, hashlib, io, json, os, resource, stat, tarfile
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(30,30))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
P=Path(__file__).resolve().parent;F=P.parent.parent;R=F.parents[2]
D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome16'
checks=[];refs={};total=0
def ck(ok,label):
    assert ok,label
    checks.append(label)
def read(p):
    global total
    p=Path(p);s=p.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2
    b=p.read_bytes();total+=len(b);assert total<8*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    return b
def sha(b):return hashlib.sha256(b).hexdigest()
mb=read(D/'HELPERS_MANIFEST01.json');ck(sha(mb)=='1e33236c7420c4346f4b026c257194c66f42c5a2ad7cdeec7ea66d4461fd1a0c','exact externally supplied source manifest')
m=json.loads(mb);inv=json.loads(read(D/'LITERAL_INVERSE01.json'))
ck(sha((D/'LITERAL_INVERSE01.json').read_bytes())==m['files']['LITERAL_INVERSE01.json']['sha256'],'inverse manifest join')
sources={};trees={}
for name in ('select16.py','capture16.py','recover16.py'):
    b=read(D/name);ck({'bytes':len(b),'sha256':sha(b)}==m['files'][name],'source hash '+name)
    text=b.decode();sources[name]=text;trees[name]=ast.parse(text)
    for change in reversed(inv['changes'][name]):
        ck(change['after'] in text,'inverse clause '+name)
        text=text.replace(change['after'],change['before'])
    ck(text.encode()==read(D.parent/'outcome15'/name.replace('16','15')),'full literal inverse '+name)
for path,row in m['references'].items():
    b=read(R/path);ck({'bytes':len(b),'sha256':sha(b)}==row,'prior anchor '+Path(path).name)
prior=json.loads(read(P.parent/'tools15/REVIEW01.json'))
ck(prior['disposition']=='WITHHOLD_OUTCOME15_ACTUAL_ROSTER_REFUSALS','outcome15 remains withheld')
# Reuse accepted13/14 checks authenticated by the prior review; no historical rerun.
supp=json.loads(read(P.parent/'tools15/ALIAS_METADATA_SUPPLEMENT01.json'))
literal={}
for node in trees['select16.py'].body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('ALIAS_MEMBERS','SYNTHETIC_GIT_EXCLUSIONS','owned','N'):
        literal[node.targets[0].id]=ast.literal_eval(node.value)
aliases=literal['ALIAS_MEMBERS'];excluded=literal['SYNTHETIC_GIT_EXCLUSIONS']
ck(aliases=={x['path']:x for x in supp['alias_members']}==m['original_alias_members'],'exact two alias pins match prior observation')
ck(excluded==supp['git_subtrees_metadata_only']==m['excluded_synthetic_git_subtrees'] and len(excluded)==3,'exact three Git subtree exclusions')
ck(literal['owned']==m['owned_directories'] and len(literal['owned'])==36,'exact current36 directory roster')
ns={'os':os,'stat':stat,'hashlib':hashlib}
nodes=[n for n in trees['select16.py'].body if isinstance(n,ast.FunctionDef) and n.name in ('alias_signature','authenticate_alias_pair','excluded_synthetic_git')]
ns.update(ALIAS_MEMBERS=aliases,SYNTHETIC_GIT_EXCLUSIONS=excluded)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<isolated-pure-authentication-functions>','exec'),ns)
for prefix in excluded:
    ck(ns['excluded_synthetic_git'](prefix) and ns['excluded_synthetic_git'](prefix+'/objects/opaque'),'exact Git subtree included in omission')
    for neighbor in (prefix+'x',prefix+'-other/HEAD',prefix.rsplit('/',1)[0]+'/working.txt','unrelated/.git/HEAD'):
        ck(not ns['excluded_synthetic_git'](neighbor),'neighbor not exempted '+neighbor)
ck(ns['authenticate_alias_pair'](R)==aliases,'actual pair bounded authentication')
# Independently inspect only these two explicitly public14B bodies; never print them.
bodies={}
for name,row in aliases.items():
    body=read(R/name);bodies[name]=body
    ck(len(body)==14 and sha(body)==row['sha256'],'actual alias14B body hash')
capture_nodes=[n for n in trees['capture16.py'].body if isinstance(n,ast.FunctionDef)]
ck([ast.dump(n) for n in nodes[:2]]==[ast.dump(n) for n in capture_nodes],'identical selector/capture authentication functions')
capture_alias=next(ast.literal_eval(n.value) for n in trees['capture16.py'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALIAS_MEMBERS' for t in n.targets))
ck(capture_alias==aliases,'capture exact alias pins')
# Fake metadata / descriptor mutations exercise the isolated real authentication function.
good=dict(st_dev=66310,st_ino=7865445,st_nlink=2,st_size=14,st_mode=stat.S_IFREG|0o664,st_mtime_ns=10,st_ctime_ns=20)
case={};calls={}
class FakePath:
    def __init__(self,name=''):self.name=name
    def __truediv__(self,name):return FakePath(name)
    @property
    def parent(self):return self
    def resolve(self,strict=True):return object() if case.get('parent') else self
    def lstat(self):
        key=('path',self.name);calls[key]=calls.get(key,0)+1;d=good.copy()
        if case.get('stage')=='before' or (case.get('stage')=='after' and calls[key]>1):d[case['field']]=case['value']
        return SimpleNamespace(**d)
class FakeOS:
    O_RDONLY=os.O_RDONLY;O_NOFOLLOW=os.O_NOFOLLOW;O_CLOEXEC=os.O_CLOEXEC;O_NONBLOCK=os.O_NONBLOCK
    def open(self,path,flags):
        ck(flags==os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,'descriptor flags retained')
        return path.name
    def close(self,fd):pass
    def read(self,fd,size):
        assert size==15
        return b'x'*14 if case.get('body') else bodies[fd]
    def fstat(self,fd):
        key=('fd',fd);calls[key]=calls.get(key,0)+1;d=good.copy()
        if case.get('stage')=='fd_before' or (case.get('stage')=='fd_after' and calls[key]>1):d[case['field']]=case['value']
        return SimpleNamespace(**d)
ns['os']=FakeOS()
ck(ns['authenticate_alias_pair'](FakePath())==aliases,'synthetic valid pair')
for stage in ('before','fd_before','fd_after','after'):
    for field,value in [('st_dev',66311),('st_ino',7865446),('st_nlink',3),('st_size',15),('st_mode',stat.S_IFLNK|0o664),('st_mtime_ns',11),('st_ctime_ns',21)]:
        if stage in ('before','fd_before') and field in ('st_mtime_ns','st_ctime_ns'):continue
        case.clear();calls.clear();case.update(stage=stage,field=field,value=value)
        try:ns['authenticate_alias_pair'](FakePath())
        except AssertionError:checks.append('refuses '+stage+' '+field)
        else:raise AssertionError('accepted mutation '+stage+' '+field)
for flag in ('body','parent'):
    case.clear();calls.clear();case[flag]=True
    try:ns['authenticate_alias_pair'](FakePath())
    except AssertionError:checks.append('refuses '+flag+' mutation')
    else:raise AssertionError('accepted '+flag)
ns['os']=os
s=sources['select16.py'];c=sources['capture16.py'];r=sources['recover16.py']
for fragment in ["{'.git', '.venv', 'node_modules', 'keys', 'apis'}", "('.env', 'hf_token.txt', 'connection.json', 'id_ed25519_storagebox_u676273')",'before.st_size <= 64*1024**2','relative not in ALIAS_MEMBERS and old',"row['original_alias']=ALIAS_MEMBERS[relative]"]:
    ck(fragment in s,'retained selector guard '+fragment)
ck(s.count('authenticate_alias_pair(ROOT)')==2 and s.index('authenticate_alias_pair(ROOT)')<s.index('for relative in sorted(names-excluded)') and s.rindex('authenticate_alias_pair(ROOT)')>s.index('rows.append(row)'),'selector before/after alias authentication')
ck(c.count('authenticate_alias_pair(R)')==2 and c.index('authenticate_alias_pair(R)')<c.index("tarfile.open(p,'x'") and c.rindex('authenticate_alias_pair(R)')>c.index('t.addfile(x,io.BytesIO(raw))'),'capture before/after alias authentication')
ck("before.st_nlink==1 or (r['path'] in ALIAS_MEMBERS" in c and "r.get('original_alias')==ALIAS_MEMBERS[r['path']]" in c,'other nlink1 and exact alias metadata guard')
ck('LNKTYPE' not in c and 't.addfile(x,io.BytesIO(raw))' in c and 'm.isfile()' in c,'capture uses regular body representation with body readback')
# Independent PAX semantics demonstration; not helper capture execution.
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w',format=tarfile.PAX_FORMAT) as archive:
    for name,body in bodies.items():
        member=tarfile.TarInfo(name);member.mode=0o664;member.size=len(body);archive.addfile(member,io.BytesIO(body))
buf.seek(0)
with tarfile.open(fileobj=buf,mode='r') as archive:
    members=archive.getmembers();ck(len(members)==2,'synthetic PAX two members')
    for member in members:ck(member.type==tarfile.REGTYPE and member.size==14 and member.mode==0o664 and archive.extractfile(member).read()==bodies[member.name],'synthetic PAX independent regular body')
# Metadata only roster inspection, pruning exact Git exclusions before descent.
roster=[];bad=[]
roots=[F/name for name in literal['owned']]+[R/name for name in prior['seven_scopes']]
for root in roots:
    ck(root.is_dir() and not root.is_symlink(),'current roster directory '+str(root.relative_to(R)))
    for parent,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[name for name in dirs if not ns['excluded_synthetic_git'](str((Path(parent)/name).relative_to(R)))]
        for name in files:
            p=Path(parent)/name;rel=str(p.relative_to(R));st=p.lstat()
            if ns['excluded_synthetic_git'](rel):continue
            roster.append((rel,st.st_size))
            if ({'.git','.venv','node_modules','keys','apis'} & set(p.parts)) or name in ('.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273'):bad.append([rel,'denied name'])
            elif stat.S_ISREG(st.st_mode) and (st.st_size>64*1024**2 or (st.st_nlink!=1 and rel not in aliases)):bad.append([rel,'regular bound'])
            elif not stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode):bad.append([rel,'type'])
ck(not bad,'no additional current explicit-roster metadata refusals')
ck(all(p.name in literal['owned'] for p in F.iterdir() if p.is_dir() and p.name.endswith('2026-10-10')),'all current Oct10 directories retained')
for prefix in excluded:ck((R/prefix).is_dir(),'excluded original Git subtree still present')
for name in ['SELECTION16.json','CAPTURE16.json','failed-outcome-increment16.tar','FRESH_GIT_RECOVERY16.json','fresh-git-recovered-outcome16.tar','GIT_OPERATIONS16.json']:
    ck(not (D/name).exists(),'fresh caller output absent '+name)
ck(not (R.parent/'onchain-pilot-recovery/real-pilot-full29-outcome-20261011-16.git').exists(),'fresh caller bare target absent')
for fragment in ["D/'SELECTION16.json'","D/'failed-outcome-increment16.tar'","D/'CAPTURE16.json'"]:ck(fragment in c,'capture caller path '+fragment)
for fragment in ["D/'CAPTURE16.json'","D/'FRESH_GIT_RECOVERY16.json'",'real-pilot-full29-outcome-20261011-16.git','assert remotehead==source',"assert parts[:2]==['100644','blob']", "sha(returned)==a['sha256']"]:ck(fragment in r,'recovery caller join '+fragment)
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SOURCE_SEAM_AND_EXPLICIT_ROSTER_CHECKS_PASS','checks':checks,'references':refs,'read_bytes':total,'metadata_entries':len(roster),'metadata_bytes':sum(x[1] for x in roster),'metadata_refusals':bad,'helper_manifest_sha256':sha(mb),'no_helper_main_execution':True,'no_git_execution':True,'no_git_internal_or_credential_body_reads':True}
with (P/'CHECKS01.json').open('x') as stream:json.dump(out,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('checks','references')},sort_keys=True))
