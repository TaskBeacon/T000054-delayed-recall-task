# Task Logic Audit

## 1. Paradigm Intent

- Task: Delayed Recall Task
- Primary construct: delayed episodic memory for temporal organization of events, temporal order, and source/context memory
- Manipulated factors:
  - temporal context boundary vs within-context pairing
  - encoding context ear/pitch
  - sequence position / lag between studied items
  - practice vs test sequence role
- Dependent measures:
  - indoor/outdoor encoding accuracy and RT
  - temporal order judgment accuracy and RT
  - temporal distance rating distribution
  - source-memory accuracy and RT
  - timeout counts by phase
- Key citations:
  - `W3048545550` - *Pupil-linked arousal signals track the temporal organization of events in memory*
  - `W2088167889` - *Prefrontal and Medial Temporal Lobe Activity at Encoding Predicts Temporal Context Memory*
  - `W2171345731` - *Human hippocampus represents space and time during retrieval of real-world memories*
  - `W2238578392` - *Recovering and preventing loss of detailed memory: differential rates of forgetting for detail types in episodic memory*

## 2. Block/Trial Workflow

### Block Structure

- Total blocks:
  - human: 4 sequence blocks
  - qa/sim: 2 sequence blocks
- Trials per block: 1
- Randomization/counterbalancing:
  - sequence item order is deterministically shuffled within each block
  - event-boundary ear alternates left/right by 8-item subevent
  - tone frequency is pseudo-randomized from the six-tone pool without repeating adjacent subevents
  - probe pairs are sampled deterministically from the studied list with matched lag constraints
- Condition weight policy:
  - `task.condition_weights` is omitted / null
  - condition generation is even/default through `BlockUnit.generate_conditions(...)`
- Condition generation method:
  - Built-in `BlockUnit.generate_conditions(...)`
  - The block labels are sufficient because each block corresponds to one complete delayed-recall sequence
  - Generated condition data shape: one label per block with `block_idx`, `block_id`, `condition_id`, and `trial_index_in_block`
- Runtime-generated trial values (if any):
  - object sequence order
  - event boundary tone assignment
  - probe-pair selection for same-context vs boundary-spanning comparisons
  - source-memory probes
  - Determinism: derived from `overall_seed + block_idx + trial_index` via a stable `random.Random` seed mix

### Trial State Machine

List each state in order with entry/exit conditions:

1. State name: `sequence_fixation`
   - Onset trigger: block start / first trial entry
   - Stimuli shown: centered fixation cross
   - Valid keys: none
   - Timeout behavior: auto-advance after a brief fixation
   - Next state: `encoding_item`
2. State name: `encoding_item`
   - Onset trigger: after fixation or after the previous ISI finishes
   - Stimuli shown: one everyday-object card with the indoor/outdoor prompt
   - Valid keys: `f` / `j`
   - Timeout behavior: log timeout and continue to the ISI
   - Next state: `encoding_isi_pre_tone`
3. State name: `encoding_isi_pre_tone`
   - Onset trigger: immediately after each object card disappears
   - Stimuli shown: blank screen
   - Valid keys: none
   - Timeout behavior: fixed-duration blank
   - Next state: `context_tone`
4. State name: `context_tone`
   - Onset trigger: 1.5 s into the 3.0 s inter-item interval
   - Stimuli shown: left- or right-ear tone
   - Valid keys: none
   - Timeout behavior: fixed-duration tone playback
   - Next state: `encoding_isi_post_tone`
5. State name: `encoding_isi_post_tone`
   - Onset trigger: after the tone finishes
   - Stimuli shown: blank screen
   - Valid keys: none
   - Timeout behavior: fixed-duration blank
   - Next state: either the next `encoding_item` or `distractor_intro`
6. State name: `distractor_task`
   - Onset trigger: after the final encoding item
   - Stimuli shown: arrow distractor trials with a simple directional prompt
   - Valid keys: `left` / `right`
   - Timeout behavior: log missed arrows and continue until the distractor interval ends
   - Next state: `temporal_order_probe`
7. State name: `temporal_order_probe`
   - Onset trigger: after the distractor interval
   - Stimuli shown: two studied object cards side-by-side and a prompt asking which appeared earlier
   - Valid keys: `f` / `j`
   - Timeout behavior: log timeout and continue
   - Next state: `temporal_distance_probe`
8. State name: `temporal_distance_probe`
   - Onset trigger: immediately after temporal-order response
   - Stimuli shown: the same pair plus a 4-point distance scale
   - Valid keys: `1` / `2` / `3` / `4`
   - Timeout behavior: log timeout and continue
   - Next state: `source_memory_probe`
