"""Smart Budget Planner — pure, testable logic for the Game Price Tracker.

Framework-agnostic (no Streamlit imports) so the algorithm can be unit-tested.
Answers one question:

    "Given a budget and a number of games to buy, which combination of tracked
     games fits, while always including any 'must include' choices?"

Design notes
------------
- Deterministic core: given the same games + options, the same set of valid
  combinations is produced (the pool is iterated in the tracker's order).
- Efficient: small pools (the common case) enumerate exactly; very large pools
  fall back to bounded random sampling. A cheap O(n log n) feasibility
  pre-check rules out impossible budgets before enumeration.
- Extensible: selection is a pluggable strategy, so other strategies (max
  value, minimise overshoot, etc.) can be added without changing callers.
- The UI drives randomness: it keeps the valid set, picks one on Generate and
  a different one on Refresh using the exclusion keys.

All monetary values are in the tracker's normalized INR.
"""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Optional, Set

# Max combinations enumerated deterministically before switching to sampling.
ENUMERATE_LIMIT = 20_000
# Distinct valid combinations we try to collect via sampling.
SAMPLE_LIMIT = 5_000
# Sampling attempts cap (safety net against pathological pools).
MAX_SAMPLE_ATTEMPTS = 50_000

_EPS = 1e-6


class BudgetPlannerError(ValueError):
    """Raised when a valid plan cannot be produced (message is user-friendly)."""


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BudgetOptions:
    """Everything the planner needs to construct a plan."""

    budget: float
    count: int
    must_include_ids: tuple[str, ...] = ()
    flex_pct: float = 0.0  # 0 = strict; e.g. 10 = may exceed budget by 10%

    @property
    def allowed(self) -> float:
        """Maximum spend, including flexibility when enabled."""
        return self.budget * (1.0 + self.flex_pct / 100.0)


@dataclass
class PlanResult:
    """A concrete shopping plan for the UI."""

    games: list[dict]
    budget: float
    allowed: float
    total: float
    remaining: float          # allowed - total (negative => over budget)
    is_over_budget: bool
    combos_count: int         # total number of valid combinations that exist

    @property
    def over_amount(self) -> float:
        return max(0.0, -self.remaining)


# ─────────────────────────────────────────────────────────────────────────────
# Selection strategy (extensible)
# ─────────────────────────────────────────────────────────────────────────────


class SelectionStrategy(ABC):
    """Pick a combination from the set of valid candidates."""

    @abstractmethod
    def pick(
        self, candidates: list[tuple[dict, ...]], exclude: Set[str]
    ) -> Optional[tuple[dict, ...]]: ...


class RandomSelection(SelectionStrategy):
    """Pick a random valid combination, preferring ones not yet shown.

    If every candidate has been excluded (already shown), falls back to any
    candidate so the UI can explain that no *new* combination exists.
    """

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self._rng = rng or random.Random()

    def pick(
        self, candidates: list[tuple[dict, ...]], exclude: Set[str]
    ) -> Optional[tuple[dict, ...]]:
        if not candidates:
            return None
        fresh = [c for c in candidates if combo_key(c) not in exclude]
        return self._rng.choice(fresh or candidates)


# ─────────────────────────────────────────────────────────────────────────────
# Core planner
# ─────────────────────────────────────────────────────────────────────────────


