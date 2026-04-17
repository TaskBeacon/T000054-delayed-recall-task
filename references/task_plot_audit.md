# Task Plot Audit

- generated_at: 2026-04-17T09:21:51
- mode: existing
- task_path: E:\Taskbeacon\T000054-delayed-recall-task

## 1. Inputs and provenance

- E:\Taskbeacon\T000054-delayed-recall-task\README.md
- E:\Taskbeacon\T000054-delayed-recall-task\config\config.yaml
- E:\Taskbeacon\T000054-delayed-recall-task\src\run_trial.py

## 2. Evidence extracted from README

- | Step | Description |
- |---|---|
- | Trial Fixation | Show a centered fixation cross before the first object in the sequence. |
- | Encoding Item | Show an object card and collect indoor/outdoor judgment with `F` / `J`. |
- | Inter-Item Delay | Show a blank interval, then a left/right ear tone, then a blank remainder. |
- | Distractor Task | Present arrow trials and collect left/right arrow-key responses. |
- | Temporal-Order Probe | Show two studied objects side by side and ask which appeared earlier. |
- | Temporal-Distance Probe | Show the same pair and collect a 1-4 subjective distance rating. |
- | Source Probe | Show one studied object and ask which ear carried the tone for that item. |
- | Sequence Summary | Show block-level accuracy and continue to the next sequence. |

## 3. Evidence extracted from config/source

- practice_sequence: phase=sequence fixation, deadline_expr=settings.fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- practice_sequence: phase=encoding item, deadline_expr=settings.item_duration_s, response_expr=n/a, stim_expr='object_card'
- practice_sequence: phase=encoding isi pre tone, deadline_expr=settings.context_tone_offset_s, response_expr=n/a, stim_expr='blank_screen'
- practice_sequence: phase=context tone, deadline_expr=settings.context_tone_duration_s, response_expr=n/a, stim_expr=str(item['tone_asset_id'])
- practice_sequence: phase=encoding isi post tone, deadline_expr=settings.post_tone_duration_s, response_expr=n/a, stim_expr='blank_screen'
- practice_sequence: phase=distractor task, deadline_expr=settings.distractor_trial_duration_s, response_expr=n/a, stim_expr='distractor_arrow'
- practice_sequence: phase=temporal order probe, deadline_expr=settings.order_response_window_s, response_expr=n/a, stim_expr='pair_cards'
- practice_sequence: phase=temporal distance probe, deadline_expr=settings.distance_response_window_s, response_expr=n/a, stim_expr='distance_scale'
- practice_sequence: phase=source memory probe, deadline_expr=settings.source_response_window_s, response_expr=n/a, stim_expr='source_probe'
- practice_sequence: phase=sequence summary, deadline_expr=None, response_expr=n/a, stim_expr='sequence_summary_text'
- test_sequence_01: phase=sequence fixation, deadline_expr=settings.fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_sequence_01: phase=encoding item, deadline_expr=settings.item_duration_s, response_expr=n/a, stim_expr='object_card'
- test_sequence_01: phase=encoding isi pre tone, deadline_expr=settings.context_tone_offset_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_01: phase=context tone, deadline_expr=settings.context_tone_duration_s, response_expr=n/a, stim_expr=str(item['tone_asset_id'])
- test_sequence_01: phase=encoding isi post tone, deadline_expr=settings.post_tone_duration_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_01: phase=distractor task, deadline_expr=settings.distractor_trial_duration_s, response_expr=n/a, stim_expr='distractor_arrow'
- test_sequence_01: phase=temporal order probe, deadline_expr=settings.order_response_window_s, response_expr=n/a, stim_expr='pair_cards'
- test_sequence_01: phase=temporal distance probe, deadline_expr=settings.distance_response_window_s, response_expr=n/a, stim_expr='distance_scale'
- test_sequence_01: phase=source memory probe, deadline_expr=settings.source_response_window_s, response_expr=n/a, stim_expr='source_probe'
- test_sequence_01: phase=sequence summary, deadline_expr=None, response_expr=n/a, stim_expr='sequence_summary_text'
- test_sequence_02: phase=sequence fixation, deadline_expr=settings.fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_sequence_02: phase=encoding item, deadline_expr=settings.item_duration_s, response_expr=n/a, stim_expr='object_card'
- test_sequence_02: phase=encoding isi pre tone, deadline_expr=settings.context_tone_offset_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_02: phase=context tone, deadline_expr=settings.context_tone_duration_s, response_expr=n/a, stim_expr=str(item['tone_asset_id'])
- test_sequence_02: phase=encoding isi post tone, deadline_expr=settings.post_tone_duration_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_02: phase=distractor task, deadline_expr=settings.distractor_trial_duration_s, response_expr=n/a, stim_expr='distractor_arrow'
- test_sequence_02: phase=temporal order probe, deadline_expr=settings.order_response_window_s, response_expr=n/a, stim_expr='pair_cards'
- test_sequence_02: phase=temporal distance probe, deadline_expr=settings.distance_response_window_s, response_expr=n/a, stim_expr='distance_scale'
- test_sequence_02: phase=source memory probe, deadline_expr=settings.source_response_window_s, response_expr=n/a, stim_expr='source_probe'
- test_sequence_02: phase=sequence summary, deadline_expr=None, response_expr=n/a, stim_expr='sequence_summary_text'
- test_sequence_03: phase=sequence fixation, deadline_expr=settings.fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_sequence_03: phase=encoding item, deadline_expr=settings.item_duration_s, response_expr=n/a, stim_expr='object_card'
- test_sequence_03: phase=encoding isi pre tone, deadline_expr=settings.context_tone_offset_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_03: phase=context tone, deadline_expr=settings.context_tone_duration_s, response_expr=n/a, stim_expr=str(item['tone_asset_id'])
- test_sequence_03: phase=encoding isi post tone, deadline_expr=settings.post_tone_duration_s, response_expr=n/a, stim_expr='blank_screen'
- test_sequence_03: phase=distractor task, deadline_expr=settings.distractor_trial_duration_s, response_expr=n/a, stim_expr='distractor_arrow'
- test_sequence_03: phase=temporal order probe, deadline_expr=settings.order_response_window_s, response_expr=n/a, stim_expr='pair_cards'
- test_sequence_03: phase=temporal distance probe, deadline_expr=settings.distance_response_window_s, response_expr=n/a, stim_expr='distance_scale'
- test_sequence_03: phase=source memory probe, deadline_expr=settings.source_response_window_s, response_expr=n/a, stim_expr='source_probe'
- test_sequence_03: phase=sequence summary, deadline_expr=None, response_expr=n/a, stim_expr='sequence_summary_text'

