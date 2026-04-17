from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import defaultdict
from statistics import fmean
from typing import Any, Iterable

DEFAULT_CONTINUE_KEY = "space"
DEFAULT_ENCODING_KEYS = ("f", "j")
DEFAULT_DISTRACTOR_KEYS = ("left", "right")
DEFAULT_DISTANCE_KEYS = ("1", "2", "3", "4")
DEFAULT_FIXATION_DURATION_S = 0.5
DEFAULT_ITEM_DURATION_S = 2.5
DEFAULT_INTER_ITEM_INTERVAL_S = 3.0
DEFAULT_TONE_ONSET_OFFSET_S = 1.5
DEFAULT_TONE_DURATION_S = 1.0
DEFAULT_DISTRACTOR_DURATION_S = 45.0
DEFAULT_DISTRACTOR_TRIAL_DURATION_S = 1.5
DEFAULT_ORDER_RESPONSE_WINDOW_S = 3.5
DEFAULT_DISTANCE_RESPONSE_WINDOW_S = 3.5
DEFAULT_SOURCE_RESPONSE_WINDOW_S = 3.5
DEFAULT_SEQUENCE_COUNT = 32
DEFAULT_EVENT_LENGTH_ITEMS = 8
DEFAULT_SAME_CONTEXT_PROBES = 4
DEFAULT_BOUNDARY_PROBES = 4
DEFAULT_SOURCE_PROBES = 8
DEFAULT_TONE_FREQUENCIES_HZ = (392.0, 440.0, 494.0, 523.25, 587.33, 659.25)
DEFAULT_TONE_EARS = ("left", "right")

INDOOR_OBJECTS = (
    "chair",
    "lamp",
    "mug",
    "pillow",
    "couch",
    "table",
    "clock",
    "keyboard",
    "notebook",
    "toaster",
    "mirror",
    "plate",
    "fork",
    "spoon",
    "cup",
    "blanket",
    "drawer",
    "cabinet",
    "vase",
    "radio",
    "camera",
    "printer",
    "towel",
    "fan",
)

OUTDOOR_OBJECTS = (
    "tree",
    "bicycle",
    "shovel",
    "mailbox",
    "bench",
    "tent",
    "tractor",
    "kite",
    "ladder",
    "hose",
    "wheelbarrow",
    "wagon",
    "umbrella",
    "fence",
    "lawnmower",
    "swing",
    "canoe",
    "backpack",
    "helmet",
    "skateboard",
    "rake",
    "truck",
    "scooter",
    "signpost",
)


