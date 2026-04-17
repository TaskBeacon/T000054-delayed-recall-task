# Delayed Recall Task

| Field | Value |
|---|---|
| Name | Delayed Recall Task |
| Version | v0.1.0-dev |
| URL / Repository | [TaskBeacon/T000054-delayed-recall-task](https://github.com/TaskBeacon/T000054-delayed-recall-task) |
| Short Description | Delayed episodic memory task with object encoding, alternating ear tones, an arrow distractor, and temporal order / distance / source probes |
| Created By | TaskBeacon build pipeline |
| Date Updated | 2026-04-17 |
| PsyFlow Version | 0.1.12 |
| PsychoPy Version | 2025.2.4 |
| Modality | Behavior |
| Language | English |

## 1. Task Overview

This task implements a delayed-recall paradigm built around sequences of everyday objects. Participants judge each object as indoors or outdoors during encoding, hear alternating left/right ear tones that bind a context cue to the item stream, complete a short arrow distractor, and then answer temporal-order, temporal-distance, and source-memory probes. One practice sequence is followed by three scored sequences.

The runtime is deterministic and audit-friendly. Sequence order, probe selection, tone assignment, and distractor scheduling are seeded from the task configuration, while participant-facing wording stays config-driven for portability.

## 2. Task Flow

![Task Flow](task_flow.png)

### Block-Level Flow

| Step | Description |
|---|---|
| Load Config | Read the mode-specific config and task metadata. |
| Collect Subject Info | Collect subject ID in human mode or inject deterministic IDs in QA/sim. |
| Initialize Runtime | Create the PsychoPy window, keyboard, triggers, and stimulus bank. |
| Show Instructions | Present the delayed-recall instructions and response-key mapping. |
| Run Sequence Block | Present one full sequence: encoding, auditory context cues, distractor, and memory probes. |
| Repeat Blocks | Run one practice block and three scored blocks in order. |
| Finish | Present the goodbye screen, send the end trigger, and quit PsychoPy. |

### Trial-Level Flow

| Step | Description |
|---|---|
| Trial Fixation | Show a centered fixation cross before the first object in the sequence. |
| Encoding Item | Show an object card and collect indoor/outdoor judgment with `F` / `J`. |
| Inter-Item Delay | Show a blank interval, then a left/right ear tone, then a blank remainder. |
| Distractor Task | Present arrow trials and collect left/right arrow-key responses. |
| Temporal-Order Probe | Show two studied objects side by side and ask which appeared earlier. |
| Temporal-Distance Probe | Show the same pair and collect a 1-4 subjective distance rating. |
| Source Probe | Show one studied object and ask which ear carried the tone for that item. |
| Sequence Summary | Show block-level accuracy and continue to the next sequence. |

### Controller Logic

| Feature | Description |
|---|---|
| Condition Scheduling | `BlockUnit.generate_conditions(...)` expands the practice and test sequence labels into ordered blocks. |
| Determinism | `build_sequence_plan(...)` uses the overall seed, block index, and condition label to generate object order, tone assignment, distractor arrows, and probe pairs. |
| Probe Selection | Temporal-order and source probes are sampled from the studied list with lag and context constraints. |
| Trial Context | Every participant-visible phase in `src/run_trial.py` calls `set_trial_context(...)` before display or response capture. |
| Simulation | The scripted and sampler responders exercise the encoding, distractor, order, distance, and source response paths. |

## 3. Configuration Summary

| Setting | Value |
|---|---|
| Subject Info | `subject_id` collected as a 3-digit integer in human mode. |
| Window | `1280 x 720`, white background, `pix` units, fullscreen off. |
| Stimuli | Config-defined instructions, fixation, object cards, probe text, and generated left/right tone assets. |
| Timing | Encoding item `2.5 s`, inter-item interval `3.0 s`, tone offset `1.5 s`, tone duration `1.0 s`, distractor interval `45.0 s`. |
| Triggers | Experiment, block, encoding, tone, distractor, probe, summary, and goodbye triggers are mapped in `config/*.yaml`. |
| Adaptive Controller | None. Sequence order and probe selection are deterministic rather than adaptive. |

### a. Subject Info

`subject_id` is collected as a 3-digit integer in human mode.

### b. Window Settings

`1280 x 720`, white background, `pix` units, fullscreen off.

### c. Stimuli

Config-defined instruction text, fixation, object cards, probe prompts, and generated sine-tone assets in `assets/tones/`.

### d. Timing

Encoding item `2.5 s`, inter-item interval `3.0 s`, tone offset `1.5 s`, tone duration `1.0 s`, distractor interval `45.0 s`, and probe windows of `3.5 s`.

### e. Triggers

Experiment, block, encoding, tone, distractor, probe, summary, and goodbye triggers are defined in the task configs.

## 4. Methods (for academic publication)

Participants study sequences of everyday objects and make indoor/outdoor judgments at encoding. A left- or right-ear tone marks each item during the inter-item interval, creating a contextual cue that can later be queried in source memory. After a short arrow distractor, participants judge temporal order for studied pairs, rate how far apart those items felt in the sequence, and report the ear associated with each cue item.

The implementation is designed for reproducibility and auditability. Trial order, tone assignment, probe sampling, and response scoring are deterministic from the task seed, while all participant-facing wording remains config-driven for localization portability and review.
