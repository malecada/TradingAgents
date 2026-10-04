"""Treatment lineage at population and fit boundaries. Stdlib at import.

Pure checks establish consistency, never authority. Runtime paths require the
real active ResearchRun and independently verify retained committed claims.
Fund vintage policy is deliberately unadmitted in this source candidate.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

LIMIT = 4 * 1024**2
PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24'
# Root must freeze an independently reviewed producer successor, not producer01.
PRODUCER_SOURCE_PINS = {'tradingagents/__init__.py': 'f3f6f89f20f49a016e061266fa802b73fa95720d060a2642573d4227646ad4e5', 'tradingagents/research/__init__.py': 'b34ced6fb4b6dd9dc1ae15645c40d62687ae7fa85f104ff77a6f1f49f874d2af', 'tradingagents/research/__main__.py': 'd5d7664ed30f9905a4911c70d69a756e5260e534365d68968808d4f5079cd70e', 'tradingagents/research/admission.py': '585d66f526d88f8488c6efcc4989a09328006e393566a596fe9e95c6c7f60cfd', 'tradingagents/research/budget_extensions.py': '59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a', 'tradingagents/research/examples.py': '0c4e4e901d14455b6742627a3c0bd42ffe65f5cf8eea7b64afbd0010dcbcbdc1', 'tradingagents/research/lifecycle.py': '88589c2dab53954711a66a22f2bf7e134a6e7d21072c5b7b508d11f04c6490dc', 'tradingagents/research/onchain_replication/__init__.py': '905f63046b02552c4d7cd90014328a48d77bcdb336b4a1f3351b453b83878fd1', 'tradingagents/research/onchain_replication/aggregation.py': '768c2ca743b2146fcc6bf606e4fa0bf41273ac15d06344d3a25a6aac78e8038f', 'tradingagents/research/onchain_replication/archive_chunks.py': 'f26f1cb62334497494f9b02579f53be9e2238889a81f56c04fd4e781542b38fe', 'tradingagents/research/onchain_replication/archive_consume.py': '9cfa242b77e42c2385e3c4cb8e51086965cc7d42768f2c52364fa3fd4ec77dc5', 'tradingagents/research/onchain_replication/archive_dispatch.py': '05eafe349dfafefe0b17ed8b8efaa3a480eff0f943988212846cabcec414f953', 'tradingagents/research/onchain_replication/archive_owner_operations.py': '5882578d065e94af588511356071b8f575aa1e8a1bbd7a9ab116e5853eb4c83f', 'tradingagents/research/onchain_replication/archive_owner_policy.py': '81b0e2fa4220c45461ffad850209e92819b65a56a7037887d1d7ba92c97956c9', 'tradingagents/research/onchain_replication/archive_owner_seal.py': '7c8c01ce43756605e4765f8e04e1cbbf1665d651d076b36eab74340acb0b07fa', 'tradingagents/research/onchain_replication/archive_owner_stage.py': '21a1f134c4ed0d4f57c266f21d4dd130d61241117b11e7f66a6466db3ddec39c', 'tradingagents/research/onchain_replication/archive_owner_writer.py': '7980139206c4b2a0e8b11763f44d23a73c4e9f067d9c10799a081664c42135d1', 'tradingagents/research/onchain_replication/archive_pair_reader.py': '11aedf0b9e5e8698831854952033f36db185c0cb4948f226912731ffc68d16df', 'tradingagents/research/onchain_replication/archive_pair_writer.py': 'c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052', 'tradingagents/research/onchain_replication/archive_transport.py': 'ef0fdc052a354af5b83e487cbc2d2cf92170149d64f90117adcb5ee37e3b572d', 'tradingagents/research/onchain_replication/archived_pair_log.py': 'e01d267c54be8bc786478d5647c90505f75f66dd96e1d57349ba3f76e6259b3f', 'tradingagents/research/onchain_replication/archived_stage.py': '1e4b09210a0a9384b778a71e1573298cb923711bcf7c7dcd3b464460001dc407', 'tradingagents/research/onchain_replication/array_neighborhoods.py': '514ef8993d962c29b81777791303904f79a31e695cb0b5d152b27bdd02e2cf3f', 'tradingagents/research/onchain_replication/baselines.py': '8ad95719b412aa633607f966e72e3246cceeceffb68e6ced90b4289637b3954a', 'tradingagents/research/onchain_replication/btc.py': '775838b3fc00534849d747f38c942f13187762b81c35ef5b1af52d67882a2dd0', 'tradingagents/research/onchain_replication/btc_source.py': 'deb5f4003ab63a69f945756f1e40fdd6212733331b2ef0133bab2ba0f69acead', 'tradingagents/research/onchain_replication/btc_store.py': '79f78d1bfc46d3e975f506407f3fcea102835235b5aa5b68cf6b1d7674c10452', 'tradingagents/research/onchain_replication/btc_subsets.py': '79f1cc4de5b5bf52e491201d05941bbe0ff29555d814f343294411f4591ed736', 'tradingagents/research/onchain_replication/btc_weekly.py': '6d52650e2bc6225c73da9841e51ab03be33ba8f3dd32a5ae504d6b76908c4aed', 'tradingagents/research/onchain_replication/cache.py': '5fbbe0df14cfc1802dd1df4da6c8bdbd1153a9fcbb4c89dd202e791d1811ddba', 'tradingagents/research/onchain_replication/calendar.py': 'c96e984a7d3482500a3a98231d859da1678cae4ca63960f33515a06dbda760f2', 'tradingagents/research/onchain_replication/cells.py': '1a15e33377030b6f3c533fd498bf75825778a59c35f2b0b8702cfaf79bb9bcfd', 'tradingagents/research/onchain_replication/census_production.py': '37ec0a081edaf2928146fab3984e362f1241809af43009eb05de307f247665b1', 'tradingagents/research/onchain_replication/checkpoints.py': '74e7bd16d4331cbac45143884e1f35a52687b19280c214457834b0cf19a457bc', 'tradingagents/research/onchain_replication/coinmetrics_prices.py': '5e14eae6fafccdfe562ab07c73ac3854f5e86751d74e468807b82be0a3a0a62f', 'tradingagents/research/onchain_replication/compact_closure.py': 'd59dc91c8aaeba381d104cd065adc2eeeb4698360a58009492ec8dd7730c22bf', 'tradingagents/research/onchain_replication/compact_denominator.py': '6579c4aa57804ecfd35010beb81df0e81f722285bea9fda856d1a7f8e466b372', 'tradingagents/research/onchain_replication/compact_dictionary.py': '1c2618cc3706f4bdbfaba0ec957e1fb908f63857403bbdcc9341181effe313dc', 'tradingagents/research/onchain_replication/compact_features.py': '584268806ac6b6ea713737e4f54a6ba0bd923397165c089f2f359dfb3d916752', 'tradingagents/research/onchain_replication/compact_graph_artifacts.py': 'fd1395b0c274b1b51dc26365fd0c2954f904492cf77ddb3d553ce40c6dc6bf8a', 'tradingagents/research/onchain_replication/compact_matcher.py': '75e4b8bad423ed198bef5017fd4c22670ff3c552bcacd2cc967901efa95bed73', 'tradingagents/research/onchain_replication/compact_mcm.py': '5858ad9fe26c2f9937dbfdf520a503b91157b4840083580ee8d6d6920c89548a', 'tradingagents/research/onchain_replication/compact_mcm_output.py': 'bd118be0c2f9c44eebb1f459184c676dfc66f0ee46cd7f2c0271dea1db11bc99', 'tradingagents/research/onchain_replication/compact_mcm_publication.py': 'd80315a270fab3c4a349e22cd114fa46041c121cdbfccbdc47ae7ce4b04edd25', 'tradingagents/research/onchain_replication/compact_native_features.py': '34a6f63125ac048df2d0f4a2b354ff2c6808ee8fc0dcc4b6a04bff1eeeb6e136', 'tradingagents/research/onchain_replication/compact_native_producer.py': 'e8f46a63eb5893736daa4bc4acac19072e8137e53c4a971dd88610b9b23ec862', 'tradingagents/research/onchain_replication/compact_owner.py': 'f4ff82b6405af36175509431440ee93e70787f46a8e3ab844ee2bccece6cfb51', 'tradingagents/research/onchain_replication/compact_pair_log.py': '4c65ca7f8caf46760eeef23e2bd44e9bc87a64a54bb18a862662be2b15da0089', 'tradingagents/research/onchain_replication/compact_policy.py': '4f4e4f91df881249540e8f7b0e33029f21e680bf7595fb0bbe075a8d8aee9d7d', 'tradingagents/research/onchain_replication/compact_publication.py': 'a620e5f84c2ec5095ae1715aae4a7962e64180075d139e424c671a2d486e935a', 'tradingagents/research/onchain_replication/compact_sample_proof.py': 'cb94729af806f10b1c719cc240ec8c2546a1aa2a79591ef62cbf852c29256893', 'tradingagents/research/onchain_replication/compact_sampler.py': '7820254d9a9ac287e55b0d20d2c26e1907b625dd743e194fae0602110593a608', 'tradingagents/research/onchain_replication/compact_samples.py': 'f14a11212edd281901aab69fbe9b1164251988472baa65da6b319d50ff436d7b', 'tradingagents/research/onchain_replication/compact_stage.py': '78a5164a711ee69b3a0406ca63a620e781776798864075c9dd820229ccd4ccc4', 'tradingagents/research/onchain_replication/compact_terminal.py': '72e2604eb4f2829e15de6afac58966d0cc82ff88c91c15335ef0e66dde932328', 'tradingagents/research/onchain_replication/compact_training.py': 'ef70263e79cf743aff6a389866a7fd86615b5bcdbd5b834ebe922ffd420bebd3', 'tradingagents/research/onchain_replication/comparison.py': 'b157f41b2b98517c67152209bac46fbedf3a2eb9471fd27f9c588a41e60c8c23', 'tradingagents/research/onchain_replication/component_store.py': 'ba0cf44dd7cf5af8c0b99cbe129f107ef7b40833a76b8162ae9d91512b566b68', 'tradingagents/research/onchain_replication/contracts.py': '3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a', 'tradingagents/research/onchain_replication/dataset.py': 'c8d701b5646395bb94e5037aefcc2d0d29a55de95cca05e019ce35d3f53561df', 'tradingagents/research/onchain_replication/dictionary.py': '32e27a4a17dc2aa993d1440d6486c75b0d4dcff341969dbf99bdff412dd7e446', 'tradingagents/research/onchain_replication/environment.py': '8b3d09acbce94502f58f5d595c0018e45e9854b8f04241705c50fb21051b8a28', 'tradingagents/research/onchain_replication/eth_source.py': '78e0731e16d2751534e3530dde7313e94950bd852f99b30cec4661dbf7db1487', 'tradingagents/research/onchain_replication/evaluation.py': '52f386ec34f9c52b5b0e995b0acfd588bb4e8566dc5425a2ed08d9dd6177d5bb', 'tradingagents/research/onchain_replication/feature_journal.py': 'd997b27bf3c5d5a1db0c77a6ce5bf9ed696800a4c88300634eec3efed349ff59', 'tradingagents/research/onchain_replication/feature_pipeline.py': '19ebe96275095ded92743a1a1bcadc4178f85cd5d39f1ed23786fba279b5fa41', 'tradingagents/research/onchain_replication/feature_residency.py': '4ea5370958b65edf0d37950f12d358ab562291c786f28a287514c77c3838ddcd', 'tradingagents/research/onchain_replication/gat.py': 'c2292bb164869bb4202a2af028a453f547d8e2930cd9d58ee4a59ffcb72913d6', 'tradingagents/research/onchain_replication/graph_baselines.py': 'f284a85a0ce3aa5dee24c748c6a376d9d44a2d775409b874540215ff0e594907', 'tradingagents/research/onchain_replication/graph_production.py': 'ef5ee5e2c8f6438e4e334d1a468397ad6f60e176d157e7849b7132737c7c85e8', 'tradingagents/research/onchain_replication/graph_residency.py': '1ded72ad7c25135780a718455b430eafa020e8f3de6ca608b04e005b798609a6', 'tradingagents/research/onchain_replication/graph_store.py': 'a762aa9e8b19a1da1a41e27bf49fb047d0104bb009a6d35561b8774d8c2958da', 'tradingagents/research/onchain_replication/hub_census_production.py': 'b9c406f19c32f2b78409b9a3260edebcad0ced042e9e4d187ff44e574d763d2a', 'tradingagents/research/onchain_replication/hub_edges.py': 'e5858170437f6d9f0a994315e2b2aa30d502844cf0a1c1b8ec782a1e693887e9', 'tradingagents/research/onchain_replication/job.py': '91dbda651cd5d87860ff9e85f267117b162d18a14d6f725f589454b42bc834e1', 'tradingagents/research/onchain_replication/job_payload.py': '0303ea2e516e57e1d4a850b3eadf13b3b23ee047b48df1417e8ae559ff171ab0', 'tradingagents/research/onchain_replication/journal_recovery.py': '1f5a280789572a01d943e80081930e324e621127b742ef67b6d93b6041ed009d', 'tradingagents/research/onchain_replication/mapped_graph.py': 'c5e93b325599a82bf65e5b31074e9c76a73b25d479ddea7d3ff3687e75f7b197', 'tradingagents/research/onchain_replication/matching.py': 'e5a4cb7966a53522532158a13ef7293d4d081a26cffba56c2eb0761a628c72a6', 'tradingagents/research/onchain_replication/matching_ancestry.py': '51221522256e3f1babb03512a8dad4d293d12638c4579d4bddcf92945db5e4bc', 'tradingagents/research/onchain_replication/matching_annealing.py': 'c1331bf7fd6bc436c2663c626c69c6bcecffcc16a8e56992c9c6bcf520ab0b47', 'tradingagents/research/onchain_replication/matching_checkpoint.py': 'de8f7077e513105719fffcf6ea13e96bfb0199056acf0227ecf744df189ee35c', 'tradingagents/research/onchain_replication/matching_death.py': 'f76a96274e77d4f728d9d7e0b93db2a8bb4e663654ae59c0480f6c66192c3ff8', 'tradingagents/research/onchain_replication/matching_hardening.py': 'c0c4a2eb21ad62d3a966e8619d84370be388e1e4a402f7608fc91abb3f796312', 'tradingagents/research/onchain_replication/matching_identity.py': 'f011658abf3b56b04a0ec33a7bdfed2c68e2e2e79791aa96c5ca7f8fd1653f89', 'tradingagents/research/onchain_replication/matching_owner.py': '36b43349bdcca5f36bd47181f47af6b03987d59fd2f20ac73472d648a58fbf97', 'tradingagents/research/onchain_replication/matching_pair.py': '3fc8a0666b2b4bf334411a85decd7dbf484b038827255714c6727ffe3846621c', 'tradingagents/research/onchain_replication/matching_policy.py': '5d552673fb772f61344d212606a5d9d2c22c91c8de44dfa501d57422c9b4e739', 'tradingagents/research/onchain_replication/matching_reference.py': '75e3269a94cf0d840c299f52c7b138b58dd138251bde6048e52e6c1149934332', 'tradingagents/research/onchain_replication/matching_sparse.py': '06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e', 'tradingagents/research/onchain_replication/mcm.py': 'd2527cdc34f1032f6ed9a3ff175fd1e7c21412e19e1d449ac53f773bd582f9df', 'tradingagents/research/onchain_replication/mcm_score_stream.py': 'c70b23d4f8d16aa418109647bdba7ccd2139a2c1ef910b5acad8535aeebde1d7', 'tradingagents/research/onchain_replication/metrics.py': '9476c2052e02be278c01360fa598a3a136a791ffaa90d90f1fde992c8a27c84b', 'tradingagents/research/onchain_replication/model.py': '2f55b04d3a707e212b2a1d9e0fb591eb3ec2b4828614edcc1a5a5d8f313d3b8e', 'tradingagents/research/onchain_replication/model_registry.py': 'c0e2202578ae708e2fc0406ece5726541952bf40f29df9dc81812c177c334543', 'tradingagents/research/onchain_replication/native_producer.py': '5b7dff71ffe2b1e6c0570b859020d82af337d753665ae77cbea95ff07d1914ed', 'tradingagents/research/onchain_replication/native_reuse.py': 'a84274b035278fb5d840f58420cdc4d70eb7c5d8ca2ee5247392cf6bb29b2bbb', 'tradingagents/research/onchain_replication/neighborhood_census.py': 'be4704d1b19028c2ce734c35483986d6b49d7eecd6f6bd9048c96208b51c02a9', 'tradingagents/research/onchain_replication/neighborhood_policy.py': 'f86e19de0bedd4c12ef73fe2ba243990256f592c604c083d8e772ce8131bc12a', 'tradingagents/research/onchain_replication/neighborhoods.py': 'b53901125dc20dbb8a38b6e0e539866fb04109053afbcba0d75b2a2a8dc38271', 'tradingagents/research/onchain_replication/neural_authority.py': 'eed5f79f4c34819fb64ac2d79069ff56e4b24d175f2d391da9856f9d50186fb2', 'tradingagents/research/onchain_replication/neural_phases.py': '11af32f66fa1d9289c713da0304a5c7e0d6dd7a0623f783597bd0f9368988d71', 'tradingagents/research/onchain_replication/neural_physical.py': '8891e3ed52142f23ae987b8985cd4ee8e09caf86658623e43a37df7140dfe190', 'tradingagents/research/onchain_replication/neural_resource.py': 'ae7cd7ff76b0ddfd5e55645ea7a36a56d12089388add620a99fc70b1bc6759b9', 'tradingagents/research/onchain_replication/parquet_ranges.py': '482c0686e552aae3157bf6cf12f802e0d284c68ce14d879000253b895450b044', 'tradingagents/research/onchain_replication/pooling.py': '054845bed22c44294ce41f2263155df0397c42b0b306755e36791ae5a3960303', 'tradingagents/research/onchain_replication/population_assembly.py': 'b287792dbb605438ac2629e2c576de7cf59caea8e776c8baa3f708b32317a450', 'tradingagents/research/onchain_replication/population_batch_projection.py': 'cc388ced1969c52dea94646733284edd763a427390be297c90097c6ed77a6267', 'tradingagents/research/onchain_replication/preservation.py': '2849670dcf847a97274cf590a2c6732cd7749e0e9e3e64e802cb2e415f08a410', 'tradingagents/research/onchain_replication/price_source.py': '66af531218352999667f2cac88c8393e70ddcf956b8e9f05db16a52c6b2f6e74', 'tradingagents/research/onchain_replication/prices.py': '5f44f1e689b614121c4b9cab5da75e17322074a9ec9f2a30a174ac353093798f', 'tradingagents/research/onchain_replication/provenance.py': 'daf6cc3e72202dff01c50034f6a5ed3d5dcbb339d0e050444f722ce82a353471', 'tradingagents/research/onchain_replication/range_source.py': '5f1e004a89e2339d1f21c941415dc3976e9523f509a1d1591f23a8ea7a836bd7', 'tradingagents/research/onchain_replication/registered_features.py': '8a79c459336773bd139f377fe44fe1006796378651d30a8eb22c966c72f7b267', 'tradingagents/research/onchain_replication/replay.py': '37cb3925ac1e4a453ed385fd560b463e88f1ddb91cf00af338c08230ed244691', 'tradingagents/research/onchain_replication/resources.py': 'b58a85744df475d267bf59a06130649bb66ef8e83d2ec0d57233b26355853047', 'tradingagents/research/onchain_replication/restart_retention.py': '15e7b2090ce87081b0cd6e2338b4d62d348d779082947729cacf0210d3c6dc7d', 'tradingagents/research/onchain_replication/run.py': '077eaeb585748dc40647b0ba46193956e87e6459fe18a92c41cb6b18ce559c1f', 'tradingagents/research/onchain_replication/sampling_policy.py': '79d1253009e6ba5e8815f82fdf3422113d5559b92e5e0e36bfec84fc2963354d', 'tradingagents/research/onchain_replication/sampling_weights.py': '5f1837f93fe0523d7c851654390584fc6c04fb803f2025fd027e74a5da8318d1', 'tradingagents/research/onchain_replication/score_batches.py': '715125e543edd383c4bdeab59d10f7a269faec18f3b5fd16af79013e1bb37555', 'tradingagents/research/onchain_replication/score_tail.py': 'b5e807e022349ca7e0d18c02512812932103865ba0779d641be6877995694870', 'tradingagents/research/onchain_replication/serialization.py': 'f711a0a931fe9fb91aadf0ad7ba6e68b638f3874e736790e05edd21acdefc65b', 'tradingagents/research/onchain_replication/source_footers.py': '65005ceca3072760befb09680f9c7aa469d5aaa5ab3f2af6a741d4ed2fef660e', 'tradingagents/research/onchain_replication/source_inventory.py': '6d868efe77d4d84af97fdb1657585ad86fda15866b44541f111656d3e09759db', 'tradingagents/research/onchain_replication/stage_retention.py': '2f608ba1735fd07fdf18eab8969854f61e9769603b84b16869a008cde108b478', 'tradingagents/research/onchain_replication/stage_retention_reader.py': 'c2ae559de8721bea87a3520d9d13591f6c47ee6cad9971c7166c2c63937736f5', 'tradingagents/research/onchain_replication/streamed_gat.py': 'e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f', 'tradingagents/research/onchain_replication/subsets.py': '59a17cb12711d8ec518f6f25ec4518f143647b79c3ef3286399dada114b7a22c', 'tradingagents/research/onchain_replication/temporal.py': 'd8adafb5a50716ce472848df05e8bbb804525ed8003958c7f9a25c82d81ad226', 'tradingagents/research/onchain_replication/training.py': '5c0380de62c670d356ea3546c7b81eed4ccab55a886bc27b6a1bbfd75c2c3369', 'tradingagents/research/onchain_replication/treatment_contract.py': 'fb148eb922431bdd46c2bd4c310d48b180d1f040c50e1d64d63ca0dc859a11fc', 'tradingagents/research/onchain_replication/treatment_production.py': '210db787eaf830974357831c4142260baf8d0043e8049f6794f31f05eb1d208c', 'tradingagents/research/onchain_replication/verification.py': 'c492cc9be2eb0956035800c26bde5d6cc2999844cd7466eb151bd3ea82815873', 'tradingagents/research/onchain_replication/weekly.py': '079a427f212738759109b31da23933549a8b7751851e3033703cdd03dc5f054a', 'tradingagents/research/onchain_replication/workflow_storage.py': 'bf52b9408008ac3616f867ebef8130e2f315f8c8febf00ab1815557d68684554', 'tradingagents/research/verify.py': '1f14343c7918e3464991b9b57ecdf74425130de5c049a4e401d896116881efce'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def stamp(value):
    require(type(value) is str and value.endswith('Z'), 'canonical UTC clock required')
    t = datetime.fromisoformat(value[:-1] + '+00:00')
    require(t.isoformat().replace('+00:00', 'Z') == value, 'canonical UTC clock required')
    return t


def pin(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'SHA256 required')


def role(value):
    require(type(value) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value) is not None, 'registered role required')


def schema(value, asset, variant, weeks):
    require(type(value) is dict and set(value) == {'schema_version', 'asset', 'variant', 'expected_weeks', 'weeks'}, 'treatment admission fields differ')
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'treatment version differs')
    require(asset in ('BTC', 'ETH') and variant in ('whale', 'fund') and (variant != 'fund' or asset == 'ETH'), 'paper treatment identity differs')
    require(value['asset'] == asset and value['variant'] == variant, 'requested treatment differs')
    require(type(weeks) in (list, tuple) and 0 < len(weeks) <= 1024 and list(weeks) == sorted(set(weeks)), 'finite full weekly denominator required')
    require(value['expected_weeks'] == list(weeks) and set(value['weeks']) == set(weeks), 'treatment weekly denominator differs')
    for week in weeks:
        t = stamp(week)
        require(t.weekday() == 0 and t.time().isoformat() == '00:00:00', 'full Monday week required')
        r = value['weeks'][week]
        require(type(r) is dict and set(r) == {'status', 'claim_input', 'terminal_input', 'ledger_input', 'job_input', 'plan_input', 'disposition_input', 'receipt_input', 'coverage_input', 'manifest_input', 'components', 'aliases'}, 'weekly lineage fields differ')
        require(r['status'] in ('complete', 'unavailable'), 'unknown treatment disposition')
        for key in ('claim_input', 'terminal_input', 'ledger_input', 'job_input', 'plan_input'):
            role(r[key])
        require(type(r['components']) is dict and len(r['components']) <= 10 and type(r['aliases']) is dict and len(r['aliases']) <= 100, 'bounded component/alias map required')
        for a, b in r['aliases'].items():
            role(a); role(b)
        for path, name in r['components'].items():
            require(path in ('graph/manifest.json', 'edge_satoshis.hex', 'incident_satoshis.hex', 'node_ids.npy', 'node_features.npy', 'edge_index.npy', 'edge_features.npy', 'edge_aggregates.npy', 'graph/node_ids.npy', 'graph/node_features.npy', 'graph/edge_index.npy', 'graph/edge_features.npy', 'graph/edge_aggregates.npy'), 'unknown component member')
            role(name)
        if r['status'] == 'complete':
            role(r['disposition_input'])
            for key in ('receipt_input', 'coverage_input', 'manifest_input'):
                role(r[key])
            require(r['components'], 'complete component lineage required')
        else:
            if r['disposition_input'] is not None: role(r['disposition_input'])
            require(all(r[k] is None for k in ('receipt_input', 'coverage_input', 'manifest_input')) and r['components'] == {}, 'unavailable must not impersonate a completed graph')
    return value


def disposition(claim, terminal, ledger, claim_hash, ledger_hash, plan, week, variant, asset, *, absent=False):
    """Pure join; caller must separately authenticate actual committed claim."""
    pin(claim_hash); pin(ledger_hash)
    require(terminal.get('claim_sha256') == claim_hash and terminal.get('experiment_id') == claim.get('experiment_id'), 'terminal/claim identity differs')
    require(type(ledger) is list and [r['id'] for r in ledger] == claim['experiment']['cells'], 'complete ordered cell denominator differs')
    ids = ['treatment-' + asset.lower() + '-' + variant + '-' + w[:10] for w in plan['expected_weeks']]
    require(claim['experiment']['cells'] == ids, 'registered treatment cells differ')
    for r in ledger:
        require(r.get('status') in ('complete', 'unavailable') and (r['status'] != 'unavailable' or r.get('reason')), 'explicit disposition required')
    if terminal.get('status') == 'complete':
        require(terminal.get('source') == claim['source'] and terminal.get('registration_sha256') == claim['registration_sha256'], 'terminal source/registration differs')
        require(terminal.get('output_sha256', {}).get('cell-ledger.json') == ledger_hash and terminal.get('cells') == ledger, 'terminal ledger differs')
        require(terminal.get('cell_count') == len(ledger) and terminal.get('unavailable_count') == sum(r['status'] == 'unavailable' for r in ledger), 'terminal counts differ')
    else:
        require(terminal.get('status') == 'failed', 'unknown/active outcome unavailable for consumption')
    selected = next(r for r in ledger if r['id'] == 'treatment-' + asset.lower() + '-' + variant + '-' + week[:10])
    if terminal['status'] == 'failed':
        require(selected['status'] == 'unavailable', 'failed producer cannot grant completed treatment admission')
    if absent:
        require(terminal['status'] == 'failed' and selected['status'] == 'unavailable' and set(selected) == {'id', 'status', 'reason'}, 'exact failed absent-row shape required')
        # Cell identity is already bound to registered asset/variant/week above.
        # Return the real fallback unchanged; never fabricate asset/week fields.
    else:
        require(selected.get('asset') == asset and selected.get('week') == week, 'cell asset/week differs')
    return selected


def graph_join(receipt, row, graph, graph_hash, coverage, coverage_hash, receipt_hash, claim, claim_hash, plan_hash, parent, parent_hash, week, asset, variant):
    """Validate exact declared graph transform; no array decoding or method change."""
    for p in (graph_hash, coverage_hash, receipt_hash, claim_hash, plan_hash, parent_hash):
        pin(p)
    require(receipt.get('schema_version') == 1 and receipt.get('kind') == 'registered-graph-treatment-receipt', 'treatment receipt schema differs')
    expected = {'asset': asset, 'variant': variant, 'week': week, 'claim_sha256': claim_hash, 'plan_sha256': plan_hash, 'source': claim['source'], 'manifest_sha256': graph_hash, 'parent_manifest_sha256': parent_hash}
    require(all(receipt.get(k) == v for k, v in expected.items()), 'treatment receipt ancestry differs')
    require(row.get('manifest_sha256') == graph_hash and row.get('coverage_sha256') == coverage_hash and row.get('treatment_receipt_sha256') == receipt_hash, 'cell component receipts differ')
    m, p = graph['metadata'], parent['metadata']
    end = (stamp(week) + timedelta(days=7)).isoformat().replace('+00:00', 'Z')
    require(m['asset'] == p['asset'] == asset and m['start_utc'] == p['start_utc'] == week and m['end_utc'] == p['end_utc'] == receipt['end_utc'] == end, 'graph asset/date differs')
    require(graph['graph_hash'] == receipt['graph_hash'] and parent['graph_hash'] == receipt['parent_graph_hash'], 'graph object ancestry differs')
    require(receipt['available_at'] == m['available_at'] and stamp(m['available_at']) >= stamp(p['available_at']) >= stamp(end) + timedelta(days=1), 'graph availability differs')
    decision = receipt['decision']
    require(decision['variant'] == variant and decision['parent_graph_hash'] == parent['graph_hash'], 'decision parent/treatment differs')
    require(decision['schema_version'] == (3 if asset == 'BTC' else 2), 'original exact treatment encoding required')
    require(m['graph_config_hash'] == sha(canonical({'parent_config': p['graph_config_hash'], 'variant': decision})), 'per-week transformation configuration differs')
    require(m['source_hashes'] == p['source_hashes'] and all(m[k] == p[k] for k in ('raw_count', 'admitted_count', 'exclusion_counts')), 'original raw counters/source membership changed')
    require(coverage['graph_config_hash'] == m['graph_config_hash'] and coverage['graph_manifest_sha256'] == graph_hash and coverage['claim_sha256'] == claim_hash and coverage['plan_sha256'] == plan_hash and coverage['asset'] == asset and coverage['week'] == week and coverage['end_utc'] == end, 'derived coverage differs')
    if variant == 'fund':
        raise ValueError('UNADMITTED: exact historical cohort and known_at policy independent admission required')
    require(receipt['cohort_sha256'] is None and receipt['cohort_review_sha256'] is None and decision['decision'] == {'threshold': .9, 'strict': True}, 'original whale threshold/cohort differs')
    require(m['available_at'] == p['available_at'], 'whale availability must preserve parent clock')
    return {'status': 'complete', 'graph_hash': graph['graph_hash'], 'available_at': m['available_at'], 'graph_config_hash': m['graph_config_hash'], 'manifest_sha256': graph_hash}


def _reader_cleanup(actions, primary):
    """All cleanup attempted; first fatal retained, then first ordinary error."""
    selected = primary
    errors = []
    for action in actions:
        try:
            action()
        except BaseException as error:
            errors.append(error)
            fatal = lambda e: isinstance(e, MemoryError) or not isinstance(e, Exception)
            if selected is None or (fatal(error) and not fatal(selected)):
                selected = error
    if selected is not None:
        others = [e for e in ([primary] if primary is not None else []) + errors if e is not selected]
        if others:
            try:
                if selected.__cause__ is not None and all(selected.__cause__ is not e for e in others):
                    others.append(selected.__cause__)
                selected.__cause__ = BaseExceptionGroup('treatment metadata cleanup failures', others)
            except BaseException:
                pass
        raise selected


def _owned_metadata_bytes(path):
    """Transfer one real fd to one stream; failures preserve acquired ownership."""
    import os, stat
    fd = None
    stream = None
    primary = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        stream = os.fdopen(fd, 'rb')
        fd = None  # Ownership transfers only after fdopen returned successfully.
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'regular metadata required')
        raw = stream.read(LIMIT + 1)
    except BaseException as error:
        primary = error
    finally:
        _reader_cleanup((lambda: stream.close() if stream is not None else None,
                         lambda: os.close(fd) if fd is not None else None), primary)
    return raw


def _reader(run, name, metadata=True):
    from ..admission import local_path
    role(name)
    item = run.admission.inputs[name]
    path = local_path(run.admission.root, item['path'])
    # Bound before ResearchRun.read_input (which otherwise reads the whole body).
    require(path.is_file() and not path.is_symlink(), 'regular admitted input required')
    if metadata:
        require(path.stat().st_size <= LIMIT, 'metadata exceeds 4MiB')
        raw = _owned_metadata_bytes(path)
        require(len(raw) <= LIMIT and sha(raw) == item['sha256'], 'metadata extent/hash differs')
        return json.loads(raw), raw, path
    from .provenance import file_hash
    require(file_hash(path) == item['sha256'], 'component bytes changed')
    return item['sha256'], path


def _closed(run, claim_role, terminal_role):
    from ..verify import verify_claim
    from .job import _terminal
    claim, raw, path = _reader(run, claim_role)
    terminal, traw, tpath = _reader(run, terminal_role)
    require(path == run.admission.root/'research_runs'/claim['experiment_id']/'claim.json', 'actual retained claim path required')
    require(tpath == path.parent/(terminal['status'] + '.json') and terminal['status'] in ('complete', 'failed'), 'actual terminal path required')
    require(not (path.parent/('failed.json' if terminal['status'] == 'complete' else 'complete.json')).exists(), 'contradictory terminal')
    require(verify_claim(path.parent) == claim, 'committed source/registration claim differs')
    require(_terminal(tpath, claim, sha(raw), run.admission.root, terminal['status']) == terminal, 'terminal output closure differs')
    return claim, terminal, raw, traw


def admit_treatment(run, input_name, *, asset, variant, weeks):
    from ..lifecycle import ResearchRun
    from .treatment_contract import schema as producer_schema, parent_receipts
    require(type(run) is ResearchRun, 'genuine active ResearchRun required')
    run._active(); run._check_source()
    require(type(PRODUCER_SOURCE_PINS) is dict and PRODUCER_SOURCE_PINS, 'UNADMITTED: exact reviewed producer successor pins required')
    from .provenance import file_hash
    source_path = Path(__file__)
    self_relative = str(source_path.relative_to(run.admission.root))
    self_hash = file_hash(source_path)
    require(run.admission.experiment['source_files'].get(self_relative) == self_hash, 'treatment verifier source is not admitted')
    # Fixed other-source pins plus the current admitted verifier close the map
    # without embedding this file's own hash into its body.
    producer_pins = {**PRODUCER_SOURCE_PINS, self_relative: self_hash}
    value, body, _ = _reader(run, input_name)
    schema(value, asset, variant, weeks)
    result = {}
    for week, reference in value['weeks'].items():
        claim, terminal, craw, _ = _closed(run, reference['claim_input'], reference['terminal_input'])
        require(all(claim['experiment']['source_files'].get(k) == v for k, v in producer_pins.items()), 'unreviewed producer source closure')
        plan, praw, _ = _reader(run, reference['plan_input'])
        producer_schema(plan)
        require((plan['asset'], plan['variant']) == (asset, variant) and week in plan['expected_weeks'], 'producer plan differs')
        job, jraw, _ = _reader(run, reference['job_input'])
        require(job['kind'] == 'treatments' and claim['inputs']['execution_job']['sha256'] == sha(jraw) and claim['inputs'][job['payload']['plan_input']]['sha256'] == sha(praw), 'actual registered job/plan differs')
        ledger, lraw, lpath = _reader(run, reference['ledger_input'])
        expected_ledger = run.admission.root/'research_runs'/claim['experiment_id']/'outputs'/'cell-ledger.json'
        if terminal['status'] == 'failed':
            expected_ledger = run.admission.root/PREFIX/'runs'/claim['experiment_id']/'postmortem-cells.json'
        require(lpath == expected_ledger, 'actual complete/postmortem ledger path differs')
        row = disposition(claim, terminal, ledger, sha(craw), sha(lraw), plan, week, variant, asset, absent=reference['disposition_input'] is None)
        actual_row_path = run.admission.root/PREFIX/'treatments'/claim['experiment_id']/(row['id']+'.json')
        if reference['disposition_input'] is None:
            require(row['status'] == 'unavailable' and terminal['status'] == 'failed' and not actual_row_path.is_symlink() and not actual_row_path.exists() and actual_row_path.resolve() == actual_row_path, 'only failed absent cell may use postmortem absence')
        else:
            saved, _, spath = _reader(run, reference['disposition_input'])
            require(saved == row and spath == actual_row_path, 'actual per-cell disposition differs')
        require(row['status'] == reference['status'], 'treatment status changed')
        if row['status'] == 'unavailable':
            result[week] = {'status': 'unavailable', 'reason': row['reason'], 'evidence_hashes': [sha(craw), sha(lraw)]}
            continue
        receipt, rraw, rpath = _reader(run, reference['receipt_input'])
        coverage, coraw, copath = _reader(run, reference['coverage_input'])
        outer, mraw, mpath = _reader(run, reference['manifest_input'])
        require(mpath == run.admission.root/row['manifest_path'] and rpath == mpath.parent/'treatment.json' and copath == mpath.parent/'coverage.json', 'actual graph receipt paths differ')
        def original(name, metadata=True):
            alias = reference['aliases'][name]
            require(run.admission.inputs[alias]['sha256'] == claim['inputs'][name]['sha256'], 'original producer input alias differs')
            return _reader(run, alias, metadata)
        parent_ref = plan['parents'][week]
        for key, name in parent_ref.items():
            if key != 'components': original(name)
        parent_outer, pmraw, _ = original(parent_ref['manifest_input'])
        pc, pt, pcraw, ptraw = _closed(run, reference['aliases'][parent_ref['claim_input']], reference['aliases'][parent_ref['terminal_input']])
        pl, plraw, _ = original(parent_ref['ledger_input'])
        parent_row = parent_receipts(pc, pt, pl, sha(pcraw), sha(pmraw), week, asset)
        require(pt['cells'] == pl and pt['output_sha256']['cell-ledger.json'] == sha(plraw), 'parent completed ledger differs')
        pcoverage, pcovraw, _ = original(parent_ref['coverage_input'])
        require(parent_row['coverage_sha256'] == sha(pcovraw), 'parent ledger coverage differs')
        require(coverage['members'] == pcoverage['members'] and pcoverage['claim_sha256'] == sha(pcraw) and pcoverage['graph_manifest_sha256'] == sha(pmraw), 'original complete coverage differs')
        for field, raw in (('parent_coverage_sha256', pcovraw), ('parent_claim_sha256', pcraw), ('parent_terminal_sha256', ptraw), ('parent_ledger_sha256', plraw)):
            require(receipt[field] == sha(raw), 'parent receipt hash differs')
        graph, parent = outer, parent_outer
        if asset == 'BTC':
            graph, grow, _ = _reader(run, reference['components']['graph/manifest.json'])
            parent, pgraw, _ = original(parent_ref['components']['graph/manifest.json'])
            require(sha(grow) == outer['graph_manifest_sha256'] and sha(pgraw) == parent_outer['graph_manifest_sha256'], 'BTC inner manifest differs')
        for manifest, components, reader, base in ((graph, reference['components'], lambda r: _reader(run, r, False), mpath.parent), (parent, parent_ref['components'], lambda r: original(r, False), original(parent_ref['manifest_input'])[2].parent)):
            expected = {('graph/' if asset == 'BTC' else '')+v['path']: v['sha256'] for v in manifest['arrays'].values()}
            if asset == 'BTC':
                current_outer = outer if manifest is graph else parent_outer
                expected.update({'graph/manifest.json': current_outer['graph_manifest_sha256'], **{n+'.hex': v['sha256'] for n,v in current_outer['sidecars'].items()}})
            require(set(components) == set(expected), 'exact component denominator differs')
            for member, expected_hash in expected.items():
                actual_hash, actual_path = reader(components[member])
                require(actual_hash == expected_hash and actual_path == base/member, 'component hash/location differs')
        result[week] = graph_join(receipt, row, graph, sha(mraw), coverage, sha(coraw), sha(rraw), claim, sha(craw), sha(praw), parent, sha(pmraw), week, asset, variant)
        result[week]['population_manifest_sha256'] = sha(canonical(graph)) if asset == 'ETH' else sha(grow)
        if asset == 'ETH':
            result[week]['population_manifest_sha256'] = sha(mraw)
    run._active(); run._check_source()
    return result


def verify_example_metadata(rows, admitted):
    """Only dates, hashes and availability; no prices/targets/test labels read."""
    for dates, hashes, available in rows:
        require(len(dates) == len(hashes) == len(available), 'example treatment membership lengths differ')
        for date, h, a in zip(dates, hashes, available, strict=True):
            step = stamp(date+'T00:00:00Z') + timedelta(days=1)
            lagged = step - timedelta(days=1)
            end = (lagged-timedelta(days=lagged.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            week = (end-timedelta(days=7)).isoformat().replace('+00:00', 'Z')
            r = admitted[week]
            require(r['status'] == 'complete' and r['graph_hash'] == h and r['available_at'] == a and stamp(a) <= step, 'example consumed unavailable/wrong/late treatment graph')


def preflight_treatment(run, reference, cell, examples):
    if cell['variant'] not in ('whale', 'fund'):
        require('treatment_input' not in reference, 'unexpected treatment evidence on untreated population')
        return
    require('treatment_input' in reference and 'treatment_weeks' in reference, 'mandatory treatment population receipt missing')
    require('treatment_population_plan_input' in reference, 'full population calendar/denominator input required')
    population_plan, _, _ = _reader(run, reference['treatment_population_plan_input'])
    require(population_plan.get('treatment_input') == reference['treatment_input'], 'population and fit treatment contracts differ')
    calendar, _, _ = _reader(run, population_plan['calendar_input'])
    from .population_assembly import required_weeks
    from .contracts import Fold
    fold = Fold(**population_plan['fold'])
    require(fold.id == cell['fold'] and fold.member_hash == examples.fold_hash, 'actual fold treatment binding differs')
    weeks = required_weeks(fold, calendar['lookback_days'])
    require(list(weeks) == reference['treatment_weeks'] == population_plan['expected_weeks'], 'full fit treatment week denominator differs')
    admitted = admit_treatment(run, reference['treatment_input'], asset=cell['asset'], variant=cell['variant'], weeks=weeks)
    verify_example_metadata(((x.input_dates, x.graph_hashes, x.graph_available_at) for partition in (examples.train, examples.test) for x in partition), admitted)
