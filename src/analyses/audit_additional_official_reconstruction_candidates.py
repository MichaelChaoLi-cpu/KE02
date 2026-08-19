#!/usr/bin/env python3
"""Audit official reconstruction candidates outside the Mashiki core.

The passage calculation is deliberately a proximity screen around a verified
2016 site point.  It does not substitute for exact current bridge or project
geometry and cannot turn a weaker 2026 exposure into a resilience test.
"""
from __future__ import annotations

import tempfile
import unicodedata
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from audit_kumamoto_takamori_probe_passage import (
    ARCHIVE_DIR,
    PASSAGE_MEMBER,
    parse_snapshot,
    read_geojson_member,
)


ROOT = Path(__file__).resolve().parents[2]
NIED = (
    ROOT
    / "data/exp/feasibility-check/nied-2016-road-condition/"
    "nied_2016_kumamoto_road_condition.geojson"
)
OUT = ROOT / "data/exp/feasibility-check/additional-reconstruction-candidates"
METRIC_CRS = 6670
SHAKEMAPS = {
    "2016 mainshock": ROOT / "data/raw/usgs/2016/us20005iis/raster.zip",
    "2026 earthquake": ROOT / "data/raw/usgs/2026/us6000tgb9/raster.zip",
}


CANDIDATES = {
    "NEW-ASO-BRIDGE": {
        "label": "New Aso Bridge functional replacement",
        "route_contains": "325",
        "end_contains": "阿蘇大橋",
        "end_excludes": "南阿蘇大橋",
        "passage_radius_m": 1000.0,
        "completion": "2021-03-07",
        "source": "https://www.qsr.mlit.go.jp/kumamoto_r/road_325.html",
        "geometry_boundary": "new bridge is officially located about 600 m downstream; exact current geometry remains required",
        "mechanism": "replacement alignment and bridge were explicitly designed for fault displacement, inspection, and rapid recovery",
    },
    "OHKIRIHATA-BRIDGE": {
        "label": "Ohkirihata Bridge repair",
        "route_contains": "熊本高森線",
        "end_contains": "大切畑橋",
        "end_excludes": "",
        "passage_radius_m": 500.0,
        "completion": "2019-09-14",
        "source": "https://www.qsr.mlit.go.jp/kumamoto_r/road_28.html",
        "geometry_boundary": "NIED names the bridge, but the 2026 evidence is only a proximity passage screen",
        "mechanism": "same named bridge was repaired as the terminal project in the Tawarayama route restoration",
    },
    "ROUTE57-TATENO": {
        "label": "National Route 57 Tateno restoration",
        "route_contains": "57",
        "start_contains": "立野",
        "end_contains": "",
        "end_excludes": "",
        "passage_radius_m": 500.0,
        "completion": "2020-10-03",
        "source": "https://www.qsr.mlit.go.jp/kumamoto_r/road_57.html",
        "geometry_boundary": "site point identifies the damaged Tateno record; exact restored slope segment remains required",
        "mechanism": "existing route reopened after slope and erosion-prevention works",
    },
}


def select_site(panel: gpd.GeoDataFrame, definition: dict[str, object]) -> tuple[gpd.GeoDataFrame, object]:
    route = panel["路線_路線"].fillna("").map(
        lambda value: unicodedata.normalize("NFKC", str(value))
    )
    start = panel["箇所_始点"].fillna("").map(
        lambda value: unicodedata.normalize("NFKC", str(value))
    )
    end = panel["箇所_終点"].fillna("").map(
        lambda value: unicodedata.normalize("NFKC", str(value))
    )
    mask = route.str.contains(
        str(definition["route_contains"]), regex=False
    )
    if definition.get("start_contains"):
        mask &= start.str.contains(
            str(definition["start_contains"]), regex=False
        )
    if definition.get("end_contains"):
        mask &= end.str.contains(
            str(definition["end_contains"]), regex=False
        )
    if definition.get("end_excludes"):
        mask &= ~end.str.contains(
            str(definition["end_excludes"]), regex=False
        )
    selected = panel.loc[mask].copy()
    if selected.empty:
        raise ValueError(f"No NIED records for {definition['label']}")
    selected["Geometry Key"] = selected.geometry.map(lambda value: value.wkb_hex)
    dominant_key = selected["Geometry Key"].value_counts().index[0]
    dominant = selected.loc[selected["Geometry Key"].eq(dominant_key)].copy()
    return dominant, dominant.geometry.iloc[0]


def passage_layers() -> list[tuple[pd.Timestamp, gpd.GeoDataFrame]]:
    layers = []
    for archive in sorted(ARCHIVE_DIR.glob("*data.zip")):
        snapshot = parse_snapshot(archive)
        if snapshot is None:
            continue
        with zipfile.ZipFile(archive) as zipped:
            if PASSAGE_MEMBER not in set(zipped.namelist()):
                continue
        layers.append(
            (snapshot, read_geojson_member(archive, PASSAGE_MEMBER).to_crs(METRIC_CRS))
        )
    return layers


