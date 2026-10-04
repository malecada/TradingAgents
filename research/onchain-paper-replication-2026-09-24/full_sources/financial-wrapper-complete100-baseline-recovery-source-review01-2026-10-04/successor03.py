"""Exact successor statement and tiny offline actual Git controls; no main/entry."""
import ast,hashlib,importlib.util,json,os,shutil,sys,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-complete100-baseline-remote01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,n):assert v,n;checks.append(n)
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
s=(A/'restore02.py').read_bytes();ck(sha(s)=='8b010b28e37978c6ea24eb0e4aaad68d715f4031a102d7396f4627fd501d06e1','successor exact8b010');ib=(A/'RESTORE_SUCCESSOR02_INVERSE01.json').read_bytes();ck(sha(ib)=='176b20e48f7c955438a0f6da1c99fe23f27420eb54055c97b944a56b8a4c49f5','exact successor inverse');(H/'SUCCESSOR_RESTORE02.py').write_bytes(s);(H/'SUCCESSOR_INVERSE01.json').write_bytes(ib);inv=json.loads(ib);change=inv['one_exact_replacement'];ck(s.decode().count(change['replacement'])==1,'unique replacement');back=s.decode().replace(change['replacement'],change['original']);old=(H/'source/restore01.py').read_bytes();ck(back.encode()==old,'successor full literal inverse');ck(ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'successor full AST inverse')
sys.path.insert(0,str(H/'utilities'));spec=importlib.util.spec_from_file_location('Rsuccessor',H/'utilities/recovery04.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);ck(shutil.disk_usage(H).free>=R.FLOOR,'actual10GiB floor')
t=H/'successor-tiny';t.mkdir(mode=0o700);origin=t/'original';origin.mkdir(mode=0o700);(origin/'ordinary').write_bytes(b'opaque\x00fixed original byte specimen');(origin/'empty').mkdir(mode=0o700);m=R.scan(origin);bundle=t/'bundle';bundle.mkdir(mode=0o700);info=R.pack(origin,m,bundle/'complete-opaque01.tar.gz')
# Exactly the three corrected statements, executed with ordinary local archive metadata only.
body=ast.parse(change['replacement'].lstrip().replace('\n        ','\n')).body
ns={'HERE':t,'label':'opaque','R':R,'bundle':bundle,'capture':{'scopes':{'opaque':{'archive':info}}},'manifest':m}
exec(compile(ast.Module(body=body,type_ignores=[]),'actual_restore02_destination_and_restore','exec'),ns)
out=t/'flat-opaque01';result=ns['result'];meta=json.loads(R.read(out,result['metadata_file']));ck(stat.S_IMODE(out.lstat().st_mode)==0o700,'real successor private destination');ck(R.read(out,meta['flat_members']['ordinary'])==(origin/'ordinary').read_bytes() and meta['manifest']==m,'actual corrected canonical complete tiny roundtrip');ck(result['research_authority'] is False,'no authority from tiny restore')
try:exec(compile(ast.Module(body=body,type_ignores=[]),'actual_restore02_repeat','exec'),ns)
except FileExistsError:checks.append('fresh existing destination refuses repeat')
else:raise AssertionError('repeat accepted')
bad=copy_info=dict(info);bad['sha256']='0'*64
negative=t/'bad-hash';negative.mkdir(mode=0o700)
try:R.restore(bundle/'complete-opaque01.tar.gz',bad,m,negative)
except ValueError:checks.append('changed archive hash refused')
else:raise AssertionError('changedhash')
# Actual tiny offline Git reconstruction uses same genuine bounded Git helper.
repo=t/'tiny-original.git';ops=[]
def git(args,cap=4194304,at=None):
 b=R.git(t if at is None else at,args,cap=cap);ops.append({'args':args,'stdout_bytes':len(b),'stdout_sha256':sha(b)});return b
ck(not repo.exists(),'fresh tiny Git repo');git(['init','--bare',str(repo)])
blob=b'opaque source body\n';oid=lambda typ,b:hashlib.sha1(typ.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest();bo=oid('blob',blob);tree=b'100644 opaque\0'+bytes.fromhex(bo);to=oid('tree',tree);commit=('tree '+to+'\nauthor Byte Review <byte@invalid> 1 +0000\ncommitter Byte Review <byte@invalid> 1 +0000\n\nopaque source only\n').encode();co=oid('commit',commit);objects=[]
for kind,b in [('blob',blob),('tree',tree),('commit',commit)]:
 p=t/(kind+'.body');p.write_bytes(b);expected=oid(kind,b);actual=git(['hash-object','-w','-t',kind,str(p)],cap=128,at=repo).decode().strip();ck(actual==expected and p.read_bytes()==b,'real original '+kind+' type/body/OID join');objects.append(expected)
git(['update-ref','refs/heads/replication-capture',co],at=repo);git(['symbolic-ref','HEAD','refs/heads/replication-capture'],at=repo);ck(git(['rev-parse','HEAD'],cap=128,at=repo).decode().strip()==co,'fresh tiny currentcommit');git(['fsck','--full','--strict','--no-reflogs',co],at=repo);ck(git(['ls-tree','-r','--name-only',co],at=repo).decode().splitlines()==['opaque'],'complete tiny current tree');ck(sorted(git(['rev-list','--objects','--no-object-names',co],at=repo).decode().splitlines())==sorted(objects),'complete reachable tiny original population')
malformed=t/'malformed-tree.body';malformed.write_bytes(b'not a Git tree')
try:git(['hash-object','-w','-t','tree',str(malformed)],cap=128,at=repo)
except ValueError as e:checks.append('genuine Git malformed tree refused');malformed_error=str(e)
else:raise AssertionError('malformed tree accepted')
ck(shutil.disk_usage(H).free>=R.FLOOR,'final actual10GiB floor');put('SUCCESSOR_CONTROLS01.json',{'checks':len(checks),'names':checks,'actual_offline_git_operations_successful':ops,'malformed_tree_refusal':malformed_error,'tiny_scope_only':True,'actual_original385_objects_reconstructed':False,'actual_root_entry_run':False,'new_restore_source_sha256':sha(s),'no_numerical_or_native_authority':True});print(json.dumps({'checks':len(checks),'tiny_git_successful_ops':len(ops),'new_source':'SOURCE_ONLY_ACCEPTED'}))
