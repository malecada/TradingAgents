"""Exclusive registered representation producers and exact completed reuse.

The outer experiment owns guard enforcement and post-death reconciliation.
This module does not launch, admit, restart, or silently retry a research job.
"""
from dataclasses import asdict
import json
from pathlib import Path
from ..lifecycle import ResearchRun,_lock,_immutable
from .cache import cache_key
from .neighborhoods import graph_hash
from .feature_pipeline import prepare_features,PreparedFeatures,representation_arm
from .feature_journal import FeatureJournal,read_feature_journal
from .serialization import dictionary_from_record
from .provenance import canonical_bytes,digest,file_hash,durable_mkdir


def representation_descriptor(graphs,examples,fold,arm,seed,configs):
    """Metadata to register after source admission and before representation fitting."""
    population=sorted(graph_hash(g) for g in graphs)
    required=sorted({h for x in (*examples.train,*examples.test) for h in x.graph_hashes})
    if not required or len(population)!=len(set(population)):raise ValueError('invalid graph population')
    return {'graph_population':population,'required_graphs':required,'fold':asdict(fold),
            'train_hash':examples.train_hash,'arm':representation_arm(arm),'seed':seed,'configs':configs}


def prepare_registered_features(run,producer,graphs,examples,fold,arm,seed,configs,*,
        plan_input,max_entries,max_array_bytes,continuation_input=None):
    if not isinstance(run,ResearchRun):raise ValueError('admitted representation run required')
    graphs=tuple(graphs)
    descriptor=representation_descriptor(graphs,examples,fold,arm,seed,configs)
    identity=cache_key(descriptor)
    run._active();run._check_source()
    plan=json.loads(run.read_input(plan_input))
    if plan.get('schema_version')!=1 or producer not in plan['producers']:raise ValueError('unregistered representation producer')
    item=plan['producers'][producer]
    if canonical_bytes(item['descriptor'])!=canonical_bytes(descriptor):raise ValueError('registered representation science differs')
    if item['max_entries']!=max_entries or item['max_array_bytes']!=max_array_bytes:raise ValueError('registered representation resource bounds differ')
    output=item['binding_output']
    journal_output=item['journal_output']
    if output==journal_output or not {output,journal_output}<=set(run.admission.experiment['outputs']):raise ValueError('unregistered representation binding/journal output')
    # Bind every actual graph to an input manifest or an output published by
    # this admitted run. This never authorizes acquisition of missing arrays.
    if set(item['graphs'])!=set(descriptor['graph_population']):raise ValueError('registered graph population differs')
    for h,reference in item['graphs'].items():
        if set(reference)=={'input'}:raw=run.read_input(reference['input'])
        elif set(reference)=={'output'}:
            p=run.directory/'outputs'/reference['output'];raw=p.read_bytes()
            if run._published_outputs.get(reference['output'])!=digest(raw):raise ValueError('graph output not published by this run')
        else:raise ValueError('one graph binding reference required')
        metadata=json.loads(raw)
        if metadata['graph_hash']!=h:raise ValueError('actual graph differs from admitted manifest')
    if continuation_input is not None:run.read_input(continuation_input)
    with _lock(run.admission.root):
        run._active();run._check_source()
        root=run.admission.root/'research_artifacts/onchain_representations'/identity
        durable_mkdir(root);prior=sorted(root.iterdir());parent=None;state=None
        owner={'experiment':run.admission.experiment_id,'source_commit':run.admission.source,
               'producer':producer,'workflow_identity':identity}
        if prior:
            if continuation_input is None:raise FileExistsError('representation already owned; use registered exact reuse or successor')
            parent_id=run.admission.experiment['parent']
            if parent_id is None or parent_id==run.admission.experiment_id:raise ValueError('new registered parent required')
            run_parent=run.admission.root/'research_runs'/parent_id
            if not (run_parent/'failed.json').is_file() or (run_parent/'complete.json').exists():raise ValueError('parent run active or complete')
            info=run.admission.inputs[continuation_input]
            path=run.admission.root/info['path']
            if path.resolve()!=(root/parent_id/'failed.json').resolve():raise ValueError('continuation is not failed parent representation')
            if any((p/'complete.json').exists() for p in prior):raise ValueError('complete numerical representation must be reused')
            if any(not (p/'failed.json').exists() for p in prior):raise ValueError('active representation owner remains')
            metadata=json.loads(path.read_bytes());parent={'path':str(path.resolve()),'sha256':info['sha256'],'owner':metadata['owner']}
            chain={path.parent.resolve()};cursor=metadata.get('parent')
            while cursor is not None:
                ancestor=Path(cursor['path'])
                if ancestor.parent.resolve() in chain or ancestor.parent.parent.resolve()!=root.resolve() or file_hash(ancestor)!=cursor['sha256']:raise ValueError('unreviewed representation ancestry')
                chain.add(ancestor.parent.resolve());cursor=json.loads(ancestor.read_bytes()).get('parent')
            if chain!={p.resolve() for p in prior}:raise ValueError('continuation would omit a prior representation attempt')
            state,_=read_feature_journal(path,info['sha256'],parent['owner'],required_graphs=descriptor['required_graphs'],max_array_bytes=max_array_bytes)
        elif continuation_input is not None:raise ValueError('continuation has no representation owner')
        journal=FeatureJournal(root/run.admission.experiment_id,owner,required_graphs=descriptor['required_graphs'],parent=parent)
        _immutable(journal.directory/'claim.json',{'owner':owner,'descriptor':descriptor,'plan_input':plan_input,
                   'binding_output':output,'registration_sha256':run.admission.registration_sha256})
    try:
        result=prepare_features(graphs,examples,fold,arm,seed,configs,max_entries=max_entries,checkpoint=journal,resume_state=state)
        path=journal.seal('complete')
        # Re-read persisted bytes before publishing the binding used by fitting.
        _,binding=read_feature_journal(path,file_hash(path),owner,required_graphs=descriptor['required_graphs'],max_array_bytes=max_array_bytes)
        if canonical_bytes(binding)!=canonical_bytes(result.binding):raise ValueError('persisted representation binding differs')
        run.write_json(output,binding)
        run.write_json(journal_output,{'path':str(path.relative_to(run.admission.root)),
            'sha256':file_hash(path),'owner':owner,'workflow_identity':identity})
        return result,path
    except BaseException as error:
        if not journal.sealed:journal.seal('failed',reason=type(error).__name__+': '+str(error))
        # A complete numerical journal stays complete even when publication fails.
        # A successor can register/read it; no representation fitting is repeated.
        _immutable(journal.directory/'attempt-failed.json',{'reason':type(error).__name__+': '+str(error),'numerical_complete':(journal.directory/'complete.json').exists()})
        raise


