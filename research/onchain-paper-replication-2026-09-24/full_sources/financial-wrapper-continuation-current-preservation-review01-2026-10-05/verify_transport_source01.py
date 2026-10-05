"""Exact three-body transport source and actual159-file archive, no public entry."""
from pathlib import Path
import sys,os,stat,json,ast,hashlib,importlib.util
H=Path(__file__).resolve().parent;F=H.parent;T=F/'financial-wrapper-continuation-current-transport-preparation01-2026-10-05';OLD=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation04-2026-10-05';sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'));from verify_capture01 import Reader,R
rd=Reader();sealed=json.loads(rd.read(T/'MANIFEST02.json','b466592af2fc2d24c5eb7e784588a5b543b7b3584cf166520eb6e82a21485c7f'))
# Exact declared bodies; no source-specific control matrices are replayed.
for row in sealed['members']:
 p=T/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'author declared modes')
 if row['kind']=='file':rd.need(len(rd.read(p,row['sha256']))==row['bytes'],'all author sealed source/evidence bytes')
 else:rd.need(row['kind']=='directory' and stat.S_ISDIR(s.st_mode),'ordinary author directory')
unchanged=('caller_remote01.py','caller_flat01.py','recover.template01.py','receipt01.py','restore_bundle01.py','flat_primitives01.py','cohort01.py','watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py')
for n in unchanged:rd.need(rd.read(T/n)==rd.read(OLD/n),'entire accepted immutable body unchanged: '+n)
new=rd.read(T/'outcome01.py','9e28b4ec5e3ef3e7e280378a82dd93484837c5f6820fc1e3d1c2824f3a9aff42');old=rd.read(OLD/'outcome01.py');nf={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)};of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};rd.need(ast.dump(nf['request_core_sha256'])==ast.dump(of['request_core_sha256']),'exact accepted signing predicate')
# Reuse bounded source import only: no entry, subprocess or restore invocation.
sys.path[:0]=[str(T),str(T/'utilities')];spec=importlib.util.spec_from_file_location('transport_outcome',T/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
craw=rd.read(T/'CAPTURE01.json',O.CAPTURE);c=O.context(craw);mr=rd.read(T/c['manifest'],c['archive_pin']['manifest_sha256']);m=json.loads(mr);R.validate(m);ar=rd.read(T/c['archive'],c['archive_pin']['sha256']);rd.need(len(ar)==c['archive_pin']['bytes']==699833 and len(m['members'])==175 and sum(r['kind']=='file' for r in m['members'])==159 and sum(r.get('bytes',0) for r in m['members'])==3411804,'actual frozen full archive denominator');expected={r['path']:r for r in m['members']};found={};seen=set();it=R.framed_members(ar);primary=None
try:
 for name,t,b in it:
  rd.need(name in expected and name not in seen,'exact archive names');seen.add(name);row=expected[name];rd.need(t.mode==row['mode'] and t.uid==t.gid==0 and t.mtime==0 and t.uname==t.gname=='','canonical PAX metadata')
  if row['kind']=='file':rd.need(t.isfile() and len(b)==t.size==row['bytes'] and R.digest(b)==row['sha256'],'every archived opaque byte');found[name]=b
  else:rd.need(t.isdir() and t.size==0,'exact archived directory')
except BaseException as e:primary=e
R._cleanup((it.close,),primary=primary)
if primary is not None:raise primary
rd.need(seen==set(expected),'complete all175 actual members');rd.tree(T/'snapshot',m)
for n,b in found.items():rd.need(rd.read(T/'snapshot'/n,R.digest(b))==b,'actual snapshot bytes')
sink=R.Sink();R.tar_stream(T/'snapshot',m,sink);rd.need(sink.count==len(ar) and sink.hash.hexdigest()==R.digest(ar),'exact canonical PAX framing/compression')
table=json.loads(found['ORIGIN_TABLE01.json']);rd.need(R.digest(found['ORIGIN_TABLE01.json'])==c['origin_table_sha256'] and table['literal_links_only'] is True and table['all_originals_retained'] is True,'actual original mode/link table');deps=json.loads(rd.read(H/'TRANSPORT_DEPENDENCIES01.json','dd10413fce4f83fbe2f86ca36367633771092e2152ab89654b381b19312fb1bb'))
expected_scopes={Path(x['path']).name:(Path(x['path']),'MANIFEST01.json',x['manifest_sha256']) for x in deps['closed_scopes']};expected_scopes[H.name]=(H,'SOURCE_PHASE_MANIFEST01.json','2bd0a0f7a5639c743ddb9bcee5e937e59ba6976d3b344f38d85c30bd50f370e4');rd.need(set(table['scopes'])==set(expected_scopes)==set(c['origin_scopes']),'all declared scopes and no future files')
links=[]
for scope,(root,sealname,h) in expected_scopes.items():
 sealraw=rd.read(root/sealname,h);seal=json.loads(sealraw);orig=table['scopes'][scope];rd.need(orig['root']==str(root) and [r for r in orig['members'] if r['path']!=sealname]==seal['members'],'exact closed or source-snapshot membership');rd.need(found[scope+'/'+sealname]==sealraw,'real source seal returned')
 for row in orig['members']:
  p=root/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'actual original source mode')
  if row['kind']=='file':rd.need(found[scope+'/'+row['path']]==rd.read(p,row['sha256']),'all159 archived original source/basis bytes')
  elif row['kind']=='symlink':rd.need(stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target'] and scope+'/'+row['path'] not in found,'link text preserved only');links.append(str(p))
  else:rd.need(stat.S_ISDIR(s.st_mode),'actual typed original dir')
actual_basis={r['path']:r for r in table['basis']};rd.need(table['basis']==c['basis'] and set(actual_basis)=={r['path'] for r in deps['additional_exact_metadata_refs']},'complete24 exact dependency paths')
for ref in deps['additional_exact_metadata_refs']:
 row=actual_basis[ref['path']];rd.need(all(row[k]==v for k,v in ref.items()) and found[row['snapshot_path']]==rd.read(Path(ref['path']),ref['sha256']),'exact genuinely accepted dependency body')
prefix='financial-wrapper-continuation-current-preservation-preparation01-2026-10-05/';selection=json.loads(found[prefix+'SELECTED_BODIES02.json']);rd.need(len(selection['bodies'])==27,'all actual incremental payload bodies')
for row in selection['bodies']:rd.need(len(found[prefix+row['path']])==row['bytes'] and R.digest(found[prefix+row['path']])==row['sha256'],'all27 source/Parent/proof/Git-tail payloads')
required=O.expected_required(c);rd.need(len(required)==3 and sum(v['bytes'] for v in required.values())==759580,'exact3 body transfer');O.W.check();rd.finish()
result={'schema_version':1,'decision':'ACCEPTED_EXACT_THREE_BODY_TRANSPORT_SOURCE_AND_LOCAL_CAPTURE_ONLY','source':O.SOURCE,'capture_sha256':O.CAPTURE,'archive_sha256':R.digest(ar),'manifest_sha256':R.digest(mr),'regular':159,'typed':175,'logical_bytes':3411804,'selected_body_count':3,'selected_bytes':759580,'expected_Git_operations':19,'old818_raw_reread':False,'new_transport_sources_in_transfer':False,'literal_link_metadata':links,'unchanged_accepted_primitives':list(unchanged),'canonical_PAX_reencoding':True,'original27_payloads_verified':True,'basis_refs':24,'source_phase_immutable':True,'checks':rd.checks,'read_bytes':rd.total,'remote_entry_release':None,'flat_entry_release':None,'numerical_authority':False,'qualifications':['flat outer caller evidence paths are receiver-relative, not Main-relative as report says','both receiver ls-remote observations require exact selected commit; a later remote push requires rebinding before entry','future final Parent request and authority are additive to recovered source-bound draft; no recursive proof capture']};R.put(H/'TRANSPORT_SOURCE_READBACK01.json',result);print(json.dumps(result))
