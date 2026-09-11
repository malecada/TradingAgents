"""Frozen 240-second public options prerequisite resident-memory harness."""
import argparse
import json
from resource_guard_v2 import run_guard


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',required=True)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:
        parser.error('child command required')
    with open(args.report,'x') as output:
        result=run_guard(command,rss_limit_bytes=512*1024**2,wall_seconds=240)
        json.dump(result,output,indent=2);output.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['child_exit_code']==0 and result['limit_reason'] is None else 1)


if __name__=='__main__':
    main()
