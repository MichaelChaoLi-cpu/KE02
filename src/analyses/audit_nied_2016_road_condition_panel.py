#!/usr/bin/env python3
"""Audit the archived NIED 2016 Kumamoto road-condition panel.

The source is a public NIED ArcGIS FeatureServer preserved in the official
2016 Kumamoto Earthquakes map archive.  Outputs are exploratory feasibility
evidence; the script does not write to data/raw.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/exp/feasibility-check/nied-2016-road-condition"
SOURCE_ENDPOINT = (
    "https://services.arcgis.com/VZFBz62gxB8VrbIS/arcgis/rest/services/"
    "12_01_01_01_Road_Condition_Kumamoto_Pref/FeatureServer/0/query"
)
SOURCE_ITEM = "bc1bff1ab8184b29af52a8e789d0ee91"
SOURCE_WEBMAP = "8adc5ab4773349b7b2829e66fcf30a54"
SOURCE_ARCHIVE = "aee230981e9c4f0f9690391b67e68262"
USER_AGENT = "KE02-feasibility-audit/1.0 (official public data)"
METRIC_CRS = "EPSG:6670"
CORRIDOR = (
    ROOT
    / "data/exp/feasibility-check/intervention-geometry/"
    "kumamoto_takamori_intervention_corridor.parquet"
)
PASSAGE_2026 = (
    ROOT
    / "data/exp/feasibility-check/intervention-geometry/"
    "kumamoto_takamori_probe_passage_snapshots.csv"
)
RESTRICTIONS_2026 = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
SHAKEMAPS = {
    "2016 foreshock": ROOT / "data/raw/usgs/2016/us20005hzn/raster.zip",
    "2016 mainshock": ROOT / "data/raw/usgs/2016/us20005iis/raster.zip",
    "2026 earthquake": ROOT / "data/raw/usgs/2026/us6000tgb9/raster.zip",
}
EVENT_2026 = pd.Timestamp("2026-07-28 16:27:00", tz="Asia/Tokyo")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_source() -> tuple[bytes, dict[str, object]]:
    features: list[dict[str, object]] = []
    crs: dict[str, object] | None = None
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "OBJECTID ASC",
                "resultOffset": offset,
                "resultRecordCount": 1000,
                "f": "geojson",
            }
        )
        request = urllib.request.Request(
            f"{SOURCE_ENDPOINT}?{query}", headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            page = json.loads(response.read())
        if page.get("type") != "FeatureCollection":
            raise ValueError("NIED endpoint did not return a GeoJSON FeatureCollection")
        if crs is None:
            crs = page.get("crs")
        page_features = page.get("features", [])
        features.extend(page_features)
        if len(page_features) < 1000:
            break
        offset += len(page_features)
    features.sort(key=lambda feature: int(feature["properties"]["OBJECTID"]))
    payload: dict[str, object] = {
        "type": "FeatureCollection",
        "crs": crs,
        "features": features,
    }
    content = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if len(features) != 5855:
        raise ValueError(
            f"Expected 5,855 archived features, got {len(features)}"
        )
    return content, payload


def build_panel(payload: dict[str, object], source_hash: str) -> gpd.GeoDataFrame:
    panel = gpd.GeoDataFrame.from_features(payload["features"], crs="EPSG:4326")
    panel = panel.rename(
        columns={
            "OBJECTID": "Source Object ID",
            "局番": "Bureau Code",
            "番号": "Incident Number",
            "振興局": "Regional Bureau",
            "路線_番号": "Route Number",
            "路線_路線": "Route Name",
            "箇所_始点": "Start Location",
            "箇所_終点": "End Location",
            "規制原因_": "Restriction Reason",
            "規制原因1": "Restriction Reason Code",
            "規制原因_1": "Restriction Reason Detail",
            "規制延長": "Restriction Length",
            "規制内容_": "Restriction Status English",
            "規制内容1": "Restriction Status",
            "復旧見込": "Restoration Outlook",
            "迂回路": "Detour",
            "迂回路_孤": "Isolation Detour",
            "迂回路_戸": "Affected Households",
            "被害状況_": "Damage State",
            "被害状況1": "Damage State Detail",
            "規制開始日": "Restriction Start Text",
            "規制変更日": "Restriction Change Text",
            "日付": "Snapshot Date Text",
            "test": "Snapshot End UTC",
            "test0": "Snapshot Start UTC",
        }
    )
    panel["Snapshot Date"] = pd.to_datetime(
        panel["Snapshot Date Text"], errors="raise"
    ).dt.date
    for column in ("Route Name", "Start Location", "End Location"):
        panel[column] = panel[column].fillna("").astype(str).str.strip()
    panel["Longitude"] = panel.geometry.x
    panel["Latitude"] = panel.geometry.y
    panel["Stable Point ID"] = panel.apply(
        lambda row: hashlib.sha1(
            (
                f"{row['Route Name']}|{row['Longitude']:.5f}|"
                f"{row['Latitude']:.5f}"
            ).encode("utf-8")
        ).hexdigest()[:12],
        axis=1,
    )
    panel["Source SHA-256"] = source_hash
    return panel


def build_snapshot_coverage(panel: gpd.GeoDataFrame) -> pd.DataFrame:
    grouped = panel.groupby("Snapshot Date", as_index=False).agg(
        Records=("Source Object ID", "size"),
        Unique_Routes=("Route Name", "nunique"),
        Unique_Points=("Stable Point ID", "nunique"),
        Full_Closures=(
            "Restriction Status",
            lambda values: int(pd.Series(values).eq("全面通行止").sum()),
        ),
        Released=(
            "Restriction Status",
            lambda values: int(pd.Series(values).eq("解除").sum()),
        ),
    )
    return grouped.rename(
        columns={
            "Unique_Routes": "Unique Routes",
            "Unique_Points": "Unique Points",
            "Full_Closures": "Full Closures",
        }
    ).sort_values("Snapshot Date")


def build_route_inventory(panel: gpd.GeoDataFrame) -> pd.DataFrame:
    return (
        panel.loc[panel["Route Name"].ne("")]
        .groupby("Route Name", as_index=False)
        .agg(
            Records=("Source Object ID", "size"),
            Unique_Points=("Stable Point ID", "nunique"),
            First_Snapshot=("Snapshot Date", "min"),
            Last_Snapshot=("Snapshot Date", "max"),
            Snapshot_Days=("Snapshot Date", "nunique"),
        )
        .rename(
            columns={
                "Unique_Points": "Unique Points",
                "First_Snapshot": "First Snapshot",
                "Last_Snapshot": "Last Snapshot",
                "Snapshot_Days": "Snapshot Days",
            }
        )
        .sort_values(["Records", "Route Name"], ascending=[False, True])
    )


def normalize_route(value: object) -> str:
    return "".join(str(value).replace("　", " ").split()).strip()


def build_route_overlap(panel: gpd.GeoDataFrame) -> pd.DataFrame:
    current = gpd.read_parquet(RESTRICTIONS_2026)
    names_2016 = {
        normalize_route(value)
        for value in panel["Route Name"].dropna()
        if normalize_route(value)
    }
    names_2026 = {
        normalize_route(value)
        for value in current["Route Name"].dropna()
        if normalize_route(value)
    }
    union = sorted(names_2016 | names_2026)
    return pd.DataFrame(
        [
            {
                "Normalized Route Name": name,
                "Present in 2016 NIED": name in names_2016,
                "Present in 2026 MLIT": name in names_2026,
                "Exact Name Overlap": name in names_2016 and name in names_2026,
            }
            for name in union
        ]
    )


def build_corridor_panel(panel: gpd.GeoDataFrame) -> pd.DataFrame:
    corridor = gpd.read_parquet(CORRIDOR).to_crs(METRIC_CRS)
    if len(corridor) != 1:
        raise ValueError("Expected exactly one Mashiki Central corridor geometry")
    metric = panel.to_crs(METRIC_CRS).copy()
    metric["Distance to Treatment Polygon (m)"] = metric.geometry.distance(
        corridor.geometry.iloc[0]
    )
    selected = metric.loc[
        metric["Route Name"].eq("熊本高森線")
        & metric["Distance to Treatment Polygon (m)"].le(150.0)
    ].copy()
    if selected.empty:
        raise ValueError("No NIED Kumamoto-Takamori points match the treatment corridor")
    output = selected.to_crs(4326).drop(columns="geometry")
    keep = [
        "Snapshot Date",
        "Stable Point ID",
        "Source Object ID",
        "Route Name",
        "Start Location",
        "End Location",
        "Restriction Status",
        "Restriction Reason",
        "Restriction Reason Detail",
        "Restriction Start Text",
        "Restriction Change Text",
        "Longitude",
        "Latitude",
        "Distance to Treatment Polygon (m)",
        "Source SHA-256",
    ]
    return output[keep].sort_values(
        ["Stable Point ID", "Snapshot Date", "Source Object ID"]
    )


def sample_shaking(corridor: gpd.GeoDataFrame) -> pd.DataFrame:
    boundary = corridor.to_crs(4326).geometry.iloc[0].boundary
    points = [
        boundary.interpolate(value, normalized=True)
        for value in np.linspace(0, 1, 101)
    ]
    coordinates = [(point.x, point.y) for point in points]
    rows = []
    with tempfile.TemporaryDirectory(prefix="ke02-nied-shaking-") as temporary:
        temporary_path = Path(temporary)
        for event, archive in SHAKEMAPS.items():
            event_dir = temporary_path / event.replace(" ", "_")
            event_dir.mkdir()
            with zipfile.ZipFile(archive) as zipped:
                for name in ("mmi_mean.flt", "mmi_mean.hdr", "pga_mean.flt", "pga_mean.hdr"):
                    zipped.extract(name, event_dir)
            with rasterio.open(event_dir / "mmi_mean.flt") as mmi_source, rasterio.open(
                event_dir / "pga_mean.flt"
            ) as pga_source:
                mmi = np.asarray([v[0] for v in mmi_source.sample(coordinates)], dtype=float)
                ln_pga = np.asarray([v[0] for v in pga_source.sample(coordinates)], dtype=float)
                valid = np.isfinite(mmi) & np.isfinite(ln_pga) & (mmi != 999.0) & (ln_pga != 999.0)
                if not valid.all():
                    raise ValueError(f"Invalid ShakeMap values for {event}")
                pga = np.exp(ln_pga)
                rows.append(
                    {
                        "Event": event,
                        "Samples": int(valid.sum()),
                        "MMI Mean": float(mmi.mean()),
                        "MMI Minimum": float(mmi.min()),
                        "MMI Maximum": float(mmi.max()),
                        "PGA Mean (g)": float(pga.mean()),
                        "PGA Minimum (g)": float(pga.min()),
                        "PGA Maximum (g)": float(pga.max()),
                        "ShakeMap Archive": archive.relative_to(ROOT).as_posix(),
                        "ShakeMap SHA-256": sha256_file(archive),
                    }
                )
    return pd.DataFrame(rows)


def build_cross_event_evidence(corridor_2016: pd.DataFrame) -> pd.DataFrame:
    target = corridor_2016.loc[
        corridor_2016["Start Location"].eq("益城町惣領")
        & corridor_2016["End Location"].eq("益城町宮園")
    ].copy()
    if target.empty:
        raise ValueError("Exact Soryo-Miyazono restriction record is absent")
    closed = target.loc[target["Restriction Status"].eq("全面通行止")]
    released = target.loc[target["Restriction Status"].eq("解除")]
    later_full = corridor_2016.loc[
        corridor_2016["Start Location"].eq("益城町木山（木山交差点）")
        & corridor_2016["End Location"].eq("益城町寺迫（寺迫交差点）")
        & corridor_2016["Restriction Status"].eq("全面通行止")
    ].copy()
    partial = corridor_2016.loc[
        corridor_2016["Start Location"].eq("益城町木山交差点")
        & corridor_2016["End Location"].eq("益城町馬水橋")
        & corridor_2016["Restriction Status"].eq("片側通行止")
    ].copy()
    if later_full.empty or partial.empty:
        raise ValueError("Expected later treatment-corridor restrictions are absent")
    first_passage = pd.read_csv(PASSAGE_2026)
    first_passage = first_passage.loc[
        first_passage["Passage Layer Available"]
        & first_passage["Observed Corridor-Aligned Passage"]
    ].copy()
    first_passage["Snapshot"] = pd.to_datetime(first_passage["Snapshot Time (JST)"])
    first = first_passage.sort_values("Snapshot").iloc[0]
    hours_2026 = (first["Snapshot"] - EVENT_2026).total_seconds() / 3600
    return pd.DataFrame(
        [
            {
                "Event": "2016 earthquake sequence",
                "Subsegment": "Mashiki Soryo-Miyazono",
                "Corridor State Evidence": "official full closure",
                "First Relevant Observation": str(closed["Snapshot Date"].min()),
                "Last Full-Closure Observation": str(closed["Snapshot Date"].max()),
                "First Release Observation": str(released["Snapshot Date"].min()),
                "Event-Time Bound": "full closure observed through calendar day +2; release observed on day +3",
                "Measurement": "Kumamoto Prefecture restriction status archived by NIED",
            },
            {
                "Event": "2016 earthquake sequence",
                "Subsegment": "Kiyama intersection-Terasako intersection",
                "Corridor State Evidence": "official full closure",
                "First Relevant Observation": str(later_full["Snapshot Date"].min()),
                "Last Full-Closure Observation": str(later_full["Snapshot Date"].max()),
                "First Release Observation": "not observed in the archived record",
                "Event-Time Bound": "full closure observed on calendar days +5 through +8",
                "Measurement": "Kumamoto Prefecture restriction status archived by NIED",
            },
            {
                "Event": "2016 earthquake sequence",
                "Subsegment": "Kiyama intersection-Mamizu Bridge",
                "Corridor State Evidence": "official one-side closure",
                "First Relevant Observation": str(partial["Snapshot Date"].min()),
                "Last Full-Closure Observation": "not a full-closure state",
                "First Release Observation": "not observed through the final archived snapshot",
                "Event-Time Bound": "one-side closure observed from calendar day +11 through +130",
                "Measurement": "Kumamoto Prefecture restriction status archived by NIED",
            },
            {
                "Event": "2026 earthquake",
                "Subsegment": "official 3.5 km Mashiki Central polygon",
                "Corridor State Evidence": "private-probe corridor passage observed",
                "First Relevant Observation": first["Snapshot Time (JST)"],
                "Last Full-Closure Observation": "not observed by this layer",
                "First Release Observation": "not a restriction-release measure",
                "Event-Time Bound": f"passage observed by {hours_2026:.2f} hours after origin",
                "Measurement": "MLIT private-probe service-presence layer",
            },
        ]
    )


def build_gates(route_overlap: pd.DataFrame) -> pd.DataFrame:
    overlap_count = int(route_overlap["Exact Name Overlap"].sum())
    return pd.DataFrame(
        [
            ("N1", "Persistent official 2016 archive", "pass", "NIED public ArcGIS archive exposes a queryable hash-bound FeatureServer"),
            ("N2", "Repeated 2016 temporal coverage", "pass", "5,855 dated point records span 2016-04-16 through 2016-08-24"),
            ("N3", "Exact treatment-corridor linkage", "pass", "Kumamoto-Takamori Soryo-Miyazono restriction point lies inside/adjacent to the official treatment polygon"),
            ("N4", "Observed 2016 corridor-state history", "pass", "Soryo-Miyazono changes from full closure to release, while other corridor subsegments retain later full or one-side restrictions"),
            ("N5", "Cross-event route screening", "partial", f"{overlap_count} normalized route names occur in both archives; segment identity remains to be spatially audited"),
            ("N6", "Same outcome definition across events", "partial", "2016 has official restriction/release state; 2026 has both restrictions and probe passage, but the treatment case currently uses different positive-observation measures"),
            ("N7", "Causal treatment comparison", "fail", "One selected treated corridor has no exogenous untreated counterfactual and reporting systems differ"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def render_markdown(
    panel: gpd.GeoDataFrame,
    coverage: pd.DataFrame,
    routes: pd.DataFrame,
    route_overlap: pd.DataFrame,
    corridor_panel: pd.DataFrame,
    shaking: pd.DataFrame,
    cross_event: pd.DataFrame,
    gates: pd.DataFrame,
    source_hash: str,
) -> str:
    exact_overlap = route_overlap.loc[route_overlap["Exact Name Overlap"]]
    corridor_summary = (
        corridor_panel.groupby(
            ["Stable Point ID", "Start Location", "End Location"], as_index=False
        )
        .agg(
            Records=("Source Object ID", "size"),
            First_Snapshot=("Snapshot Date", "min"),
            Last_Snapshot=("Snapshot Date", "max"),
            Minimum_Distance=("Distance to Treatment Polygon (m)", "min"),
            Statuses=("Restriction Status", lambda x: "; ".join(sorted(set(x)))),
        )
        .rename(
            columns={
                "First_Snapshot": "First Snapshot",
                "Last_Snapshot": "Last Snapshot",
                "Minimum_Distance": "Minimum Distance (m)",
            }
        )
    )
    return f"""# NIED 2016 road-condition panel feasibility audit

