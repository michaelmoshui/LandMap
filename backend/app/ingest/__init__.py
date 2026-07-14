"""Ingestion scripts that pull real data from the open-data portals.

Each region gets a module (currently ``app.ingest.gva``) whose ``main()``
fetches from the portals listed in SOURCES.md and writes GeoJSON snapshots
under ``app/data/<region>/``. The layer service serves those snapshots when
present (see ``app.services.layers``), so ingestion runs offline/one-shot and
the API never depends on third-party uptime.
"""