def _seed_blob(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        return repr(value)


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(_seed_blob(part).encode("utf-8"))
        digest.update(b"\0")
    return int.from_bytes(digest.digest()[:8], "big", signed=False)


def _get_setting(settings: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(settings, name):
            value = getattr(settings, name)
            if value is not None:
                return value
    return default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_token(value: Any) -> str:
    token = str(value or "").strip().lower()
    token = token.replace(" ", "_")
    token = re.sub(r"[^a-z0-9_]+", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token


def _format_label(value: str) -> str:
    return str(value).strip().replace("_", " ").title()


def format_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "n/a"


def format_ms(value: Any) -> str:
    try:
        return f"{float(value):.1f} ms"
    except Exception:
        return "n/a"


def format_s(value: Any) -> str:
    try:
        return f"{float(value):.2f} s"
    except Exception:
        return "n/a"


def parse_condition(condition: Any) -> dict[str, Any]:
    if isinstance(condition, dict):
        raw = (
            condition.get("condition")
            or condition.get("condition_id")
            or condition.get("trial_kind")
            or condition.get("label")
        )
    else:
        raw = condition

    token = _normalize_token(raw)
    if not token:
        raise ValueError("Condition token is missing.")

    if token.startswith("practice"):
        return {
            "condition_id": token,
            "sequence_role": "practice",
            "sequence_index": 0,
            "is_practice": True,
        }

    match = re.search(r"(\d+)$", token)
    sequence_index = int(match.group(1)) if match else 1
    return {
        "condition_id": token,
        "sequence_role": "test",
        "sequence_index": sequence_index,
        "is_practice": False,
    }


def _lag_bucket(lag: int) -> str:
    lag = max(1, int(lag))
    if lag <= 2:
        return "1"
    if lag <= 4:
        return "2"
    if lag <= 6:
        return "3"
    return "4"


def _pick_with_fallback(rng: random.Random, candidates: list[dict[str, Any]], used_keys: set[str]) -> dict[str, Any] | None:
    available = [item for item in candidates if item["pair_key"] not in used_keys]
    if not available:
        return None
    return available[rng.randrange(len(available))]


def _build_probe_pairs(
    *,
    items: list[dict[str, Any]],
    same_count: int,
    boundary_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    same_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    boundary_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for start_idx, left_item in enumerate(items):
        for right_idx in range(start_idx + 1, len(items)):
            right_item = items[right_idx]
            lag = right_idx - start_idx
            if lag <= 0:
                continue
            pair_key = f"{start_idx}-{right_idx}"
            pair = {
                "pair_key": pair_key,
                "lag": lag,
                "distance_bucket": _lag_bucket(lag),
                "left_item_index": start_idx,
                "right_item_index": right_idx,
                "left_label": left_item["object_label"],
                "right_label": right_item["object_label"],
                "left_event_index": left_item["event_index"],
                "right_event_index": right_item["event_index"],
            }
            same_event = left_item["event_index"] == right_item["event_index"]
            boundary_span = right_item["event_index"] == left_item["event_index"] + 1
            if same_event:
                same_groups[lag].append(pair)
            elif boundary_span:
                boundary_groups[lag].append(pair)

    desired_lags = list(range(1, min(5, max(2, len(items) // 2))))
    if not desired_lags:
        desired_lags = [1]

    selected: list[dict[str, Any]] = []
    used_keys: set[str] = set()

    def _draw(group_map: dict[int, list[dict[str, Any]]], count: int, pair_type: str) -> None:
        if count <= 0:
            return
        lag_cycle = desired_lags[:]
        if not lag_cycle:
            lag_cycle = [1]
        for idx in range(count):
            lag = lag_cycle[idx % len(lag_cycle)]
            candidates = group_map.get(lag, [])
            chosen: dict[str, Any] | None = None
            if candidates:
                shuffled = candidates[:]
                rng.shuffle(shuffled)
                chosen = _pick_with_fallback(rng, shuffled, used_keys)
            if chosen is None:
                all_candidates: list[dict[str, Any]] = []
                for cand_list in group_map.values():
                    all_candidates.extend(cand_list)
                if all_candidates:
                    shuffled = all_candidates[:]
                    rng.shuffle(shuffled)
                    chosen = _pick_with_fallback(rng, shuffled, used_keys)
            if chosen is None:
                continue
            used_keys.add(chosen["pair_key"])
            chosen = dict(chosen)
            chosen["pair_type"] = pair_type
            earlier_on_left = rng.random() < 0.5
            if earlier_on_left:
                chosen["left_is_earlier"] = True
                chosen["correct_key"] = "f"
                chosen["earlier_side"] = "left"
            else:
                chosen["left_is_earlier"] = False
                chosen["correct_key"] = "j"
                chosen["earlier_side"] = "right"
            selected.append(chosen)

    _draw(same_groups, same_count, "same_context")
    _draw(boundary_groups, boundary_count, "boundary_spanning")

    if len(selected) < same_count + boundary_count:
        remaining = same_count + boundary_count - len(selected)
        all_candidates: list[dict[str, Any]] = []
        for cand_list in same_groups.values():
            all_candidates.extend(cand_list)
        for cand_list in boundary_groups.values():
            all_candidates.extend(cand_list)
        shuffled = all_candidates[:]
        rng.shuffle(shuffled)
        for cand in shuffled:
            if cand["pair_key"] in used_keys:
                continue
            used_keys.add(cand["pair_key"])
            cand = dict(cand)
            cand["pair_type"] = cand["pair_type"] if "pair_type" in cand else "fallback"
            if rng.random() < 0.5:
                cand["left_is_earlier"] = True
                cand["correct_key"] = "f"
                cand["earlier_side"] = "left"
            else:
                cand["left_is_earlier"] = False
                cand["correct_key"] = "j"
                cand["earlier_side"] = "right"
            selected.append(cand)
            remaining -= 1
            if remaining <= 0:
                break

    return selected[: same_count + boundary_count]


def _sample_event_items(
    *,
    rng: random.Random,
    indoor_pool: list[str],
    outdoor_pool: list[str],
    count_per_category: int,
) -> list[dict[str, Any]]:
    indoor_shuffled = indoor_pool[:]
    outdoor_shuffled = outdoor_pool[:]
    rng.shuffle(indoor_shuffled)
    rng.shuffle(outdoor_shuffled)

    indoor_items = indoor_shuffled[:count_per_category]
    outdoor_items = outdoor_shuffled[:count_per_category]

    event_items: list[dict[str, Any]] = []
    for label in indoor_items:
        event_items.append(
            {
                "object_label": _format_label(label),
                "object_context": "indoor",
                "correct_key": "f",
            }
        )
    for label in outdoor_items:
        event_items.append(
            {
                "object_label": _format_label(label),
                "object_context": "outdoor",
                "correct_key": "j",
            }
        )
    rng.shuffle(event_items)
    return event_items


def build_sequence_plan(
    *,
    settings: Any,
    condition: Any,
    block_idx: int,
    trial_index: int,
    overall_seed: int,
) -> dict[str, Any]:
    parsed = parse_condition(condition)
    condition_id = parsed["condition_id"]
    sequence_role = parsed["sequence_role"]
    sequence_index = int(parsed["sequence_index"])
    is_practice = bool(parsed["is_practice"])

    sequence_count = _coerce_int(_get_setting(settings, "sequence_trial_count", default=DEFAULT_SEQUENCE_COUNT), DEFAULT_SEQUENCE_COUNT)
    event_length = _coerce_int(_get_setting(settings, "event_length_items", default=DEFAULT_EVENT_LENGTH_ITEMS), DEFAULT_EVENT_LENGTH_ITEMS)
    if sequence_count <= 0:
        raise ValueError("sequence_trial_count must be positive.")
    if event_length <= 0:
        raise ValueError("event_length_items must be positive.")
    if sequence_count % event_length != 0:
        raise ValueError("sequence_trial_count must be divisible by event_length_items.")

    event_count = sequence_count // event_length
    count_per_category = event_length // 2
    if event_length % 2 != 0:
        raise ValueError("event_length_items must be even so indoor/outdoor counts are balanced.")

    item_duration_s = _coerce_float(_get_setting(settings, "item_duration_s", default=DEFAULT_ITEM_DURATION_S), DEFAULT_ITEM_DURATION_S)
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
        _get_setting(settings, "distractor_duration_s", default=DEFAULT_DISTRACTOR_DURATION_S),
        DEFAULT_DISTRACTOR_DURATION_S,
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

    same_probe_count = _coerce_int(
        _get_setting(settings, "same_context_probe_count", default=DEFAULT_SAME_CONTEXT_PROBES),
        DEFAULT_SAME_CONTEXT_PROBES,
    )
    boundary_probe_count = _coerce_int(
        _get_setting(settings, "boundary_probe_count", default=DEFAULT_BOUNDARY_PROBES),
        DEFAULT_BOUNDARY_PROBES,
    )
    source_probe_count = _coerce_int(
        _get_setting(settings, "source_probe_count", default=DEFAULT_SOURCE_PROBES),
        DEFAULT_SOURCE_PROBES,
    )

    tone_frequencies = list(
        _get_setting(settings, "context_tone_frequencies_hz", default=DEFAULT_TONE_FREQUENCIES_HZ) or DEFAULT_TONE_FREQUENCIES_HZ
    )
    if not tone_frequencies:
        tone_frequencies = list(DEFAULT_TONE_FREQUENCIES_HZ)

    tone_ears = list(_get_setting(settings, "tone_ear_cycle", default=DEFAULT_TONE_EARS) or DEFAULT_TONE_EARS)
    if not tone_ears:
        tone_ears = list(DEFAULT_TONE_EARS)

    indoor_pool = list(_get_setting(settings, "indoor_objects", default=INDOOR_OBJECTS) or INDOOR_OBJECTS)
    outdoor_pool = list(_get_setting(settings, "outdoor_objects", default=OUTDOOR_OBJECTS) or OUTDOOR_OBJECTS)
    if len(indoor_pool) < count_per_category:
        raise ValueError("indoor_objects pool is too small for the requested event length.")
    if len(outdoor_pool) < count_per_category:
        raise ValueError("outdoor_objects pool is too small for the requested event length.")

    rng = random.Random(stable_seed(overall_seed, block_idx, trial_index, condition_id))
    indoor_order = indoor_pool[:]
    outdoor_order = outdoor_pool[:]
    rng.shuffle(indoor_order)
    rng.shuffle(outdoor_order)

    encoding_items: list[dict[str, Any]] = []
    indoor_cursor = 0
    outdoor_cursor = 0
    for event_idx in range(event_count):
        event_items = _sample_event_items(
            rng=rng,
            indoor_pool=indoor_order[indoor_cursor : indoor_cursor + count_per_category],
            outdoor_pool=outdoor_order[outdoor_cursor : outdoor_cursor + count_per_category],
            count_per_category=count_per_category,
        )
        indoor_cursor += count_per_category
        outdoor_cursor += count_per_category

        event_ear = str(tone_ears[event_idx % len(tone_ears)]).strip().lower() or "left"
        tone_frequency_hz = float(tone_frequencies[(sequence_index + event_idx) % len(tone_frequencies)])
        tone_frequency_label = int(round(tone_frequency_hz))
        for within_event_index, event_item in enumerate(event_items):
            item_index = len(encoding_items)
            encoding_items.append(
                {
                    "item_index": item_index,
                    "event_index": event_idx,
                    "within_event_index": within_event_index,
                    "object_label": event_item["object_label"],
                    "object_context": event_item["object_context"],
                    "correct_key": event_item["correct_key"],
                    "tone_ear": event_ear,
                    "tone_frequency_hz": tone_frequency_hz,
                    "tone_asset_id": f"tone_{event_ear}_{tone_frequency_label}",
                }
            )

    probe_rng = random.Random(stable_seed(overall_seed, block_idx, trial_index, condition_id, "probes"))
    memory_pairs = _build_probe_pairs(
        items=encoding_items,
        same_count=same_probe_count,
        boundary_count=boundary_probe_count,
        rng=probe_rng,
    )

    source_left = [item for item in encoding_items if item["tone_ear"] == "left"]
    source_right = [item for item in encoding_items if item["tone_ear"] == "right"]
    probe_rng.shuffle(source_left)
    probe_rng.shuffle(source_right)
    source_pairs: list[dict[str, Any]] = []
    left_target = math.ceil(source_probe_count / 2)
    right_target = source_probe_count // 2
    for item in source_left[:left_target]:
        source_pairs.append(
            {
                "item_index": item["item_index"],
                "object_label": item["object_label"],
                "tone_ear": "left",
                "correct_key": "f",
            }
        )
    for item in source_right[:right_target]:
        source_pairs.append(
            {
                "item_index": item["item_index"],
                "object_label": item["object_label"],
                "tone_ear": "right",
                "correct_key": "j",
            }
        )
    probe_rng.shuffle(source_pairs)

    distractor_trials = max(1, int(round(distractor_duration_s / distractor_trial_duration_s)))
    arrow_cycle = ["left", "right"]
    distractor_items: list[dict[str, Any]] = []
    for idx in range(distractor_trials):
        direction = arrow_cycle[idx % len(arrow_cycle)]
        distractor_items.append(
            {
                "trial_index": idx,
                "arrow_direction": direction,
                "arrow_symbol": "←" if direction == "left" else "→",
                "correct_key": direction,
            }
        )

    summary_label = "Practice Complete" if is_practice else "Sequence Complete"
    next_step_label = "Press space to continue."
    if is_practice:
        next_step_label = "Press space to begin the scored sequences."

    return {
        "condition_id": condition_id,
        "sequence_role": sequence_role,
        "sequence_index": sequence_index,
        "is_practice": is_practice,
        "trial_kind": sequence_role,
        "block_idx": int(block_idx),
        "trial_index": int(trial_index),
        "sequence_count": sequence_count,
        "event_length_items": event_length,
        "event_count": event_count,
        "item_duration_s": item_duration_s,
        "inter_item_interval_s": inter_item_interval_s,
        "tone_onset_offset_s": tone_onset_offset_s,
        "tone_duration_s": tone_duration_s,
        "distractor_duration_s": distractor_duration_s,
        "distractor_trial_duration_s": distractor_trial_duration_s,
        "order_response_window_s": order_response_window_s,
        "distance_response_window_s": distance_response_window_s,
        "source_response_window_s": source_response_window_s,
        "encoding_items": encoding_items,
        "memory_pairs": memory_pairs,
        "source_pairs": source_pairs,
        "distractor_items": distractor_items,
        "summary_label": summary_label,
        "next_step_label": next_step_label,
        "source_probe_count": source_probe_count,
        "same_context_probe_count": same_probe_count,
        "boundary_probe_count": boundary_probe_count,
        "tone_frequencies_hz": tone_frequencies,
        "tone_ears": tone_ears,
        "indoor_objects": indoor_pool,
        "outdoor_objects": outdoor_pool,
    }


def summarize_accuracy(records: Iterable[dict[str, Any]], key: str = "response_correct") -> float | None:
    values = [1.0 if bool(rec.get(key, False)) else 0.0 for rec in records]
    if not values:
        return None
    return fmean(values)


def summarize_rt(records: Iterable[dict[str, Any]], key: str = "response_rt") -> float | None:
    values = [float(rec[key]) for rec in records if isinstance(rec.get(key), (int, float))]
    if not values:
        return None
    return fmean(values)


def summarize_timeout_count(records: Iterable[dict[str, Any]]) -> int:
    return sum(1 for rec in records if bool(rec.get("timed_out", False)))


def bucket_distance_label(lag: int) -> str:
    return _lag_bucket(lag)


def distance_bucket_label_text(bucket: str) -> str:
    bucket = str(bucket).strip()
    if bucket == "1":
        return "very close"
    if bucket == "2":
        return "close"
    if bucket == "3":
        return "far"
    return "very far"


def resolve_tone_asset_id(ear: str, frequency_hz: float) -> str:
    return f"tone_{str(ear).strip().lower()}_{int(round(float(frequency_hz)))}"


def make_probe_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(records),
        "accuracy": summarize_accuracy(records),
        "mean_rt_s": summarize_rt(records),
        "timeouts": summarize_timeout_count(records),
    }


__all__ = [
    "DEFAULT_CONTINUE_KEY",
    "DEFAULT_ENCODING_KEYS",
    "DEFAULT_DISTANCE_KEYS",
    "DEFAULT_DISTRACTOR_KEYS",
    "DEFAULT_EVENT_LENGTH_ITEMS",
    "DEFAULT_FIXATION_DURATION_S",
    "DEFAULT_ITEM_DURATION_S",
    "DEFAULT_INTER_ITEM_INTERVAL_S",
    "DEFAULT_ORDER_RESPONSE_WINDOW_S",
    "DEFAULT_DISTANCE_RESPONSE_WINDOW_S",
    "DEFAULT_SOURCE_RESPONSE_WINDOW_S",
    "DEFAULT_SEQUENCE_COUNT",
    "DEFAULT_TONE_DURATION_S",
    "DEFAULT_TONE_EARS",
    "DEFAULT_TONE_FREQUENCIES_HZ",
    "DEFAULT_TONE_ONSET_OFFSET_S",
    "INDOOR_OBJECTS",
    "OUTDOOR_OBJECTS",
    "bucket_distance_label",
    "build_sequence_plan",
    "distance_bucket_label_text",
    "format_ms",
    "format_pct",
    "format_s",
    "make_probe_summary",
    "parse_condition",
    "resolve_tone_asset_id",
    "stable_seed",
    "summarize_accuracy",
    "summarize_rt",
    "summarize_timeout_count",
]
