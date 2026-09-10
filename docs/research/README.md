# New-program admission and immutable run helper

This additive helper prepares the next authorized program. It contains no strategy,
market downloader, account client, scheduler or deployment operation. Historical
registries, runners, financial ledgers, raw stores and evidence are unchanged.
Passing these engineering checks is not admission of a trading strategy.

## Commands that are safe during preparation

```bash
.venv/bin/python -m tradingagents.research --help
.venv/bin/python -m tradingagents.research examples
.venv/bin/python -m pytest tests/research --import-mode=importlib
```

`examples` creates two synthetic runs in one disposable Git repository: a
development calculation explicitly reuses
an invented spent sample, followed by a child calculation on a declared unseen
invented window. Both calculate the sum/count of two invented scalars. The
temporary repository is removed after independent structural verification. These
are plumbing demonstrations, with no market history or financial interpretation.
Prospective design/binding, failures and concurrent attempts are exercised by
additional temporary synthetic test fixtures.

The following is a **template for a later separately authorized registration**;
there is no real new-program registration to execute during this preparation:

```bash
.venv/bin/python -m tradingagents.research check \
  --root . --registration research/PROGRAM/gates.json \
  --experiment EXPERIMENT --source FULL_EXECUTION_COMMIT
```

`check` reads registration/source/provenance metadata and prior run receipts. It
does not open empirical input files, claim a run or produce outcomes. A valid
future design reports `waiting_for_prospective_window_or_bindings`. This is not
permission to evaluate early. `check` does not read or apply account permissions.

## Register before outcomes

New-program gates belong in a new committed `research/PROGRAM/gates.json` file.
The exact `experiments.EXPERIMENT` key, its committed charter and pinned sources
are the new program's gate. This preserves the charter-plus-`gates.json`-key rule;
it does not route new work through old `data/predlab/gates.json` or
`data/rebuild/gates.json`, and does not create a second interpretation of their
historical criteria. The charter still must specify economic assumptions,
selection, uncertainty/multiplicity, costs, forensics, resources and decisions.
The helper validates structural admission, not the scientific adequacy of prose.

Schema version 1 has these fields:

| Field | Required content |
|---|---|
| `schema_version`, `program_id` | `1`, stable program identity. |
| `families` | Map of family keys to `mechanism_id`, `attempt_budget`, `prior_attempts`, `history_reference`. |
| `datasets` | Map of local names to canonical `identity`, `history_reference`, `exposures`. |
| Dataset `exposures` | Prior intervals `{start, end, state}`; state is `exposed` or `spent`. |
| `experiments` | Map of globally unique experiment IDs to the fields below. |
| `family`, `parent`, `question` | Existing family key, explicit parent experiment ID or null, falsifiable question. |
| `charter` | Committed `{path, sha256}` containing the complete experiment contract. |
| `stage`, `reuse` | Stage `discovery`, `development` or `confirmation`; reuse `exploratory` or `fresh`. |
| `windows` | `{dataset, start, end, availability}`; availability `existing` or `prospective`. |
| `selection` | Confirmation requires committed `{path, sha256}` freezing the selected rule/thresholds; otherwise null is permitted. |
| `source_files` | Every runner/implementation/configuration dependency mapped from path to SHA-256. |
| `runtime_hashes` | Exact result of `tradingagents.research.runtime_hashes()` for these helper sources. |
| `inputs` | Named inputs `{path, sha256, dataset}` matching registered windows; prospective hashes may initially be null. |
| `cells` | Complete nonempty unique cell-ID denominator, including cases that might be unavailable. |
| `outputs` | Complete unique JSON basenames written inside the new run's `outputs/` directory. |

Timestamps require explicit UTC; intervals are `[start, end)`. File paths must be
relative to and resolve inside the checkout. Dataset identity must denote the
same underlying sample across aliases/version names. An independent reviewer
must check the initial history references against the canonical audits and spent
holdouts. Neither renamed dataset keys nor overlapping intervals create fresh
data. Existing exposed data can be used for explicitly exploratory development;
confirmation rejects any overlap with prior exposures or another run claim.

Family budgets include `prior_attempts` plus **all claimed attempts**, including
failed/incomplete starts, across every program under the shared `research_runs/`
root. Another family key with the same mechanism cannot reset the budget.
Previously recorded family budget/history fields cannot change through ordinary
admission. Exhausted unrelated families remain legal registry history. Budget
extensions require a separately reviewed engineering/policy amendment that
preserves the old limit and cumulative count; this helper deliberately does not
offer an implicit reset or extension switch. Result-informed children must name
a terminal parent whose original registration is unchanged.

