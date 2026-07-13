"""API contract for searchable boundaries (municipalities, neighborhoods, lots).

Keep this stable. Changing it requires updating the frontend API client
(`frontend/src/api/`) and the e2e tests in the same change.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BoundaryKind = Literal["municipality", "neighborhood", "lot"]


class BoundarySummary(BaseModel):
    """A search result: enough to list, select, and later fetch the geometry."""

    id: str = Field(..., examples=["hood-kitsilano"])
    name: str = Field(..., examples=["Kitsilano"])
    kind: BoundaryKind
