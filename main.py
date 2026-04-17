from contextlib import nullcontext
from functools import partial
from pathlib import Path
from statistics import fmean

import pandas as pd
from psychopy import core

from psyflow import (
    BlockUnit,
    StimBank,
    StimUnit,
    SubInfo,
    TaskRunOptions,
    TaskSettings,
    context_from_config,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
    set_trial_context,
)

from src.run_trial import run_trial
from src.utils import DEFAULT_CONTINUE_KEY, format_pct

MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _show_text_screen(
    stim_bank: StimBank,
    win,
    kb,
    runtime,
    stim_name: str,
    *,
    phase: str,
    trial_id: str,
    block_id: str,
    condition_id: str,
    valid_keys: list[str],
    task_factors: dict | None = None,
    **fmt_kwargs,
) -> None:
    unit = StimUnit(stim_name, win, kb, runtime=runtime)
    unit.add_stim(stim_bank.get_and_format(stim_name, **fmt_kwargs))
    set_trial_context(
        unit,
        trial_id=trial_id,
        phase=phase,
        deadline_s=None,
        valid_keys=list(valid_keys),
        block_id=block_id,
        condition_id=condition_id,
        task_factors=task_factors or {},
        stim_id=stim_name,
    )
    unit.wait_and_continue(keys=list(valid_keys))


def _mean_numeric(records: list[dict], key: str) -> float | None:
    values = [float(rec[key]) for rec in records if isinstance(rec.get(key), (int, float))]
    if not values:
        return None
    return fmean(values)


def _mean_bool(records: list[dict], key: str) -> float | None:
    values = [1.0 if bool(rec.get(key, False)) else 0.0 for rec in records]
    if not values:
        return None
    return fmean(values)


def _count_timeouts(records: list[dict]) -> int:
    return sum(1 for rec in records if bool(rec.get("timed_out", False)))


def _flatten_nested(all_data: list[dict], key: str) -> list[dict]:
    nested: list[dict] = []
    for block in all_data:
        nested.extend(_as_list(block.get(key)))
    return nested


