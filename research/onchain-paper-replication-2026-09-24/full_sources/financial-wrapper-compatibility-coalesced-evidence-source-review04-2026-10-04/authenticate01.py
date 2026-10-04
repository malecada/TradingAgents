from pathlib import Path
import os,stat,json,hashlib,ast,types
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-coalesced-evidence-correction04-2026-10-04';R=D.parent/'financial-wrapper-compatibility-composed-recovery-review02-2026-10-04';checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def raw(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p,'known regular bounded');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);b=b''
 try:
  t=os.fstat(fd);ok((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns),'actual descriptor join')
  while c:=os.read(fd,65536):b+=c;ok(len(b)<=4194304,'actual byte cap')
 finally:os.close(fd)
 ok(len(b)==s.st_size and p.lstat()==s,'actual regular unchanged');return b
pins={'copy_layout01.py':'fcadbfcde1bf9d9d61887af27de2dff610b5d7cce188a4cb77da1c99d6989fda','INPUTS01.json':'5c4c9ebbc976d057a1896f106c18fc00c8c0a179e2beaf047bc5ed329ea40f04','MANIFEST01.json':'83b5754bc4a01d3fcc56eee89001233daeca7871ac55c81f8879b6bff9f6ca1f','MACHINE01.json':'efa861a6210a8f8ed071d563aea9daf5a8e80f14773c3e27ed11e7b3056ce844'}
for n,pin in pins.items():ok(h(raw(P/n))==pin,'fixed author pin '+n)
seal=json.loads(raw(P/'MANIFEST01.json'));rows={x['path']:x for x in seal['members']};ok(len(rows)==len(seal['members']),'unique author seal');actual=set()
for root,ds,fs in os.walk(P,followlinks=False):
 for n in ds+fs:
  p=Path(root)/n;rel=p.relative_to(P).as_posix()
  if rel=='MANIFEST01.json':continue
  actual.add(rel);x=rows[rel];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==x['mode'],'literal mode')
  if x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'actual dir')
  elif x['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'],'literal symlink not followed')
  else:ok(stat.S_ISREG(s.st_mode) and s.st_nlink==x['nlink'] and s.st_size==x['bytes'] and h(raw(p))==x['sha256'],'actual typed regular body')
ok(actual==set(rows),'complete435 author namespace');spec=json.loads(raw(P/'INPUTS01.json'));closure=json.loads(raw(R/'CLOSURE01.json'));ok(h(raw(R/'MANIFEST01.json'))=='4c1bafac000b164f4534e0308169214c9fd7f3f72cab2f4389a1647e6ada3cde','genuine source review seal');origins=closure['provenance'];ok(len(origins)==51,'actual51 old origins');oldpairs={(x['path'],x['original_path'],x['sha256'],x['bytes'],x['original_mode'],x['copy_mode']) for x in origins};newpairs={(x['path'],x['original_path'],x['sha256'],x['bytes'],x['original_mode'],x['copy_mode']) for x in spec['rows'] if x['role'] in ('receipt','source-evidence')};ok(oldpairs==newpairs,'all51 original entries exactly preserved');ok(len(spec['rows'])==57 and sum(x['role']=='receipt' for x in spec['rows'])==38 and sum(x['role']=='source-evidence' for x in spec['rows'])==13,'actual57/38/13');ok(sum(x['bytes'] for x in spec['rows'])==1384187,'exact byte denominator')
for x in spec['rows']:
 for key,mkey in [('path','copy_mode'),('original_path','original_mode')]:
  p=Path(x[key]);b=raw(p);ok(h(b)==x['sha256'] and len(b)==x['bytes'] and stat.S_IMODE(p.lstat().st_mode)==x[mkey] and p.lstat().st_nlink==1,'every exact input/original body/mode')
M=types.ModuleType('copier');M.__file__=str(P/'copy_layout01.py');exec(compile(raw(P/'copy_layout01.py'),M.__file__,'exec'),M.__dict__)
for b,n,pin in [(M.PRECLAIM_BYTES,'preclaim01.py','557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'),(M.OWNED_IO_BYTES,'owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb')]:ok(b==raw(P/n) and h(b)==pin and ast.dump(ast.parse(b))==ast.dump(ast.parse(raw(P/n))),'complete embedded byte/AST dependency pin')
# Independent genuine 57-body component copy into this review's owned ordinary engineering scope, never fixed public output.
r=M.PC.Reader();r.read(P/'INPUTS01.json');result=M.copy_layout(spec,D/'owned-complete57',r);ok(result['status']=='DRAFT_COPIED_NOT_AUTHORITY' and result['copied_regular_bodies']==57 and result['receipt_bodies']==38 and r.total<8388608,'actual full component57 under8MiB');draft=json.loads(raw(D/'owned-complete57/DRAFT_LAYOUT01.json'));ok(all(draft[k] is None for k in ('new_accepted_machine','new_accepted_report','new_review_manifest','final_parent','actual_root_exit','whole_preclaim8MiB_fit')),'no fabricated accepted authority');copied={x['destination']:x for x in spec['rows']}
for x in spec['rows']:ok(h(raw(D/'owned-complete57'/x['destination']))==x['sha256'],'all57 copiedbytes independently rehash')
for n in ('MACHINE01.json','MANIFEST01.json','REPORT01.md'):
 row=copied['concrete-policy/'+n];ok(row['role']=='receipt' and row['output_mode']==row['original_mode'] and {'path':str(D/'owned-complete57'/row['destination']),'sha256':row['sha256']} in draft['receipt_candidates'],'three genuine same-path receipt coalescences')
reader=M.PC.Reader();manifestref=draft['review_reference_candidates']['manifest'];manifest=json.loads(reader.reference(manifestref))
for n in ('proof','machine','report'):M.PC._sealed(manifest,manifestref,draft['review_reference_candidates'][n],reader)
reader.finish();ok(not M.OUTPUT.exists(),'fixed Root not invoked');out={'checks':len(checks),'author_pins':pins,'typed_author_members':len(rows),'literal_input_rows':len(spec['rows']),'retained_originals':len(origins),'complete_component_result':result,'proof_seal_component_passed':True,'no_fixed_public_entry':True,'authority_granted':False,'deadline_defect_reviewed_separately':True};(D/'AUTHENTICATION01.json').write_text(json.dumps(out,indent=2)+'\n');print(len(checks),r.total)
