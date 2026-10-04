from pathlib import Path
import json,hashlib,stat,os,ast,sys
D=Path(__file__).resolve().parent;B=D.parent;H=lambda b:hashlib.sha256(b).hexdigest();records=[]
for name,pin in [('financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04','02de70069dbe4b71010b75e29cd0a8debcd72836b170e1b42317506a99e23583'),('financial-wrapper-compatibility-operational-delta-flat-review03-2026-10-04','be398a209e0f5750b57820dcafb64731d2ca5bdb403dfe6622ac2fc9cfb9b0be'),('financial-wrapper-compatibility-operational-delta-remote-outcome-review03-2026-10-04','231ae543b65e63854e12a9433cbb9085b151539d0c03c90f0983f42adf75eb86')]:
 root=B/name;raw=(root/'MANIFEST01.json').read_bytes();assert H(raw)==pin;m=json.loads(raw)
 for r in m['members']:
  p=root/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  else:raise AssertionError(r)
 records.append({'root':str(root),'manifest_sha256':pin,'authenticated_members':len(m['members'])})
source=(D/'restore01.py').read_text();old=(D/'ORIGINAL_restore01.py').read_text();inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes());rebuilt=source
for e in reversed(inv['edits']):assert rebuilt.count(e['new'])==1;rebuilt=rebuilt.replace(e['new'],e['old'])
assert rebuilt==old and ast.dump(ast.parse(rebuilt))==ast.dump(ast.parse(old));assert H(old.encode())=='6d7688080efb716b7a79d1291b4f27e62e0315e5d7a8153b2890d1f9fab35214'
for n in ['watch01.py','utilities/owned_io.py','utilities/recovery_pax01.py','utilities/bounded_git01.py']:assert (D/n).read_bytes()==(B/'financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04'/n).read_bytes()
profile=json.loads((D/'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json').read_bytes());assert H((D/'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json').read_bytes())=='d238a23846a5bfc4b61fcc8b94092532d0ebfe1f0878833f22a6e100e1c27e29';selected=Path(profile['actual_selected_root']);observed={'.':selected.lstat()}
for p in selected.rglob('*'):observed[str(p.relative_to(selected))]=p.lstat()
assert set(observed)==set(profile['directory_modes'])|set(profile['files']);actual=[]
for name,s in observed.items():
 assert s.st_uid==profile['expected_owner_uid']==os.geteuid();p=selected/name
 if name in profile['directory_modes']:assert stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==profile['directory_modes'][name]
 else:
  row=profile['files'][name];assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==row['mode'] and s.st_nlink==1 and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256']
 actual.append({'path':name,'mode':stat.S_IMODE(s.st_mode),'owner':s.st_uid,'signature':[s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks]})
I=selected.parent
for filename,key in [('REMOTE_RECOVERY01.json','actual_remote_receipt_sha256'),('SELECTED_BODIES01.json','selection_sha256'),('ROOT_REMOTE03_EXIT01.json','actual_Root_exit_sha256')]:assert H((I/filename).read_bytes())==profile[key]
assert not any((I/n).exists() for n in ['FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','flat-operational-delta01','flat-failed-remote02-01'])
result={'lineages':records,'total_authentic_members':sum(r['authenticated_members'] for r in records),'source_sha256':H(source.encode()),'inverse_exact':True,'all_three_primitives_and_watch_unchanged':True,'actual_selected_readback':actual,'actual_original_modes_preserved':True,'runtime':sys.version,'numeric_modules_present':[n for n in ('numpy','torch','pandas','scipy') if n in sys.modules],'actual_flat_outcome':None,'public_run_or_entry':False};assert not result['numeric_modules_present'];(D/'AUTHENTICATION01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['total_authentic_members','source_sha256','actual_original_modes_preserved']}))
