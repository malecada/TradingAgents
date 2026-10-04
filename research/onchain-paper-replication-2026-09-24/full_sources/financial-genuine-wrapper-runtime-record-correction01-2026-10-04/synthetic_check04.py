import copy,hashlib,importlib.util,importlib.metadata as M,json,os,sys,sysconfig
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');sys.path.insert(0,str(CAP));spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.record_synthetic_candidate',ROOT/'candidate.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C);owned=ROOT/'opaque_controls04';owned.mkdir();site=owned/'site';site.mkdir();meta=site/'tiny_pkg-1.0.dist-info';meta.mkdir();record=meta/'RECORD';metadata=meta/'METADATA';metadata.write_bytes(b'Name: tiny-pkg\nVersion: 1.0\n\nopaque synthetic distribution\n');body=b'tiny_pkg-1.0.dist-info/RECORD,,\ntiny_pkg/_vendor/vendor-2.0.dist-info/RECORD,,\n';record.write_bytes(body);vendor=site/'tiny_pkg/_vendor/vendor-2.0.dist-info';vendor.mkdir(parents=True);(vendor/'RECORD').write_bytes(b'opaque vendored RECORD');row={'name':'tiny-pkg','version':'1.0','record':str(record),'record_sha256':hashlib.sha256(body).hexdigest()};checks=[]
def good(name,value):assert value,name;checks.append(name)
def refuses(name,f):
 try:f()
 except (C.Unavailable,ValueError,OSError,TypeError,KeyError):checks.append(name)
 else:raise AssertionError(name)
with patch.object(sys,'prefix',str(owned)),patch.object(sysconfig,'get_path',lambda k:str(site)):
 good('actual-own-metadata-valid',C._runtime_record(row)['record']==str(record));d=next(iter(M.distributions(path=[str(site)],name='tiny-pkg')));good('old-vendored-record-ambiguity',len([f for f in d.files if str(f).endswith('.dist-info/RECORD')])==2)
 for field,values in {'name':['',None,42,'../bad','other'], 'version':['',None,42,'2.0'], 'record':[None,42,'../bad',str(record)+'/../RECORD',str(metadata)],'record_sha256':[None,42,'g'*64,'0'*64]}.items():
  for index,v in enumerate(values):
   q=copy.deepcopy(row);q[field]=v;refuses(field+str(index),lambda:C._runtime_record(q))
 for value in (None,[],{},dict(row,extra=True)):refuses('row-schema-'+str(type(value)),lambda:C._runtime_record(value))
 for name in ('tiny_pkg','Tiny.Pkg','TINY-PKG'):q=dict(row,name=name);good('normalized-name-'+name,C._runtime_record(q)['name']=='tiny-pkg')
 # Own genuine duplicate metadata roots, with identical Name and Version.
 duplicate=site/'tiny_pkg-9.0.dist-info';duplicate.mkdir();(duplicate/'METADATA').write_bytes(metadata.read_bytes());(duplicate/'RECORD').write_bytes(b'opaque');refuses('duplicate-installed-origin',lambda:C._runtime_record(row));duplicate.rename(owned/'retained-duplicate');M.MetadataPathFinder.invalidate_caches()
 old=metadata.read_bytes()
 for i,b in enumerate((b'Name: wrong\nVersion: 1.0\n',b'Name: tiny-pkg\nVersion: 2.0\n',b'Name: tiny-pkg\nName: tiny-pkg\nVersion: 1.0\n',b'Name: tiny-pkg\nVersion: 1.0\nVersion: 1.0\n',b'Name: tiny-pkg\n')):
  metadata.write_bytes(b);refuses('metadata-header-'+str(i),lambda:C._runtime_record(row));(owned/('bad-metadata-'+str(i))).write_bytes(b)
 metadata.write_bytes(old)
 record.rename(meta/'RECORD.saved');refuses('missing-record',lambda:C._runtime_record(row));record.mkdir();refuses('directory-record',lambda:C._runtime_record(row));record.rename(meta/'RECORD.directory');record.symlink_to('RECORD.saved');refuses('redirect-record',lambda:C._runtime_record(row));record.rename(meta/'RECORD.symlink');(meta/'RECORD.saved').rename(record)
 # A legitimate unchanged runtime hardlink is not a second installed origin.
 os.link(metadata,owned/'metadata-hardlink');good('metadata-hardlink-supported',C._runtime_record(row)['version']=='1.0')
 external=owned/'source';external.mkdir();egg=external/'tiny_pkg.egg-info';egg.mkdir();(egg/'PKG-INFO').write_bytes(b'Name: tiny-pkg\nVersion: 9.9\n');sys.path.insert(0,str(external))
 try:
  good('default-lookup-shadow-demonstrated',M.version('tiny-pkg')=='9.9');good('explicit-installation-excludes-source-shadow',C._runtime_record(row)['version']=='1.0')
 finally:sys.path.remove(str(external))
 # Metadata site origin must remain canonical and within pinned interpreter prefix.
 with patch.object(sysconfig,'get_path',lambda k:str(owned/'missing')):refuses('wrong-installed-site',lambda:C._runtime_record(row))
 with patch.object(sysconfig,'get_path',lambda k:str(site/'..'/'site')):refuses('noncanonical-site',lambda:C._runtime_record(row))
assert not any(x in sys.modules for x in ('numpy','pandas','torch','scipy'))
print(json.dumps({'checks':len(checks),'names':checks,'no_numerical_imports':True,'scope':'owned tiny real dist-info/egg-info metadata; no real Run/Owner/claim'},sort_keys=True))
