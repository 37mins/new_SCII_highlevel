# Large-dataset 96-epoch request: scope pending

## September26 evening: current-run scope resolved; external data research only

The user approved **native L8 CP96→192**,96additional online PPO iterations,
768fresh training games plus pre/post8each,12wallh/96GPUh. They subsequently
approved save-every16/sixnewcheckpoints,384GiB inclusive new source/output cap
and448GiB training admission. See [the continuation record](qwen-l8same-cp192-20260926.md).
This replaces the earlier starting-weight/budget uncertainty for THIS run only;
it does not turn the small Parquet file into a large96-epoch corpus or authorize
silently substituting SFT/offline RL. The sections below remain historical.

Read-only filename inventory at18:09–18:13 Beijing found another old pair at
`/data/yangjinyue/sc2-spb2-level7-20260814/data/sc2`:train.parquet3120bytes and
test.parquet3115bytes. The current frozen runtime/data has train/test3479bytes
each and rush_bo.json3136bytes. No recursive server-wide search, Parquet row
read or source-data equivalence check was performed; the older pair is not
established as a larger or better dataset. No raw corpus was downloaded to197.

Later runtime verification: the actual r2 pre96 launcher at18:57 reported
train/test dataset length1, filtered length1 and train/val dataloader size1
in its bounded entry-log tail. This is direct evidence for the current frozen
input, not a row-count assertion for the older3120/3115byte files. Fresh SC2
trajectories are collected online; the Parquet row is not768stored game records.

### Public candidate review (official sources checked September26)

