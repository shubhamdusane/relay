"""Budget gate — hard caps per key / per day / per month.

Tracks spend via append-only JSONL log. Deterministic check BEFORE call, record AFTER.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from relay.pricing import estimate_cost


class BudgetExceeded(Exception):
    """Raised when a projected call would blow the budget."""


@dataclass
class Budget:
    """Spend tracker with hard caps.

    Args:
        daily_usd: max USD per calendar day (UTC). None = no cap.
        monthly_usd: max USD per calendar month (UTC). None = no cap.
        log_path: JSONL file to append spend records.
        key: identifier for multi-tenant tracking.
    """

    daily_usd: Optional[float] = None
    monthly_usd: Optional[float] = None
    log_path: str = "relay_spend.jsonl"
    key: str = "default"
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # ---------- public ----------

    def check(self, model: str, input_tokens: int, output_tokens_est: int = 0) -> None:
        """Raise BudgetExceeded if projected call would exceed a cap."""
        if self.daily_usd is None and self.monthly_usd is None:
            return
        q = estimate_cost(model, input_tokens, output_tokens_est)
        spent_day, spent_month = self._spent()
        if self.daily_usd is not None and spent_day + q.total_usd > self.daily_usd:
            raise BudgetExceeded(
                f"daily cap ${self.daily_usd:.4f} would be exceeded "
                f"(spent=${spent_day:.4f}, projected=${q.total_usd:.6f})"
            )
        if self.monthly_usd is not None and spent_month + q.total_usd > self.monthly_usd:
            raise BudgetExceeded(
                f"monthly cap ${self.monthly_usd:.4f} would be exceeded "
                f"(spent=${spent_month:.4f}, projected=${q.total_usd:.6f})"
            )

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Persist a spend record. Returns USD charged."""
        q = estimate_cost(model, input_tokens, output_tokens)
        rec = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "key": self.key,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": q.total_usd,
        }
        with self._lock:
            Path(self.log_path).parent.mkdir(parents=True, exist_ok=True) if os.path.dirname(
                self.log_path
            ) else None
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        return q.total_usd

    def total(self) -> float:
        """All-time USD spent for this key."""
        return self._sum(predicate=lambda rec: rec["key"] == self.key)

    def today(self) -> float:
        spent_day, _ = self._spent()
        return spent_day

    def month(self) -> float:
        _, spent_month = self._spent()
        return spent_month

    # ---------- internal ----------

    def _spent(self) -> tuple[float, float]:
        now = datetime.now(timezone.utc)
        today_prefix = now.strftime("%Y-%m-%d")
        month_prefix = now.strftime("%Y-%m")
        day = 0.0
        month = 0.0
        p = Path(self.log_path)
        if not p.exists():
            return 0.0, 0.0
        with self._lock:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("key") != self.key:
                        continue
                    ts = rec.get("ts", "")
                    usd = float(rec.get("usd", 0.0))
                    if ts.startswith(month_prefix):
                        month += usd
                    if ts.startswith(today_prefix):
                        day += usd
        return day, month

    def _sum(self, predicate) -> float:
        total = 0.0
        p = Path(self.log_path)
        if not p.exists():
            return 0.0
        with self._lock:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if predicate(rec):
                        total += float(rec.get("usd", 0.0))
        return total
