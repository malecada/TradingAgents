from pathlib import Path
import ast,hashlib,json,tarfile,io,stat
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37';R=F/'pilot39-outcome-increment37-review-2026-10-12';sha=lambda b:hashlib.sha256(b).hexdigest();h=lambda p:sha(p.read_bytes())
s=json.loads((D/'SELECTION37.json').read_bytes());c=json.loads((D/'CAPTURE37.json').read_bytes());scope=json.loads((D/'TOOL_SCOPE01.json').read_bytes())
assert h(R/'SOURCE_REVIEW01.json')=='2df67ee86cc0fa7ad1433a7030e50ebd66ac365cae834d5713ea3319312c8172'
assert c['selection']['sha256']==h(D/'SELECTION37.json') and Path(c['selection']['path'])==D/'SELECTION37.json'
assert s['files']==c['files']==318 and len(s['directories'])==c['directories']==56 and s['symlinks']==0
assert s['exact_prior36_baseline_reused']==scope['baseline_pins'] and s['closed_scopes']==scope['closed_scopes']
t=ast.parse((D/'select37.py').read_text());helpers=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='helper_names' for x in n.targets));assert len(helpers)==13
rows={v['path']:v for v in s['rows']};assert len(rows)==318 and set(rows)=={v['path'] for v in scope['selected_pins']}|{str(D/n) for n in helpers}
for pin in scope['selected_pins']:
 assert rows[pin['path']]==dict(pin,type='regular')
expected=sorted(s['rows']+s['directories'],key=lambda x:x['path']);raw=Path(c['archive']['path']).read_bytes();assert len(raw)==c['archive']['bytes']==11663360 and sha(raw)==c['archive']['sha256']=='9356d093879b3c2dc2565ec11994e92adb29b793f1d574d37ec080a1528a770e'
rebuilt=io.BytesIO();total=0
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive,tarfile.open(fileobj=rebuilt,mode='w',format=tarfile.PAX_FORMAT) as encoded:
 members=archive.getmembers();assert [x.name for x in members]==[x['path'] for x in expected]
 for m,row in zip(members,expected,strict=True):
  assert m.mode==int(row['mode'],8) and m.uid==m.gid==m.mtime==0 and not m.uname and not m.gname
  assert set(m.pax_headers)<= {'path'} and ('path' not in m.pax_headers or m.pax_headers['path']==row['path'])
  item=tarfile.TarInfo(row['path']);item.mode=int(row['mode'],8);item.uid=item.gid=item.mtime=0
  if row['type']=='directory':assert m.isdir() and m.size==0;item.type=tarfile.DIRTYPE;encoded.addfile(item)
  else:
   assert row['type']=='regular' and m.isfile() and m.size==row['bytes'];body=archive.extractfile(m).read();assert sha(body)==row['sha256'];total+=len(body)
   p=Path(row['path']);st=p.lstat();assert stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==m.mode and st.st_size==len(body) and h(p)==row['sha256']
   item.size=len(body);encoded.addfile(item,io.BytesIO(body))
assert total==s['body_bytes']==c['regular_bytes']==11035256 and rebuilt.getvalue()==raw
print(json.dumps({'status':'PASS','files':318,'directories':56,'regular_bytes':total,'archive_bytes':len(raw),'archive_sha256':sha(raw),'exact_sorted_typed_pax_reencode':True,'current_selected_source_hashes_modes_join':True,'scope_pin_and13helper_roster_exact':True,'evidence':{str(p):h(p) for p in [D/'SELECTION37.json',D/'CAPTURE37.json',D/'TOOL_SCOPE01.json',D/'HELPERS_MANIFEST01.json',D/'select37.py',D/'capture37.py',D/'recover37.py',Path(c['archive']['path']),R/'SOURCE_REVIEW01.json']},'qualification':'Actual local captured scope only; opaque byte hashes, no decoding or filesystem extraction, no external return.'},indent=2))
