# Independent initial training verification review

No material defect identified in the test's bounded synthetic smoke-test design. Acceptance of its execution is pending terminal check01 evidence; the inspected log is still active. No tests or numerical jobs were run by the reviewer. No maintained implementation change is part of this test.

The test uses the actual fresh compact producer and its actual returned native feature map, rather than fabricated MCM values or a detached precomputed learned embedding. `build_model('proposed', 'direction', config)` constructs the maintained ReplicationModel: learned MLP, two GAT layers, mean pooling, price concatenation, LSTM, additive temporal attention and classification head. Only the explicit fixture dimensions are changed to two MCM columns and two time steps. Graph embeddings are computed inside this model's forward call. Its graph reuse dictionary is local to that call, not a cache across weight updates.

Forward output shape/finiteness and cross-entropy backward are checked. Every model parameter must have a present finite gradient, and at least one graph parameter and one temporal parameter must change after Adam. These assertions establish connection to the full parameterized model if they pass; they do not assert a nonzero gradient or actual update for every parameter or each narrower MLP/GAT/LSTM/attention/head group. There is only one optimizer step, so unchanged learned outputs across successive updates are not tested.

Returned native tensor inputs must remain non-trainable and without attached gradients. The test drops the batch, graph-sequence lists and forward output, collects wrappers, and requires zero tracked live tensor bytes. A fresh saved-feature hash verification must match the initial hashes, followed by the actual full producer finalization. This proves saved fixed values and final retained evidence remain intact if it passes. It does not directly hash temporary returned tensor values before release, nor prove release of untracked aliases, autograd storage, model buffers or all RSS.

Prices are manually divided by 100 and targets are taken from the two supplied training rows. The maintained batch_factory, fitted train-only scaler, execute_batch, fit_cell, checkpoint/recovery, prediction/metric path and regression head are not invoked. This is an actual model optimizer step using compact inputs, not an actual fitted-dispatch or OS-guarded execution. Synthetic registered fixtures mock the OS guard and do not establish paper-level numerical equivalence, full-scale resources, timing/financial validity or empirical release. These are scope limits, not reasons to rerun the active test or broaden its claim.

Direct source bindings inspected:

- test_compact_native_training.py: `e88920681ca697901bc94fe4ab6953b35bb52ebc29856144a0f5b87f4d04f4ba`
- model.py: `ed4d5417202bb13ebc682d88d56942db74201feddc1b4d20511e54684fc252a0`
- model_registry.py: `c0e2202578ae708e2fc0406ece5726541952bf40f29df9dc81812c177c334543`
- temporal.py: `d8adafb5a50716ce472848df05e8bbb804525ed8003958c7f9a25c82d81ad226`
- gat.py: `c2292bb164869bb4202a2af028a453f547d8e2930cd9d58ee4a59ffcb72913d6`
- original model.json before the explicit in-test dimension overrides: `20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d`
