import sys,dataclasses as D,json,stat,ast
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.with_name('financial-batch-output-codec-spool-integration-preparation03-2026-10-04');sys.path.insert(0,str(A));import router06 as R
checks=[]
def ok(v,label):assert v,label;checks.append(label)
def refuse(fn,label):
 try:fn()
 except (ValueError,TypeError):checks.append(label);return
 raise AssertionError(label)
invs=[]
for k,name in enumerate(('one','two')):
 src=H/('successor-source-'+name);out=H/('successor-complete-recovered-%02d'%k);desc=R.C.parse(R.R.read(src,'start.json'))['descriptor'];tp=R.sha(R.R.read(src,'terminal.json'));inv=R.inspect(src,R.sha(('source-'+name).encode()),desc,tp);invs.append(inv)
 raw=bytearray()
 for f in inv.files:
  body=R.R.read(out,f.name);ok(body==R.R.read(src,f.name),'recovered exact '+name+'/'+f.name);ok(stat.S_IMODE((out/f.name).stat().st_mode)==0o600,'mode '+name+'/'+f.name)
  if f.kind=='chunk':
   payload=body[R.C.HEADER.size:-32];ok(len(payload)==f.raw_size and R.sha(payload)==f.raw_sha256 and len(raw)==f.raw_offset,'raw chunk ordered '+f.name);raw.extend(payload)
 ok(R.sha(raw)==inv.raw_sha256 and len(raw)==inv.logical_bytes,'whole raw '+name)
rt=R.route(tuple(invs),7);ok(len(rt.partitions)==14,'fourteen retained partitions');ok(sum(len(i.files) for i in invs)==95,'95 original files')
for n,p in enumerate(rt.partitions):
 for j,f in enumerate(p.files):
  for field,val in [('mode',384.0),('ordinal',float(f.ordinal)),('raw_offset',float(f.raw_offset)),('size',float(f.size)),('raw_size',float(f.raw_size))]:
   fs=list(p.files);fs[j]=D.replace(f,**{field:val});ps=list(rt.partitions);ps[n]=D.replace(p,files=tuple(fs));bad=D.replace(rt,partitions=tuple(ps));refuse(bad.pin,'typed partition %d/%d/%s'%(n,j,field))
  if f.kind=='chunk':
   fs=list(p.files);fs[j]=D.replace(f,raw_offset=f.raw_offset+4);ps=list(rt.partitions);ps[n]=D.replace(p,files=tuple(fs));refuse(D.replace(rt,partitions=tuple(ps)).pin,'derivative offset %d/%d'%(n,j))
 for field,val in [('target',False),('index',float(p.index)),('start',False)]:
  ps=list(rt.partitions);ps[n]=D.replace(p,**{field:val});refuse(D.replace(rt,partitions=tuple(ps)).pin,'typed partition coordinate')
 for field in ('logical_reservation','allocated_reservation'):
  ps=list(rt.partitions);ps[n]=D.replace(p,plan=D.replace(p.plan,**{field:getattr(p.plan,field)+1}));refuse(D.replace(rt,partitions=tuple(ps)).pin,'exact derivative plan')
refuse(lambda:R.production(),'production unavailable') if hasattr(R,'production') else None
ok(all(x not in sys.modules for x in ['numpy','torch','pandas','tradingagents.research.lifecycle']),'no science imports')
(H/'INDEPENDENT01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'scope':'opaque engineering bytes only'},indent=2)+'\n');print(len(checks))
