"""Deterministic integer-only preparation. Never loads graphs or grants authority.

Expected hashes MUST come from caller-authenticated metadata references, not from
an untrusted document alongside itself. Digest equality authenticates these bytes
against those arguments only; original provenance/admission remains external.
"""
import hashlib
import json
import re

LIMIT = 65536
META = 8192
INTEGER_MAX = 2**63 - 1
GRAPH_FIELDS = {'graph_sha256','nodes','edges','node_features','edge_features',
                'node_itemsize','edge_itemsize'}
LIMIT_FIELDS = {'extraction_limit','max_pair_entries','max_state_bytes',
                'normalization_chunk_entries','hardening_buffer_bytes',
                'max_score_buffer_bytes','max_checkpoint_bytes','max_file_bytes',
                'max_buffer_bytes','max_output_bytes','max_numeric_bytes','max_entries',
                'edge_chunk','score_chunk_edges','score_chunk_cells','log_chunk_events',
                'max_total_checkpoints'}


class MetadataUnavailable(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def need(ok, message):
    if not ok: raise ValueError(message)


def integer(value, name, zero=False):
    need(type(value) is int and (0 if zero else 1) <= value <= INTEGER_MAX,
         'invalid bounded integer: '+name)
    return value


def bounded(value):
    return integer(value, 'derived capacity', zero=True)


def sha(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SHA256 required')


def authenticate(value, expected, name):
    if value is None or expected is None:
        raise MetadataUnavailable(name+' and its authenticated digest are required')
    sha(expected)
    need(digest(value)==expected,name+' metadata digest differs')


def graph(item, extra):
    need(type(item) is dict and set(item)==GRAPH_FIELDS|extra,'graph metadata fields differ')
    sha(item['graph_sha256'])
    for field in GRAPH_FIELDS-{'graph_sha256'}: integer(item[field],field,zero=field=='edges')
    need(item['node_itemsize'] in (1,2,4,8) and item['edge_itemsize'] in (1,2,4,8),'unsupported numeric item width')


def prepare(topology, motifs, *, expected_topology_sha256, expected_motifs_sha256, limits):
    """Check every target maximum against every preserved original motif.

    Topology maximum is exact for node cardinality; global E is deliberately a
    conservative bound on induced directed edge columns (duplicates preserved).
    Storage figures are named components, never a total filesystem/RSS bound.
    Limits are explicit caller arguments; this function never modifies them.
    """
    authenticate(topology,expected_topology_sha256,'topology')
    authenticate(motifs,expected_motifs_sha256,'original motifs')
    need(type(topology) is dict and set(topology)=={'hop_depth','direction','includes_center','graphs'},'topology schema')
    need(type(topology['hop_depth']) is int and topology['hop_depth']==1 and topology['direction']=='weak'
         and topology['includes_center'] is True,'exact full weak-one-hop census required')
    need(type(motifs) is dict and set(motifs)=={'dictionary_sha256','dictionary_config_sha256','representatives'},'motif schema')
    sha(motifs['dictionary_sha256']);sha(motifs['dictionary_config_sha256'])
    targets=topology['graphs']; representatives=motifs['representatives']
    if type(representatives) is not list or not representatives:
        raise MetadataUnavailable('exact preserved representative dimensions are unavailable')
    need(type(targets) is list and bool(targets),'nonempty complete target list required')
    need(type(limits) is dict and set(limits)==LIMIT_FIELDS,'explicit complete capacity limits required')
    for name,value in limits.items():integer(value,name)
    need(limits['score_chunk_edges']<=65536,'bounded scoring chunk required')
    need(limits['score_chunk_cells']*80<=8*1024**2 and limits['log_chunk_events']*168<=8*1024**2,'bounded persistence chunks required')
    seen=set()
    for target in targets:
        graph(target,{'maximum_cardinality','maximum_center_index'})
        integer(target['maximum_cardinality'],'maximum_cardinality')
        integer(target['maximum_center_index'],'maximum_center_index',zero=True)
        need(target['maximum_cardinality']<=target['nodes'] and target['maximum_center_index']<target['nodes'],'census maximum outside graph')
        need(target['graph_sha256'] not in seen,'duplicate target');seen.add(target['graph_sha256'])
    for index,motif in enumerate(representatives):
        graph(motif,{'motif_index'})
        need(type(motif['motif_index']) is int and motif['motif_index']==index,'complete ordered motif dimensions required')
    maxima={}; refusals=[]; pairs=[]; stages=[]
    def requirement(name, value, limit=None, witness=None):
        bounded(value)
        if value>maxima.get(name,{}).get('required',-1):maxima[name]={'required':value,'witness':witness}
        if limit is not None and value>limits[limit]:
            refusals.append({'requirement':name,'required':value,'limit_field':limit,'available':limits[limit],'witness':witness})
    total_cells=total_scores=total_events=total_event_files=total_score_files=0
    for target in targets:
        n=target['maximum_cardinality']; N=target['nodes']; E=target['edges']; ident=target['graph_sha256']
        nw=target['node_features']*target['node_itemsize']; ew=target['edge_features']*target['edge_itemsize']
        index_bytes=16*(E+N+1)+16*E+40*(N+1)+4*N+limits['edge_chunk']*(64+2*nw+2*ew)
        local_bytes=n*nw+E*(16+ew)
        extraction=index_bytes+2*local_bytes
        requirement('extraction_nodes',n,'extraction_limit',ident)
        requirement('index_and_complete_output_upper_bytes',extraction,'max_buffer_bytes',ident)
        cells=bounded(N*len(representatives));output=bounded(4*cells)
        # Binary chunks contain records only; JSON headers are separate files.
        largest_score_chunk=min(cells,limits['score_chunk_cells'])
        largest_event_chunk=min(2*cells+limits['max_total_checkpoints'],limits['log_chunk_events'])
        requirement('score_tail_records_single_file_bytes',80*largest_score_chunk,'max_file_bytes',ident)
        requirement('float64_score_data_single_file_bytes',8*largest_score_chunk,'max_file_bytes',ident)
        requirement('pair_event_chunk_single_file_bytes',168*largest_event_chunk,'max_file_bytes',ident)
        requirement('persistence_json_single_file_allowance_bytes',META,'max_file_bytes',ident)
        requirement('mcm_entries',cells,'max_entries',ident)
        requirement('resident_mcm_output_bytes',output,'max_output_bytes',ident)
        requirement('kernel_declared_numeric_bytes',output+limits['max_buffer_bytes'],'max_numeric_bytes',ident)
        requirement('needed_extraction_plus_output_bytes',output+extraction,None,ident)
        chunks=(cells+limits['score_chunk_cells']-1)//limits['score_chunk_cells']
        events=2*cells # Progress events added globally below.
        scores=88*cells+(4*chunks+4)*META
        total_cells+=cells;total_scores+=scores;total_events+=events
        total_event_files+=(events+limits['log_chunk_events']-1)//limits['log_chunk_events']
        total_score_files+=4*chunks+4
        stages.append({'target':ident,'pair_occurrences':cells,'score_chunks':chunks,
                       'score_and_tail_logical_reservation_bytes':bounded(scores),
                       'induced_edge_columns_upper':E,'induced_edge_bound_kind':'global-E-conservative'})
        for motif in representatives:
            need(target['node_features']==motif['node_features'] and target['edge_features']==motif['edge_features'],'attribute dimensions mismatch')
            m=motif['nodes']; entries=bounded(n*m);witness={'target':ident,'center':target['maximum_center_index'],'motif':motif['motif_index']}
            state=32*entries;checkpoint=state+512+3*LIMIT
            normal=max(m,n if m==1 else 2*n)
            hard=17*entries+n+m+16*min(n,m)
            score=80*min(n,m)+32*min(limits['score_chunk_edges'],motif['edges'])
            for name,value,cap in [('pair_entries',entries,'max_pair_entries'),('retained_pair_state_bytes',state,'max_state_bytes'),
                ('normalization_axis_entries',normal,'normalization_chunk_entries'),('hardening_explicit_bytes',hard,'hardening_buffer_bytes'),
                ('score_only_explicit_bytes',score,'max_score_buffer_bytes'),('logical_checkpoint_bytes',checkpoint,'max_checkpoint_bytes'),
                ('checkpoint_single_array_file_bytes',8*entries+128,'max_file_bytes')]:requirement(name,value,cap,witness)
            hard_meta={'version':1,'safe':True,'phase':'scan','shape':[n,m],
                       'input_sha256':'0'*64,'max_pair_entries':limits['max_pair_entries'],
                       'max_explicit_bytes':limits['hardening_buffer_bytes'],'cursor':entries,
                       'pairs':[],'order_sha256':'0'*64,'order_bytes':8*entries+128}
            # Worst digit-width bound for all min(n,m) retained greedy pairs.
            hard_meta_bytes=len(json.dumps(hard_meta,sort_keys=True,separators=(',',':')))+1
            hard_meta_bytes+=min(n,m)*(len(str(n-1))+len(str(m-1))+4)-1
            requirement('hardening_manifest_upper_bytes',hard_meta_bytes,None,witness)
            if hard_meta_bytes>LIMIT:
                refusals.append({'requirement':'hardening_manifest_upper_bytes','required':hard_meta_bytes,
                    'limit_field':'fixed_hardening_manifest_limit','available':LIMIT,'witness':witness,
                    'qualification':'conservative digit-width envelope; exact realized pairs unknown'})
            # Per selected retained pair: six arrays (+256 header bound each), one control.
            mw=motif['node_features']*motif['node_itemsize']; mew=motif['edge_features']*motif['edge_itemsize']
            retained_inputs=local_bytes+m*mw+motif['edges']*(16+mew)+6*256+16384
            requirement('retained_pair_input_upper_bytes',retained_inputs,None,witness)
            input_file=max(n*nw,E*16,E*ew,m*mw,motif['edges']*16,motif['edges']*mew)+256
            requirement('retained_input_single_file_upper_bytes',input_file,'max_file_bytes',witness)
            pairs.append({'witness':witness,'pair_entries':entries,'state_bytes':state,'normalization_axis_entries':normal,
                          'checkpoint_bytes':checkpoint,'checkpoint_max_regular_files':7,'checkpoint_max_directories_including_root':3})
    generations=limits['max_total_checkpoints']; cp=maxima['logical_checkpoint_bytes']['required']
    # Scalar metadata accounting only; cannot predict numerical convergence/generations.
    progress_files=(generations+limits['log_chunk_events']-1)//limits['log_chunk_events']
    event_bytes=(total_events+generations)*168+2*META*len(targets)
    components={'all_target_pair_occurrences':bounded(total_cells),'score_and_tail_logical_bytes':bounded(total_scores),
                'pair_event_logical_bytes':bounded(event_bytes),'event_chunk_files_upper':bounded(total_event_files+progress_files+len(targets)),
                'score_and_tail_files_upper':bounded(total_score_files),
                'per_generation_state_regular_files_upper':7,'per_generation_state_directories_including_root':3,
                'all_permitted_checkpoint_publication_bytes':bounded(generations*(cp+2*META)),
                'all_permitted_checkpoint_state_files_upper':bounded(7*generations),
                'per_selected_pair_input_files':7,'checkpoint_generation_budget':generations}
    return {'execution_admitted':False,'complete_resource_envelope_proven':False,'metadata_checks_satisfied':True,'reported_limits_satisfied':not refusals,
            'topology_sha256':expected_topology_sha256,'motifs_sha256':expected_motifs_sha256,
            'dictionary_sha256':motifs['dictionary_sha256'],'dictionary_config_sha256':motifs['dictionary_config_sha256'],
            'limits':dict(limits),'universal_component_envelopes':maxima,'refusals':refusals,'pairs':pairs,'stages':stages,
            'storage_components':components,
            'unresolved':['Caller must establish complete target/motif coverage and authenticate original references.',
                          'Global E may overstate induced edges; selected-input Python IDs/control serialization size is unproved.',
                          'Hardening manifest uses conservative digit-width bound; Python IDs, native sort/SciPy scratch, graph validation and process RSS need separate admission.',
                          'Total filesystem includes retention controls/replay/generation policy, archive transfer/control, journal and other roots; components here are not a complete storage reservation.',
                          'Checkpoint count is an explicit schedule budget, not a completion guarantee.']}
