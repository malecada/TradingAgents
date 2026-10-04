from pathlib import Path
import json,hashlib,stat,os,ast,subprocess,sys
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-wrapper-compatibility-final-bundle-transport-preparation02-2026-10-05';A=F/'financial-wrapper-compatibility-final-bundle-transport-preparation01-2026-10-04';checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def read(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304 and p.resolve()==p,'bounded ordinary source');b=p.read_bytes();ok(p.lstat()==s and len(b)==s.st_size,'current source read');return b
seal=json.loads(read(P/'MANIFEST01.json'));ok(h(read(P/'MANIFEST01.json'))=='0397cd77dd98624b051f0d779540f45265f0ca71c00e0c339cf6927ee697bb9a','author complete seal pin');ok(h(read(P/'MACHINE01.json'))=='c7115ab6090ff42f20a996784738b47bf9cd50a7160469c48abcfc9b4beff594','author machine pin');seen=set()
for x in seal['members']:
 p=P/x['path'];seen.add(x['path']);s=p.lstat();ok(stat.S_IMODE(s.st_mode)==x['mode'],'exact mode')
 if x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory')
 else:ok(len(read(p))==x['bytes'] and h(read(p))==x['sha256'],'source seal body')
ok(seen=={p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST01.json'},'full45 author population')
pins={'watch01.py':'bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18','utilities/owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','utilities/bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f','utilities/recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','cohort01.py':'0bf4cb4ca7f2ce8182b775614be4c54b577f4959852fe191186195a8b0ad75ab'}
for round in ('BASELINE','FINAL_SUPPLEMENT'):
 for n,pin in pins.items():ok(h(read(P/round/n))==pin,'reused exact accepted primitive')
 binder=read(P/round/'binding01.py').decode();ok("ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')" in binder,'fixed actual Main ROOT')
# Original accepted receiver exact whole-source inverse; no network or helper entry.
s=read(P/'recover.template01.py').decode();inv=json.loads(read(A/'SOURCE_INVERSE01.json'))
for edit in reversed(inv['literal_edits']):ok(s.count(edit['new'])==1,'exact receiver seam');s=s.replace(edit['new'],edit['old'])
original=read(A/'ORIGINAL_REMOTE01.py');ok(s.encode()==original and h(original)=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf' and ast.dump(ast.parse(s))==ast.dump(ast.parse(original)),'whole accepted remote inverse')
# Reuse only author54 changed-seam controls; do not replay older generic matrices.
script=read(P/'check01.py').decode().replace('D=Path(__file__).resolve().parent',"D=Path("+repr(str(P))+")");(D/'seam_replay01.py').write_text(script);r=subprocess.run([sys.executable,'-B',str(D/'seam_replay01.py')],capture_output=True,timeout=20);(D/'SEAM_REPLAY01.stdout').write_bytes(r.stdout);(D/'SEAM_REPLAY01.stderr').write_bytes(r.stderr);ok(r.returncode==0 and json.loads(r.stdout)['checks']==54,'exact54 changed-seam controls')
# Actual envelope is an independent dependency, not fabricated by this review.
envelope=F/'financial-wrapper-compatibility-preclaim-baseline-envelope01-2026-10-05/ENVELOPE01.json';availability={'path':str(envelope),'exists':envelope.exists(),'validated':False}
if envelope.exists():availability['sha256']=h(read(envelope))
(D/'AUTHENTICATION01.json').write_text(json.dumps({'checks':len(checks),'author_typed_members':len(seen),'changed_seam_controls':54,'unchanged_primitive_pins':pins,'whole_receiver_inverse':True,'actual_envelope':availability,'actual_commit_selection_validated':False,'actual_entry':False,'flat_release':False,'reason':'FT02_INPUT_COHORT_AFTER_RECEIPT'},indent=2)+'\n');print(len(checks),availability)
