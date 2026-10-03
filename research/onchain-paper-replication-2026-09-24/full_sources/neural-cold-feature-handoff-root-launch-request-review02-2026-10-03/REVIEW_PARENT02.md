# External parent_wait02 independent source review

**WITHHELD.** Exact parent source a549aa257d4c31da79e03d113dd34143cbba723eb6dcb901adff9726996f74ec has two material cleanup/evidence defects. The exact child request and command remain independently accepted prospective metadata in REVIEW_REQUEST02.md; no actual parent main or capsule command was invoked.

## RP1: first fatal can be replaced during receipt and stream finalization

Locations: parent_wait02.py:60–70 and181–196, together with the surrounding stdout/stderr context managers beginning at160.

The file writer suppresses every close exception when any body exception exists. An ordinary body ValueError followed by a real MemoryError at close raises ValueError and loses the first actual fatal. The directory fsync uses an unprotected finally close, so its MemoryError can be replaced by a later ordinary OSError. Both failures were independently reproduced against actual write with real exclusive tiny files/real close operations and injected error objects; each acquired descriptor was closed exactly once by the test.

After wait_owned returns an already-selected primary, main publishes wait.json/failure.json without reduction against that primary. An exact extraction of the post-wait statements shows OSError from wait publication replaces an existing MemoryError. The implicit stdout/stderr __exit__ calls can similarly replace a prior fatal or skip later receipt publication; they do not use select.

Required correction: one explicit first-actual-fatal reducer must span file/directory closure, both stream closes, post-wait receipt assembly/write, absence checks and failure publication. Attempt independent cleanup/recording actions even after another fails. Preserve genuine observed wait values and original receipts; no success or wait may be fabricated when no actual wait exists. Ordinary failures must not suppress a later actual fatal; an earlier actual fatal must remain the exact returned/raised object across later ordinary or fatal failures.

## RP2: signal failure skips wait and leaves the owned wrapper alive

Location: parent_wait02.py:104–115. SIGTERM, child.wait and forced cleanup share one outer try. If killpg raises, control jumps directly to the exception handler and skips the wait/forced-reap branch entirely.

A real new tiny stdlib sleeping child was used, with on_child raising an exact MemoryError and os.killpg injecting OSError. wait_owned returned while PID3381025 was still alive and un-reaped, retaining the primary but failing its cleanup obligation. The independent reviewer harness then explicitly killed/reaped only that owned child and confirmed absence. No native or research process was involved.

Required correction: signaling, bounded wait, forced signaling and final reap must each be independently attempted and reduced against the primary. A failed signal must not bypass wait or the remaining authorized cleanup. Uncertain descendant closure must remain failed/uncertain; do not guess unrelated PID/unit identities or infer cleanup from a returned function alone.

## Checks that passed and limits

Normal on_child MemoryError terminated/reaped the new tiny child PID3381024 (exit-15), preserving exact identity. Actual SIGTERM cancellation terminated/reaped PID3381026 (exit-15) and restored the original handlers. All three test children were absent at completion. These positive cases do not excuse RP2 and do not establish native descendant/cgroup cleanup or resistance to external SIGKILL.

The prospective main route otherwise binds the exact command-document/request/launcher bytes, locked interpreter/argv/cwd, materialization identity and fixed child output root. It reserves a distinct parent output, uses inherited4MiB file limits, records actual PID/start and constructs the eight-field wait only from observed child returncode. Those are coherent source intentions, not an executed parent receipt. The2700s active monitoring and150s/5s cleanup are separate phases; no hard whole-invocation deadline is claimed. Root must preserve this source and failures and review a new immutable correction. No capsule/source/gate/claim, original job, numerical import or network was touched.

check_parent01.py/log preserve all four concrete counterexamples plus positive tiny-child checks. This review does not relax or mutate the actual child request ef024344, command3f20df21, accepted launcher02 or frozen A2. Correcting this parent remains separate from final external backup/recovery and root-only activation.
