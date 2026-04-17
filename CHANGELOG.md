# CHANGELOG

## [v0.1.0-dev] - 2026-04-17

### Added

- Built a delayed recall task with object encoding, alternating ear tones, an arrow distractor, temporal-order probes, temporal-distance ratings, and source-memory probes.
- Added deterministic sequence planning, seed-stable probe sampling, and a task-specific sampler responder for QA and simulation.
- Added config-defined participant text, generated tone assets, and reference artifacts for the evidence bundle.

### Changed

- Replaced the initial scaffold with delayed-recall task logic aligned to the selected literature and the local task-build workflow.
- Updated the configs to support practice and scored sequence blocks, response mappings, and short QA/sim profiles.

### Fixed

- Normalized the reference bundle so `task_id` resolves to `T000054` and the curated author metadata is encoding-clean.