9. State name: `source_memory_probe`
   - Onset trigger: after the distance response
   - Stimuli shown: a studied object card and a prompt asking whether the tone was left or right ear
   - Valid keys: `f` / `j`
   - Timeout behavior: log timeout and continue
   - Next state: `sequence_summary`
10. State name: `sequence_summary`
    - Onset trigger: after the final source probe
    - Stimuli shown: summary / break screen
    - Valid keys: `space`
    - Timeout behavior: wait for continue
    - Next state: next block or goodbye

## 3. Condition Semantics

For each condition token in `task.conditions`:

- Condition ID: `practice_sequence`
  - Participant-facing meaning: warm-up sequence with the full delayed-recall flow
  - Concrete stimulus realization (visual/audio): 32 everyday-object cards, alternating left/right ear tones, distractor arrows, then temporal-order / distance / source probes
  - Outcome rules: practice data are logged; the sequence is included in summaries but treated as a warm-up
- Condition ID: `test_sequence_01`
  - Participant-facing meaning: scored delayed-recall sequence 1
  - Concrete stimulus realization (visual/audio): same flow as practice with a new deterministic object order and tone schedule
  - Outcome rules: sequence contributes to reported performance metrics
- Condition ID: `test_sequence_02`
  - Participant-facing meaning: scored delayed-recall sequence 2
  - Concrete stimulus realization (visual/audio): same flow as practice with a different seeded object order and probes
  - Outcome rules: sequence contributes to reported performance metrics
- Condition ID: `test_sequence_03`
  - Participant-facing meaning: scored delayed-recall sequence 3
  - Concrete stimulus realization (visual/audio): same flow as practice with a different seeded object order and probes
  - Outcome rules: sequence contributes to reported performance metrics

Also document where participant-facing condition text/stimuli are defined:

- Participant-facing text source (config stimuli / code formatting / generated assets):
  - instructions, prompts, and scale labels are config-defined in `config/*.yaml`
  - object labels are generated from the fixed object pool in `src/utils.py` and formatted into config-backed object-card templates
  - tone files are generated reference assets under `assets/`
- Why this source is appropriate for auditability:
  - all visible wording stays in config templates
  - the object pool is fixed and deterministic, so the same seed yields the same sequence
  - generated tones are simple reproducible assets rather than opaque binary media from an external source
- Localization strategy (how language variants are swapped via config without code edits):
  - English is the default language for this task
  - all participant-facing prompts are stored as config text templates, so future language variants can be swapped by replacing the YAML stimulus text only

## 4. Response and Scoring Rules

- Response mapping:
  - indoor/outdoor encoding: `f` = indoor, `j` = outdoor
  - temporal-order probe: `f` = earlier-left item, `j` = earlier-right item
  - temporal-distance rating: `1` = very close, `2` = close, `3` = far, `4` = very far
  - source memory: `f` = left ear, `j` = right ear
- Response key source (config field vs code constant):
  - config fields define the key labels and visible prompt wording
  - runtime code reads those keys from `TaskSettings`
- If code-defined, why config-driven mapping is not sufficient:
  - no exception is required; the key labels remain config-driven
- Missing-response policy:
  - missed responses are logged as timeouts and the task proceeds to the next phase
- Correctness logic:
  - encoding trial correctness is based on the object's indoor/outdoor tag
  - temporal-order correctness is based on selecting the earlier-studied object
  - source-memory correctness is based on selecting the cue ear actually used at encoding
  - temporal-distance ratings are descriptive rather than strictly correct/incorrect; the runtime records the selected rating and the true lag bucket
- Reward/penalty updates:
  - no explicit points or reward schedule
  - summary metrics are descriptive only
- Running metrics:
  - encoding accuracy, order accuracy, source accuracy, mean RT, timeout counts, and mean distance ratings by pair type

## 5. Stimulus Layout Plan

For every screen with multiple simultaneous options/stimuli:

- Screen name: `encoding_item`
  - Stimulus IDs shown together: `object_card_frame`, `object_card_text`, `encoding_prompt_text`
  - Layout anchors (`pos`): centered card; prompt below the card
  - Size/spacing (`height`, width, wrap): large object label centered; prompt in smaller text below
  - Readability/overlap checks: card and prompt are vertically separated with explicit y-offsets
  - Rationale: keep the object word legible and keep the response rule visible without covering the stimulus
