# Correction to pair-route attribution

The original REPORT.md and MANIFEST01.json remain immutable. CORRECTION01.json supersedes their resource-verification and equivalence wording.

RESULT02.json self-observes CPU affinity[2]. There is no retained launcher/getrlimit receipt proving continuous affinity, address-space limit, timeout, nice level or thread settings. The original conversation invocation requested taskset CPU2,512MiB AS,nice10,thread variables1 and25s timeout; its author-transcribed tool result is chunk13bd93,exit0. That transcription is reported evidence, not an independently authenticated launcher receipt.

The earlier4MiB file-ceiling claim is withdrawn. The invocation used Bash `ulimit -f8192`, ordinarily8MiB with non-POSIX1024-byte units. Actual unit mode and RLIMIT_FSIZE were not recorded. Neither4MiB enforcement nor retrospective compliance may be credited. Semicolon-separated ulimit commands lacked a failure gate/readback. Script self-reported duration1.025s and original tool reports were short; these do not prove resource enforcement.

The13.727/20.109ms direct and13.885/20.391ms memo-miss medians include fresh purpose generation (counter/string/encoding/SHA256) and lambda dispatch inside the timer. Memo-hit medians likewise include this overhead. No subtraction or rerun was made. Separately staged calls are an attribution experiment rather than an instrumented decomposition of the exact route.

Exact score bits, iterations and convergence were compared among direct PairExecutor, memo miss/hits and the separate staged engine.score_only path. The bare annealing path checked only phase==done; its state and result bits were not compared. No bare-versus-route equivalence claim follows.

The narrow finding remains that these two synthetic, authority_poll=None routes took milliseconds, while the recorded actual26 mixed memo-call mean was427ms. This does not attribute the real gap to shapes, authority or any other cause. No genuine Owner/Binding, population throughput, resource admission or live-source change is established. Original logs/scripts and all prior claims are retained for review; this correction performs no numerical execution.
