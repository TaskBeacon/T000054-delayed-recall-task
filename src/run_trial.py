from __future__ import annotations

from typing import Any

from psychopy import core
from psyflow import StimUnit, next_trial_id, set_trial_context

from src.utils import (
    DEFAULT_CONTINUE_KEY,
    DEFAULT_DISTANCE_KEYS,
    DEFAULT_DISTRACTOR_KEYS,
    DEFAULT_DISTRACTOR_TRIAL_DURATION_S,
    DEFAULT_DISTANCE_RESPONSE_WINDOW_S,
    DEFAULT_FIXATION_DURATION_S,
    DEFAULT_INTER_ITEM_INTERVAL_S,
    DEFAULT_ITEM_DURATION_S,
    DEFAULT_ORDER_RESPONSE_WINDOW_S,
    DEFAULT_SOURCE_RESPONSE_WINDOW_S,
    DEFAULT_TONE_DURATION_S,
    DEFAULT_TONE_ONSET_OFFSET_S,
    build_sequence_plan,
    distance_bucket_label_text,
    format_ms,
    format_pct,
)


def _get_setting(settings: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(settings, name):
            value = getattr(settings, name)
            if value is not None:
                return value
    return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _make_unit(
    *,
    win,
    kb,
    runtime,
    unit_label: str,
    stims: list[Any],
    trial_id: int,
    phase: str,
    block_id: str,
    condition_id: str,
    valid_keys: list[str],
    task_factors: dict[str, Any],
    stim_id: str,
) -> StimUnit:
    unit = StimUnit(unit_label, win, kb, runtime=runtime)
    for stim in stims:
        if stim is not None:
            unit.add_stim(stim)
    set_trial_context(
        unit,
        trial_id=trial_id,
        phase=phase,
        deadline_s=None,
        valid_keys=list(valid_keys),
        block_id=block_id,
        condition_id=condition_id,
        task_factors=task_factors,
        stim_id=stim_id,
    )
    return unit


def _capture_response_snapshot(unit: StimUnit) -> dict[str, Any]:
    response = unit.get_state("response", None)
    response_key = str(response).strip().lower() if response is not None else ""
    response_rt = unit.get_state("rt", None)
    snapshot = {
        "responded": bool(response_key),
        "response_key": response_key,
        "response_rt": float(response_rt) if isinstance(response_rt, (int, float)) else None,
        "response_correct": bool(unit.get_state("hit", False)),
        "timed_out": not bool(response_key),
    }
    response_time_global = unit.get_state("response_time_global", None)
    if isinstance(response_time_global, (int, float)):
        snapshot["response_time_global"] = float(response_time_global)
    return snapshot


def _mean_numeric(records: list[dict[str, Any]], key: str) -> float | None:
    values = [float(rec[key]) for rec in records if isinstance(rec.get(key), (int, float))]
    if not values:
        return None
    return sum(values) / len(values)


def _mean_bool(records: list[dict[str, Any]], key: str) -> float | None:
    values = [1.0 if bool(rec.get(key, False)) else 0.0 for rec in records]
    if not values:
        return None
    return sum(values) / len(values)


def _count_timeouts(records: list[dict[str, Any]]) -> int:
    return sum(1 for rec in records if bool(rec.get("timed_out", False)))


def _response_trigger_map(settings: Any, keys: list[str]) -> dict[str, Any]:
    trigger_map = getattr(settings, "triggers", {}) or {}
    return {str(key): trigger_map.get(f"response_{key}") for key in keys}


def _tone_stim(stim_bank, tone_asset_id: str):
    if hasattr(stim_bank, "has") and stim_bank.has(tone_asset_id):
        return stim_bank.get(tone_asset_id)
    return stim_bank.get(tone_asset_id)


def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    block_id=None,
    block_idx=None,
):
    """Run one delayed-recall sequence trial."""
    trial_id = int(next_trial_id())
    block_id_val = str(block_id) if block_id is not None else "block_0"
    block_idx_val = int(block_idx) if block_idx is not None else 0
    overall_seed = int(getattr(settings, "overall_seed", 54054))

    plan = build_sequence_plan(
        settings=settings,
        condition=condition,
        block_idx=block_idx_val,
        trial_index=0,
        overall_seed=overall_seed,
    )

    fixation_duration_s = _coerce_float(
        _get_setting(settings, "fixation_duration_s", "fixation_duration", default=DEFAULT_FIXATION_DURATION_S),
        DEFAULT_FIXATION_DURATION_S,
    )
    item_duration_s = _coerce_float(
        _get_setting(settings, "item_duration_s", default=DEFAULT_ITEM_DURATION_S),
        DEFAULT_ITEM_DURATION_S,
    )
    inter_item_interval_s = _coerce_float(
        _get_setting(settings, "inter_item_interval_s", default=DEFAULT_INTER_ITEM_INTERVAL_S),
        DEFAULT_INTER_ITEM_INTERVAL_S,
    )
    tone_onset_offset_s = _coerce_float(
        _get_setting(settings, "context_tone_offset_s", default=DEFAULT_TONE_ONSET_OFFSET_S),
        DEFAULT_TONE_ONSET_OFFSET_S,
    )
    tone_duration_s = _coerce_float(
        _get_setting(settings, "context_tone_duration_s", default=DEFAULT_TONE_DURATION_S),
        DEFAULT_TONE_DURATION_S,
    )
    distractor_duration_s = _coerce_float(
        _get_setting(settings, "distractor_duration_s", default=float(DEFAULT_DISTRACTOR_TRIAL_DURATION_S) * 30.0),
        float(DEFAULT_DISTRACTOR_TRIAL_DURATION_S) * 30.0,
    )
    distractor_trial_duration_s = _coerce_float(
        _get_setting(settings, "distractor_trial_duration_s", default=DEFAULT_DISTRACTOR_TRIAL_DURATION_S),
        DEFAULT_DISTRACTOR_TRIAL_DURATION_S,
    )
    order_response_window_s = _coerce_float(
        _get_setting(settings, "order_response_window_s", default=DEFAULT_ORDER_RESPONSE_WINDOW_S),
        DEFAULT_ORDER_RESPONSE_WINDOW_S,
    )
    distance_response_window_s = _coerce_float(
        _get_setting(settings, "distance_response_window_s", default=DEFAULT_DISTANCE_RESPONSE_WINDOW_S),
        DEFAULT_DISTANCE_RESPONSE_WINDOW_S,
    )
    source_response_window_s = _coerce_float(
        _get_setting(settings, "source_response_window_s", default=DEFAULT_SOURCE_RESPONSE_WINDOW_S),
        DEFAULT_SOURCE_RESPONSE_WINDOW_S,
    )

    encoding_keys = [str(key).strip().lower() for key in list(getattr(settings, "encoding_keys", ["f", "j"]))]
    if not encoding_keys:
        encoding_keys = ["f", "j"]
    distractor_keys = [str(key).strip().lower() for key in list(getattr(settings, "distractor_keys", DEFAULT_DISTRACTOR_KEYS))]
    if not distractor_keys:
        distractor_keys = list(DEFAULT_DISTRACTOR_KEYS)
    distance_keys = [str(key).strip() for key in list(getattr(settings, "distance_keys", DEFAULT_DISTANCE_KEYS))]
    if not distance_keys:
        distance_keys = list(DEFAULT_DISTANCE_KEYS)
    source_keys = [str(key).strip().lower() for key in list(getattr(settings, "source_keys", encoding_keys))]
    if not source_keys:
        source_keys = list(encoding_keys)

    interval_remainder_s = inter_item_interval_s - tone_onset_offset_s - tone_duration_s
    if interval_remainder_s < -1e-6:
        raise ValueError(
            "inter_item_interval_s must be at least context_tone_offset_s + context_tone_duration_s."
        )
    post_tone_duration_s = max(0.0, interval_remainder_s)

    trial_start_time = core.getAbsTime()
    trial_data: dict[str, Any] = {
        "trial_id": trial_id,
        "block_id": block_id_val,
        "block_idx": block_idx_val,
        "trial_index_in_block": 0,
        "trial_phase": "sequence_block",
        "trial_kind": str(plan["trial_kind"]),
        "condition_id": str(plan["condition_id"]),
        "condition_token": str(plan["condition_id"]),
        "sequence_role": str(plan["sequence_role"]),
        "sequence_index": int(plan["sequence_index"]),
        "is_practice": bool(plan["is_practice"]),
        "sequence_count": int(plan["sequence_count"]),
        "event_count": int(plan["event_count"]),
        "item_duration_s": item_duration_s,
        "inter_item_interval_s": inter_item_interval_s,
        "tone_onset_offset_s": tone_onset_offset_s,
        "tone_duration_s": tone_duration_s,
        "distractor_duration_s": distractor_duration_s,
        "distractor_trial_duration_s": distractor_trial_duration_s,
        "order_response_window_s": order_response_window_s,
        "distance_response_window_s": distance_response_window_s,
        "source_response_window_s": source_response_window_s,
        "encoding_records": [],
        "distractor_records": [],
        "order_records": [],
        "distance_records": [],
        "source_records": [],
        "summary_label": str(plan["summary_label"]),
        "next_step_label": str(plan["next_step_label"]),
    }

    fixation_unit = _make_unit(
        win=win,
        kb=kb,
        runtime=trigger_runtime,
        unit_label="sequence_fixation",
        stims=[stim_bank.get("fixation")],
        trial_id=trial_id,
        phase="sequence_fixation",
        block_id=block_id_val,
        condition_id=plan["condition_id"],
        valid_keys=[],
        task_factors={
            "stage": "sequence_fixation",
            "sequence_role": plan["sequence_role"],
            "sequence_index": plan["sequence_index"],
            "is_practice": plan["is_practice"],
        },
        stim_id="fixation",
    )
    set_trial_context(
        fixation_unit,
        trial_id=trial_id,
        phase="sequence_fixation",
        deadline_s=settings.fixation_duration_s,
        valid_keys=[],
        block_id=block_id_val,
        condition_id=plan["condition_id"],
        task_factors={
            "stage": "sequence_fixation",
            "sequence_role": plan["sequence_role"],
            "sequence_index": plan["sequence_index"],
            "is_practice": plan["is_practice"],
        },
        stim_id="fixation",
    )
    fixation_record: dict[str, Any] = {}
    fixation_unit.show(
        duration=fixation_duration_s,
        onset_trigger=settings.triggers.get("sequence_fixation_onset"),
    ).to_dict(fixation_record)
    trial_data["fixation_record"] = fixation_record

    response_trigger_encoding = _response_trigger_map(settings, encoding_keys)
    response_trigger_distractor = _response_trigger_map(settings, distractor_keys)
    response_trigger_distance = _response_trigger_map(settings, distance_keys)
    response_trigger_source = _response_trigger_map(settings, source_keys)

    encoding_records: list[dict[str, Any]] = []
    distractor_records: list[dict[str, Any]] = []
    order_records: list[dict[str, Any]] = []
    distance_records: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []

    for item in list(plan["encoding_items"]):
        item_label = str(item["object_label"])
        encoding_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"encoding_item_{item['item_index']}",
            stims=[
                stim_bank.get("object_card_frame"),
                stim_bank.get_and_format("object_card_text", object_label=item_label),
                stim_bank.get("encoding_prompt_text"),
            ],
            trial_id=trial_id,
            phase="encoding_item",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=encoding_keys,
            task_factors={
                "stage": "encoding_item",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
                "within_event_index": item["within_event_index"],
                "object_label": item_label,
                "object_context": item["object_context"],
                "tone_ear": item["tone_ear"],
                "tone_frequency_hz": item["tone_frequency_hz"],
                "tone_asset_id": item["tone_asset_id"],
                "correct_key": item["correct_key"],
            },
            stim_id="object_card",
        )
        set_trial_context(
            encoding_unit,
            trial_id=trial_id,
            phase="encoding_item",
            deadline_s=settings.item_duration_s,
            valid_keys=encoding_keys,
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "encoding_item",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
                "within_event_index": item["within_event_index"],
                "object_label": item_label,
                "object_context": item["object_context"],
                "tone_ear": item["tone_ear"],
                "tone_frequency_hz": item["tone_frequency_hz"],
                "tone_asset_id": item["tone_asset_id"],
                "correct_key": item["correct_key"],
            },
            stim_id="object_card",
        )
        encoding_record: dict[str, Any] = {}
        encoding_unit.capture_response(
            keys=encoding_keys,
            correct_keys=[str(item["correct_key"])],
            duration=item_duration_s,
            onset_trigger=settings.triggers.get("encoding_item_onset"),
            response_trigger=response_trigger_encoding,
            timeout_trigger=settings.triggers.get("response_timeout"),
            terminate_on_response=False,
        ).to_dict(encoding_record)
        encoding_record.update(
            {
                "stage": "encoding_item",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
                "within_event_index": item["within_event_index"],
                "object_label": item_label,
                "object_context": item["object_context"],
                "tone_ear": item["tone_ear"],
                "tone_frequency_hz": item["tone_frequency_hz"],
                "tone_asset_id": item["tone_asset_id"],
                "response_key": str(encoding_record.get("response", "") or "").strip().lower(),
                "response_correct": bool(encoding_record.get("hit", False)),
                "timed_out": bool(encoding_record.get("response") in (None, "")),
            }
        )
        encoding_records.append(encoding_record)

        pre_tone_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"encoding_isi_pre_tone_{item['item_index']}",
            stims=[stim_bank.get("blank_screen")],
            trial_id=trial_id,
            phase="encoding_isi_pre_tone",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=[],
            task_factors={
                "stage": "encoding_isi_pre_tone",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
            },
            stim_id="blank_screen",
        )
        set_trial_context(
            pre_tone_unit,
            trial_id=trial_id,
            phase="encoding_isi_pre_tone",
            deadline_s=settings.context_tone_offset_s,
            valid_keys=[],
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "encoding_isi_pre_tone",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
            },
            stim_id="blank_screen",
        )
        pre_tone_unit.show(
            duration=tone_onset_offset_s,
            onset_trigger=settings.triggers.get("encoding_isi_pre_tone_onset"),
        )

        tone_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"context_tone_{item['item_index']}",
            stims=[stim_bank.get("blank_screen"), _tone_stim(stim_bank, str(item["tone_asset_id"]))],
            trial_id=trial_id,
            phase="context_tone",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=[],
            task_factors={
                "stage": "context_tone",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
                "tone_ear": item["tone_ear"],
                "tone_frequency_hz": item["tone_frequency_hz"],
                "tone_asset_id": item["tone_asset_id"],
            },
            stim_id=str(item["tone_asset_id"]),
        )
        set_trial_context(
            tone_unit,
            trial_id=trial_id,
            phase="context_tone",
            deadline_s=settings.context_tone_duration_s,
            valid_keys=[],
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "context_tone",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "item_index": item["item_index"],
                "event_index": item["event_index"],
                "tone_ear": item["tone_ear"],
                "tone_frequency_hz": item["tone_frequency_hz"],
                "tone_asset_id": item["tone_asset_id"],
            },
            stim_id=str(item["tone_asset_id"]),
        )
        tone_unit.show(
            duration=tone_duration_s,
            onset_trigger=settings.triggers.get("context_tone_onset"),
        )

        if post_tone_duration_s > 0:
            post_tone_unit = _make_unit(
                win=win,
                kb=kb,
                runtime=trigger_runtime,
                unit_label=f"encoding_isi_post_tone_{item['item_index']}",
                stims=[stim_bank.get("blank_screen")],
                trial_id=trial_id,
                phase="encoding_isi_post_tone",
                block_id=block_id_val,
                condition_id=plan["condition_id"],
                valid_keys=[],
                task_factors={
                    "stage": "encoding_isi_post_tone",
                    "sequence_role": plan["sequence_role"],
                    "sequence_index": plan["sequence_index"],
                    "is_practice": plan["is_practice"],
                    "item_index": item["item_index"],
                    "event_index": item["event_index"],
                },
                stim_id="blank_screen",
            )
            set_trial_context(
                post_tone_unit,
                trial_id=trial_id,
                phase="encoding_isi_post_tone",
                deadline_s=settings.post_tone_duration_s,
                valid_keys=[],
                block_id=block_id_val,
                condition_id=plan["condition_id"],
                task_factors={
                    "stage": "encoding_isi_post_tone",
                    "sequence_role": plan["sequence_role"],
                    "sequence_index": plan["sequence_index"],
                    "is_practice": plan["is_practice"],
                    "item_index": item["item_index"],
                    "event_index": item["event_index"],
                },
                stim_id="blank_screen",
            )
            post_tone_unit.show(
                duration=post_tone_duration_s,
                onset_trigger=settings.triggers.get("encoding_isi_post_tone_onset"),
            )

    for arrow_item in list(plan["distractor_items"]):
        distractor_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"distractor_task_{arrow_item['trial_index']}",
            stims=[
                stim_bank.get("blank_screen"),
                stim_bank.get_and_format("distractor_arrow_text", arrow_symbol=arrow_item["arrow_symbol"]),
                stim_bank.get("distractor_prompt_text"),
            ],
            trial_id=trial_id,
            phase="distractor_task",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=distractor_keys,
            task_factors={
                "stage": "distractor_task",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "trial_index": arrow_item["trial_index"],
                "arrow_direction": arrow_item["arrow_direction"],
                "arrow_symbol": arrow_item["arrow_symbol"],
                "correct_key": arrow_item["correct_key"],
            },
            stim_id="distractor_arrow",
        )
        set_trial_context(
            distractor_unit,
            trial_id=trial_id,
            phase="distractor_task",
            deadline_s=settings.distractor_trial_duration_s,
            valid_keys=distractor_keys,
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "distractor_task",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "trial_index": arrow_item["trial_index"],
                "arrow_direction": arrow_item["arrow_direction"],
                "arrow_symbol": arrow_item["arrow_symbol"],
                "correct_key": arrow_item["correct_key"],
            },
            stim_id="distractor_arrow",
        )
        distractor_record: dict[str, Any] = {}
        distractor_unit.capture_response(
            keys=distractor_keys,
            correct_keys=[str(arrow_item["correct_key"])],
            duration=distractor_trial_duration_s,
            onset_trigger=settings.triggers.get("distractor_arrow_onset"),
            response_trigger=response_trigger_distractor,
            timeout_trigger=settings.triggers.get("response_timeout"),
            terminate_on_response=False,
        ).to_dict(distractor_record)
        distractor_record.update(
            {
                "stage": "distractor_task",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "trial_index": arrow_item["trial_index"],
                "arrow_direction": arrow_item["arrow_direction"],
                "arrow_symbol": arrow_item["arrow_symbol"],
                "correct_key": arrow_item["correct_key"],
                "response_key": str(distractor_record.get("response", "") or "").strip().lower(),
                "response_correct": bool(distractor_record.get("hit", False)),
                "timed_out": bool(distractor_record.get("response") in (None, "")),
            }
        )
        distractor_records.append(distractor_record)

    for pair_index, pair in enumerate(list(plan["memory_pairs"])):
        left_label = str(pair["left_label"])
        right_label = str(pair["right_label"])

        order_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"temporal_order_probe_{pair_index}",
            stims=[
                stim_bank.get("pair_card_frame_left"),
                stim_bank.get_and_format("pair_card_text_left", object_label=left_label),
                stim_bank.get("pair_card_frame_right"),
                stim_bank.get_and_format("pair_card_text_right", object_label=right_label),
                stim_bank.get("order_prompt_text"),
            ],
            trial_id=trial_id,
            phase="temporal_order_probe",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=encoding_keys,
            task_factors={
                "stage": "temporal_order_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "left_label": left_label,
                "right_label": right_label,
                "left_event_index": pair["left_event_index"],
                "right_event_index": pair["right_event_index"],
                "left_is_earlier": pair["left_is_earlier"],
                "earlier_side": pair["earlier_side"],
                "correct_key": pair["correct_key"],
            },
            stim_id="pair_cards",
        )
        set_trial_context(
            order_unit,
            trial_id=trial_id,
            phase="temporal_order_probe",
            deadline_s=settings.order_response_window_s,
            valid_keys=encoding_keys,
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "temporal_order_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "left_label": left_label,
                "right_label": right_label,
                "left_event_index": pair["left_event_index"],
                "right_event_index": pair["right_event_index"],
                "left_is_earlier": pair["left_is_earlier"],
                "earlier_side": pair["earlier_side"],
                "correct_key": pair["correct_key"],
            },
            stim_id="pair_cards",
        )
        order_record: dict[str, Any] = {}
        order_unit.capture_response(
            keys=encoding_keys,
            correct_keys=[str(pair["correct_key"])],
            duration=order_response_window_s,
            onset_trigger=settings.triggers.get("temporal_order_probe_onset"),
            response_trigger=response_trigger_encoding,
            timeout_trigger=settings.triggers.get("response_timeout"),
            terminate_on_response=False,
        ).to_dict(order_record)
        order_record.update(
            {
                "stage": "temporal_order_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "left_label": left_label,
                "right_label": right_label,
                "left_is_earlier": pair["left_is_earlier"],
                "earlier_side": pair["earlier_side"],
                "correct_key": pair["correct_key"],
                "response_key": str(order_record.get("response", "") or "").strip().lower(),
                "response_correct": bool(order_record.get("hit", False)),
                "timed_out": bool(order_record.get("response") in (None, "")),
            }
        )
        order_records.append(order_record)

        distance_unit = _make_unit(
            win=win,
            kb=kb,
            runtime=trigger_runtime,
            unit_label=f"temporal_distance_probe_{pair_index}",
            stims=[
                stim_bank.get("pair_card_frame_left"),
                stim_bank.get_and_format("pair_card_text_left", object_label=left_label),
                stim_bank.get("pair_card_frame_right"),
                stim_bank.get_and_format("pair_card_text_right", object_label=right_label),
                stim_bank.get("distance_prompt_text"),
                stim_bank.get("distance_option_1"),
                stim_bank.get("distance_option_2"),
                stim_bank.get("distance_option_3"),
                stim_bank.get("distance_option_4"),
            ],
            trial_id=trial_id,
            phase="temporal_distance_probe",
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            valid_keys=distance_keys,
            task_factors={
                "stage": "temporal_distance_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "distance_bucket_label": distance_bucket_label_text(pair["distance_bucket"]),
                "left_label": left_label,
                "right_label": right_label,
                "correct_key": pair["distance_bucket"],
            },
            stim_id="distance_scale",
        )
        set_trial_context(
            distance_unit,
            trial_id=trial_id,
            phase="temporal_distance_probe",
            deadline_s=settings.distance_response_window_s,
            valid_keys=distance_keys,
            block_id=block_id_val,
            condition_id=plan["condition_id"],
            task_factors={
                "stage": "temporal_distance_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "distance_bucket_label": distance_bucket_label_text(pair["distance_bucket"]),
                "left_label": left_label,
                "right_label": right_label,
                "correct_key": pair["distance_bucket"],
            },
            stim_id="distance_scale",
        )
        distance_record: dict[str, Any] = {}
        distance_unit.capture_response(
            keys=distance_keys,
            correct_keys=[str(pair["distance_bucket"])],
            duration=distance_response_window_s,
            onset_trigger=settings.triggers.get("temporal_distance_probe_onset"),
            response_trigger=response_trigger_distance,
            timeout_trigger=settings.triggers.get("response_timeout"),
            terminate_on_response=False,
        ).to_dict(distance_record)
        distance_record.update(
            {
                "stage": "temporal_distance_probe",
                "sequence_role": plan["sequence_role"],
                "sequence_index": plan["sequence_index"],
                "is_practice": plan["is_practice"],
                "pair_index": pair_index,
                "pair_key": pair["pair_key"],
                "pair_type": pair["pair_type"],
                "lag": pair["lag"],
                "distance_bucket": pair["distance_bucket"],
                "distance_bucket_label": distance_bucket_label_text(pair["distance_bucket"]),
                "left_label": left_label,
                "right_label": right_label,
                "response_key": str(distance_record.get("response", "") or "").strip(),
                "distance_bucket_match": bool(distance_record.get("hit", False)),
                "timed_out": bool(distance_record.get("response") in (None, "")),
            }
        )
        distance_records.append(distance_record)

        if pair_index < len(plan["source_pairs"]):
            source_item = plan["source_pairs"][pair_index]
            source_label = str(source_item["object_label"])

            source_unit = _make_unit(
                win=win,
                kb=kb,
                runtime=trigger_runtime,
                unit_label=f"source_memory_probe_{pair_index}",
                stims=[
                    stim_bank.get("source_card_frame"),
                    stim_bank.get_and_format("source_card_text", object_label=source_label),
                    stim_bank.get("source_prompt_text"),
                    stim_bank.get("source_left_label"),
                    stim_bank.get("source_right_label"),
                ],
                trial_id=trial_id,
                phase="source_memory_probe",
                block_id=block_id_val,
                condition_id=plan["condition_id"],
                valid_keys=source_keys,
                task_factors={
                    "stage": "source_memory_probe",
                    "sequence_role": plan["sequence_role"],
                    "sequence_index": plan["sequence_index"],
                    "is_practice": plan["is_practice"],
                    "pair_index": pair_index,
                    "item_index": source_item["item_index"],
                    "object_label": source_label,
                    "tone_ear": source_item["tone_ear"],
                    "correct_key": source_item["correct_key"],
                },
                stim_id="source_probe",
            )
            set_trial_context(
                source_unit,
                trial_id=trial_id,
                phase="source_memory_probe",
                deadline_s=settings.source_response_window_s,
                valid_keys=source_keys,
                block_id=block_id_val,
                condition_id=plan["condition_id"],
                task_factors={
                    "stage": "source_memory_probe",
                    "sequence_role": plan["sequence_role"],
                    "sequence_index": plan["sequence_index"],
                    "is_practice": plan["is_practice"],
                    "pair_index": pair_index,
                    "item_index": source_item["item_index"],
                    "object_label": source_label,
                    "tone_ear": source_item["tone_ear"],
                    "correct_key": source_item["correct_key"],
                },
                stim_id="source_probe",
            )
            source_record: dict[str, Any] = {}
            source_unit.capture_response(
                keys=source_keys,
                correct_keys=[str(source_item["correct_key"])],
                duration=source_response_window_s,
                onset_trigger=settings.triggers.get("source_memory_probe_onset"),
                response_trigger=response_trigger_source,
                timeout_trigger=settings.triggers.get("response_timeout"),
                terminate_on_response=False,
            ).to_dict(source_record)
            source_record.update(
                {
                    "stage": "source_memory_probe",
                    "sequence_role": plan["sequence_role"],
                    "sequence_index": plan["sequence_index"],
                    "is_practice": plan["is_practice"],
                    "pair_index": pair_index,
                    "item_index": source_item["item_index"],
                    "object_label": source_label,
                    "tone_ear": source_item["tone_ear"],
                    "correct_key": source_item["correct_key"],
                    "response_key": str(source_record.get("response", "") or "").strip().lower(),
                    "response_correct": bool(source_record.get("hit", False)),
                    "timed_out": bool(source_record.get("response") in (None, "")),
                }
            )
            source_records.append(source_record)

    all_response_records = encoding_records + distractor_records + order_records + distance_records + source_records
    encoding_accuracy = _mean_bool(encoding_records, "response_correct")
    distractor_accuracy = _mean_bool(distractor_records, "response_correct")
    order_accuracy = _mean_bool(order_records, "response_correct")
    same_order_accuracy = _mean_bool([rec for rec in order_records if rec.get("pair_type") == "same_context"], "response_correct")
    boundary_order_accuracy = _mean_bool(
        [rec for rec in order_records if rec.get("pair_type") == "boundary_spanning"],
        "response_correct",
    )
    distance_bucket_match_rate = _mean_bool(distance_records, "distance_bucket_match")
    source_accuracy = _mean_bool(source_records, "response_correct")
    overall_mean_rt_s = _mean_numeric(all_response_records, "response_rt")
    total_timeouts = _count_timeouts(all_response_records)
    sequence_duration_s = core.getAbsTime() - trial_start_time

    trial_data.update(
        {
            "encoding_records": encoding_records,
            "distractor_records": distractor_records,
            "order_records": order_records,
            "distance_records": distance_records,
            "source_records": source_records,
            "encoding_accuracy": encoding_accuracy,
            "distractor_accuracy": distractor_accuracy,
            "order_accuracy": order_accuracy,
            "same_order_accuracy": same_order_accuracy,
            "boundary_order_accuracy": boundary_order_accuracy,
            "distance_bucket_match_rate": distance_bucket_match_rate,
            "source_accuracy": source_accuracy,
            "mean_rt_s": overall_mean_rt_s,
            "mean_rt_ms": overall_mean_rt_s * 1000.0 if isinstance(overall_mean_rt_s, (int, float)) else None,
            "total_timeouts": total_timeouts,
            "sequence_duration_s": sequence_duration_s,
        }
    )

    summary_unit = _make_unit(
        win=win,
        kb=kb,
        runtime=trigger_runtime,
        unit_label="sequence_summary",
        stims=[
            stim_bank.get_and_format(
                "sequence_summary_text",
                sequence_label=str(plan["summary_label"]),
                encoding_accuracy=format_pct(encoding_accuracy),
                same_order_accuracy=format_pct(same_order_accuracy),
                boundary_order_accuracy=format_pct(boundary_order_accuracy),
                source_accuracy=format_pct(source_accuracy),
                mean_rt_ms=format_ms(overall_mean_rt_s * 1000.0 if isinstance(overall_mean_rt_s, (int, float)) else None),
                next_step_label=str(plan["next_step_label"]),
            )
        ],
        trial_id=trial_id,
        phase="sequence_summary",
        block_id=block_id_val,
        condition_id=plan["condition_id"],
        valid_keys=[str(getattr(settings, "continue_key", DEFAULT_CONTINUE_KEY)).strip().lower() or DEFAULT_CONTINUE_KEY],
        task_factors={
            "stage": "sequence_summary",
            "sequence_role": plan["sequence_role"],
            "sequence_index": plan["sequence_index"],
            "is_practice": plan["is_practice"],
            "encoding_accuracy": encoding_accuracy,
            "distractor_accuracy": distractor_accuracy,
            "order_accuracy": order_accuracy,
            "same_order_accuracy": same_order_accuracy,
            "boundary_order_accuracy": boundary_order_accuracy,
            "source_accuracy": source_accuracy,
            "total_timeouts": total_timeouts,
            "mean_rt_s": overall_mean_rt_s,
            "summary_label": plan["summary_label"],
            "next_step_label": plan["next_step_label"],
        },
        stim_id="sequence_summary_text",
    )
    set_trial_context(
        summary_unit,
        trial_id=trial_id,
        phase="sequence_summary",
        deadline_s=None,
        valid_keys=[str(getattr(settings, "continue_key", DEFAULT_CONTINUE_KEY)).strip().lower() or DEFAULT_CONTINUE_KEY],
        block_id=block_id_val,
        condition_id=plan["condition_id"],
        task_factors={
            "stage": "sequence_summary",
            "sequence_role": plan["sequence_role"],
            "sequence_index": plan["sequence_index"],
            "is_practice": plan["is_practice"],
            "encoding_accuracy": encoding_accuracy,
            "distractor_accuracy": distractor_accuracy,
            "order_accuracy": order_accuracy,
            "same_order_accuracy": same_order_accuracy,
            "boundary_order_accuracy": boundary_order_accuracy,
            "source_accuracy": source_accuracy,
            "total_timeouts": total_timeouts,
            "mean_rt_s": overall_mean_rt_s,
            "summary_label": plan["summary_label"],
            "next_step_label": plan["next_step_label"],
        },
        stim_id="sequence_summary_text",
    )
    summary_record: dict[str, Any] = {}
    summary_unit.wait_and_continue(
        keys=[str(getattr(settings, "continue_key", DEFAULT_CONTINUE_KEY)).strip().lower() or DEFAULT_CONTINUE_KEY]
    ).to_dict(summary_record)
    trial_data["summary_record"] = summary_record

    trial_data["trial_phase"] = "sequence_summary"
    trial_data["response_key"] = str(summary_record.get("response", "") or "").strip().lower()
    trial_data["response_rt"] = summary_record.get("rt", None)
    trial_data["response_correct"] = bool(summary_record.get("hit", False))
    trial_data["responded"] = bool(trial_data["response_key"])
    trial_data["timed_out"] = bool(summary_record.get("response") in (None, ""))

    return trial_data
