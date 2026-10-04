import dataclasses as D,json
from pathlib import Path
import router05 as A
P=Path(__file__).resolve().parent;root=P/'new-source';desc=A.C.parse(A.R.read(root,'start.json'))['descriptor'];terminal=A.sha(A.R.read(root,'terminal.json'));inv=A.inspect(root,'b'*64,desc,terminal);route=A.route((inv,),4);rows=[]
class Text(str):pass
class Bytes(bytes):pass

def refuse(label,fn):
 try:fn()
 except (ValueError,TypeError) as e:rows.append({'case':label,'error':type(e).__name__,'message':str(e)})
 else:raise AssertionError(label+' accepted')
for k in ('ordinal','size','mode','raw_offset','raw_size'):
 v=getattr(inv.files[0],k)
 for tag,value in [('float',float(v)),('bool',bool(v))]:
  bad=D.replace(inv,files=(D.replace(inv.files[0],**{k:value}),)+inv.files[1:])
  refuse('File.'+k+'-'+tag,lambda bad=bad:A.current(bad))
for k in ('name','kind','sha256','raw_sha256'):
 bad=D.replace(inv,files=(D.replace(inv.files[0],**{k:Text(getattr(inv.files[0],k))}),)+inv.files[1:])
 refuse('File.'+k+'-subclass',lambda bad=bad:A.current(bad))
for k in ('target_key','root','terminal_sha256','raw_sha256'):
 bad=D.replace(inv,**{k:Text(getattr(inv,k))});refuse('Inventory.'+k+'-subclass',lambda bad=bad:A.current(bad))
for k,value in [('descriptor',Bytes(inv.descriptor)),('descriptor',bytearray(inv.descriptor)),('logical_bytes',float(inv.logical_bytes)),('logical_bytes',True),('files',list(inv.files)),('root_identity',list(inv.root_identity)),('original_signatures',list(inv.original_signatures))]:
 bad=D.replace(inv,**{k:value});refuse('Inventory.'+k+'-'+type(value).__name__,lambda bad=bad:A.current(bad))
for j in range(3):
 fields=list(inv.root_identity);fields[j]=float(fields[j]);bad=D.replace(inv,root_identity=tuple(fields));refuse('root-identity-float-'+str(j),lambda bad=bad:A.current(bad))
for j in range(7):
 fields=list(inv.original_signatures[0][1]);fields[j]=float(fields[j]);bad=D.replace(inv,original_signatures=((inv.original_signatures[0][0],tuple(fields)),)+inv.original_signatures[1:]);refuse('file-signature-float-'+str(j),lambda bad=bad:A.current(bad))
for value in (list(inv.original_signatures[0]),(inv.original_signatures[0][0],list(inv.original_signatures[0][1]))):
 bad=D.replace(inv,original_signatures=(value,)+inv.original_signatures[1:]);refuse('nested-signature-list',lambda bad=bad:A.current(bad))
for k in ('target','index','start'):
 for value in (False,0.0):
  bad=D.replace(route,partitions=(D.replace(route.partitions[0],**{k:value}),)+route.partitions[1:]);refuse('Partition.'+k+'-'+type(value).__name__,lambda bad=bad:A.validate_route(bad))
for k,value in [('inventories',list(route.inventories)),('partitions',list(route.partitions)),('members_per_plan',4.0),('members_per_plan',True)]:
 bad=D.replace(route,**{k:value});refuse('Route.'+k+'-'+type(value).__name__,lambda bad=bad:A.validate_route(bad))
part=route.partitions[0]
for k,value in [('files',list(part.files)),('files',(D.replace(part.files[0],mode=384.0),)+part.files[1:])]:
 bad=D.replace(route,partitions=(D.replace(part,**{k:value}),)+route.partitions[1:]);refuse('nested-partition-'+type(value).__name__,lambda bad=bad:A.validate_route(bad))
A.validate_route(route)
(P/'STRICT01.json').write_text(json.dumps({'count':len(rows),'rows':rows,'original_route_passes':True,'callbacks_invoked':0},sort_keys=True,indent=2)+'\n');print(len(rows),'strict refusals passed')
