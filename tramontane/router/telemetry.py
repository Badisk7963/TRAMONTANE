"""Fleet telemetry — records routing outcomes for self-learning router."""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_DB = "tramontane_telemetry.db"


@dataclass
class RoutingOutcome:
    """Outcome of a single routing decision."""

    task_type: str
    complexity: int
    model_used: str
    reasoning_effort: str | None
    success: bool
    cost_eur: float
    latency_s: float
    output_tokens: int
    agent_role: str = ""
    timestamp: float = field(default_factory=time.time)


class FleetTelemetry:
    """Collects routing outcomes and provides data-driven routing suggestions.

    Stores outcomes in SQLite. After enough data, the router can query
    this instead of using hand-crafted rules.
    """

    def __init__(self, db_path: str = DEFAULT_DB) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS routing_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                complexity INTEGER NOT NULL,
                model_used TEXT NOT NULL,
                reasoning_effort TEXT,
                success INTEGER NOT NULL,
                cost_eur REAL NOT NULL,
                latency_s REAL NOT NULL,
                output_tokens INTEGER NOT NULL,
                agent_role TEXT,
                timestamp REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_complexity
                ON routing_outcomes(task_type, complexity);
            CREATE INDEX IF NOT EXISTS idx_model
                ON routing_outcomes(model_used);
        """)
        self._conn.commit()

    def record(self, outcome: RoutingOutcome) -> None:
        """Record a routing outcome."""
        self._conn.execute(
            """INSERT INTO routing_outcomes
               (task_type, complexity, model_used, reasoning_effort,
                success, cost_eur, latency_s, output_tokens,
                agent_role, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                outcome.task_type,
                outcome.complexity,
                outcome.model_used,
                outcome.reasoning_effort,
                int(outcome.success),
                outcome.cost_eur,
                outcome.latency_s,
                outcome.output_tokens,
                outcome.agent_role,
                outcome.timestamp,
            ),
        )
        self._conn.commit()

    def suggest_model(
        self,
        task_type: str,
        complexity: int,
        min_samples: int = 10,
    ) -> str | None:
        """Suggest the best model based on historical data.

        Returns the model with highest success rate at lowest cost,
        or None if insufficient data.
        """
        rows = self._conn.execute(
            """SELECT model_used, reasoning_effort,
                      COUNT(*) as total,
                      SUM(success) as successes,
                      AVG(cost_eur) as avg_cost,
                      AVG(latency_s) as avg_latency
               FROM routing_outcomes
               WHERE task_type = ? AND complexity = ?
               GROUP BY model_used, reasoning_effort
               HAVING total >= ?
               ORDER BY (CAST(successes AS REAL) / total) DESC,
                        avg_cost ASC""",
            (task_type, complexity, min_samples),
        ).fetchall()

        if not rows:
            return None

        best = rows[0]
        success_rate = best["successes"] / best["total"]

        if success_rate < 0.7:
            return None

        logger.info(
            "Telemetry suggests %s (effort=%s) for %s/complexity=%d: "
            "%.0f%% success, EUR %.4f avg cost (%d samples)",
            best["model_used"],
            best["reasoning_effort"],
            task_type,
            complexity,
            success_rate * 100,
            best["avg_cost"],
            best["total"],
        )
        return str(best["model_used"])

    def get_model_stats(self, model: str | None = None) -> list[dict[str, object]]:
        """Get performance stats for one or all models."""
        if model:
            rows = self._conn.execute(
                """SELECT model_used, reasoning_effort,
                          COUNT(*) as total,
                          SUM(success) as successes,
                          AVG(cost_eur) as avg_cost,
                          AVG(latency_s) as avg_latency,
                          AVG(output_tokens) as avg_tokens
                   FROM routing_outcomes
                   WHERE model_used = ?
                   GROUP BY model_used, reasoning_effort""",
                (model,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT model_used, reasoning_effort,
                          COUNT(*) as total,
                          SUM(success) as successes,
                          AVG(cost_eur) as avg_cost,
                          AVG(latency_s) as avg_latency,
                          AVG(output_tokens) as avg_tokens
                   FROM routing_outcomes
                   GROUP BY model_used, reasoning_effort
                   ORDER BY total DESC""",
            ).fetchall()

        return [dict(row) for row in rows]

    @property
    def total_outcomes(self) -> int:
        """Total recorded outcomes."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM routing_outcomes",
        ).fetchone()
        return row[0] if row else 0
