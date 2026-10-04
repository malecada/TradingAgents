from pathlib import Path
import json,hashlib,sys,importlib.util,io
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-complete100-failed-preservation-tooling02-2026-10-04';C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';sys.path.insert(0,str(A));spec=importlib.util.spec_from_file_location('flat_review02',A/'restore01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);R=m.R;sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
cap=json.loads((C/'CAPTURE01.json').read_bytes());s=m.load_scopes(C,cap);m.validate_union(C,cap,s)
for label,row in s.items():
 raw=(C/('complete-'+label+'01.tar.gz')).read_bytes();frames=list(R.framed_members(raw));ok(len(frames)==len(row['manifest']['members']),'complete frames '+label)
 for (name,t,b),r in zip(frames,row['manifest']['members']):ok(name==r['path']and t.mode==r['mode']and ((r['kind']=='directory'and t.isdir()and not b)or(r['kind']=='file'and t.isfile()and len(b)==r['bytes']and sha(b)==r['sha256'])),'actual opaque frame '+label+'/'+name)
 sink=io.BytesIO();R.tar_stream(Path(cap['scopes'][label]['snapshot']),row['manifest'],sink);ok(sink.getvalue()==raw,'canonical archive '+label)
# Source remains same10-scope utility; fresh exact aligned opaque roundtrip.
t=D/'flat-tiny';t.mkdir(mode=0o700);bundle=t/'bundle';bundle.mkdir(mode=0o700);small={}
for label in m.LABELS:
 p=t/('source-'+label);p.mkdir(mode=0o700);(p/'opaque').write_bytes(label.encode());mf=R.scan(p);arc=R.pack(p,mf,bundle/('complete-'+label+'01.tar.gz'));small[label]={'manifest':mf,'archive':arc}
out=t/'out';out.mkdir(mode=0o700);calls=[];result=m.restore_scopes(bundle,small,out,lambda:calls.append(1));ok(len(result)==10 and len(calls)==40,'fresh10scope40boundaries')
for label,r in result.items():
 meta=json.loads(R.read(out/('flat-'+label+'01'),r['metadata_file']));ok(meta['manifest']==small[label]['manifest'],'tiny literalmetadata '+label);ok(R.read(out/('flat-'+label+'01'),meta['flat_members']['opaque'])==label.encode(),'tiny literalbody '+label)
try:m.restore_scopes(bundle,small,out,lambda:None)
except ValueError:checks.append('oneuse replay refuses')
else:raise AssertionError('replay')
(D/'DOMAIN02.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'actual_Root_restore':False,'actual_scope_count':len(s)},indent=2,sort_keys=True)+'\n');print(len(checks))
