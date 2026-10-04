from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;B=H.parent;C=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();mapping=(C/'union-bytes01/ORIGINAL_TREES01.json').read_bytes();direct=json.loads((C/'UNION_AUTHENTICATION01.json').read_bytes())['direct_bodies'][0];pins={n:sha((C/n).read_bytes()) for n in ['union-manifest.json','SHARD_INDEX01.json','UNION_AUTHENTICATION01.json']};s=(H/'original-restore_sharded01.py').read_text();edits=[]
def edit(a,b,count=1):
 global s
 assert s.count(a)==count,(a,s.count(a));s=s.replace(a,b);edits.append({'old':a,'new':b,'count':count})
edit('import recovery04 as R','import recovery_pax01 as R')
edit("'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'","'recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2'")
edit("EXPECTED_ORIGINALS_SHA256='40b4002ee1b0edf1d2d4e4202cf3d5c98834eb9656b02558caedf40d7261dc30'","EXPECTED_ORIGINALS_SHA256="+repr(sha((H/'EXPECTED_ORIGINALS01.json').read_bytes()))+"\nDIRECT="+repr(direct)+"\nACTUAL_CAPTURE_PINS="+repr(pins))
a=s[s.index('def validate_expected_trees'):s.index('def request')];edit(a,"""def validate_expected_trees(trees):
 raw=R.read(H,'EXPECTED_ORIGINALS01.json');R.require(R.digest(raw)==EXPECTED_ORIGINALS_SHA256,'exact complete five-tree original census pin');expected=json.loads(raw)
 R.require(type(trees)is list and len(trees)==5 and trees==expected['scope_trees'],'complete exact five witness roots/membership/body/modes/literal links')
 return expected

""")
edit("'expected_shards','output_root','review','release'","'expected_shards','output_root','review','framer_review','direct_body','release'")
edit('financial-genuine-wrapper-claimedrun-final-union-sharded-flat-20261004-01','financial-genuine-wrapper-claimedrun-witness-sharded-flat-20261004-01')
edit(" for role in ('manifest','shard_index','union_auth'):selected_reference(q[role])",""" for role in ('manifest','shard_index','union_auth','direct_body'):selected_reference(q[role])
 R.require(q['direct_body']=={'path':DIRECT['source_path'],'bytes':DIRECT['bytes'],'sha256':DIRECT['sha256']},'sole exact actual raw direct body')
 for role,name in [('manifest','union-manifest.json'),('shard_index','SHARD_INDEX01.json'),('union_auth','UNION_AUTHENTICATION01.json')]:R.require(q[role]['sha256']==ACTUAL_CAPTURE_PINS[name],'exact actual witness capture pin')
 R.require(q['expected_members']==2703 and q['expected_files']==2302 and q['expected_shards']==57,'actual fixed witness capture counts')
 reference(q['framer_review'])""")
