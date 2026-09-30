# Independent registered failed-ancestry review

Initial acceptance withheld for A1–A3 below. The scope is a read-only registered ancestry/death prerequisite, not current worker-lease admission, numerical source compatibility, workload membership, orphan recovery or numerical continuation. No tests, jobs, empirical bodies or arrays were executed/read during review. Only this review was written; implementation and test ownership remain separate.

## A1 — parent metadata is opened before fixed-path admission

In the initially inspected `ancestry.py:164–167`, a retained parent reference becomes `current` and is read before the next loop applies the fixed `work/<declared-ancestor>/failed.json`, proof membership, cycle and depth checks at lines119–120. `_read` restricts root containment, file type and2MiB size, but does not restrict the path to a journal filename or workflow subtree.

A pinned malformed parent can therefore point to another compact regular file under the root with an ancestor-named parent directory. Line165's lifecycle-parent name check passes, then the foreign file is opened before eventual rejection. This violates the metadata-only path boundary even if acceptance is later refused. Validate exact parent layout, declared owner/proof membership, reference fields, cycle and depth before any referenced read. A synthetic foreign-file fixture should assert that it is never opened, not merely that verification eventually raises.

## A2 — earlier ancestor death inventories are not rechecked at chain end

`death.verify` checks each ancestor's optional final and complete-terminal inventory, but its successful snapshot is consumed once at `ancestry.py:151`. The outer recheck at lines170–172 only checks existing metadata signatures and representation directories. It does not revisit optional guard-final inventory for already-checked ancestors.

With chainB→A, create B's previously absent `guard/final.json` while A's death observation runs. B's supplied proof/signatures remain unchanged; the representation directory inventory is unchanged, and the function can return with B's new terminal evidence omitted. This recreates the accepted death component's corrected D1 at the composition boundary. Recheck whole-chain death/terminal inventories before returning, then recheck retained signatures and directories. Test mutation of an earlier ancestor during a later ancestor's observation; lifecycle terminal contradictions must also remain refusals. The result remains a finite checked observation rather than a lock.

## A3 — historical producer continuation routes are not joined

Lines139–149 join the historical lifecycle experiment, representation claim and pair-policy hash, but do not inspect the ancestor's registered execution-job/producer-plan route and its continuation input. Lines159–161 accept an end-of-chain journal with `parent=None` without comparing that claim to the historical producer's registered continuation.

A historical B contract may explicitly continue A while B's start and failed manifest both omit that parent. If A's representation directory is missing and only B's proof is supplied, existing directory/set checks cannot recover the omission. Current C can still register B as its immediate parent: lifecycle source admission verifies committed historical contracts, but does not rehash all historical input bodies. The precheck can therefore accept a truncated representation chain despite an immutable historical continuation requirement.

Read each ancestor's exact registered execution job and selected producer plan through its recorded input hash, join producer/descriptor/policy and continuation routing to its journal metadata, and validate the declared continuation path/hash/owner before reading it or terminating traversal. A legitimate first representation with an unrelated lifecycle parent and no declared representation continuation need not be rejected. Add a fixture whose historical continuation contract remains pinned while the journal omits it, admitted before the current successor starts; avoid an incidental current-input-drift rejection.

## Sound checks and evidence limits

The inspected component requires an actual active ResearchRun and re-admits source, binds its own and the accepted death helper's source hashes, reads current routing inputs with registered hashes, checks the selected representation/producer and exact workflow sibling set, and uses bounded regular nonsymlink metadata reads with stable signatures. The ordered supplied proof set must match the traversed chain, and current representation creation is refused before this prerequisite. Return flags explicitly withhold continuation, arrays, numerical compatibility and output verification.

Saved `green01.log` reports17 passes in6.745seconds, SHA-256 `31a1e1ca1dfafcd12999fa109399711cb5c5e802d97bc1ca16e84c5bb7d6f5ff`. The initial fixtures use actual tiny Git registrations, ResearchRun claims and FeatureJournal objects while mocking OS death/boot/cgroup predicates. These do not establish live guarded continuation. Initial inspected source SHA-256: `613d1f4c3bff2a26b875b7a557701229085884bd584d2fb2b2e79a45221450de`. HEAD is `2b3bb582f17bf570ab11e1b01457574acfbaaeb7`. Expanded regression work is owned by the implementation agent; no passing outcome from that work is assumed here.
