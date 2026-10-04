from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent
inverse=json.loads((D/'INVERSE02.json').read_text());checks=[]
def check(v,name):
 assert v,name
 checks.append(name)
for row in inverse:
 check(row['new']==(D/row['file']).read_text(),row['file']+' actual bytes')
 ast.parse(row['original']);ast.parse(row['new'])
r=inverse[0];check(r['original'].count('format=tarfile.PAX_FORMAT')==2,'exact two canonical writers');check(r['new'].replace('format=tarfile.USTAR_FORMAT','format=tarfile.PAX_FORMAT')==r['original'],'USTAR literal inverse')
for row,allowed in [(inverse[1],{'run','restore_archives'}),(inverse[2],{'contract','main'})]:
 old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(row['original']).body if isinstance(n,ast.FunctionDef)}
 new={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(row['new']).body if isinstance(n,ast.FunctionDef)}
 for name in old.keys()-allowed:check(old[name]==new[name],row['file']+' unchanged '+name)
oldroot=D.parent/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05'
for name in ('watch01.py','binding01.py','receipt01.py','cohort01.py','KNOWN_REQUIRED01.json','recover.template01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):
 check((D/name).read_bytes()==(oldroot/name).read_bytes(),'unchanged '+name)
s=(D/'restore_successor02.py').read_text();check("selected=RECEIVER/'selected'" in s and "str(RECEIVER/'fresh-compatibility-baseline02.git')" in s,'fixed old receiver reads')
s=(D/'caller03.py').read_text();check("D=F/'financial-wrapper-compatibility-baseline-flat-root02-2026-10-05'" in s,'fixed fresh writable root')
check("c['phase']=='FLAT'" in s,'remote invocation refused')
check("prefix='ROOT_BASELINE_FLAT02'" in s,'distinct caller receipts')
check("evidence if key in ('selection','remote_receipt','remote_root_exit','selected_mode_profile')" in s,'original receiver evidence kept read only')
for n in ('ARCHIVE_CHECK01.json','PAUSE_CHECK02.json'):check((D/n).is_file(),'retained '+n)
(D/'FINAL_CHECK01.json').write_text(json.dumps({'checks':checks,'count':len(checks)},indent=2)+'\n')
print(len(checks))