edit("decision':'accepted-exact-one-use-final-union-sharded-flat'","decision':'accepted-exact-one-use-witness-sharded-plus-direct-flat'")
edit("H,'restore_sharded01.py'","H,'restore_witness01.py'")
edit("row['git_mode'] in ('100644','100755')","row['git_mode'] in ('100644','100755') and (ref['path']!=DIRECT['source_path'] or row['git_mode']=='100644')")
edit("'regular_bodies','shards'}","'regular_bodies','shards','direct_bodies'}")
edit("index['kind']=='complete-final-union-shards-v1'","index['kind']=='complete-witness-shards-plus-direct-v1' and index['direct_bodies']==[DIRECT]")
edit("'schema_version','status','index','shard_count','union_mapping_sha256'","'schema_version','status','index','shard_count','direct_bodies','direct_regular_members','union_mapping_sha256'")
edit("auth['status']=='complete-final-caller-review-sharded-byte-capture'","auth['status']=='complete-witness-shards-plus-required-direct-body-capture' and auth['direct_bodies']==[DIRECT] and type(auth['direct_regular_members']) is int and auth['direct_regular_members']==1")
edit("'scope_trees','original_regular_logical_bytes'","'scope_trees','direct_bodies','direct_regular_bodies','archived_regular_bodies','original_regular_logical_bytes'")
edit(" trees=mapping['scope_trees'];validate_expected_trees(trees);"," R.require(mapping['direct_bodies']==[DIRECT] and type(mapping['direct_regular_bodies']) is int and mapping['direct_regular_bodies']==1 and type(mapping['archived_regular_bodies']) is int and mapping['archived_regular_bodies']==2301,'exact direct/archived count')\n trees=mapping['scope_trees'];validate_expected_trees(trees);")
edit("   expected.add(target);R.require(target in ordinary and ordinary[target]['kind']==kind,'complete virtual original member')","""   if kind=='file' and 'direct_source_path' in row:
    R.require(scope==DIRECT['scope'] and n==DIRECT['path'] and row['direct_source_path']==DIRECT['source_path'] and 'union_path' not in row and target not in ordinary and all(row[k]==DIRECT[k] for k in ('bytes','sha256','mode')),'exact sole direct original disjoint metadata');regular+=1;logical+=row['bytes'];continue
   expected.add(target);R.require(target in ordinary and ordinary[target]['kind']==kind,'complete virtual original member')""")
edit("'original_trees':20","'original_trees':5",2)
edit("mapping['original_regular_logical_bytes']==logical<=64*1024**2","mapping['original_regular_logical_bytes']==logical and logical+len(metadata_raw)<=64*1024**2 and q['expected_logical_bytes']+DIRECT['bytes']==logical+len(metadata_raw)")
edit('def run(q):',"""def restore_direct(out,body):
 R.require(len(body)==DIRECT['bytes'] and R.digest(body)==DIRECT['sha256'],'actual direct raw byte join')
 dest=out/'direct-selected';reserve(dest);path=dest/'original.body'
 with R.new_file(path) as fd:
  offset=0
  while offset<len(body):
   n=os.write(fd,body[offset:]);R.require(n>0,'short direct write');offset+=n
  os.fsync(fd)
 R.require(stat.S_IMODE(path.lstat().st_mode)==0o600 and R.read(dest,path.name)==body,'fresh private direct body actual readback')
 return {'descriptor':DIRECT,'file':'direct-selected/original.body','bytes':len(body),'sha256':R.digest(body),'original_mode_metadata_only':DIRECT['mode'],'actual_private_mode':384,'research_authority':False}

def run(q):""")
edit("base_refs=[q[k] for k in ('manifest','shard_index','union_auth')]","base_refs=[q[k] for k in ('manifest','shard_index','union_auth','direct_body')]")
edit("  ref=global_files['ORIGINAL_TREES01.json'];","  floor();direct_result=restore_direct(out,bodies[q['direct_body']['path']]);floor()\n  ref=global_files['ORIGINAL_TREES01.json'];")
edit("'shards':results,'union_semantic_joins':union","'shards':results,'direct_body':direct_result,'union_semantic_joins':union")
edit("'status':'COMPLETE_FINAL_UNION_SHARDED_ORDINARY_FLAT_BYTES'","'status':'COMPLETE_WITNESS_SHARDED_PLUS_DIRECT_ORIGINAL_BYTES'")
edit("'actual_shards':results,'union_semantic_joins':union","'actual_shards':results,'actual_direct_body':direct_result,'union_semantic_joins':union")
(H/'restore_witness01.py').write_text(s);(H/'INVERSE01.json').write_text(json.dumps({'edits':edits},indent=2)+'\n');(H/'ACTUAL_CAPTURE_PINS01.json').write_text(json.dumps({'pins':pins,'mapping_sha256':sha(mapping),'direct':direct,'census_sha256':sha((H/'EXPECTED_ORIGINALS01.json').read_bytes())},indent=2)+'\n')