## 4. Mapping to task_plot_spec

- timeline collection: one representative timeline per unique trial logic
- phase flow inferred from run_trial set_trial_context order and branch predicates
- participant-visible show() phases without set_trial_context are inferred where possible and warned
- duration/response inferred from deadline/capture expressions
- stimulus examples inferred from stim_id + config stimuli
- conditions with equivalent phase/timing logic collapsed and annotated as variants
- root_key: task_plot_spec
- spec_version: 0.2

## 5. Style decision and rationale

- Single timeline-collection view selected by policy: one representative condition per unique timeline logic.

## 6. Rendering parameters and constraints

- output_file: task_flow.png
- dpi: 300
- max_conditions: 4
- screens_per_timeline: 11
- screen_overlap_ratio: 0.1
- screen_slope: 0.08
- screen_slope_deg: 25.0
- screen_aspect_ratio: 1.4545454545454546
- qa_mode: local
- auto_layout_feedback:
  - layout pass 1: crop-only; left=0.027, right=0.031, blank=0.110
- auto_layout_feedback_records:
  - pass: 1
    metrics: {'left_ratio': 0.0272, 'right_ratio': 0.0309, 'blank_ratio': 0.1101}
- validator_warnings:
  - timelines[0].phases[9] missing duration_ms; renderer will annotate as n/a.

## 7. Output files and checksums

- E:\Taskbeacon\T000054-delayed-recall-task\references\task_plot_spec.yaml: sha256=056b2f09c36e83c9b675b861d98a4b6f3a0cb0b800c9a2fef8a0a2139af0d47c
- E:\Taskbeacon\T000054-delayed-recall-task\references\task_plot_spec.json: sha256=22d1a32a0140fe9ace7ddc725c95e5cd02740014bd9f268502899e4b03eb2d80
- E:\Taskbeacon\T000054-delayed-recall-task\references\task_plot_source_excerpt.md: sha256=18f2c61a36134a8e0fb20d04123e184fc2a0a5341001b87862f1a15c86688ffc
- E:\Taskbeacon\T000054-delayed-recall-task\task_flow.png: sha256=e3dee108741ea3027038bee3fa2b9e15a61b9d26faf0769cb518f3455934a1b9

## 8. Inferred/uncertain items

- practice_sequence:context tone:stimulus unresolved, used textual fallback
- practice_sequence:sequence summary:unresolved variable 'None'
- test_sequence_01:context tone:stimulus unresolved, used textual fallback
- test_sequence_01:sequence summary:unresolved variable 'None'
- test_sequence_02:context tone:stimulus unresolved, used textual fallback
- test_sequence_02:sequence summary:unresolved variable 'None'
- test_sequence_03:context tone:stimulus unresolved, used textual fallback
- test_sequence_03:sequence summary:unresolved variable 'None'
- collapsed equivalent condition logic into representative timeline: practice_sequence, test_sequence_01, test_sequence_02, test_sequence_03
- unparsed if-tests defaulted to condition-agnostic applicability: interval_remainder_s < -1e-06; not distance_keys; not distractor_keys; not encoding_keys; not source_keys; pair_index < len(plan['source_pairs'])
