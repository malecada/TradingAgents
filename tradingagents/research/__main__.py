"""Read-only admission/verification and temporary synthetic demonstrations."""
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check committed admission metadata; never start a run or read empirical inputs")
    check.add_argument("--root", default=".")
    check.add_argument("--registration", required=True)
    check.add_argument("--experiment", required=True)
    check.add_argument("--source", required=True)
    check.add_argument("--design-source")
    check.add_argument("--bindings")
    verify = commands.add_parser("verify", help="Independently check retained hashes/denominators; no scientific validation")
    verify.add_argument("--run", required=True)
    commands.add_parser("examples", help="Run two synthetic examples in disposable temporary Git repositories")
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "check":
        from .admission import admit
        admission = admit(**args)
        result = {"experiment": admission.experiment_id, "stage": admission.experiment["stage"],
                  "ready": admission.ready, "status": "metadata_admitted" if admission.ready else "waiting_for_prospective_window_or_bindings",
                  "empirical_inputs_opened": False, "run_started": False}
    elif command == "verify":
        from .verify import verify_run
        result = verify_run(args["run"])
    else:
        from .examples import examples
        result = examples()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
