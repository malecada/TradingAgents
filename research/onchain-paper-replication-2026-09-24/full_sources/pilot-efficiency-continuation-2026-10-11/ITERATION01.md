# Initial bounded-body implementation result

The first focused offline run passed 19 tests in 2.75 seconds. After identity, failure and phase controls, 29 tests passed in 1.83 seconds. The complete three-batch driver/Journal/NumericExecution synthetic integration then passed as part of 30 tests in 2.47 seconds. No failed test occurred in those three runs. These results used an in-memory prefix limited to 64 MiB of recovered bodies and are not a full-scale continuation result.

The full integration fixture compared 96 ordered cells against a synthetic failed parent stopped after 64 durable cells followed by a fresh 32-cell successor. Scores, f32 output bytes and origin SHA were identical; NumericExecution.finish and verify succeeded. It used a deterministic synthetic memo executor and explicitly installed a parser-test seal. It did not claim a genuine ResearchRun or empirical admission.

The initial implementation is superseded by the streamed-reference implementation. No source snapshot of the transient initial working files was taken; this report preserves the observed test outputs and limitations, not a claim of exact source recoverability.
