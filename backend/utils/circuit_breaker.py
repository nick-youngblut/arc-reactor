from __future__ import annotations

from dataclasses import dataclass

from circuitbreaker import CircuitBreaker


@dataclass(frozen=True)
class Breakers:
    benchling: CircuitBreaker
    gemini: CircuitBreaker


def create_breakers(settings: object) -> Breakers:
    benchling_failure_threshold = getattr(settings, "benchling_cb_failure_threshold", 5)
    benchling_recovery_timeout = getattr(settings, "benchling_cb_recovery_timeout", 30)
    gemini_failure_threshold = getattr(settings, "gemini_cb_failure_threshold", 3)
    gemini_recovery_timeout = getattr(settings, "gemini_cb_recovery_timeout", 60)

    benchling_breaker = CircuitBreaker(
        failure_threshold=benchling_failure_threshold,
        recovery_timeout=benchling_recovery_timeout,
    )
    gemini_breaker = CircuitBreaker(
        failure_threshold=gemini_failure_threshold,
        recovery_timeout=gemini_recovery_timeout,
    )

    return Breakers(benchling=benchling_breaker, gemini=gemini_breaker)


def breaker_state(breaker: CircuitBreaker) -> str:
    if hasattr(breaker, "current_state"):
        state = breaker.current_state
        return getattr(state, "name", str(state))
    if hasattr(breaker, "state"):
        state = breaker.state
        return getattr(state, "name", str(state))
    if getattr(breaker, "opened", False):
        return "open"
    return "closed"


def is_breaker_open(breaker: CircuitBreaker) -> bool:
    if getattr(breaker, "opened", False):
        return True
    state = breaker_state(breaker).lower()
    return state == "open"
