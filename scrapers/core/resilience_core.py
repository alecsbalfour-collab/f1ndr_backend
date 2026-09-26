# scrapers/core/resilience_core.py
"""
Per-platform circuit breakers.

A breaker opens after `failure_threshold` consecutive failures and rejects calls
until `reset_seconds` pass. It then goes half-open: the next call is allowed
through, and a success closes it while a failure re-opens it.
"""

import time
from typing import Callable, Dict


class CircuitOpenError(RuntimeError):
    """Raised when a call is rejected because the circuit is open."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        if self._clock() - self._opened_at >= self.reset_seconds:
            return "half_open"
        return "open"

    def before_call(self) -> None:
        if self.state == "open":
            remaining = self.reset_seconds - (self._clock() - self._opened_at)
            raise CircuitOpenError(
                f"Circuit open for {self.name}; retry in {remaining:.0f}s"
            )

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self.state == "half_open" or self._failures >= self.failure_threshold:
            self._opened_at = self._clock()

    def snapshot(self) -> dict:
        return {
            "state": self.state,
            "consecutive_failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "reset_seconds": self.reset_seconds,
        }


class BreakerRegistry:
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get(self, name: str, failure_threshold: int, reset_seconds: float) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, failure_threshold, reset_seconds)
        return self._breakers[name]

    def snapshot(self) -> Dict[str, dict]:
        return {name: breaker.snapshot() for name, breaker in self._breakers.items()}

    def reset(self) -> None:
        self._breakers.clear()


breaker_registry = BreakerRegistry()