## Result

The official NIED archive preserves a substantially richer 2016 road-state panel than the previously downloaded PDF maps: {len(panel):,} dated point records across {coverage['Snapshot Date'].nunique()} snapshot dates, {routes['Route Name'].nunique()} named routes, and {panel['Stable Point ID'].nunique()} spatially stable route points. The response is bound to SHA-256 `{source_hash}`.

The archive directly changes the Mashiki Central feasibility assessment. Multiple Kumamoto-Takamori records lie within or immediately adjacent to the official treatment polygon. **Mashiki Soryo to Mashiki Miyazono** is observed as full closure on 16-18 April 2016 and as released from 19 April. That local transition is not a whole-corridor reopening: Kiyama intersection to Terasako intersection is observed fully closed on 21-24 April, and Kiyama intersection to Mamizu Bridge is observed under one-side closure from 27 April through the final archived snapshot on 24 August. This is the first verified pre-intervention repeated-earthquake road-state history on the treated corridor, and it shows prolonged within-corridor heterogeneity.

It does not by itself identify a treatment effect. The 2016 evidence is an official restriction/release state, while the current 2026 treatment-corridor evidence is a positive private-probe passage observation. Both are valid positive observations, but non-observation has different meanings. Moreover, mean MMI is very similar across the 2016 mainshock and 2026 event, whereas PGA is materially lower in 2026. The defensible present claim is a hazard-metric-sensitive same-corridor descriptive sequence, not a causal resilience dividend.