| Candidate | Verified contents / access | Fit and unresolved boundary |
|---|---|---|
| [MSC](https://github.com/wuhuikai/MSC) | Official global-feature download link, train/val/test split, global state evaluation and build-order prediction, including Terran/TvT. Features contain outcome and action labels. Spatial features are not hosted; generation instructions exist. | My first **task-fit** candidate for a small Planner state→build-order/SFT pilot, not proven better performance. Download and dataset license not yet verified. Older SC2 version/action mapping, observation visibility, labels and temporal leakage require checks. Never expose final outcome or future action as input. |
| [SC-Phi2](https://github.com/junaiddk1/sc-phi2) | Official paper repository includes SC2TextData.xlsx, race action descriptions and training notebooks based on MSC. | Useful textual build-order formatting reference; spreadsheet rows/size/license and exact split were not inspected. Not a validated ready-made dataset for our canonical action support. |
| [SC2EGSet v2.1.0](https://zenodo.org/records/17829625) | December5,2025 release; preprocessed SC2ReSet game states,22.1GB published files, explicit CC BY4.0. Official [SC2_Datasets API](https://github.com/Kaszanas/SC2_Datasets). | Candidate for professional-game state analysis / supervised targets after schema inspection. Not automatically text Planner trajectories or on-policy samples. Availability of our exact desired action/observation labels remains unverified. API code license and data license must be treated separately. |
| [TextStarCraftII](https://github.com/sc2musa/Large-Language-Models-play-StarCraftII) | Official text-environment / LLM-agent repository; current README supports Protoss, lists Terran as under development. | Lower immediate fit for our Terran Core comparison. A compatible complete training-data export/license has not been verified; changing its prompt/executor would introduce a new system comparison. |
| [AlphaStar Unplugged](https://github.com/google-deepmind/alphastar/blob/main/alphastar/unplugged/data/README.md) | Official data path requires replay conversion rather than providing prebuilt training tensors; detailed prior review below. | Not first choice for a small near-term text-Planner dataset; substantial format/version/storage work and a distinct offline objective. |

Recommendation is conditional, not a claim of an already better dataset:
after launching the unchanged online continuation, start data due diligence
with a small **MSC Terran/TvT** sample and the SC-Phi2 formatting approach,
provided licensing and actual availability are confirmed. Preserve match-level
train/test separation and prevent replay/player/future-information leakage.
Map observations and actions to our versioned canonical protocol, record
unsupported-action coverage instead of silently salvaging labels, and keep
Executor/reward/observation budgets symmetric between Qwen and SpB. Any SFT
warm-start or offline-RL experiment is a separately approved method; report
initialization/data/compute changes and held-out online evaluation. More rows
or a longer wall clock alone does not prove improved decision-making.

No data download, package installation, license acceptance, external-document
publication, new-model training or automatic dataset replacement was performed
as part of this research. Public repository visibility alone is not proof of
a usable license. This turn's server writes are limited to the separately
approved CP96→192 deployment and counted new output/source roots.

September26, after the completed L8 same96 run: the user selected the second
offered meaning, a fixed large dataset traversed96times, not merely increasing
games per each of96outer RL iterations. This selection is recorded as a
request, not a launched experiment or an approved quantified compute budget.

The dataset path/source, format, row count, train/evaluation partition and
training objective remain unspecified. Asked the user for the dataset path
or link, or whether a dataset must first be constructed. No dataset or model
was substituted, no new RUN_ID/deployment/queue was created, and no GPU work
or server operation occurred in this turn. Prior48wallh/384GPUh/768training
game approval is not reused for an undefined expansion. Initial model versus
existing CP96 and new hard resource ceilings also remain to be frozen before
an eventual formal dispatch.

## Verified implementation boundary

Read the existing repository data paths and training implementation, compared
against the actual L8 frozen runtime
`eef0f049bb09b7a51188ae67a6c35436a3bf055f`:

- `scripts/train_sc2.sh:170` selects `data/train.parquet`; train batch size1.
- `verl/trainer/ppo/ray_trainer.py:646` computes default total steps as
  `len(train_dataloader) * trainer.total_epochs`; lines648–649 replace that
  count when `trainer.total_training_steps` is explicitly set.
- The completed L8 run had explicit total_training_steps96. Merely keeping
  total_epochs96 while changing a data file would not establish96full passes.
- The trainer's epoch/dataloader loops collect fresh trajectories before
  update_actor. `agent_system/multi_turn_rollout/rollout_loop.py:412` resets
  the environment using optional env_kwargs, and lines651onward repeat task
  inputs by env.rollout.n and collect trajectories. The existing SC2 path is
  online interaction, not a loader for repeatedly optimizing saved game logs.
- A fixed task/prompt/scenario dataset traversed96times while collecting
  new trajectories and a static recorded-trajectory dataset trained96times
  are distinct designs. Historical rollouts must not silently become fresh
  on-policy samples. An offline design needs its own compatible objective,
  data/provenance/split checks and approved protocol; PPO minibatch epochs
  must not be silently changed to96as a substitute for dataset epochs.

For unchanged one-task batches and eight rollouts, a dataset yielding B
training batches per complete pass implies96*Bouter collect/update iterations
and96*B*8natural training games, before evaluation. Dataset length, batch size,
drop_last/filtering, protocol and resume state must be resolved before using
that formula for an actual budget. Repeating placeholder rows alone must not
be presented as increased scenario diversity. No duration is promised yet.

## Read-only checks and limitations

The local tracked train.parquet is3479bytes and its Git blob
`42f81060e7e11ca3f61810109d39006dc84f7fb0` matches the frozen L8 Git object.
This establishes file identity, not a large dataset, row count or suitability.
Both system Python and the bundled Python lack pyarrow; attempted Parquet
inspection failed with ModuleNotFoundError. No package was installed and no
row count/content is claimed. No alternate private/server dataset was searched.
The local ray_trainer/rollout_loop files have no diff from the frozen runtime.
Existing complete L8 timing/technical/scientific conclusions remain unchanged.

Validation was read-only source/config-path and Git-object comparison plus
`git diff --check`; no CPU/GPU experiment or training test ran. This is a
clarification record in the same experiment record/branch, not implementation
of a new training protocol. Await the dataset specification, then determine
feasibility, exact96-epoch accounting, starting weights and new budget.

## Historical dataset follow-up — September 26, 17:56 Beijing

The user asked which dataset the earlier approximately 30-hour, "96 epoch"
run used, whether it can be reused, or whether a suitable dataset can be found.
This follow-up is read-only investigation, not authority for a new dataset
download, protocol change or GPU dispatch. No server operation occurred.

### Verified file identity and historical accounting

`shasum -a 256 data/train.parquet data/test.parquet` and `wc -c` returned:

| File | Bytes | SHA-256 |
|---|---:|---|
| train.parquet | 3479 | `7c8f6b07eacef5e06963b475c3c36e90196da870fae095b12c2ea0f7faf10912` |
| test.parquet | 3479 | `4dbe5e3ff68df3fbf76e91284b28b06c52bf7495193013a4bf4ed7ca417a0cd7` |

These exact hashes match both the historical Canonical r6 artifact table in
[`docs/provenance.md`](../../../docs/provenance.md) and the immutable inputs in
the [August 28 Qwen2507 manifest](../../qwen3-4b-instruct-2507-level5-v1/manifest.json).
The train Git blob also matches the actual L8 frozen runtime, as recorded above.
Thus these identified runs already use the same small input file; there is no
evidence here of a larger historical offline dataset that was replaced by a
smaller dataset for L8. Hash identity does not establish row count, and the
Parquet row-count limitation above still applies.

- The [completed August 18 Qwen r6 manifest](../../qwen3-4b-level5-r6/manifest.json)
  explicitly records 96 GiGPO updates, eight rollouts per update, 768 rollouts
  and exit0; completion was August 19 at 01:47:13 UTC. Its current manifest
  does not supply a start time, so it does not prove the remembered 30 hours.
- The August 28 Qwen2507 full96 entry explicitly plans 96 updates / 768
  rollouts and records a start time. Its local `running` label is historical,
  not a current server-status check or confirmation of completion.
- Neither example establishes 96 passes over a large saved-trajectory corpus.
  They must not be presented as a positive identification of the user's
  approximately 30-hour run. Exact run identity and elapsed-time attribution
  remain unresolved; slower wall time alone is not evidence of more data.
- The already verified L8 timing receipt
  [`qwen-l8same-step-semantics-20260926-1729.json`](qwen-l8same-step-semantics-20260926-1729.json)
  records 96 returned outer iterations: summed step timers 22397.47890112363
  seconds (about 6h13m17s, 233.31 seconds per step). This is accumulated
  training timing, not whole-suite wall time, and does not diagnose the old run.

Only the two small Parquet files were found by the tracked/local repository
filename inventory for Parquet inputs. No server-wide data inventory was
performed, and absence of a ready dataset across all servers is not claimed.

### Public candidates and compatibility boundary

Official sources checked September 26:

- [Blizzard replay API documentation](https://github.com/Blizzard/s2client-proto/blob/master/samples/replay-api/README.md)
  documents replay-pack access and version matching, with API credentials and
  an AI/ML license prerequisite. Access/download availability was not tested;
  no credentials were accessed, license accepted or replay downloaded.
- [AlphaStar Unplugged dataset generation](https://github.com/google-deepmind/alphastar/blob/main/alphastar/unplugged/data/README.md)
  explicitly does not provide pre-built training datasets. It describes
  replay download, partitioning and SC2-based conversion to TFRecords. Its
  published full-scale conversion/storage costs are large; a raw replay
  archive is not a ready-to-use dataset for this repository.
- [AlphaStar Unplugged training README](https://github.com/google-deepmind/alphastar/blob/main/alphastar/unplugged/README.md)
  currently lists behavior cloning as the released algorithm. Its offline
  tensor observations/actions do not directly match this project's textual
  canonical Planner/Executor protocol. Using those sources would require a
  separately validated adapter, objective and split, not a Parquet-path swap
  or pretending old samples are fresh on-policy PPO trajectories.

Recommendation, not an implemented or approved change: if the desired goal
is still the existing SC2 online RL task with 96 complete passes, define a
versioned fixed scenario/task dataset, verify that each row actually controls
the intended SC2 initialization, and collect fresh games on every pass.
Keep held-out evaluation separate and freeze group/seed/advantage semantics;
copying placeholder rows alone is not increased task diversity. First fix
dataset size, batch accounting, starting weights and new resource budget.
If the user instead wants fixed recorded-game offline learning, treat that
as a distinct method requiring its own design and approval, not as continuation
of the completed L8 PPO run. No new launch is claimed.

Validation: local Git/file-hash and manifest/source inspection, official-source
reading and `git diff --check` only. No training tests or experiments ran.

## Runtime estimate clarification — September 26, 18:04 Beijing

For the user's question about runtime with `data/train.parquet`, reread the
saved L8 timing receipt above, not a new server snapshot. Under unchanged
Qwen/L8/eight-GPU settings and an explicit 96-update target (768 fresh games),
the measured step timers total 6h13m17s, averaging 3.89 minutes per outer step.
A rough planning estimate is 6–8 hours for training; loading and the short/
final evaluations can add time, and resource waits or failures are excluded.
This is not an estimate for an undefined larger dataset traversed 96 times.
The small input filename/byte size alone does not determine RL duration, and
without a verified dataloader batch count a single full dataset pass is not
equated to one outer step. No new experiment was launched. Validation:
selected JSON/config inspection and `git diff --check`; no runtime tests.
