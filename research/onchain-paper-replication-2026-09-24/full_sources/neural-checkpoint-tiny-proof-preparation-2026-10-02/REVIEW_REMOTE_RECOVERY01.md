# Independent checkpoint-attempt remote recovery review

Disposition: **accepted for the stated selected-source and complete raw-owned-tree recovery scope**. The recovered record remains a failed outer attempt with separately passed tiny numerical/profile components. No computation was replayed and no closed identity was reopened.

## Exact recovery and independent verification

| Object | SHA-256 |
|---|---|
| REMOTE_EXECUTION_RECOVERY01.json | 5e91cb4aa2aab9cba204ad7dc78ddea9676ed0dd4d587747b6eb04102e1cd990 |
| recover_execution01.py | 25094da36ad84dd9fbcbdef85864a85a7575b741ac1931c24352e9b00d97256c |
| remote-recovery01.log | 2d74f0310e5ac29efdd4be3a23bfafeb7dd69fca4f5ba5aa6cac20ce2a833d28 |
| recovered raw archive | 124ae811761a9bc87e6388420dd5c391f78180db8f7478162f29ab73eb7e5f45 |
| recovered raw inventory | 845bc057ceae7b9c1f82fd67e0ce313b3c27e9709ee4ac29dfeb5d2bf3b5bb7f |
| recovered execution result | 85d8bef932d6079a81d0ade096f98f93f034d9df5b40d3fdff704b400862059d |
| recovered independent execution review | af9d487a36b1a24b71e4e23f807bcf263488695f468c40eeb6d80372d88a6dd9 |

The actual remote recovery commit is `3a56c4b28c1d05595c765cd93046496104c7ecb2`. The original numerical execution commit remains `09f2a2066a445d7399dac3165014e0ffd0019269`; the later recovery commit does not replace that execution identity.

Independent read-only Git inspection confirmed the fresh bare repository's FETCH_HEAD equals the stated recovery commit, shallow status is true, and its declared partial-clone filter is `blob:none`. All 155 reported blobs were read directly from existing bare Git objects using `GIT_NO_LAZY_FETCH=1` and `protocol.allow=never`. Their exact sizes and SHA-256 values match the report, totaling 8,830,373 selected blob bytes. All separately saved recovery files also match their corresponding bare Git blobs. No remote URL or credentials were printed, no fetch was repeated, and neither the repository nor FETCH_HEAD was changed.

The independently recovered release02 supplies the expected source map. All 142 original selected Git-source bodies are present among those 155 blobs and match every release hash. This includes the original model configuration, selected source/launcher/oracle/coordinator, guard helper and production closure. The remaining selected blobs retain the release/correction, source manifest, source/native/execution reviews, original outer traceback and exit receipt, collector source/log, final result and whole raw archive/inventory.

Streaming inspection of the recovered archive, without extraction, independently verified all 282 exact members: 245 regular files and 37 directories, 7,539,340 regular-body bytes. Every name is unique and under the original owned identity, with no traversal, link or unexpected member type. Every member's mode matches the independently recovered inventory; every file's size and SHA-256 matches. The archive hash matches both the recovered inventory and result. The inventory's original 8,581,120 allocated bytes are retained historical filesystem evidence, not a promise that restoration elsewhere consumes the same allocation.

## Preserved outcome and proof limits

The recovered result, original failed launcher terminal and separately retrieved outer exit/traceback join exactly. Outer session 85714 exited 1 with `KeyError('file_size_limit')`; the missing optional ready field has not been added retrospectively. The original native controls, coordinator/arm intents, 10/2/2 case rows, 147/22/22 phase records, checkpoints and cleanup evidence are all inside the complete recovered archive. The recovered execution review preserves the three passed components and 3,823 bitwise-identical tiny tensor comparisons separately from failed overall completion. The retrospective collector does not deserialize or execute those checkpoints.

External transfer provenance rests on the separately executed fresh-fetch procedure and retained success report/log, corroborated here by its exact fetched objects and saved files. A configured remote or bare directory alone would not prove external recovery. This review made no new network request and does not attest the remote's future availability.

The selected installed uv runtime, its hard-link aliases, runtime binaries and empirical input stores were not remotely recovered. Distribution/version and runtime-body pins are metadata, not those installed bodies. The archive is complete for this original owned engineering attempt, while the 155-blob selection is not a backup of the entire repository or every historical preparation artifact. No numerical import, model replay, checkpoint deserialization, native job, admission or claim was performed by this review.

The failed parent remains terminal; there is no retry, refund, budget 65, full-graph capacity inference or financial-fit result. Existing paper-family history remains 36 closed attempts and adopted ceiling 64. Saved backing-storage diagnostics, sampled cgroup current and cumulative unit peaks retain their distinct qualifications from REVIEW_EXECUTION01.md.
