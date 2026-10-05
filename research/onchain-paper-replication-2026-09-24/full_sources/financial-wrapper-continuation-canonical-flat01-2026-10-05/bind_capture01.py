"""Bind actual canonical delta bytes to a fresh source bundle; no entry or authority."""
import argparse,json,os,shutil,time
from pathlib import Path
import outcome01 as O
R=O.R
SOURCE_ROOT=O.ROOT/Path(O.CAPTURE_PATH).parent
BOUND_ROOT=O.F/'financial-wrapper-continuation-canonical-transport-bound01-2026-10-05'
def pin(v):R.require(type(v)is str and len(v)==64 and all(x in '0123456789abcdef' for x in v),'actual non-null SHA256');return v
def prepare(capture_sha,manifest_sha,archive_sha):
 start=time.monotonic();provided={'CAPTURE01.json':pin(capture_sha),'archive-manifest.json':pin(manifest_sha),'increment.tar.gz':pin(archive_sha)};bodies={};fingerprints={}
 def tick():R.require(time.monotonic()-start<120,'finite120s binding');R.require(shutil.disk_usage(O.HERE).free>=R.FLOOR,'10GiB floor')
 for n,p in provided.items():
  tick();before=R.sig((SOURCE_ROOT/n).lstat());raw=R.read(SOURCE_ROOT,n);R.require(R.sig((SOURCE_ROOT/n).lstat())==before and R.digest(raw)==p,'actual stable declared delta pin');bodies[n]=raw;fingerprints[SOURCE_ROOT/n]=before
 c=json.loads(bodies['CAPTURE01.json']);m=json.loads(bodies['archive-manifest.json']);R.validate(m)
 R.require(c['kind']=='continuation-current-incremental-byte-capture' and c['source']==O.SOURCE and c['numerical_authority'] is False and c['external_recovery'] is False and c['old818_copied'] is False,'actual canonical scope/exclusions')
 R.require(c['archive']=='increment.tar.gz' and c['manifest']=='archive-manifest.json' and c['archive_pin']=={'bytes':len(bodies['increment.tar.gz']),'sha256':archive_sha,'manifest_sha256':manifest_sha},'actual archive/manifest framing pins')
 R.require(c['typed']==len(m['members']) and c['regular']==sum(r['kind']=='file' for r in m['members']) and c['logical_bytes']==sum(r.get('bytes',0) for r in m['members']) and c['logical_bytes']<=28*1024**2,'actual complete finite counts')
 for n in O.HELPERS:
  tick();before=R.sig((O.HERE/n).lstat());raw=R.read(O.HERE,n);R.require(R.sig((O.HERE/n).lstat())==before,'helper changed through read cleanup');bodies[n]=raw;fingerprints[O.HERE/n]=before
 raw=bodies['outcome01.py'];needle=b'CAPTURE=None';R.require(raw.count(needle)==1,'one exact unbound capture literal');bodies['outcome01.py']=raw.replace(needle,('CAPTURE='+repr(capture_sha)).encode())
 # All actual input reads/cleanup have completed. No alias/currentness promise beyond this final sample.
 for p,s in fingerprints.items():tick();R.require(R.sig(p.lstat())==s,'late binding input changed')
 tick();return bodies,{'schema_version':1,'source':O.SOURCE,'capture_sha256':capture_sha,'manifest_sha256':manifest_sha,'archive_sha256':archive_sha,'required':{str(Path(O.CAPTURE_PATH).parent/n):{'bytes':len(bodies[n]),'sha256':provided[n]} for n in provided},'files':{n:{'bytes':len(v),'sha256':R.digest(v)} for n,v in bodies.items()},'actual_remote_commit':None,'actual_remote_receipt':None,'actual_flat_receipt':None,'release':None,'numerical_authority':False}
def materialize(bodies):
 R.require(not os.path.lexists(BOUND_ROOT) and BOUND_ROOT.parent.resolve()==BOUND_ROOT.parent,'fixed fresh bound-source directory');R.require(sum(map(len,bodies.values()))<=64*1024**2,'bounded source bundle');start=time.monotonic();BOUND_ROOT.mkdir(mode=0o700);(BOUND_ROOT/'utilities').mkdir(mode=0o700)
 for name,raw in bodies.items():
  R.require(time.monotonic()-start<120 and shutil.disk_usage(BOUND_ROOT).free>=R.FLOOR,'finite source publication/floor');R.path_name(name)
  with R.new_file(BOUND_ROOT/name) as fd:
   offset=0
   while offset<len(raw):n=os.write(fd,raw[offset:]);R.require(n>0,'short source write');offset+=n
   os.fsync(fd)
  R.require(R.read(BOUND_ROOT,name)==raw,'bound-source byte readback')
 R.require(time.monotonic()-start<120 and shutil.disk_usage(BOUND_ROOT).free>=R.FLOOR,'final publication bound')
def main():
 p=argparse.ArgumentParser();p.add_argument('--capture-sha256',required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--materialize',action='store_true');a=p.parse_args();bodies,receipt=prepare(a.capture_sha256,a.manifest_sha256,a.archive_sha256)
 if a.materialize:materialize(bodies)
 print(json.dumps(dict(receipt,Root_materialized=a.materialize),sort_keys=True))
if __name__=='__main__':main()
