from pathlib import Path
H=Path(__file__).resolve().parent;S=Path.cwd()/'tradingagents/research/onchain_replication'
for n in ('stage_retention.py','stage_retention_reader.py'):(H/('original_'+n)).write_bytes((S/n).read_bytes())
s=(S/'stage_retention.py').read_text()
s=s.replace("_AUTH=WeakKeyDictionary()", "_AUTH=WeakKeyDictionary()\nINPUT_JSON_FIELD='max_selected_input_json_bytes'\nINPUT_JSON_MAX=1024**3-1")
s=s.replace("set(policy)==FIELDS", "set(policy) in (FIELDS,FIELDS|{INPUT_JSON_FIELD})",1)
s=s.replace("    require(policy['max_replays']>=2", "    if INPUT_JSON_FIELD in policy:\n        require(type(policy[INPUT_JSON_FIELD]) is int and 0<policy[INPUT_JSON_FIELD]<=INPUT_JSON_MAX,\n            'bounded selected input JSON allowance')\n    require(policy['max_replays']>=2",1)
point='def _inventory(root):'
helpers='''def selected_input_limit(policy):
    return policy.get(INPUT_JSON_FIELD,store.CONTROL)


def _input_record(name):
    p=Path(name)
    return len(p.parts)==2 and p.parts[0]=='inputs' and p.name.startswith('input-') and p.suffix=='.json'


def _record_limit(name,policy):
    return selected_input_limit(policy) if _input_record(name) else store.CONTROL


def _json_extent(value):
    """Exact ensure_ascii compact JSON extent without constructing encoded bodies."""
    if isinstance(value,str):
        size=2
        for char in value:
            code=ord(char)
            size+=(2 if char in '\\\\"\\b\\f\\n\\r\\t' else 6 if code<32 or 127<=code<=65535 else 12 if code>65535 else 1)
        return size
    if type(value) is int:return len(str(value))
    if type(value) in (list,tuple):return 2+max(0,len(value)-1)+sum(_json_extent(v) for v in value)
    if type(value) is dict:return 2+max(0,len(value)-1)+sum(_json_extent(k)+1+_json_extent(v) for k,v in value.items())
    raise ValueError('unsupported selected input metadata value')


def selected_input_bound(index,records):
    """Conservative JSON bound including all escaped IDs and six file descriptors.

    records contain original identities and actual numeric nbytes, not arrays.
    Header reserve256 bounds the existing asserted NPY representation below.
    """
    require(type(index) is int and 0<=index<2 and len(records)==2,'selected input member index')
    graphs=[]
    for direction,record in enumerate(records):
        files={}
        for name in ('node_features','edge_index','edge_features'):
            size=record['numeric_bytes'][name]
            require(type(size) is int and 0<=size<2**63,'selected input numeric extent')
            files[name]={'path':f'input-{index:012d}-{direction}-{name}.npy','bytes':size+256,'sha256':'0'*64}
        graphs.append({'node_ids':record['node_ids'],'parent_hash':record['parent_hash'],
            'center_id':record['center_id'],'typed_identity':'0'*64,'files':files})
    return _json_extent({'schema_version':1,'graphs':graphs})+1


def _input_records(graphs):
    return [{'node_ids':g.node_ids,'parent_hash':g.parent_hash,'center_id':g.center_id,
        'numeric_bytes':{n:getattr(g,n).nbytes for n in ('node_features','edge_index','edge_features')}} for g in graphs]


def _selected_raw(value,policy):
    # Extent refusal precedes encoding, including escaped strings, never truncate.
    maximum=selected_input_limit(policy)
    require(_json_extent(value)+1<=maximum,'selected input JSON capacity')
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n').encode()
    require(len(raw)<=maximum,'selected input JSON encoded extent');return raw


'''
s=s.replace(point,helpers+point)
s=s.replace("else store.CONTROL\n            raw=store._read(path,cap)","else _record_limit(str(path.relative_to(root)),policy)\n            raw=store._read(path,cap)",1)
s=s.replace("        ref=_write(self.root/name,value);self.expected[name]=ref;self._refresh();return ref", "        if INPUT_JSON_FIELD in self.policy and _input_record(name):\n            ref=store._write_bytes(self.root/name,_selected_raw(value,self.policy))\n        else:ref=_write(self.root/name,value)\n        self.expected[name]=ref;self._refresh();return ref",1)
s=s.replace("store._read(self.root/name,store.CONTROL))==sha", "store._read(self.root/name,_record_limit(name,self.policy)))==sha",1)
s=s.replace("    def _inputs(self,index,a,b):\n", "    def _inputs(self,index,a,b):\n        if INPUT_JSON_FIELD in self.policy:return self._inputs_bounded(index,a,b)\n",1)
anchor='    def _count(self):'
body='''    def _inputs_bounded(self,index,a,b):
        records=_input_records((a,b));metadata_upper=selected_input_bound(index,records)
        require(metadata_upper<=selected_input_limit(self.policy),'selected input JSON capacity before serialization')
        upper=sum(v+256 for r in records for v in r['numeric_bytes'].values())+metadata_upper
        self._reserve('inputs',input_bytes=upper,cumulative_bytes=upper+2*store.CONTROL,control_bytes=2*store.CONTROL)
        require(records==_input_records((a,b)) and metadata_upper==selected_input_bound(index,_input_records((a,b)))
            and [graph_identity(a),graph_identity(b)]==self.active['purpose']['typed_graphs'],
            'selected inputs changed across reservation callback')
        encoded=[];graphs=[]
        for direction,g in enumerate((a,b)):
            item={'node_ids':list(g.node_ids),'parent_hash':g.parent_hash,'center_id':g.center_id,
                'typed_identity':graph_identity(g),'files':{}}
            for name in ('node_features','edge_index','edge_features'):
                output=memory_io.BytesIO();np.save(output,getattr(g,name),allow_pickle=False);raw=output.getvalue();output.close()
                require(len(raw)<=getattr(g,name).nbytes+256,'selected numeric NPY header reserve')
                relative=f'input-{index:012d}-{direction}-{name}.npy'
                encoded.append((relative,raw));item['files'][name]={'path':relative,'bytes':len(raw),'sha256':io._hash(raw)}
            graphs.append(item)
        meta={'schema_version':1,'graphs':graphs};raw=_selected_raw(meta,self.policy)
        require(sum(len(v) for _,v in encoded)+len(raw)<=upper,'selected input serialization exceeded reservation')
        for name,body in encoded:
            store._write_bytes(self.root/'inputs'/name,body)
            self.input_files[name]={'bytes':len(body),'sha256':io._hash(body)};self._refresh()
        self._write(f'inputs/input-{index:012d}.json',meta);self.live()
'''
s=s.replace(anchor,body+anchor);(H/'stage_retention.py').write_text(s)
r=(S/'stage_retention_reader.py').read_text()
r=r.replace("meta=retention._read(root/'inputs'/name)","meta=json.loads(store._read(root/'inputs'/name,retention.selected_input_limit(policy)))")
r=r.replace("identities=[];input_upper+=store.CONTROL", "identities=[];numeric_records=[]\n        if retention.INPUT_JSON_FIELD not in policy:input_upper+=store.CONTROL")
r=r.replace("                actual=AttributedGraph", "                numeric_records.append({'node_ids':graph['node_ids'],'parent_hash':graph['parent_hash'],\n                    'center_id':graph['center_id'],'numeric_bytes':{k:v.nbytes for k,v in arrays.items()}})\n                actual=AttributedGraph")
r=r.replace("        require(identities==purpose['typed_graphs']", "        if retention.INPUT_JSON_FIELD in policy:\n            bound=retention.selected_input_bound(index,numeric_records)\n            require(bound<=retention.selected_input_limit(policy),'selected input JSON reservation bound')\n            input_upper+=bound\n        require(identities==purpose['typed_graphs']")
r=r.replace("proof=retention._read(obj/f'progress-{i:020d}.json')", "proof=json.loads(store._read(obj/f'progress-{i:020d}.json',store.control_limit(claim['pair_policy'])))")
r=r.replace("C=store.CONTROL;G=store.GENERATION_CONTROL;", "C=store.CONTROL;G=store.generation_control(claim['pair_policy']);SC=store.control_limit(claim['pair_policy']);")
r=r.replace("+s*7*C+n*3*C", "+s*(6*SC+C)+n*3*C")
(H/'stage_retention_reader.py').write_text(r)
