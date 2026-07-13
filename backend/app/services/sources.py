"""Region and data-source catalog, parsed from the repo's SOURCES.md.

SOURCES.md is the human-curated list of open-data portals per metro region.
This module turns it into API data: each ``## <Region>`` section that contains
source bullets becomes a region, and each ``* **Name**`` bullet (with nested
``**Description**``/``**Endpoint**`` fields) becomes a :class:`DataSource`.

The file is bind-mounted into the backend container (see the compose files) and
re-read on each request, so editing SOURCES.md updates the API without a
rebuild. If the file is missing, built-in region defaults keep the app working.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.schemas.layers import DataSource, RegionMeta

# Viewports are presentation details, not source metadata, so they live here
# rather than in SOURCES.md. Unknown regions fall back to a Canada-wide view.
_REGION_VIEWPORTS: dict[str, tuple[tuple[float, float], float]] = {
    "gva": ((-123.02, 49.24), 10.5),
    "gta": ((-79.38, 43.71), 9.8),
}
_FALLBACK_VIEWPORT: tuple[tuple[float, float], float] = ((-96.0, 56.0), 3.2)

# Regions served even when SOURCES.md cannot be read.
_FALLBACK_REGION_TITLES: dict[str, str] = {
    "gta": "Greater Toronto Area",
    "gva": "Greater Vancouver Area",
}

_H2_RE = re.compile(r"^##\s+(?P<title>[^#].*?)\s*$")
_H3_RE = re.compile(r"^###\s+(?P<title>[^#].*?)\s*$")
# A source entry: a top-level bullet whose whole content is a bold name.
_SOURCE_NAME_RE = re.compile(r"^\*\s+\*\*(?P<name>.+?)\*\*\s*$")
# Nested "*   **Field**: value" bullets under a source entry.
_FIELD_RE = re.compile(r"^\s+\*\s+\*\*(?P<field>[^*]+?)\*\*\s*:\s*(?P<value>.+?)\s*$")
_LINK_RE = re.compile(r"\[[^\]]*\]\((?P<url>[^)\s]+)\)")
_ACRONYM_RE = re.compile(r"\(([A-Za-z]{2,6})\)")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _region_id(heading: str) -> str:
    """'Greater Toronto Area (GTA)' -> 'gta'; otherwise slugified heading."""
    match = _ACRONYM_RE.search(heading)
    return match.group(1).lower() if match else _slugify(heading)


def _region_title(heading: str) -> str:
    """Strip the acronym/qualifier: 'Greater Vancouver Area (GVA) / ...' -> base name."""
    return heading.split(" (")[0].strip()


def _viewport(region_id: str) -> tuple[tuple[float, float], float]:
    return _REGION_VIEWPORTS.get(region_id, _FALLBACK_VIEWPORT)


def parse_sources_md(text: str) -> tuple[list[RegionMeta], list[DataSource]]:
    """Parse SOURCES.md text into regions and data sources.

    Only ``##`` sections that contain at least one complete source entry
    (name + Endpoint link) become regions, which naturally skips prose
    sections like the programmatic-access notes.
    """
    regions: list[RegionMeta] = []
    sources: list[DataSource] = []
    seen_ids: set[str] = set()

    heading = ""
    group = ""
    pending: dict[str, str] | None = None

    def flush_pending() -> None:
        nonlocal pending
        if pending and pending.get("url") and heading:
            region_id = _region_id(heading)
            base = _slugify(pending["name"]) or "source"
            source_id = base
            suffix = 2
            while source_id in seen_ids:
                source_id = f"{base}-{suffix}"
                suffix += 1
            seen_ids.add(source_id)
            if all(r.id != region_id for r in regions):
                center, zoom = _viewport(region_id)
                regions.append(
                    RegionMeta(
                        id=region_id, title=_region_title(heading), center=center, zoom=zoom
                    )
                )
            sources.append(
                DataSource(
                    id=source_id,
                    name=pending["name"],
                    description=pending.get("description", ""),
                    url=pending["url"],
                    region=region_id,
                    group=group,
                )
            )
        pending = None

    for line in text.splitlines():
        if h2 := _H2_RE.match(line):
            flush_pending()
            heading = h2.group("title")
            group = ""
        elif h3 := _H3_RE.match(line):
            flush_pending()
            group = h3.group("title")
        elif name := _SOURCE_NAME_RE.match(line):
            flush_pending()
            pending = {"name": name.group("name")}
        elif pending is not None and (field := _FIELD_RE.match(line)):
            key = field.group("field").strip().lower()
            value = field.group("value")
            if key == "description":
                pending["description"] = value.replace("*", "")
            elif key == "endpoint":
                link = _LINK_RE.search(value)
                pending["url"] = link.group("url") if link else value
    flush_pending()

    return regions, sources


def _fallback_regions() -> list[RegionMeta]:
    regions = []
    for region_id, title in _FALLBACK_REGION_TITLES.items():
        center, zoom = _viewport(region_id)
        regions.append(RegionMeta(id=region_id, title=title, center=center, zoom=zoom))
    return regions


def _load_catalog() -> tuple[list[RegionMeta], list[DataSource]]:
    try:
        text = Path(settings.sources_path).read_text(encoding="utf-8")
    except OSError:
        return _fallback_regions(), []
    regions, sources = parse_sources_md(text)
    return (regions, sources) if regions else (_fallback_regions(), [])


def list_regions() -> list[RegionMeta]:
    """All regions, parsed from SOURCES.md (with built-in fallbacks)."""
    return _load_catalog()[0]


def get_region(region_id: str) -> RegionMeta | None:
    return next((r for r in list_regions() if r.id == region_id), None)


def list_sources(region: str | None = None) -> list[DataSource]:
    """Data sources from SOURCES.md, optionally filtered to one region."""
    sources = _load_catalog()[1]
    if region is None:
        return sources
    return [s for s in sources if s.region == region]
