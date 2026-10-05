from pathlib import Path
import sys,json,hashlib,ast,os
D=Path(__file__).resolve().parent;sys.path[:0]=[str(D),str(D/'utilities')];import outcome01 as O
R=O.R;pop=json.loads((D/'POPULATION01.json').read_text());capture=O.ROOT/pop['capture']['path'];raw=R.read(capture.parent,capture.name);c=O.context(raw);assert [len(x) for x in O.LANES]==[7,7,6,6] and set(sum((list(x) for x in O.LANES),[]))==set(range(26))
try:O.selected_required({'status':'DRAFT_NOT_RELEASED'},0,c)
except (ValueError,KeyError):pass
else:raise AssertionError('draft accepted')
# Reused genuine PAX/flat utility, four tiny independent engineering lanes.
results=[]
for i in range(4):
 source=D/('tiny2-source-%d'%i);selected=D/('tiny2-selected-%d'%i);output=D/('tiny2-flat-%d'%i)
 for p in (source,selected,output):p.mkdir(mode=0o700)
 data=b'opaque-engineering-lane-'+str(i).encode();(source/'data').write_bytes(data);os.chmod(source/'data',0o600);m=R.scan(source);mr=R.encode(m);(selected/'manifest.json').write_bytes(mr);os.chmod(selected/'manifest.json',0o600);a=R.pack(source,m,selected/'archive.tar.gz')
 q={'bundles':[{'name':'opaque','archive':{'path':'archive.tar.gz','bytes':a['bytes'],'sha256':a['sha256']},'manifest':{'path':'manifest.json','bytes':len(mr),'sha256':R.digest(mr)}}]};res=O.restore_archives(q,selected,output,lambda:None);meta=json.loads((output/'flat-opaque'/res['opaque']['metadata_file']).read_bytes());assert (output/'flat-opaque'/meta['flat_members']['data']).read_bytes()==data;results.append({'lane':i,'opaque_exact':True})
P=D.parent/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05'
for n in ('watch01.py','cohort01.py','receipt01.py','recover.template01.py','caller_remote01.py','caller_flat01.py'):assert (D/n).read_bytes()==(P/n).read_bytes()
for n in ('recovery_pax01.py','owned_io.py','bounded_git01.py'):assert (D/'utilities'/n).read_bytes()==(P/'utilities'/n).read_bytes()
a={n.name:ast.dump(n) for n in ast.parse((P/'restore_bundle01.py').read_text()).body if isinstance(n,ast.FunctionDef)};b={n.name:ast.dump(n) for n in ast.parse((D/'flat_primitives01.py').read_text()).body if isinstance(n,ast.FunctionDef)};assert all(a[n]==v for n,v in b.items())
for p in D.glob('*.py'):ast.parse(p.read_text())
(D/'CHECKS02.json').write_text(json.dumps({'actual_capture_manifest_authenticated':True,'full_original845_1074_coverage':True,'four_fixed_lane_counts':[7,7,6,6],'draft_refused':True,'four_tiny_PAX_roundtrips':results,'primitive_bytes_AST_unchanged':True,'actual_remote_or_lane_execution':False},indent=2)+'\n');print('actual metadata closure and four tiny PAX roundtrips passed')
