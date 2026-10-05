"""Final complete cross-lane bytes/current originals; no new research authority."""
from outcome01 import *
from original_tree01 import inventory,signatures,unchanged

def join(request,request_sha,release,release_sha):
 R.require(HERE==lane_root(3,'flat'),'final join belongs to the fourth fixed flat root');W.census(HERE)
 inputs=VerifiedCohort()
 def body(ref):
  p=Path(ref['path']);b=input_read(inputs,p.parent,p.name);R.require(len(b)==ref['bytes'] and R.digest(b)==ref['sha256'],'actual final proof pin');return b
 raw=input_read(inputs,HERE,request);R.require(R.digest(raw)==request_sha,'actual final join request');q=json.loads(raw);rel=input_read(inputs,HERE,release);R.require(R.digest(rel)==release_sha,'actual final join release')
 R.require(json.loads(rel)=={'schema_version':1,'decision':'ACCEPTED_EXACT_FOUR_LANE_JOIN','request_sha256':request_sha,'source_sha256':R.digest(input_read(inputs,HERE,'join01.py')),'numerical_authority':False},'independent cross-lane release')
 R.require(len(q['lanes'])==4,'all four actual lanes');c=context(body(q['capture']));body(q['source407_basis']);outputs=VerifiedCohort();seen=set();original_pins={}
 for i,lane in enumerate(q['lanes']):
  receipt=json.loads(body(lane['receipt']));body(lane['review']);R.require(receipt['lane']==i and receipt['capture_sha256']==CAPTURE and receipt['piece_ids']==list(LANES[i]),'actual exact lane receipt');root=lane_root(i,'flat')
  for j in LANES[i]:
   p=c['pieces'][j];name='piece-%03d'%j;r=receipt['scopes'][name];flat=root/('flat-'+name);raw=outputs.read(flat,r['metadata_file']);R.require(R.digest(raw)==r['metadata_sha256'],'actual full flat metadata');m=json.loads(raw);R.validate(m['manifest']);R.require(R.digest(R.encode(m['manifest']))==p['archive_pin']['manifest_sha256'],'canonical original piece manifest');mapping=m['flat_members'];expected={b['member']:(b['bytes'],b['sha256']) for b in p['bodies']};R.require(set(mapping)==set(expected),'complete cross-lane flat names');outputs.tree(flat,set(mapping.values())|{r['metadata_file']})
   for b in p['bodies']:
    key=(b['role'],b['path']);R.require(key not in seen,'original body repeated across lanes');seen.add(key);raw=outputs.read(flat,mapping[b['member']]);R.require((len(raw),R.digest(raw))==expected[b['member']],'complete current restored original body')
  W.check()
 R.require(len(seen)==845,'all845 originals recovered')
 for role,v in c['originals'].items():
  root=Path(v['root']);before=signatures(root,v['manifest']);R.require(inventory(root,role=='capsule')==v['manifest'],'current entire original capsule/Parent differs');original_pins.update(before)
 R.require(not os.path.lexists(HERE/'FOUR_LANE_RECOVERY01.json'),'fresh final composition receipt')
 R.put(HERE/'FOUR_LANE_RECOVERY01.json',{'schema_version':1,'capture_sha256':CAPTURE,'complete_original_files':845,'original_typed':1074,'original_raw_bytes':77970429,'piece_count':26,'lanes':4,'source':SOURCE,'Git407':'separate pinned baseline reused','POSIX':False,'numerical_authority':False,'request_sha256':request_sha})
 inputs.read(HERE,'FOUR_LANE_RECOVERY01.json')
 for attr in ('pins','byte_proofs','trees','anchors'):
  target=getattr(inputs,attr);source=getattr(outputs,attr);R.require(all(k not in target or target[k]==v for k,v in source.items()),'cross-lane proof agreement');target.update(source)
 for path,pin in original_pins.items():R.require(path not in inputs.pins or inputs.pins[path]==pin,'original/evidence agreement')
 W.census(HERE);inputs.check();unchanged(original_pins)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--release',required=True);p.add_argument('--release-sha256',required=True);a=p.parse_args();join(a.request,a.sha256,a.release,a.release_sha256)
