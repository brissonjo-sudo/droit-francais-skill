"""Configuration et garde-fous du serveur MCP public."""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping


class RuntimeConfigurationError(ValueError):
    """Configuration invalide, formulée sans recopier les secrets."""


class RuntimeCapacityError(RuntimeError):
    """Capacité temporairement épuisée."""


def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeConfigurationError(f"{name} doit être un entier.") from exc
    if value <= 0:
        raise RuntimeConfigurationError(f"{name} doit être strictement positif.")
    return value


def _positive_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeConfigurationError(f"{name} doit être un nombre.") from exc
    if value <= 0:
        raise RuntimeConfigurationError(f"{name} doit être strictement positif.")
    return value


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    host: str
    port: int
    log_level: str
    max_concurrent_requests: int
    tool_calls_per_minute: int
    queue_timeout_seconds: float
    max_request_body_bytes: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "RuntimeSettings":
        values = os.environ if env is None else env
        port_name = "PORT" if values.get("PORT") else "MCP_PORT"
        port = _positive_int(values, port_name, 8000)
        if port > 65535:
            raise RuntimeConfigurationError(
                f"{port_name} doit être compris entre 1 et 65535."
            )
        log_level = values.get("MCP_LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise RuntimeConfigurationError("MCP_LOG_LEVEL est invalide.")
        environment = values.get("MCP_ENV", "development").strip().lower()
        if environment not in {"development", "test", "production"}:
            raise RuntimeConfigurationError(
                "MCP_ENV doit valoir development, test ou production."
            )
        return cls(
            environment=environment,
            host=values.get("MCP_HOST", "127.0.0.1"),
            port=port,
            log_level=log_level,
            max_concurrent_requests=_positive_int(
                values, "MCP_MAX_CONCURRENT_REQUESTS", 8
            ),
            tool_calls_per_minute=_positive_int(
                values, "MCP_TOOL_CALLS_PER_MINUTE", 120
            ),
            queue_timeout_seconds=_positive_float(
                values, "MCP_QUEUE_TIMEOUT_SECONDS", 2.0
            ),
            max_request_body_bytes=_positive_int(
                values, "MCP_MAX_REQUEST_BODY_BYTES", 1_048_576
            ),
        )

    def validate_public(self, env: Mapping[str, str] | None = None) -> None:
        """Refuse un démarrage public mal configuré sans afficher de valeur."""
        values = os.environ if env is None else env
        if self.environment != "production":
            return

        missing = [
            name
            for name in ("LEGIFRANCE_CLIENT_ID", "LEGIFRANCE_CLIENT_SECRET")
            if not values.get(name, "").strip()
        ]
        if not (
            values.get("JUDILIBRE_KEY_ID", "").strip()
            or values.get("PISTE_KEY_ID", "").strip()
        ):
            missing.append("JUDILIBRE_KEY_ID (ou PISTE_KEY_ID)")
        if missing:
            raise RuntimeConfigurationError(
                "Variables obligatoires absentes en production : " + ", ".join(missing)
            )
        if values.get("LEGIFRANCE_ENV", "prod").lower() != "prod":
            raise RuntimeConfigurationError(
                "LEGIFRANCE_ENV doit valoir prod en production."
            )
        if values.get("JUDILIBRE_ENV", "prod").lower() != "prod":
            raise RuntimeConfigurationError(
                "JUDILIBRE_ENV doit valoir prod en production."
            )


class RequestGovernor:
    """Limite la concurrence et le débit des outils par instance."""

    def __init__(
        self,
        max_concurrent: int,
        requests_per_minute: int,
        queue_timeout_seconds: float,
    ) -> None:
        self._semaphore = threading.BoundedSemaphore(max_concurrent)
        self._requests_per_minute = requests_per_minute
        self._queue_timeout_seconds = queue_timeout_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    @contextmanager
    def slot(self) -> Iterator[None]:
        acquired = self._semaphore.acquire(timeout=self._queue_timeout_seconds)
        if not acquired:
            raise RuntimeCapacityError("Serveur temporairement occupé ; réessayer.")
        try:
            now = time.monotonic()
            with self._lock:
                while self._timestamps and self._timestamps[0] <= now - 60:
                    self._timestamps.popleft()
                if len(self._timestamps) >= self._requests_per_minute:
                    raise RuntimeCapacityError(
                        "Quota temporaire de consultation atteint ; réessayer plus tard."
                    )
                self._timestamps.append(now)
            yield
        finally:
            self._semaphore.release()
