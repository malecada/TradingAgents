"""Complete typed inventory hierarchy; every new file uses actual8KiB serializer."""
import hashlib,json,pathlib,re,stat,time
META=8192;FILE=4*1024**2;ENTRIES=32768;PAGES=2048;FANOUT=32;GIB=1024**3
POLICY={'schema_version':1,'kind':'refusal-complete-inventory-v1','max_encoded_file_bytes':META,'max_encoded_row_bytes':FILE,'max_members':ENTRIES,'max_leaf_pages':PAGES,'max_fanout':FANOUT,'max_index_levels':2,'publication_entry_headroom_required':True,'raw_authentication_seconds':30}
TAIL=('authenticated-refusal.json','terminal.json','post-tail-storage.json','post-terminal-failure.json')
def require(value,message):
    if not value:raise ValueError(message)
def encode(value):return (json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def member(row):
    require(type(row) is dict and row.get('kind') in ('file','directory'),'inventory member kind differs')
    fields={'path','bytes','allocated','kind'}|({'sha256'} if row['kind']=='file' else set())
    require(set(row)==fields and type(row['path']) is str and 0<len(row['path'])<=2048,'inventory member fields/path bound')
    p=pathlib.PurePosixPath(row['path']);require(not p.is_absolute() and '..' not in p.parts and str(p)==row['path'],'inventory member path is not canonical relative')
    require(all(type(row[k]) is int and 0<=row[k]<=GIB for k in ('bytes','allocated')),'inventory member extent differs')
    if row['kind']=='file':require(row['bytes']<=FILE and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'inventory file extent/hash differs')
    return row

def prepare(index,identity):
    """Validate and size every body BEFORE caller publishes even the first page."""
    require(type(identity) is str and re.fullmatch('[a-zA-Z0-9-]{1,96}',identity) is not None,'bounded inventory identity required')
    require(set(index)=={'schema_version','root','members','root_allocated','tail_exclusion'} and type(index['schema_version']) is int and index['schema_version']==1,'original inventory schema differs')
    rows=index['members'];require(type(rows) is list and len(rows)<=ENTRIES,'inventory entry denominator exceeds bound')
    require(type(index['root']) is str and pathlib.PurePosixPath(index['root']).is_absolute() and len(index['root'])<=2048 and type(index['root_allocated']) is int and 0<=index['root_allocated']<=GIB,'inventory original root differs')
    paths=[];aggregate=0;groups=[];group=[]
    def page(values):return {'schema_version':1,'kind':'refusal-inventory-page-v1','identity':identity,'members':values}
    for row in rows:
        member(row);paths.append(row['path']);aggregate+=len(encode(row));require(aggregate<=FILE,'inventory encoded row aggregate exceeds4MiB')
        require(len(encode(page([row])))<=META,'unsupported encoded inventory row exceeds8KiB before publication')
        if group and len(encode(page(group+[row])))>META:groups.append(group);group=[]
        group.append(row)
    if group:groups.append(group)
    require(paths==sorted(set(paths)) and len(groups)<=PAGES,'inventory sorted unique member/page denominator differs')
    files=[];refs=[]
    def add(name,value,count):
        raw=encode(value);require(len(raw)<=META,'inventory encoded envelope exceeds8KiB');files.append((name,value));return {'path':name,'sha256':digest(raw),'bytes':len(raw),'members':count}
    for i,g in enumerate(groups):refs.append(add('inventory-page-'+str(i).zfill(4)+'.json',page(g),len(g)))
    level=0
    while len(refs)>FANOUT:
        next_refs=[]
        for i in range(0,len(refs),FANOUT):
            children=refs[i:i+FANOUT];count=sum(r['members'] for r in children)
            value={'schema_version':1,'kind':'refusal-inventory-index-v1','identity':identity,'level':level,'children':children,'member_count':count}
            next_refs.append(add('inventory-index-'+str(level)+'-'+str(i//FANOUT).zfill(4)+'.json',value,count))
        refs=next_refs;level+=1;require(level<=2,'inventory hierarchy depth exceeded')
    value={'schema_version':1,'kind':'refusal-complete-inventory-v1','identity':identity,'root':index['root'],'root_allocated':index['root_allocated'],'children':refs,'level':level,'member_count':len(rows),'encoded_row_bytes':aggregate,'page_count':len(groups),'inventory_files':len(files)+1,'tail_names':list(TAIL),'directory_extents':'Original prepublication observations; subsequent directory growth counted by actual post-tail storage watch.'}
    add('inventory.json',value,len(rows));return files

def publish(root,outer,index,identity,save):
    plan=prepare(index,identity)
    # Inventory files and at most four tail files must themselves fit the same
    # global watched entry denominator; do not pretend the row cap reserves room.
    require(len(index['members'])+1+len(plan)+len(TAIL)<=ENTRIES,'inventory/tail publication has no watched entry headroom')
    require(sum(row['bytes'] for row in index['members'] if row['kind']=='file')+sum(len(encode(v)) for n,v in plan)+len(TAIL)*META<=GIB,'inventory/tail logical headroom unavailable')
    for name,value in plan:save(name,value)
    return authenticate(root,outer,identity)

def authenticate(root,outer,identity,expected=None):
    """Read complete hierarchy, original members/hashes and only finite own tail."""
    from raw_receipts01 import body
    root=pathlib.Path(root);outer=pathlib.Path(outer);prefix=str(outer.relative_to(root));start=time.monotonic()
    require(outer.resolve()==outer and outer.is_relative_to(root),'inventory outer redirected')
    def read(name):
        require('/' not in name and re.fullmatch(r'inventory(?:-page-[0-9]{4}|-index-[01]-[0-9]{4})?\.json',name) is not None,'inventory reference name differs')
        raw=body(root,prefix+'/'+name,META);value=json.loads(raw);require(encode(value)==raw,'inventory encoding/noncanonical duplicate fields differ');return raw,value
    raw,index=read('inventory.json');reference={'path':prefix+'/inventory.json','sha256':digest(raw),'bytes':len(raw)}
    if expected is not None:require(reference==expected,'original inventory root reference changed')
    require(index.get('kind')=='refusal-complete-inventory-v1' and index.get('schema_version')==1 and index.get('identity')==identity and index.get('root')==str(root),'inventory root authority differs')
    require(set(index)=={'schema_version','kind','identity','root','root_allocated','children','level','member_count','encoded_row_bytes','page_count','inventory_files','tail_names','directory_extents'} and index['tail_names']==list(TAIL),'inventory root schema/tail denominator differs')
    seen={'inventory.json'};rows=[];page_count=0
    def children(refs,level):
        nonlocal page_count
        require(type(level) is int and 0<=level<=2 and type(refs) is list and len(refs)<=FANOUT,'finite inventory level/fanout differs')
        total=0
        for ref in refs:
            require(type(ref) is dict and set(ref)=={'path','sha256','bytes','members'} and ref['path'] not in seen,'duplicate inventory page/reference')
            seen.add(ref['path']);data,value=read(ref['path']);require(digest(data)==ref['sha256'] and len(data)==ref['bytes'],'inventory child original bytes differ')
            require(type(value.get('schema_version')) is int and value['schema_version']==1 and value.get('identity')==identity,'inventory child identity differs')
            if level==0:
                require(set(value)=={'schema_version','kind','identity','members'} and value['kind']=='refusal-inventory-page-v1' and type(value['members']) is list and value['members'],'inventory leaf differs');count=len(value['members']);rows.extend(member(r) for r in value['members']);page_count+=1
            else:
                require(set(value)=={'schema_version','kind','identity','level','children','member_count'} and value['kind']=='refusal-inventory-index-v1' and value['level']==level-1,'inventory branch differs');count=children(value['children'],level-1);require(count==value['member_count'],'inventory branch count differs')
            require(type(ref['members']) is int and ref['members']==count,'inventory reference count differs');total+=count
            require(len(rows)<=ENTRIES and len(seen)<=2115 and page_count<=PAGES and time.monotonic()-start<=30,'inventory authentication finite bound exceeded')
        return total
    require(children(index['children'],index['level'])==index['member_count'] and page_count==index['page_count'] and len(seen)==index['inventory_files'],'inventory complete denominator differs')
    require(sum(len(encode(r)) for r in rows)==index['encoded_row_bytes']<=FILE,'inventory encoded rows differ')
    paths=[r['path'] for r in rows];require(paths==sorted(set(paths)),'inventory member omission/order/duplicate differs')
    expected_plan=prepare({'schema_version':1,'root':index['root'],'members':rows,'root_allocated':index['root_allocated'],'tail_exclusion':'reader reconstruction'},identity)
    require({n for n,v in expected_plan}==seen,'inventory noncanonical hierarchy membership')
    for name,value in expected_plan:
        actual,value_actual=read(name);require(actual==encode(value),'inventory complete canonical hierarchy differs')
    observed=[]
    for path in root.rglob('*'):
        rel=str(path.relative_to(root));require(path.resolve()==path and path.lstat().st_dev==root.stat().st_dev,'inventory current member redirected');observed.append(rel)
        require(len(observed)<=ENTRIES and time.monotonic()-start<=30,'current tree finite bound exceeded')
    own={prefix+'/'+n for n in seen}|{prefix+'/'+n for n in TAIL if (outer/n).exists()}
    require(set(paths).isdisjoint(own) and set(observed)==set(paths)|own,'inventory original/current member set differs')
    for row in rows:
        path=root/row['path'];info=path.lstat()
        if row['kind']=='file':require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==row['bytes'] and info.st_blocks*512==row['allocated'] and digest(body(root,row['path']))==row['sha256'],'inventory original raw file changed')
        else:require(stat.S_ISDIR(info.st_mode),'inventory original directory changed')
        require(time.monotonic()-start<=30,'inventory raw verification deadline exceeded')
    return reference