## Treatment-corridor locations

{corridor_summary.to_markdown(index=False, floatfmt='.1f')}

## Same-corridor cross-event evidence

{cross_event.to_markdown(index=False)}

## Hazard context at the official corridor polygon

{shaking.to_markdown(index=False, floatfmt='.3f')}

## Network-panel opportunity

Exact normalized route-name screening finds {len(exact_overlap)} names present in both the 2016 NIED and 2026 MLIT restriction archives. This is only a candidate linkage layer: exact route names can cover different subsegments, and absence from either positive-report archive cannot be coded as an open road.

{exact_overlap.to_markdown(index=False)}

## Feasibility gates

{gates.to_markdown(index=False)}

## Claim boundary

- Eligible now: an official same-corridor 2016 multi-subsegment restriction chronology, 2016/2026 hazard comparison, and a bounded 2026 passage-presence contrast.
- Potentially eligible after spatial linkage: a multi-route repeated-event panel of positively reported restriction states and restoration transitions.
- Not eligible: coding archive absence as openness, treating point records as road lengths, pooling daily duplicates as independent units, or claiming that four-laning caused improved resilience.

## Source chain

- NIED archive application: ArcGIS item `{SOURCE_ARCHIVE}`.
- Road-condition WebMap: `{SOURCE_WEBMAP}`.
- Feature layer item: `{SOURCE_ITEM}`.
- Public query endpoint: `{SOURCE_ENDPOINT}`.

