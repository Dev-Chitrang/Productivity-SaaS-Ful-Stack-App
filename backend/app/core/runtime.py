"""
Centralized runtime resource configuration.

All production scaling values are derived from the number of CPU cores
available at startup.  Non-production environments use safe development
defaults so that the developer experience is unchanged.

Usage:
    from app.core.runtime import runtime

    # Uvicorn workers
    workers = runtime.uvicorn_workers        # int

    # SQLAlchemy async-engine pool
    pool = runtime.db_pool                   # dict[str, int | bool]

    # Celery worker flags
    celery = runtime.celery                  # dict[str, int]

    # Redis connection pool
    redis_max = runtime.redis_max_connections  # int
"""

from __future__ import annotations

import os
import math

from app.core.config import settings

# ---------------------------------------------------------------------------
# CPU detection
# ---------------------------------------------------------------------------

def _detect_cpu_cores() -> int:
    """Return the number of CPUs visible to this process.

    ``os.cpu_count()`` returns the count from ``sched_getconf(NPROCESSORS_ONLN)``
    on Linux and respects cgroup limits in Python ≥3.13.  For containers running
    on older Python where cgroup quotas are not reflected, we fall back to
    reading the CGroup v2 quota directly.
    """
    count = os.cpu_count() or 1

    # Attempt to read cgroup v2 CPU quota (relevant for Docker/K8s on older Pythons)
    try:
        with open("/sys/fs/cgroup/cpu.max") as fh:
            quota_str, period_str = fh.read().split()
            if quota_str != "max":                       # "max" = no limit
                quota = int(quota_str)
                period = int(period_str)
                cgroup_cpus = math.ceil(quota / period)
                if cgroup_cpus > 0:
                    count = min(count, cgroup_cpus)
    except (OSError, ValueError, ZeroDivisionError):
        pass  # not in a cgroup-v2 environment or file format unexpected

    return max(count, 1)


CPU_CORES: int = _detect_cpu_cores()

# ---------------------------------------------------------------------------
# Production settings — derived from CPU_CORES
# ---------------------------------------------------------------------------

# -- Uvicorn ----------------------------------------------------------------
# Recommended: (CPU_CORES * 2) + 1.  Minimum 2 so that one worker can serve
# requests while the other handles periodic housekeeping.
_env_override = os.environ.get("UVICORN_WORKERS")
UVICORN_WORKERS: int = max(int(_env_override), 1) if _env_override else max((CPU_CORES * 2) + 1, 2)

# -- SQLAlchemy connection pool ---------------------------------------------
# pool_size:        persistent connections per worker.  We budget ~10 % of
#                   total workers per pool slot, with a floor of 5.
# max_overflow:     burst connections above pool_size.  Sized at 2× pool_size
#                   to absorb request spikes without exhausting the database.
# pool_timeout:     seconds to wait for a connection before raising.
# pool_recycle:     recycle connections after 1 hour to avoid stale TCP state.
# pool_pre_ping:    issue a lightweight SELECT on checkout to discard dead
#                   connections (always enabled).
DB_POOL_SIZE: int = max(UVICORN_WORKERS // 10, 5)
DB_MAX_OVERFLOW: int = DB_POOL_SIZE * 2
DB_POOL_TIMEOUT: int = 30
DB_POOL_RECYCLE: int = 3600          # 1 hour

# -- Redis ------------------------------------------------------------------
# Max connections per application instance.  Sized to cover all uvicorn
# workers plus headroom for Celery and ad-hoc diagnostics.
REDIS_MAX_CONNECTIONS: int = UVICORN_WORKERS + 10

# -- Celery -----------------------------------------------------------------
# concurrency:      worker pool size.  Matches CPU_CORES by default because
#                   Celery tasks are predominantly I/O-bound (DB, email, AI).
# prefetch_multi:   how many tasks each worker child prefetches.  Lower
#                   values improve fair scheduling at the cost of slight
#                   throughput reduction.  1× is the safest default for
#                   mixed workloads.
# max_tasks_per_child: recycle worker children after 1000 tasks to bound
#                   memory growth from long-running or leaky tasks.
CELERY_CONCURRENCY: int = max(CPU_CORES, 1)
CELERY_PREFETCH_MULTIPLIER: int = 1
CELERY_MAX_TASKS_PER_CHILD: int = 1000

# ---------------------------------------------------------------------------
# Production flag (convenience for callers)
# ---------------------------------------------------------------------------
IS_PRODUCTION: bool = settings.ENVIRONMENT == "PRODUCTION"


# ---------------------------------------------------------------------------
# Grouped accessors — keep callers' import surface small
# ---------------------------------------------------------------------------

class _DBPool:
    """SQLAlchemy ``create_async_engine`` keyword arguments."""

    __slots__ = ()

    def as_kwargs(self) -> dict:
        if not IS_PRODUCTION:
            return {}           # use SQLAlchemy defaults
        return {
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW,
            "pool_timeout": DB_POOL_TIMEOUT,
            "pool_recycle": DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }


class _Celery:
    """``celery worker`` CLI overrides."""

    __slots__ = ()

    @property
    def concurrency(self) -> int:
        return CELERY_CONCURRENCY if IS_PRODUCTION else 1

    @property
    def prefetch_multiplier(self) -> int:
        return CELERY_PREFETCH_MULTIPLIER if IS_PRODUCTION else 4

    @property
    def max_tasks_per_child(self) -> int | None:
        return CELERY_MAX_TASKS_PER_CHILD if IS_PRODUCTION else None


class _Runtime:
    """Facade that groups every calculated value."""

    __slots__ = ("db_pool", "celery")

    def __init__(self) -> None:
        self.db_pool = _DBPool()
        self.celery = _Celery()

    # -- scalar helpers ------------------------------------------------------

    @property
    def uvicorn_workers(self) -> int:
        return UVICORN_WORKERS if IS_PRODUCTION else 1

    @property
    def redis_max_connections(self) -> int:
        return REDIS_MAX_CONNECTIONS if IS_PRODUCTION else 20

    def __repr__(self) -> str:
        return (
            f"<Runtime cpu_cores={CPU_CORES} "
            f"uvicorn_workers={self.uvicorn_workers} "
            f"db_pool_size={DB_POOL_SIZE if IS_PRODUCTION else 'default'} "
            f"celery_concurrency={self.celery.concurrency}>"
        )


# Singleton — import ``runtime`` to access every calculated value.
runtime = _Runtime()