def sample_shaking(point: object) -> dict[str, dict[str, float]]:
    coordinate = (point.x, point.y)
    result: dict[str, dict[str, float]] = {}
    with tempfile.TemporaryDirectory(prefix="ke02-extra-rebuild-shaking-") as temp:
        for event, archive in SHAKEMAPS.items():
            event_dir = Path(temp) / event.replace(" ", "_")
            event_dir.mkdir()
            with zipfile.ZipFile(archive) as zipped:
                for name in (
                    "mmi_mean.flt",
                    "mmi_mean.hdr",
                    "pga_mean.flt",
                    "pga_mean.hdr",
                ):
                    zipped.extract(name, event_dir)
            with rasterio.open(event_dir / "mmi_mean.flt") as mmi_source:
                mmi = float(next(mmi_source.sample([coordinate]))[0])
            with rasterio.open(event_dir / "pga_mean.flt") as pga_source:
                pga = float(np.exp(next(pga_source.sample([coordinate]))[0]))
            result[event] = {"mmi": mmi, "pga": pga}
    return result


def build_audit() -> pd.DataFrame:
    panel = gpd.read_file(NIED).to_crs(4326)
    layers = passage_layers()
    rows = []
    for candidate_id, definition in CANDIDATES.items():
        records, point = select_site(panel, definition)
        metric_point = gpd.GeoSeries([point], crs=4326).to_crs(METRIC_CRS).iloc[0]
        radius = float(definition["passage_radius_m"])
        positive_times = []
        nearest_distances = []
        for snapshot, passage in layers:
            distances = passage.geometry.distance(metric_point)
            nearest_distances.append(float(distances.min()))
            if distances.le(radius).any():
                positive_times.append(snapshot)
        exposure = sample_shaking(point)
        mmi_2016 = exposure["2016 mainshock"]["mmi"]
        mmi_2026 = exposure["2026 earthquake"]["mmi"]
        pga_2016 = exposure["2016 mainshock"]["pga"]
        pga_2026 = exposure["2026 earthquake"]["pga"]
        closed = records.loc[records["規制内容1"].eq("全面通行止")]
        rows.append(
            {
                "Candidate ID": candidate_id,
                "Candidate": definition["label"],
                "Official Completion": definition["completion"],
                "2016 NIED Records at Dominant Point": len(records),
                "2016 First Full-Closure Snapshot": pd.to_datetime(closed["日付"]).min().date(),
                "2016 Last Full-Closure Snapshot": pd.to_datetime(closed["日付"]).max().date(),
                "Passage Screen Radius (m)": radius,
                "2026 Available Passage Snapshots": len(layers),
                "2026 Positive Proximity Snapshots": len(positive_times),
                "2026 First Positive Proximity Snapshot": min(positive_times).isoformat() if positive_times else "",
                "Minimum 2026 Trace Distance (m)": min(nearest_distances),
                "2016 MMI": mmi_2016,
                "2026 MMI": mmi_2026,
                "MMI Difference (2026-2016)": mmi_2026 - mmi_2016,
                "2016 PGA (g)": pga_2016,
                "2026 PGA (g)": pga_2026,
                "PGA Ratio (2026/2016)": pga_2026 / pga_2016,
                "Hazard Direction": "2026 substantially weaker" if mmi_2026 < mmi_2016 - 1 else "other",
                "Geometry/Measurement Boundary": definition["geometry_boundary"],
                "Mechanism": definition["mechanism"],
                "Official Source": definition["source"],
                "Core Sample Status": "exclude_hazard_and_geometry_not_comparable",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit = build_audit()
    if not audit["2026 Positive Proximity Snapshots"].gt(0).all():
        raise ValueError("An official reconstruction candidate lacks positive passage proximity")
    if not audit["MMI Difference (2026-2016)"].lt(-1.0).all():
        raise ValueError("The substantially-weaker-2026 exposure gate has changed")
    audit.to_csv(OUT / "candidate_audit.csv", index=False)
    gates = pd.DataFrame(
        [
            ("A1", "Official reconstruction identity", "pass", "three projects have official completion and mechanism records"),
            ("A2", "2016 positive road-state history", "pass", "all three have named NIED full-closure records"),
            ("A3", "2026 positive passage proximity", "pass", "all three have at least one trace within the declared screening radius"),
            ("A4", "Exact common outcome geometry", "fail", "passage proximity is not an exact bridge or restored-segment outcome"),
            ("A5", "Comparable repeated shock", "fail", "2026 MMI is 1.6-2.3 units lower and PGA is only 20-30% of 2016"),
            ("A6", "Additional core natural-experiment unit", "fail", "none can enter the core estimator"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )
    gates.to_csv(OUT / "candidate_gate.csv", index=False)
    report = [
        "# Additional official reconstruction-candidate audit",
        "",
        "## Result",
        "",
        "New Aso Bridge, Ohkirihata Bridge, and the restored National Route 57 Tateno section all have an official post-2016 reconstruction record, a named 2016 NIED full-closure history, and positive 2026 probe passage near the site. None enters the core repeated-shock sample.",
        "",
        "The decisive failure is exposure comparability: the 2026 MMI is 1.6-2.3 units lower and the 2026 PGA is only about 20-30% of the 2016 value at these sites. Positive passage after the weaker event therefore cannot demonstrate a resilience dividend. In addition, the current passage evidence is proximity-based rather than exact asset-aligned geometry.",
        "",
        "These projects remain useful as mechanism or external-context cases. New Aso Bridge is especially valuable for explaining intentional fault-displacement and rapid-recovery design, but not as an additional natural-experiment observation.",
        "",
        "## Candidate audit",
        "",
        audit.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Gates",
        "",
        gates.to_markdown(index=False),
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_additional_official_reconstruction_candidates.py",
        "```",
    ]
    (OUT / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(OUT / "README.md")


if __name__ == "__main__":
    main()