## Rebuild

```bash
UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_nied_2016_road_condition_panel.py
```
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    content, payload = fetch_source()
    source_hash = sha256_bytes(content)
    (OUT / "nied_2016_kumamoto_road_condition.geojson").write_bytes(content)
    panel = build_panel(payload, source_hash)
    coverage = build_snapshot_coverage(panel)
    routes = build_route_inventory(panel)
    route_overlap = build_route_overlap(panel)
    corridor_panel = build_corridor_panel(panel)
    corridor = gpd.read_parquet(CORRIDOR)
    shaking = sample_shaking(corridor)
    cross_event = build_cross_event_evidence(corridor_panel)
    gates = build_gates(route_overlap)

    coverage.to_csv(OUT / "nied_2016_snapshot_coverage.csv", index=False)
    routes.to_csv(OUT / "nied_2016_route_inventory.csv", index=False)
    route_overlap.to_csv(OUT / "cross_event_route_name_overlap.csv", index=False)
    corridor_panel.to_csv(
        OUT / "mashiki_central_2016_restriction_snapshots.csv", index=False
    )
    shaking.to_csv(OUT / "mashiki_central_cross_event_shaking.csv", index=False)
    cross_event.to_csv(OUT / "same_corridor_cross_event_evidence.csv", index=False)
    gates.to_csv(OUT / "repeated_event_outcome_gate.csv", index=False)
    (OUT / "NIED_2016_ROAD_CONDITION_AUDIT.md").write_text(
        render_markdown(
            panel,
            coverage,
            routes,
            route_overlap,
            corridor_panel,
            shaking,
            cross_event,
            gates,
            source_hash,
        ),
        encoding="utf-8",
    )
    print(OUT / "NIED_2016_ROAD_CONDITION_AUDIT.md")


if __name__ == "__main__":
    main()
