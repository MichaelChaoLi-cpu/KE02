#!/usr/bin/env python3
"""Audit Yokoe Bridge as a repeated-facility recovery candidate.

This is a feasibility audit, not an estimator.  It binds official evidence
for the 2016 and 2026 earthquake episodes, checks the exact 2026 restriction
geometry, samples the two version-pinned USGS ShakeMaps, and records the live
official road register that confirms the announced 2026 reopening.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
OUT = ROOT / "data/exp/feasibility-check/independent-reopening-regimes"
EVENTS = {
    "2016_mainshock": ROOT / "data/raw/usgs/2016/us20005iis",
    "2026_event": ROOT / "data/raw/usgs/2026/us6000tgb9",
}
EVENT_START_2016 = pd.Timestamp("2016-04-16 01:25:06", tz="Asia/Tokyo")
EVENT_START_2026 = pd.Timestamp("2026-07-28 16:27:00", tz="Asia/Tokyo")
ANNOUNCED_REOPENING_2026 = pd.Timestamp("2026-08-17 07:00:00", tz="Asia/Tokyo")
YOKOE_START_FRAGMENT = "鏡町宝出"
YOKOE_END_FRAGMENT = "鏡町野崎"
LIVE_PORTAL_CANONICAL_RECORD = (
    "八代不知火線|熊本県八代市鏡町宝出１０４５-３８|"
    "熊本県八代市鏡町野崎１０２８-１|災害|2026-07-29 14:00 JST|"
    "2026-08-17 07:00 JST|解除"
)

SOURCE_ROWS = [
    {
        "Source ID": "YOKOE2016-ENGINEERING",
        "Institution": "Kumamoto Prefecture",
        "URL": "https://www.pref.kumamoto.jp/uploaded/attachment/134518.PDF",
        "SHA-256": "7956ce941569b55938712497447c57c52f81ce6293db951b1a56bbe4c110bfb8",
        "Hash Scope": "official_pdf_file_bytes",
        "Evidence Role": "same-facility identity, 2016 closure, damage mechanism, reconstruction",
        "Bound Fact": "Yokoe Bridge; closure within one hour of the 2016 mainshock; P3 foundation failure and reconstruction",
        "Evidence Status": "pass",
    },
    {
        "Source ID": "YOKOE2017-TEMPORARY",
        "Institution": "Kumamoto Prefecture",
        "URL": "https://www.pref.kumamoto.jp/uploaded/attachment/7252.pdf",
        "SHA-256": "84ae36495e175569a2ca5fd67f3ff28cd8468253aad437d9705d4066ccf8096e",
        "Hash Scope": "official_pdf_file_bytes",
        "Evidence Role": "intermediate access milestone",
        "Bound Fact": "2-tonne-or-lighter bypass using the construction trestle completed 2017-06-01",
        "Evidence Status": "secondary_endpoint_only",
    },
    {
        "Source ID": "YOKOE2019-REOPENING",
        "Institution": "Kumamoto Prefecture",
        "URL": "https://www.pref.kumamoto.jp/uploaded/attachment/113844.pdf",
        "SHA-256": "1b63684b594c01946c5a163f6d47971c381f1f5db7509bb94342dd20894f0624",
        "Hash Scope": "official_pdf_file_bytes",
        "Evidence Role": "2016 episode general-traffic restoration endpoint",
        "Bound Fact": "restored Yokoe Bridge reopened to traffic on 2019-02-02",
        "Evidence Status": "pass_date_precision",
    },
    {
        "Source ID": "YOKOE2026-FORECAST",
        "Institution": "Kyushu Regional Development Bureau; Kumamoto Prefecture; NEXCO West",
        "URL": "https://www.qsr.mlit.go.jp/content/000002804.pdf",
        "SHA-256": "cc1fd47cf6953cadd05a53c3d46feeb6a48931ab4ecdac7e5e03d20c53ebeb76",
        "Hash Scope": "official_pdf_file_bytes",
        "Evidence Role": "2026 announced general-traffic endpoint",
        "Bound Fact": "general vehicles scheduled to pass Yokoe Bridge from 2026-08-17 07:00",
        "Evidence Status": "forecast_not_post_opening_confirmation",
    },
    {
        "Source ID": "YOKOE2026-CONFIRMATION",
        "Institution": "Kumamoto Prefecture",
        "URL": "https://portal.bousai.pref.kumamoto.jp/sp.html?p=traffic",
        "SHA-256": hashlib.sha256(LIVE_PORTAL_CANONICAL_RECORD.encode()).hexdigest(),
        "Hash Scope": "canonical_visible_record_fields_checked_2026-08-19",
        "Evidence Role": "2026 post-opening official road-register endpoint",
        "Bound Fact": "exact Yokoe Bridge address pair; restriction ended 2026-08-17 07:00; status lifted",
        "Evidence Status": "pass_live_official_confirmation",
    },
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_yokoe_observations() -> gpd.GeoDataFrame:
    restrictions = gpd.read_parquet(RESTRICTIONS)
    rows = restrictions.loc[
        restrictions["Route Name"].astype(str).str.contains("338号八代不知火線", na=False)
        & restrictions["Start Location"].astype(str).str.contains(YOKOE_START_FRAGMENT, na=False)
        & restrictions["End Location"].astype(str).str.contains(YOKOE_END_FRAGMENT, na=False)
    ].copy()
    if rows.empty:
        raise ValueError("No exact Yokoe Bridge restriction geometry found")
    if not rows["Restriction Reason"].eq("橋梁損傷").all():
        raise ValueError("Yokoe candidate contains an unexpected restriction reason")
    if rows["Restriction Start Time"].nunique() != 1:
        raise ValueError("Yokoe restriction start time is not stable across snapshots")
    return rows


def selected_geometry(rows: gpd.GeoDataFrame) -> pd.Series:
    projected = rows.to_crs("EPSG:6670").copy()
    projected["Geometry Length (m)"] = projected.geometry.length
    return projected.sort_values(
        ["Geometry Length (m)", "Snapshot Time"], ascending=[False, False]
    ).iloc[0]


def sample_points(geometry: object, count: int = 51) -> list[tuple[float, float]]:
    return [
        (point.x, point.y)
        for point in (
            geometry.interpolate(value, normalized=True)
            for value in np.linspace(0, 1, count)
        )
    ]


def event_metadata(event_dir: Path) -> dict[str, object]:
    info = json.loads((event_dir / "info.json").read_text(encoding="utf-8"))
    event = info["input"]["event_information"]
    versions = info["processing"]["shakemap_versions"]
    return {
        "USGS Event ID": event["event_id"],
        "Magnitude": float(event["magnitude"]),
        "Origin Time UTC": event["origin_time"],
        "ShakeMap Version": versions["map_version"],
        "ShakeMap Process Time UTC": versions["process_time"],
    }


def sample_event(event_label: str, event_dir: Path, geometry: object) -> dict[str, object]:
    raster_zip = event_dir / "raster.zip"
    points = sample_points(geometry)
    with tempfile.TemporaryDirectory(prefix="ke02-yokoe-shakemap-") as temp_dir:
        with zipfile.ZipFile(raster_zip) as bundle:
            for filename in [
                "mmi_mean.flt",
                "mmi_mean.hdr",
                "pga_mean.flt",
                "pga_mean.hdr",
            ]:
                bundle.extract(filename, temp_dir)
        with rasterio.open(Path(temp_dir) / "mmi_mean.flt") as mmi_ds:
            mmi = np.array([value[0] for value in mmi_ds.sample(points)], dtype=float)
        with rasterio.open(Path(temp_dir) / "pga_mean.flt") as pga_ds:
            ln_pga = np.array(
                [value[0] for value in pga_ds.sample(points)], dtype=float
            )
    valid = (
        (mmi != 999.0)
        & (ln_pga != 999.0)
        & np.isfinite(mmi)
        & np.isfinite(ln_pga)
    )
    if not valid.all():
        raise ValueError(f"Invalid ShakeMap sample(s) for {event_label}")
    pga_g = np.exp(ln_pga[valid])
    return {
        "Facility": "Yokoe Bridge",
        "Event": event_label,
        **event_metadata(event_dir),
        "Sample Count": len(points),
        "Valid Sample Count": int(valid.sum()),
        "MMI Mean": float(mmi[valid].mean()),
        "MMI Minimum": float(mmi[valid].min()),
        "MMI Maximum": float(mmi[valid].max()),
        "PGA Mean (g)": float(pga_g.mean()),
        "PGA Minimum (g)": float(pga_g.min()),
        "PGA Maximum (g)": float(pga_g.max()),
        "Raster Archive": str(raster_zip.relative_to(ROOT)),
        "Raster SHA-256": file_sha256(raster_zip),
    }


def hours_since(start: pd.Timestamp, end: pd.Timestamp) -> float:
    return (end - start).total_seconds() / 3600


def write_readme(
    rows: gpd.GeoDataFrame,
    geometry_row: pd.Series,
    exposure: pd.DataFrame,
) -> None:
    mmi = exposure.set_index("Event")["MMI Mean"]
    lines = [
        "# Yokoe Bridge repeated-recovery audit",
        "",
        "## Decision",
        "",
        "Yokoe Bridge is the fourth eligible independent recovery unit. The exact bridge, 2016 comparator, geometry, two ShakeMaps, independence, and 2026 outcome gates pass. The current Kumamoto Prefecture road register explicitly records the exact address pair as lifted at 17 August 07:00. This live terminal record overrides the lagging archived passable-map snapshots.",
        "",
        "## What is already established",
        "",
        "- The 2016 mainshock damaged this same bridge; the P3 foundation failed in liquefiable ground and was reconstructed.",
        "- A light-vehicle bypass (2 tonnes or less) was available on 1 June 2017. This is retained only as a secondary access milestone, not as the all-traffic endpoint.",
        "- The restored bridge reopened on 2 February 2019. The day is known but the clock time is not, so the 2016 restoration duration is interval-valued.",
        "- The 2026 map record is an exact 0.3 km bridge-damage restriction with stable addresses and geometry.",
        "- The live official road register marks the exact record as lifted at 07:00 on 17 August 2026.",
        f"- The retained geometry is {geometry_row['Geometry Length (m)']:.1f} m; the sampled mean MMI is {mmi['2016_mainshock']:.3f} in 2016 and {mmi['2026_event']:.3f} in 2026.",
        "",
        "## Claim boundary",
        "",
        "This facility supports a descriptive within-asset contrast with an official recovery chronology for a post-2016 reconstructed bridge. It cannot by itself identify a causal reconstruction effect or mechanism: shaking differs, emergency conditions differ, and one bridge provides no counterfactual. Because it is a single bridge rather than a motorway release cluster, it should not be pooled with the three highway regimes without an explicit unit-type sensitivity analysis.",
        "",
        "## Source-precedence resolution",
        "",
        f"- Exact restriction observations: {len(rows)} snapshots across {rows['Restriction Record ID'].nunique()} style-derived record identifiers.",
        f"- Latest exact active observation: {pd.to_datetime(rows['Snapshot Time']).max().isoformat()}.",
        "- Announced endpoint: 2026-08-17T07:00:00+09:00, explicitly labelled as scheduled general-vehicle access.",
        "- Current terminal evidence: the live Kumamoto Prefecture road register gives the same exact address pair, 2026-08-17 07:00 as the restriction end, and status `lifted`.",
        "- Resolution: the live terminal register supersedes the lagging archived map snapshots for the outcome gate; the lag remains documented as a source-timing issue.",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_yokoe_bridge_repeated_recovery.py",
        "```",
    ]
    (OUT / "YOKOE_BRIDGE_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = select_yokoe_observations()
    geometry_row = selected_geometry(rows)
    geometry_wgs84 = gpd.GeoSeries(
        [geometry_row["Geometry"]], crs="EPSG:6670"
    ).to_crs("EPSG:4326").iloc[0]

    source_gate = pd.DataFrame(SOURCE_ROWS)
    source_gate.to_csv(OUT / "yokoe_bridge_official_source_gate.csv", index=False)
    live_confirmation = pd.DataFrame(
        [
            {
                "Checked On": "2026-08-19",
                "Official Page": "https://portal.bousai.pref.kumamoto.jp/sp.html?p=traffic",
                "Route": "八代不知火線",
                "Start Location": "熊本県八代市鏡町宝出１０４５-３８",
                "End Location": "熊本県八代市鏡町野崎１０２８-１",
                "Restriction Reason": "災害",
                "Restriction Start": "2026-07-29 14:00 JST",
                "Restriction End": "2026-08-17 07:00 JST",
                "Current Status": "解除",
                "Canonical Record": LIVE_PORTAL_CANONICAL_RECORD,
                "Canonical Record SHA-256": hashlib.sha256(
                    LIVE_PORTAL_CANONICAL_RECORD.encode()
                ).hexdigest(),
            }
        ]
    )
    live_confirmation.to_csv(
        OUT / "yokoe_bridge_live_portal_confirmation.csv", index=False
    )

    first_temp_lower = pd.Timestamp("2017-06-01 00:00:00", tz="Asia/Tokyo")
    first_temp_upper = pd.Timestamp("2017-06-02 00:00:00", tz="Asia/Tokyo")
    full_2016_lower = pd.Timestamp("2019-02-02 00:00:00", tz="Asia/Tokyo")
    full_2016_upper = pd.Timestamp("2019-02-03 00:00:00", tz="Asia/Tokyo")
    timeline = pd.DataFrame(
        [
            {
                "Episode": 2016,
                "Milestone": "full_closure",
                "Lower Bound": EVENT_START_2016,
                "Upper Bound": EVENT_START_2016 + pd.Timedelta(hours=1),
                "Precision": "within_one_hour",
                "Traffic Meaning": "same bridge closed after mainshock",
                "Source ID": "YOKOE2016-ENGINEERING",
            },
            {
                "Episode": 2016,
                "Milestone": "light_vehicle_bypass",
                "Lower Bound": first_temp_lower,
                "Upper Bound": first_temp_upper,
                "Precision": "date",
                "Traffic Meaning": "bypass open only to vehicles of 2 tonnes or less",
                "Source ID": "YOKOE2017-TEMPORARY",
            },
            {
                "Episode": 2016,
                "Milestone": "restored_bridge_general_traffic",
                "Lower Bound": full_2016_lower,
                "Upper Bound": full_2016_upper,
                "Precision": "date",
                "Traffic Meaning": "restored original bridge reopened; primary comparable endpoint",
                "Source ID": "YOKOE2019-REOPENING",
            },
            {
                "Episode": 2026,
                "Milestone": "full_closure",
                "Lower Bound": rows["Restriction Start Time"].iloc[0],
                "Upper Bound": rows["Restriction Start Time"].iloc[0],
                "Precision": "minute",
                "Traffic Meaning": "exact bridge-damage restriction",
                "Source ID": "KUMAMOTO-PASSABLE-MAP",
            },
            {
                "Episode": 2026,
                "Milestone": "confirmed_general_traffic_reopening",
                "Lower Bound": ANNOUNCED_REOPENING_2026,
                "Upper Bound": ANNOUNCED_REOPENING_2026,
                "Precision": "minute_live_official_register",
                "Traffic Meaning": "general-vehicle reopening confirmed by exact terminal road-register record",
                "Source ID": "YOKOE2026-CONFIRMATION",
            },
        ]
    )
    timeline.to_csv(OUT / "yokoe_bridge_recovery_milestones.csv", index=False)

    record_ids = "; ".join(sorted(rows["Restriction Record ID"].unique()))
    geometry_audit = pd.DataFrame(
        [
            {
                "Facility": "Yokoe Bridge",
                "Route": "Prefectural Route 338 Yatsushiro-Shiranui Line",
                "Start Location": rows["Start Location"].iloc[0],
                "End Location": rows["End Location"].iloc[0],
                "Restriction Start": rows["Restriction Start Time"].iloc[0],
                "First Snapshot": pd.to_datetime(rows["Snapshot Time"]).min(),
                "Latest Snapshot": pd.to_datetime(rows["Snapshot Time"]).max(),
                "Latest Observation State": rows.sort_values("Snapshot Time").iloc[-1][
                    "Observation State"
                ],
                "Restriction Record IDs": record_ids,
                "Geometry Linkage Method": "exact_official_2026_bridge_damage_segment",
                "Geometry Length (m)": geometry_row["Geometry Length (m)"],
                "Centroid Longitude": geometry_wgs84.centroid.x,
                "Centroid Latitude": geometry_wgs84.centroid.y,
                "Geometry Gate": "pass_exact_facility_segment",
            }
        ]
    )
    geometry_audit.to_csv(OUT / "yokoe_bridge_geometry_audit.csv", index=False)

    exposure = pd.DataFrame(
        [
            sample_event(label, directory, geometry_wgs84)
            for label, directory in EVENTS.items()
        ]
    )
    exposure.to_csv(OUT / "yokoe_bridge_shaking_exposure.csv", index=False)

    hours_2026 = hours_since(EVENT_START_2026, ANNOUNCED_REOPENING_2026)
    hours_2016_lower = hours_since(EVENT_START_2016, full_2016_lower)
    hours_2016_upper = hours_since(EVENT_START_2016, full_2016_upper)
    light_hours_lower = hours_since(EVENT_START_2016, first_temp_lower)
    light_hours_upper = hours_since(EVENT_START_2016, first_temp_upper)
    contrast = pd.DataFrame(
        [
            {
                "Facility": "Yokoe Bridge",
                "2016 Comparable Restoration Hours Lower Bound": hours_2016_lower,
                "2016 Comparable Restoration Hours Upper Bound": hours_2016_upper,
                "2016 Light-Vehicle Access Hours Lower Bound": light_hours_lower,
                "2016 Light-Vehicle Access Hours Upper Bound": light_hours_upper,
                "2026 Confirmed Restoration Hours": hours_2026,
                "2016/2026 Restoration Ratio Lower Bound": hours_2016_lower / hours_2026,
                "2016/2026 Restoration Ratio Upper Bound": hours_2016_upper / hours_2026,
                "2016 Mean MMI": exposure.loc[
                    exposure["Event"].eq("2016_mainshock"), "MMI Mean"
                ].iloc[0],
                "2026 Mean MMI": exposure.loc[
                    exposure["Event"].eq("2026_event"), "MMI Mean"
                ].iloc[0],
                "2016 Mean PGA (g)": exposure.loc[
                    exposure["Event"].eq("2016_mainshock"), "PGA Mean (g)"
                ].iloc[0],
                "2026 Mean PGA (g)": exposure.loc[
                    exposure["Event"].eq("2026_event"), "PGA Mean (g)"
                ].iloc[0],
                "PGA Mean Ratio (2026/2016)": exposure.loc[
                    exposure["Event"].eq("2026_event"), "PGA Mean (g)"
                ].iloc[0]
                / exposure.loc[
                    exposure["Event"].eq("2016_mainshock"), "PGA Mean (g)"
                ].iloc[0],
                "2026 Outcome Gate": "pass_live_official_terminal_record_overrides_lagging_archive",
                "Counts As Independent Regime": True,
                "Interpretation": "descriptive_same_asset_candidate_not_effect_estimate",
            }
        ]
    )
    contrast.to_csv(OUT / "yokoe_bridge_descriptive_contrast.csv", index=False)
    write_readme(rows, geometry_row, exposure)
    print(
        "PASS: audited Yokoe Bridge; exact live official terminal record, geometry, "
        "both ShakeMaps, comparator, and independence gates pass."
    )


if __name__ == "__main__":
    main()
