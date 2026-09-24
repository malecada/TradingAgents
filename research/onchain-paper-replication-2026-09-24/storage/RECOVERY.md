# Storage preservation and recovery boundaries

The compact checkpoint preserves its pinned Git tree. Transaction backup is a
separate inventory and is incomplete until every batch has a verified completion
receipt. A directory listing, upload exit status or remotely computed hash alone
does not establish a completed retrieval check.

For each successful raw batch, retain its remote `bundle.tar`, `manifest.json`
and `complete.json`. The manifest maps generated `files/00000000` archive names
to original source and resolved locations, lengths, timestamps and expected
SHA256 values. These numeric names avoid interpreting archived absolute paths.

To recover a selected batch on a provisioned host:

1. Retrieve its manifest and completion marker, and check their hashes against
   the retained local receipts. Use strict SSH host-key verification and the
   separately configured key; never store key material in the repository.
2. Download the archive to a new owned directory with a size/time bound. Verify
   archive length/SHA256 and every member using `preservation.verify_bundle`.
   The verifier does not require the original source paths to exist and does not
   extract any archived path.
3. Restore verified members into a new staging root. Preserve the manifest's
   original path/hash mapping. Never extract over existing originals or reinterpret
   generated member names as the original directory layout automatically.
4. Register an explicit original-to-restored path mapping before a subsequent
   research job. Original frozen mappings and all closed claim identities remain
   unchanged. Byte recovery does not itself admit a new experiment or establish
   the historical source vintage.

Failed bundles and partial uploads remain at their existing identities. A new
continuation must first reconcile their retained receipts and live ownership.
Do not rerun the transfer script for a completed/failed phase or duplicate its
active controller. Verified generated spool archives may be removed only under
the transfer's recorded cleanup rule; original raw data remains in place.

The retained-ETH inventory is not an inventory of the whole research workspace.
Large pilot graph arrays, SQLite scratch and other historical raw stores need
separate manifests and recovery verification. The Storage Box is archive storage;
full-sized execution still requires suitable RAM and local scratch capacity.