def run(options: TaskRunOptions):
    """Run task in human/qa/sim mode with one auditable runtime flow."""
    task_root = Path(__file__).resolve().parent
    cfg = load_config(str(options.config_path))

    output_dir: Path | None = None
    runtime_scope = nullcontext()
    runtime_ctx = None
    if options.mode in ("qa", "sim"):
        runtime_ctx = context_from_config(task_dir=task_root, config=cfg, mode=options.mode)
        output_dir = runtime_ctx.output_dir
        runtime_scope = runtime_context(runtime_ctx)

    with runtime_scope:
        if options.mode == "qa":
            subject_data = {"subject_id": "qa"}
        elif options.mode == "sim":
            participant_id = "sim"
            if runtime_ctx is not None and runtime_ctx.session is not None:
                participant_id = str(runtime_ctx.session.participant_id or "sim")
            subject_data = {"subject_id": participant_id}
        else:
            subform = SubInfo(cfg["subform_config"])
            subject_data = subform.collect()

        settings = TaskSettings.from_dict(cfg["task_config"])
        if options.mode in ("qa", "sim") and output_dir is not None:
            settings.save_path = str(output_dir)
        settings.add_subinfo(subject_data)

        if options.mode == "qa" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "qa_trace.csv")
            settings.log_file = str(output_dir / "qa_psychopy.log")
            settings.json_file = str(output_dir / "qa_settings.json")
        elif options.mode == "sim" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "sim_trace.csv")
            settings.log_file = str(output_dir / "sim_psychopy.log")
            settings.json_file = str(output_dir / "sim_settings.json")

        settings.triggers = cfg["trigger_config"]
        trigger_runtime = initialize_triggers(mock=True) if options.mode in ("qa", "sim") else initialize_triggers(cfg)

        win, kb = initialize_exp(settings)

        stim_bank = StimBank(win, cfg["stim_config"])
        stim_bank = stim_bank.preload_all()

        settings.save_to_json()

        task_start_time = core.getAbsTime()

        trigger_runtime.send(settings.triggers.get("exp_onset"))

        continue_key = str(getattr(settings, "continue_key", DEFAULT_CONTINUE_KEY)).strip().lower() or DEFAULT_CONTINUE_KEY

        _show_text_screen(
            stim_bank,
            win,
            kb,
            trigger_runtime,
            "instruction_text",
            phase="instruction_text",
            trial_id="instruction",
            block_id="instruction",
            condition_id="instruction",
            valid_keys=[continue_key],
            task_factors={"stage": "instruction_text"},
        )

        all_data: list[dict] = []
        conditions = list(getattr(settings, "conditions", []))

        for block_i, condition_label in enumerate(conditions):
            block_seed = int(getattr(settings, "overall_seed", 54054)) + (block_i * 1009)
            block = (
                BlockUnit(
                    block_id=f"block_{block_i}",
                    block_idx=block_i,
                    settings=settings,
                    window=win,
                    keyboard=kb,
                )
                .generate_conditions(
                    n_trials=1,
                    condition_labels=[condition_label],
                    order="sequential",
                    seed=block_seed,
                )
                .on_start(lambda b: trigger_runtime.send(settings.triggers.get("block_onset")))
                .on_end(lambda b: trigger_runtime.send(settings.triggers.get("block_end")))
                .run_trial(
                    partial(
                        run_trial,
                        stim_bank=stim_bank,
                        trigger_runtime=trigger_runtime,
                        block_id=f"block_{block_i}",
                        block_idx=block_i,
                    )
                )
                .to_dict(all_data)
            )
            _ = block

        encoding_records = _flatten_nested(all_data, "encoding_records")
        distractor_records = _flatten_nested(all_data, "distractor_records")
        order_records = _flatten_nested(all_data, "order_records")
        distance_records = _flatten_nested(all_data, "distance_records")
        source_records = _flatten_nested(all_data, "source_records")

        all_response_records = encoding_records + distractor_records + order_records + distance_records + source_records

        encoding_accuracy = _mean_bool(encoding_records, "response_correct")
        order_accuracy = _mean_bool(order_records, "response_correct")
        source_accuracy = _mean_bool(source_records, "response_correct")
        total_timeouts = _count_timeouts(all_response_records)
        total_elapsed_min = (core.getAbsTime() - task_start_time) / 60.0

        _show_text_screen(
            stim_bank,
            win,
            kb,
            trigger_runtime,
            "good_bye_text",
            phase="good_bye",
            trial_id="good_bye",
            block_id="good_bye",
            condition_id="good_bye",
            valid_keys=[continue_key],
            task_factors={
                "stage": "good_bye",
                "total_sequences": len(all_data),
                "encoding_accuracy": encoding_accuracy,
                "order_accuracy": order_accuracy,
                "source_accuracy": source_accuracy,
                "total_timeouts": total_timeouts,
                "total_elapsed_min": total_elapsed_min,
            },
            total_sequences=len(all_data),
            encoding_accuracy=format_pct(encoding_accuracy),
            order_accuracy=format_pct(order_accuracy),
            source_accuracy=format_pct(source_accuracy),
            total_timeouts=total_timeouts,
            total_elapsed_min=f"{total_elapsed_min:.2f} min",
        )

        trigger_runtime.send(settings.triggers.get("exp_end"))

        pd.DataFrame(all_data).to_csv(settings.res_file, index=False)

        trigger_runtime.close()
        core.quit()


def main() -> None:
    task_root = Path(__file__).resolve().parent
    options = parse_task_run_options(
        task_root=task_root,
        description="Run task in human/qa/sim mode.",
        default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
        modes=MODES,
    )
    run(options)


if __name__ == "__main__":
    main()
