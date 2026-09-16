"""Reviewed one-time failure closure; never replays the empirical benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tradingagents.research import ResearchRun
from tradingagents.research.admission import admit
from tradingagents.research.verify import verify_run


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',required=True)
    args=parser.parse_args();root=Path(args.root).resolve();here=Path(__file__).resolve().parent
    binding_path=here/'failure-closure-bindings.json';binding=json.loads(binding_path.read_bytes())
    if str(root)!=binding['execution_root']:raise ValueError('execution root differs')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=binding['source']:
        raise ValueError('fixed execution HEAD changed')
    run_dir=root/'research_runs'/binding['experiment']
    guard_path=root/'research/onchain-graph-2026-09-16/motifs/resource.json'
    if sha(guard_path)!=binding['guard_sha256']:raise ValueError('guard bytes changed')
    guard=json.loads(guard_path.read_bytes())
    if (guard['child_exit_code']!=-15 or guard['limit_reason']!=binding['resource_limit_reason']
        or guard['elapsed_time_kill'] is not False or guard['peak_sampled_tree_rss_bytes']<=guard['rss_limit_bytes']):
        raise ValueError('terminal memory-guard failure not established')
    if any((run_dir/n).exists() for n in ['complete.json','failed.json']):raise ValueError('run already terminal')
    def outputs():return {p.name:sha(p) for p in sorted((run_dir/'outputs').iterdir()) if p.is_file()}
    if sha(run_dir/'claim.json')!=binding['claim_sha256'] or outputs()!=binding['output_sha256']:
        raise ValueError('original claim or partial outputs changed')
    admission=admit(root=root,registration='research/onchain-graph-2026-09-16/motifs/gates.json',
        experiment=binding['experiment'],source=binding['source'],_own_claim=binding['experiment'])
    run=ResearchRun(admission);run._claim_sha256=binding['claim_sha256']
    run._check_inputs()
    run.fail('Sampled2GiB process-tree memory limit exceeded during Local40 computation after graph-build and bounded-oracle receipts. Guard terminated child SIGTERM(-15); no full-day motif vectors or summary retained. Reviewed failure-only closure, no replay or finish. Guard SHA256 '+binding['guard_sha256'])
    if sha(run_dir/'claim.json')!=binding['claim_sha256'] or outputs()!=binding['output_sha256']:
        raise ValueError('closure modified original bytes')
    verified=verify_run(run_dir)
    report={'operation':'failure-only closure','source':binding['source'],'binding_sha256':sha(binding_path),
        'claim_sha256':binding['claim_sha256'],'guard_sha256':binding['guard_sha256'],
        'output_sha256_unchanged':binding['output_sha256'],'failed_sha256':sha(run_dir/'failed.json'),
        'verification':verified,'replay':False,'successful_completion':False,
        'cell_progress':[{'id':n,'status':'evidenced-before-resource-failure'} for n in ['input-semantics','ordered-events','bounded-oracle']]
            +[{'id':n,'status':'unavailable','reason':'memory guard terminated local motif computation'} for n in ['local-motifs','local-export']]}
    with (root/'research/onchain-graph-2026-09-16/motifs/failure-closure.json').open('x') as f:
        json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))


if __name__=='__main__':main()
