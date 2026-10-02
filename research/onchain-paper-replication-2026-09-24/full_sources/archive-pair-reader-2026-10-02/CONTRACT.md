# Cold archived pair verification

Add an explicit read-only source route, separate from the closed writer and its
already consumed read attempts. The caller must supply the trusted archive
completion hash, expected owner, complete scope and exact archive policy.
Validate fixed canonical metadata, ordered manifests, disposition records,
retained original copy/read receipts and exact bounded inventories. Every remote
chunk is fetched again through a fresh exclusive consumption attempt and fully
replayed using the unchanged compact event format. Successful local caches are
disposed only by the existing consumption helper.

The new root attempt binds the source completion and read-metadata allowance.
Old source paths remain read-only, including on failure. Successful return needs
full source and new-consumption metadata verification after the last external
callback and after the new completion record is published. Failed or terminal
read attempts cannot reopen. Root descriptor cleanup uncertainty is fatal;
failure records belong to the new attempt, never the closed source.

Finite chunk count, bounded metadata and a 10GiB floor are logical safeguards,
not measured whole-workflow resource bounds or filesystem reservations. The
caller must bound actual transport, OS guard, concurrent readers, aggregate read
attempts and retained metadata. No remote availability promise, scientific-stage
admission, checkpoint-body verification, score-stream join, current-owner
selection or historical-source disposal follows from this helper.
