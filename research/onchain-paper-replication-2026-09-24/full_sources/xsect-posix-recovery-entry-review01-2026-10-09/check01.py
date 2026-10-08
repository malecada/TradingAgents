import ast,hashlib,json,os,resource,inspect
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];A=P.parent/'xsect-posix-recovery-entry01-2026-10-09'
os.nice(10);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(40,40))
ns={'__file__':str(A/'restore.py'),'__name__':'review_only'};exec(compile((A/'restore.py').read_bytes(),str(A/'restore.py'),'exec'),ns);fixture=P/'fixture';fixture.mkdir();ns['ROOT']=fixture
# Tiny metadata stand-ins. No real closure evidence or transport is fabricated.
def save(name,x):
 p=fixture/name;p.write_text(json.dumps(x,sort_keys=True));raw=p.read_bytes();return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
rows=[{'bytes':3,'relative_path':'a'},{'bytes':2,'relative_path':'b'}];dirs=[{'relative_path':'.'}];batch={'index':0,'start':0,'stop':2,'raw_bytes':5}
refs={n:save(n,x) for n,x in [('CONTENT_ROWS01.json',rows),('DIRECTORIES01.json',dirs),('BATCHES01.json',{'batches':[batch]})]}
bc={'identity':'toy-backup','source_root':'/toy-original','remote':'toy-remote','input_refs':refs};bc_ref=save('backup.json',bc)
manifest={'members':[{**row,'member':f'files/{i:08d}'} for i,row in enumerate(rows)],'files':2,'raw_bytes':5,'archive_bytes':10240,'archive_sha256':'a'*64};mr=save('manifest.json',manifest)
receipt={'status':'complete','originals_preserved':True,'downloaded_members_verified':True,'source_hashes_verified':True,'start_index':0,'files':2,'raw_bytes':5,'archive_bytes':10240,'archive_sha256':'a'*64,'manifest_sha256':mr['sha256'],'remote':'toy-remote/batch-0000'};rr=save('receipt.json',receipt)
complete={'status':'complete','originals_preserved':True,'files':2,'raw_bytes':5,'batches':[{'index':0,'receipt_sha256':rr['sha256'],**receipt}]};cr=save('complete.json',complete)
c={'backup_contract_ref':bc_ref,'backup_complete_ref':cr,'backup_identity':'toy-backup','original_root':'/toy-original','expected_files':2,'expected_raw_bytes':5,'expected_directories':1,'expected_batches':1,'max_archive_bytes':10240,'selection':[{'index':0,'receipt_ref':rr,'manifest_ref':mr}]};checks=[]
assert ns['validate_selection'](c)==(rows,dirs,[(batch,receipt,manifest)]);checks.append('complete_batch_receipt_manifest_numeric_tar_join')
def refusal(label,fn):
 try:fn()
 except (ValueError,KeyError) as e:checks.append(label+':'+type(e).__name__)
 else:raise AssertionError(label)
import copy
x=copy.deepcopy(c);x['selection'][0]['index']=1;refusal('batch_order',lambda:ns['validate_selection'](x))
x=copy.deepcopy(c);x['backup_complete_ref']['sha256']='0'*64;refusal('body_hash',lambda:ns['validate_selection'](x))
x=copy.deepcopy(c);bad=copy.deepcopy(complete);bad['batches'][0]['receipt_sha256']='0'*64;x['backup_complete_ref']=save('bad-complete.json',bad);refusal('receipt_join',lambda:ns['validate_selection'](x))
bad=copy.deepcopy(manifest);bad['members'][0]['member']='files/a';br=save('bad-manifest.json',bad);badreceipt=dict(receipt,manifest_sha256=br['sha256']);brr=save('bad-receipt.json',badreceipt);bcpl=dict(complete,batches=[{'index':0,'receipt_sha256':brr['sha256'],**badreceipt}]);x=copy.deepcopy(c);x['backup_complete_ref']=save('bad-complete2.json',bcpl);x['selection'][0].update(receipt_ref=brr,manifest_ref=br);refusal('nonnumeric_member',lambda:ns['validate_selection'](x))
# Stop early at closure refusal, never create positive native eligibility evidence.
oldchecked=ns['checked'];ns['checked']=lambda ref:json.dumps({'identity':'toy-native','actual_root_exit_code':None,'original_process_paths_absent':False} if ref=='terminal' else {}).encode()
refusal('native_still_active',lambda:ns['eligibility']({'native_terminal_ref':'terminal','native_final_ref':'guard','native_identity':'toy-native'},1));ns['checked']=oldchecked
# Bind actual helper signatures, without executing recovery or creating authority.
h=ast.parse((P.parent/'xsect-posix-recovery01-2026-10-08/recover.py').read_bytes());funcs={n.name:n for n in h.body if isinstance(n,ast.FunctionDef)}
for name in ['create_new_tree','recover_bundle','verify_new_tree']:
 fn=funcs[name];stub=ast.FunctionDef(name=name,args=fn.args,body=[ast.Pass()],decorator_list=[]);ast.fix_missing_locations(stub);env={};exec(compile(ast.Module(body=[stub],type_ignores=[]),'signature_only','exec'),env)
 common=dict(directories=[],original_root='x',max_files=2,max_total_bytes=5,max_file_bytes=3)
 if name=='create_new_tree':common.pop('directories');inspect.signature(env[name]).bind('target',[],[],**common)
 elif name=='recover_bundle':inspect.signature(env[name]).bind('archive',{},[],'target',root_pin=(1,2),batch={},max_archive_bytes=10240,**common)
 else:inspect.signature(env[name]).bind('target',[],root_pin=(1,2),restore_directories=True,**common)
checks.append('all_three_real_helper_signatures_join')
result={'status':'PASS_FOCUSED_SOURCE_ONLY','checks':checks,'actual_affinity':sorted(os.sched_getaffinity(0)),'restore_sha256':hashlib.sha256((A/'restore.py').read_bytes()).hexdigest(),'bind_sha256':hashlib.sha256((A/'bind.py').read_bytes()).hexdigest(),'qualification':'Synthetic metadata and refusal-only closure stub; no actual closure/eligibility/admission/transport/full restoration claimed.'};(P/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