- Screen name: `temporal_order_probe`
  - Stimulus IDs shown together: `pair_left_card_frame`, `pair_left_card_text`, `pair_right_card_frame`, `pair_right_card_text`, `order_prompt_text`
  - Layout anchors (`pos`): left card at negative x, right card at positive x, prompt centered below
  - Size/spacing (`height`, width, wrap): cards sized for wide-screen readability; text wraps disabled because labels are short
  - Readability/overlap checks: cards are separated horizontally enough to avoid label collision
  - Rationale: the earlier/later choice must be visually unambiguous
- Screen name: `temporal_distance_probe`
  - Stimulus IDs shown together: same pair cards plus `distance_prompt_text` and four scale labels
  - Layout anchors (`pos`): scale labels distributed in a row beneath the pair
  - Size/spacing (`height`, width, wrap): scale labels use small/medium height with consistent spacing
  - Readability/overlap checks: each of the four labels is individually anchored
  - Rationale: a four-point scale should read like a single response bar, not overlapping text
- Screen name: `source_memory_probe`
  - Stimulus IDs shown together: `source_object_card_frame`, `source_object_card_text`, `source_prompt_text`, `source_left_label`, `source_right_label`
  - Layout anchors (`pos`): object card centered; ear labels placed left/right below the prompt
  - Size/spacing (`height`, width, wrap): prompt medium size, ear labels large enough to read quickly
  - Readability/overlap checks: left/right labels are separated by a large horizontal gap
  - Rationale: source memory should be a fast binary choice

## 6. Trigger Plan

Map each phase/state to trigger code and semantics.

- `exp_onset`: start of task
- `block_onset`: start of each sequence block
- `sequence_fixation_onset`: fixation before the first encoding item
- `encoding_item_onset`: object card onset
- `encoding_response_f` / `encoding_response_j`: indoor/outdoor response
- `context_tone_onset`: auditory boundary cue
- `distractor_arrow_onset`: arrow distractor trial onset
- `distractor_response_left` / `distractor_response_right`: distractor response
- `temporal_order_probe_onset`: pair-recognition onset
- `temporal_order_response_f` / `temporal_order_response_j`: order response
- `temporal_distance_probe_onset`: distance-rating onset
- `temporal_distance_response_1` / `temporal_distance_response_2` / `temporal_distance_response_3` / `temporal_distance_response_4`: distance rating
- `source_memory_probe_onset`: source-memory onset
- `source_response_f` / `source_response_j`: ear-source response
- `sequence_summary_onset`: sequence break / summary screen
- `good_bye_onset`: goodbye screen
- `block_end`: end of sequence block
- `exp_end`: task end

## 7. Architecture Decisions (Auditability)

- `main.py` runtime flow style (simple single flow / helper-heavy / why):
  - simple single flow using `BlockUnit.generate_conditions(...)` for sequence scheduling and `run_trial(...)` for one complete delayed-recall sequence per block
- `utils.py` used? (yes/no)
  - yes
- If yes, exact purpose (adaptive controller / sequence generation / asset pool / other):
  - deterministic object-pool sampling
  - tone schedule generation
  - probe-pair selection
  - scoring helpers / summary statistics
- Custom controller used? (yes/no):
  - no
- If yes, why PsyFlow-native path is insufficient:
  - n/a
- Legacy/backward-compatibility fallback logic required? (yes/no):
  - no
- If yes, scope and removal plan:
  - n/a

## 8. Inference Log

List any inferred decisions not directly specified by references:

- Decision: use object-word cards rather than bundled object photos
  - Why inference was required: the reference paper does not ship a reusable object image set in the task workspace
  - Citation-supported rationale: the paper clearly requires everyday-object stimuli and a delayed memory test; the representation form is adapted for buildability while preserving the task logic
- Decision: split the 3.0 s inter-item interval into 1.5 s blank + 1.0 s tone + 0.5 s blank
  - Why inference was required: the paper specifies tone onset at 1.5 s into the interval but does not force the exact runtime screen implementation
  - Citation-supported rationale: matches the described timing while keeping the audio cue auditable
- Decision: use a small fixed probe set per sequence rather than every possible pair
  - Why inference was required: the references describe the probe logic but not a repo-sized exhaustive test set
  - Citation-supported rationale: preserves same-context vs boundary-spanning comparison while keeping the human/QA runtime tractable
- Decision: treat temporal-distance ratings as descriptive rather than strictly scored
  - Why inference was required: the published methods emphasize memory organization rather than a single objective rating key
  - Citation-supported rationale: the rating still captures perceived lag while avoiding a fabricated correctness rule

## Contract Note

- Participant-facing labels/instructions/options should be config-defined whenever possible.
- `src/run_trial.py` should not hardcode participant-facing text that would require code edits for localization.
