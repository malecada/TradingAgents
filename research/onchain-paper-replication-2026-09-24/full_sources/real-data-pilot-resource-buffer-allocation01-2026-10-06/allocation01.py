"""Scalar selected-route arithmetic; no resource admission or numerical authority."""
ARCHIVE_MAX=8*1024**2
TYPED_MAX=4*1024**2
META=8192


def need(ok,message):
    if not ok:raise ValueError(message)


def positive(n):need(type(n) is int and 0<n<2**63,'finite positive integer required')


def graph(rows,chunk_cells,tail_part,output_part,pair_chunk):
    for n in (rows,chunk_cells,tail_part,output_part,pair_chunk):positive(n)
    need(chunk_cells<=65536 and tail_part<=TYPED_MAX and tail_part%80==0
         and output_part<=TYPED_MAX and output_part%4==0 and pair_chunk<=ARCHIVE_MAX,'selected original chunk bounds differ')
    cells=rows*32;full,last=divmod(cells,chunk_cells);batches=full+bool(last)
    tail_parts=full*((80*chunk_cells+tail_part-1)//tail_part)+(0 if not last else (80*last+tail_part-1)//tail_part)
    actual_cells=min(cells,chunk_cells);tail=actual_cells*80;batch=actual_cells*8
    tp=min(tail_part,tail);op=min(output_part,cells*4)
    # All graph output matrices are charged separately, never also in scratch.
    # A get's staging and linked destination are the same inode, not two bodies.
    # A live partial pair chunk can coexist with typed tail/batch work.
    disk={'pair_preserve_with_unsealed_tail':3*pair_chunk+tail+batch,
          'tail_part_preserve':pair_chunk+tail+batch+3*tp,
          'tail_semantic_recovery':pair_chunk+tail+batch+tp,
          'batch_preserve_before_tail_disposal':pair_chunk+tail+3*batch,
          'closed_batch_recovery_for_cast':batch,
          'output_part_preserve':3*op}
    required={'score-tail-f64':{'max_preserved_bytes':cells*80,'max_recovered_bytes':cells*80,
                              'max_chunks':2*tail_parts,'max_operations':batches},
              'score-batch-f64':{'max_preserved_bytes':cells*8,'max_recovered_bytes':cells*8,
                               'max_chunks':2*batches,'max_operations':batches+1},
              'mcm-output-f32':{'max_preserved_bytes':cells*4,'max_recovered_bytes':0,
                              'max_chunks':(cells*4+output_part-1)//output_part,'max_operations':1}}
    # Each typed preserve/read attempt leaves three successful compact bodies;
    # allow a fourth failure marker at each attempt conservatively. These are
    # outside _Operation._publish's ledger-only typed control accumulator.
    attempts=2*tail_parts+2*batches+required['mcm-output-f32']['max_chunks']
    return {'rows':rows,'cells':cells,'batch_count':batches,'tail_preserve_parts':tail_parts,
            'required_typed_allowances':required,'retained_matrix_logical_bytes':cells*4,
            'selected_payload_overlap_upper_bytes':max(disk.values()),'phase_logical_payload_bounds':disk,
            'typed_attempt_metadata_allowance_bytes':attempts*4*META,
            'typed_attempt_directory_count':attempts,
            'ram_lexical_payload_extents':{'tail_records_file_bytes':tail,'live_batch_bytes':batch,
                'tail_part_bytes':tp,'output_part_bytes':op,'pair_parse_bytes':pair_chunk},
            'qualification':'Conservative selected payload overlap, not total store/RAM. Parsing copies, numerical resident objects, retained control bodies, allocation rounding and directory metadata require separate accounting.'}


def check_typed_allowances(result,actual):
    for kind,required in result['required_typed_allowances'].items():
        for key,n in required.items():
            need(type(actual[kind][key]) is int and actual[kind][key]>=n,
                 'mandatory original traversal underfunded: '+kind+'/'+key)


def allocated_file_upper(logical_bytes,file_count,allocation_unit):
    for n in (file_count,allocation_unit):positive(n)
    need(type(logical_bytes) is int and logical_bytes>=0,'logical bytes required')
    # Regular-file rounding only. Filesystem metadata, sparse/COW semantics and
    # directories are not inferred from this value.
    return logical_bytes+file_count*(allocation_unit-1)
