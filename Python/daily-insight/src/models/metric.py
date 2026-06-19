"""Metric record schema — matches the C# RailenginePoweredStatusPage example."""

from __future__ import annotations

from pydantic import BaseModel


class MetricRecord(BaseModel):
    """One metric reading as stored in Railengine.

    Fields mirror the camelCase JSON keys produced by the status-page example
    (`metric`, `timestamp`, `value`), so no field aliases are needed.
    """

    metric: str
    timestamp: int
    value: float