## Prospective data: freeze first, bind bytes later

Future input bytes cannot be hashed before they exist. The design commit may
therefore register a prospective input with `sha256: null`, while freezing its
input name/path/dataset, interval, capture/validation procedure in the charter,
source files, selection and thresholds. The design's Git commit timestamp must
precede the prospective window's start. The **entire design registration stays
byte-identical** at execution; append later hypotheses to a separate registration
file when necessary. Execution HEAD must descend from the design commit.

After the registered capture and independent admission of data, commit a separate
bindings JSON object with exactly:

```json
{
  "schema_version": 1,
  "design_commit": "FULL_DESIGN_COMMIT",
  "experiment": "EXPERIMENT",
  "registration_sha256": "DESIGN_REGISTRATION_SHA256",
  "inputs": {
    "REGISTERED_PENDING_INPUT": {
      "sha256": "CAPTURED_INPUT_SHA256",
      "capture_manifest": {"path": "CAPTURE_MANIFEST_PATH", "sha256": "MANIFEST_SHA256"}
    }
  }
}
```

Bindings must cover exactly the pending input names. They cannot change paths,
windows, rules, thresholds or sample denominators. The capture manifests must
also be committed and match their hashes. Use the execution commit as `--source`,
with `--design-source FULL_DESIGN_COMMIT --bindings PATH_TO_BINDINGS.json`.
The helper verifies the unchanged charter/selection/implementation against both
commits and waits until the sample ends. Git timestamps and declared capture
metadata are **not independent proof** of prior public registration, honest
chronology or availability; retain pushed commit evidence and independent source
review. Capture metadata must never become an alternate configuration channel.

## Run API and immutable evidence

```python
from tradingagents.research import ResearchRun

with ResearchRun.start(
    root=checkout,
    registration=registration_path,
    experiment=experiment_id,
    source=execution_commit,
    # design_source=pre_window_commit, bindings=bindings_path,  # prospective only
) as run:
    raw = run.read_input("registered_input_name")
    # Runner validates clock/schema/coverage and executes only the frozen design.
    run.write_json("registered_output.json", result)
    run.finish(all_registered_cells)
```

Each cell is `{id, status, ...}`, with status `complete` or `unavailable`.
Unavailable cases require a reason and remain in the complete denominator.

`start` checks metadata/source before empirical bytes, serializes admission under
a shared OS file lock, exclusively claims `research_runs/EXPERIMENT/`, and then
hash-checks every registered input before returning control to the runner.
Hashing necessarily reads bytes; it does not parse values or run an experiment.
`read_input` returns only named, hash-verified input bytes. The runner owns
semantic admission of units, instruments, clocks, availability and coverage.
Normal writes are restricted to declared JSON outputs. Source and input hashes
are checked again before completion; published outputs cannot be overwritten or
silently modified. Concurrent starts/completions produce one owner/terminal record.

`claim.json` preserves the gate, ancestry, family budget, exposures and provenance.
`complete.json` is published atomically once, with output hashes and every cell.
These completion files form a **sharded append-only ledger**; there is no second
mutable aggregate index or write into a historical financial ledger. Claimed
attempts and completed/unavailable cells are different denominators. Back up the
whole new run directory, including failed/pending claims, not just successes.

Caught failures and contexts that exit without completion retain `failed.json`
plus partial outputs. SIGKILL, power loss or a partial filesystem failure can
leave a claim without a terminal receipt. Such a claim still consumes an attempt,
marks its windows exposed, and blocks automatic retry. Recovery requires review
and a preserved explicit decision, never deleting the claim or reusing its ID.

## Independent integrity check and limits

```bash
.venv/bin/python -m tradingagents.research verify --run research_runs/EXPERIMENT
```

The verifier separately reconstructs claim fields from committed registration,
design, source and input bindings, then reads the terminal records, recomputes
output hashes and independently reconciles counts/identities. Prior claims pass
the same committed-snapshot check before admission trusts budgets/exposures. It does
not import admission or accounting logic, open empirical inputs, rerun outputs
or certify scientific validity. Independent cashflow/statistical reconstruction
remains separate and experiment-specific.

This is a cooperative workflow control, not a security sandbox. Python code can
read outside this API, administrators can edit/delete files, and someone can
misdeclare history or covertly rename an economic mechanism. A complete imported
history, canonical source catalogue, single durable run root, proper backups and
independent review remain required. External sibling stores, Parquet outputs,
resuming interrupted empirical work, automatically extending budgets and
scheduling are deliberately outside this initial API. Extend only for a concrete
registered need, preserving old contracts and synthetic regression coverage.