def reuse_registered_features(run,journal_input,expected_descriptor,*,max_array_bytes,journal_output=None):
    """Registered completed bytes only; no producer claim, sampler or optimizer."""
    if not isinstance(run,ResearchRun):raise ValueError('admitted representation run required')
    run._active();run._check_source()
    if (journal_input is None)==(journal_output is None):raise ValueError('one admitted journal reference required')
    if journal_input is not None:
        raw=run.read_input(journal_input);info=run.admission.inputs[journal_input]
    else:
        output=run.directory/'outputs'/journal_output;reference=output.read_bytes()
        if run._published_outputs.get(journal_output)!=digest(reference):raise ValueError('journal reference not published by this run')
        info=json.loads(reference);raw=(run.admission.root/info['path']).read_bytes()
        if digest(raw)!=info['sha256']:raise ValueError('published journal bytes differ')
    record=json.loads(raw)
    identity=cache_key(expected_descriptor)
    path=run.admission.root/info['path']
    root=run.admission.root/'research_artifacts/onchain_representations'/identity
    if not path.resolve().is_relative_to(root.resolve()) or path.name!='complete.json' or record['status']!='complete' or record['workflow_identity']!=identity:raise ValueError('completed representation identity differs')
    if record['owner']['workflow_identity']!=identity or path.parent.name!=record['owner']['experiment']:raise ValueError('completed representation owner differs')
    state,binding=read_feature_journal(path,info['sha256'],record['owner'],required_graphs=expected_descriptor['required_graphs'],max_array_bytes=max_array_bytes)
    features={h:state['completed_graphs'][h]['feature'] for h in expected_descriptor['required_graphs']}
    dictionary=None if 'dictionary' not in state else dictionary_from_record(state['dictionary'])
    return PreparedFeatures(features,binding,dictionary)