class BudgetPlanner:
    """Validate options and enumerate every budget-valid combination."""

    def __init__(
        self,
        games: list[dict],
        options: BudgetOptions,
        rng: Optional[random.Random] = None,
    ) -> None:
        if options.budget <= 0:
            raise BudgetPlannerError("Please enter a budget greater than zero.")
        if options.count < 1:
            raise BudgetPlannerError("Please choose at least one game to buy.")

        self.options = options
        self._rng = rng or random.Random()

        # Only games with a known current price can be priced into a plan.
        self._priceable = [g for g in games if _price(g) is not None]

        self.must_games = self._resolve_must_include()
        must_ids = set(options.must_include_ids)
        self._pool = [g for g in self._priceable if g.get("id") not in must_ids]

        self._validate()
        self._combos = self._compute_valid_combinations()

    # -- validation -----------------------------------------------------------
    def _resolve_must_include(self) -> list[dict]:
        ids = set(self.options.must_include_ids)
        by_id = {g.get("id"): g for g in self._priceable if g.get("id")}
        missing = ids - set(by_id)
        if missing:
            raise BudgetPlannerError(
                "Some must-include games are not tracked or have no current price: "
                + ", ".join(sorted(missing))
            )
        return [by_id[i] for i in self.options.must_include_ids]

    def _validate(self) -> None:
        opt = self.options

        if opt.count > len(self._priceable):
            raise BudgetPlannerError(
                f"You asked for {opt.count} game(s), but only "
                f"{len(self._priceable)} tracked game(s) have a current price."
            )

        must_cost = sum(_price(g) for g in self.must_games)
        if must_cost > opt.allowed + _EPS:
            raise BudgetPlannerError(
                f"The {len(self.must_games)} must-include game(s) alone cost "
                f"₹{must_cost:,.0f}, exceeding the allowed budget of ₹{opt.allowed:,.0f}."
            )

        needed = opt.count - len(self.must_games)
        if needed > 0:
            cheapest = sum(sorted(_price(g) for g in self._pool)[:needed])
            if must_cost + cheapest > opt.allowed + _EPS:
                raise BudgetPlannerError(
                    f"No combination of {opt.count} game(s) fits the allowed budget "
                    f"of ₹{opt.allowed:,.0f}. Try a higher budget, fewer games, "
                    f"or flexible budget."
                )

    # -- enumeration ----------------------------------------------------------
    def _compute_valid_combinations(self) -> list[tuple[dict, ...]]:
        opt = self.options
        needed = opt.count - len(self.must_games)
        must_cost = sum(_price(g) for g in self.must_games)

        if needed == 0:
            return [tuple(self.must_games)]

        pool = self._pool
        n_pool = len(pool)
        valid: list[tuple[dict, ...]] = []

        if math.comb(n_pool, needed) <= ENUMERATE_LIMIT:
            for combo in combinations(pool, needed):
                cost = must_cost + sum(_price(g) for g in combo)
                if cost <= opt.allowed + _EPS:
                    valid.append(tuple(self.must_games) + combo)
        else:
            valid = self._sample_valid(pool, needed, must_cost)

        return valid

    def _sample_valid(
        self, pool: list[dict], needed: int, must_cost: float
    ) -> list[tuple[dict, ...]]:
        """Bounded random sampling for very large pools."""
        opt = self.options
        n_pool = len(pool)
        seen: Set[str] = set()
        valid: list[tuple[dict, ...]] = []
        attempts = 0

        while len(valid) < SAMPLE_LIMIT and attempts < MAX_SAMPLE_ATTEMPTS:
            attempts += 1
            idxs = tuple(sorted(self._rng.sample(range(n_pool), needed)))
            key = ",".join(str(i) for i in idxs)
            if key in seen:
                continue
            seen.add(key)
            combo = tuple(pool[i] for i in idxs)
            if must_cost + sum(_price(g) for g in combo) <= opt.allowed + _EPS:
                valid.append(tuple(self.must_games) + combo)

        # Safety net: bounded sweep if sampling found nothing.
        if not valid:
            for combo in combinations(pool, needed):
                if must_cost + sum(_price(g) for g in combo) <= opt.allowed + _EPS:
                    valid.append(tuple(self.must_games) + combo)
                if len(valid) >= ENUMERATE_LIMIT:
                    break
        return valid

    # -- public API -----------------------------------------------------------
    @property
    def valid_combinations(self) -> list[tuple[dict, ...]]:
        return list(self._combos)

    def generate(
        self,
        strategy: Optional[SelectionStrategy] = None,
        exclude: Optional[Set[str]] = None,
    ) -> PlanResult:
        """Build a PlanResult, optionally avoiding already-shown combinations."""
        strategy = strategy or RandomSelection(self._rng)
        combo = strategy.pick(self._combos, exclude or set())
        return self._build_result(combo)

    def _build_result(self, combo: tuple[dict, ...]) -> PlanResult:
        total = sum(_price(g) for g in combo)
        allowed = self.options.allowed
        remaining = allowed - total
        return PlanResult(
            games=list(combo),
            budget=self.options.budget,
            allowed=allowed,
            total=total,
            remaining=remaining,
            is_over_budget=remaining < -_EPS,
            combos_count=len(self._combos),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────


def _price(game: dict) -> Optional[float]:
    p = game.get("current_price")
    return float(p) if p is not None else None


def combo_key(combo: tuple[dict, ...]) -> str:
    """Stable fingerprint of a combination, for refresh de-duplication."""
    return ",".join(sorted(g.get("id", "") for g in combo))


__all__ = [
    "BudgetPlanner",
    "BudgetOptions",
    "PlanResult",
    "BudgetPlannerError",
    "SelectionStrategy",
    "RandomSelection",
    "combo_key",
]