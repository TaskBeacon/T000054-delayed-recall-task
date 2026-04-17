from __future__ import annotations

import random as _py_random
from dataclasses import dataclass
from typing import Any

from psyflow.sim.contracts import Action, Feedback, Observation, SessionInfo


@dataclass
class TaskSamplerResponder:
    """Task-specific responder for the delayed-recall task."""

    key: str | None = None
    continue_key: str = "space"
    continue_rt_s: float = 0.35
    encoding_hit_rate: float = 0.98
    distractor_hit_rate: float = 0.95
    order_hit_rate: float = 0.93
    distance_exact_rate: float = 0.80
    source_hit_rate: float = 0.95
    timeout_rate: float = 0.02
    rt_mean_s: float = 0.82
    rt_sd_s: float = 0.20
    rt_min_s: float = 0.18
    practice_bonus: float = 0.02

    def __post_init__(self) -> None:
        self._rng: Any = None
        self.continue_rt_s = max(self.rt_min_s, float(self.continue_rt_s))
        self.encoding_hit_rate = max(0.0, min(1.0, float(self.encoding_hit_rate)))
        self.distractor_hit_rate = max(0.0, min(1.0, float(self.distractor_hit_rate)))
        self.order_hit_rate = max(0.0, min(1.0, float(self.order_hit_rate)))
        self.distance_exact_rate = max(0.0, min(1.0, float(self.distance_exact_rate)))
        self.source_hit_rate = max(0.0, min(1.0, float(self.source_hit_rate)))
        self.timeout_rate = max(0.0, min(1.0, float(self.timeout_rate)))
        self.rt_mean_s = float(self.rt_mean_s)
        self.rt_sd_s = max(1e-6, float(self.rt_sd_s))
        self.rt_min_s = max(0.0, float(self.rt_min_s))
        self.practice_bonus = max(0.0, float(self.practice_bonus))

    def start_session(self, session: SessionInfo, rng: Any) -> None:
        self._rng = rng

    def on_feedback(self, fb: Feedback) -> None:
        return None

    def end_session(self) -> None:
        self._rng = None

    def _sample_random(self) -> float:
        rng = self._rng
        if hasattr(rng, "random"):
            return float(rng.random())
        return float(_py_random.random())

    def _sample_normal(self, mean: float, sd: float) -> float:
        rng = self._rng
        if hasattr(rng, "normal"):
            return float(rng.normal(mean, sd))
        if hasattr(rng, "gauss"):
            return float(rng.gauss(mean, sd))
        return float(mean)

    def _pick_valid_key(self, valid_keys: list[str], preferred: str | None = None) -> str | None:
        if preferred and preferred in valid_keys:
            return preferred
        if self.key and self.key in valid_keys:
            return self.key
        return valid_keys[0] if valid_keys else None

    def _profile(self, obs: Observation) -> dict[str, Any]:
        task_factors = dict(getattr(obs, "task_factors", {}) or {})
        if not task_factors and isinstance(getattr(obs, "extras", None), dict):
            task_factors = dict(obs.extras.get("task_factors", {}) or {})

        stage = str(task_factors.get("stage", getattr(obs, "phase", ""))).strip().lower()
        sequence_role = str(task_factors.get("sequence_role", "")).strip().lower()

        if any(token in stage for token in ("instruction", "sequence_summary", "good_bye")):
            return {
                "mode": "continue",
                "stage": stage,
                "task_factors": task_factors,
                "timeout_rate": 0.0,
                "rt_mean_s": self.continue_rt_s,
            }

        hit_rate = self.encoding_hit_rate
        rt_mean = self.rt_mean_s
        if stage == "encoding_item":
            hit_rate = self.encoding_hit_rate
            rt_mean = self.rt_mean_s - 0.06
        elif stage == "distractor_task":
            hit_rate = self.distractor_hit_rate
            rt_mean = self.rt_mean_s - 0.03
        elif stage == "temporal_order_probe":
            hit_rate = self.order_hit_rate
            rt_mean = self.rt_mean_s + 0.03
        elif stage == "temporal_distance_probe":
            hit_rate = self.distance_exact_rate
            rt_mean = self.rt_mean_s + 0.05
        elif stage == "source_memory_probe":
            hit_rate = self.source_hit_rate
            rt_mean = self.rt_mean_s + 0.02

        if sequence_role == "practice":
            hit_rate = min(1.0, hit_rate + self.practice_bonus)
            rt_mean -= 0.02

        return {
            "mode": "response",
            "stage": stage,
            "task_factors": task_factors,
            "timeout_rate": self.timeout_rate,
            "hit_rate": max(0.0, min(1.0, hit_rate)),
            "rt_mean_s": max(self.rt_min_s, rt_mean),
        }

    def _distance_choice(self, valid_keys: list[str], true_bucket: str) -> tuple[str | None, str]:
        if true_bucket and true_bucket in valid_keys and self._sample_random() < self.distance_exact_rate:
            return true_bucket, "hit"

        bucket_num = None
        try:
            bucket_num = int(true_bucket)
        except Exception:
            bucket_num = None

        neighbor_keys: list[str] = []
        if bucket_num is not None:
            for candidate in (bucket_num - 1, bucket_num + 1):
                candidate_key = str(candidate)
                if candidate_key in valid_keys:
                    neighbor_keys.append(candidate_key)

        if neighbor_keys:
            chosen = neighbor_keys[0] if len(neighbor_keys) == 1 else neighbor_keys[int(self._sample_random() * len(neighbor_keys))]
            return chosen, "near"

        wrong_keys = [key for key in valid_keys if key != true_bucket]
        if wrong_keys:
            return wrong_keys[0], "miss"
        return self._pick_valid_key(valid_keys, true_bucket), "miss"

    def act(self, obs: Observation) -> Action:
        valid_keys = [str(key) for key in list(obs.valid_keys or [])]
        if not valid_keys:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "no_valid_keys"})

        rng = self._rng
        if rng is None:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "rng_missing"})

        profile = self._profile(obs)
        task_factors = profile["task_factors"]
        stage = str(profile["stage"])
        sequence_role = str(task_factors.get("sequence_role", "")).strip().lower()

        if profile["mode"] == "continue":
            rt = max(self.rt_min_s, self._sample_normal(profile["rt_mean_s"], self.rt_sd_s))
            chosen_key = self._pick_valid_key(valid_keys, self.continue_key)
            return Action(
                key=chosen_key,
                rt_s=rt,
                meta={
                    "source": "task_sampler",
                    "outcome": "continue",
                    "stage": stage,
                    "sequence_role": sequence_role,
                },
            )

        if self._sample_random() < float(profile["timeout_rate"]):
            return Action(
                key=None,
                rt_s=None,
                meta={
                    "source": "task_sampler",
                    "outcome": "timeout",
                    "stage": stage,
                    "sequence_role": sequence_role,
                },
            )

        rt = max(self.rt_min_s, self._sample_normal(profile["rt_mean_s"], self.rt_sd_s))

        if stage == "temporal_distance_probe":
            true_bucket = str(
                task_factors.get("distance_bucket", task_factors.get("true_distance_bucket", ""))
            ).strip()
            chosen_key, outcome = self._distance_choice(valid_keys, true_bucket)
            return Action(
                key=chosen_key,
                rt_s=rt,
                meta={
                    "source": "task_sampler",
                    "outcome": outcome,
                    "stage": stage,
                    "sequence_role": sequence_role,
                    "correct_key": true_bucket,
                },
            )

        correct_key = task_factors.get("correct_key") or getattr(obs, "correct_key", None) or self.key
        correct_key = str(correct_key).strip() if correct_key is not None else None

        if self._sample_random() > float(profile["hit_rate"]):
            wrong_keys = [key for key in valid_keys if key != correct_key]
            chosen_key = wrong_keys[0] if wrong_keys else self._pick_valid_key(valid_keys, correct_key)
            return Action(
                key=chosen_key,
                rt_s=rt,
                meta={
                    "source": "task_sampler",
                    "outcome": "miss",
                    "stage": stage,
                    "sequence_role": sequence_role,
                    "correct_key": correct_key,
                },
            )

        chosen_key = self._pick_valid_key(valid_keys, correct_key)
        return Action(
            key=chosen_key,
            rt_s=rt,
            meta={
                "source": "task_sampler",
                "outcome": "hit",
                "stage": stage,
                "sequence_role": sequence_role,
                "correct_key": correct_key,
            },
        )

