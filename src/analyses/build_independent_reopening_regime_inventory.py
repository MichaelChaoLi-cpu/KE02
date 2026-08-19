#!/usr/bin/env python3
"""Build the independent reopening-regime expansion inventory.

This is a feasibility asset, not an estimator. It separates named road
segments from independent 2026 reopening decisions, applies conservative
cross-event inclusion gates, and keeps right-censored candidates visible for
future official-source updates.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LINKAGE = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage"
OUT = ROOT / "data/exp/feasibility-check/independent-reopening-regimes"
RESTRICTIONS = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
CLUSTERS = LINKAGE / "reopening_cluster_pilot_contrasts.csv"
CONTRASTS = LINKAGE / "matched_corridor_pilot_contrasts.csv"
INTERVALS_2016 = LINKAGE / "mlit_2016_highway_closure_intervals.csv"
GEOMETRY_AUDIT = LINKAGE / "expanded_repeated_corridor_geometry_audit.csv"
YOKOE_GATE = OUT / "yokoe_bridge_descriptive_contrast.csv"
YOKOE_GEOMETRY = OUT / "yokoe_bridge_geometry_audit.csv"

EVENT_START_2026 = pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo")
SOURCE_CHECK_DATE = "2026-08-19"


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", "", text).replace("インターチェンジ", "IC")


def endpoint_pair(start: object, end: object) -> str:
    values = sorted([clean_text(start), clean_text(end)])
    return "|".join(values)


def semicolon(values: pd.Series) -> str:
    return "; ".join(sorted({str(value) for value in values if pd.notna(value) and str(value)}))


def observation_summary(
    restrictions: gpd.GeoDataFrame,
    *,
    record_id: str,
) -> dict[str, object]:
    rows = restrictions.loc[restrictions["Restriction Record ID"].eq(record_id)].copy()
    if rows.empty:
        raise ValueError(f"Missing official restriction record: {record_id}")
    rows = rows.sort_values("Snapshot Time")
    active_states = {"active_full_closure", "active_emergency_access_only"}
    active = rows.loc[rows["Observation State"].isin(active_states), "Snapshot Time"]
    lifted = rows.loc[rows["Observation State"].eq("restriction_lifted"), "Snapshot Time"]
    last_active = active.max() if not active.empty else pd.NaT
    first_lifted = (
        lifted.loc[lifted.gt(last_active)].min()
        if not lifted.empty and pd.notna(last_active)
        else (lifted.min() if not lifted.empty else pd.NaT)
    )
    return {
        "2026 Restriction Record IDs": record_id,
        "Observed Endpoint Pair": endpoint_pair(
            rows.iloc[-1]["Start Location"], rows.iloc[-1]["End Location"]
        ),
        "Observed States": semicolon(rows["Observation State"]),
        "First Observed": rows["Snapshot Time"].min(),
        "Last Observed": rows["Snapshot Time"].max(),
        "Last Active Observation": last_active,
        "First Lifted Observation": first_lifted,
    }


def current_eligible_rows(
    clusters: pd.DataFrame,
    contrasts: pd.DataFrame,
) -> list[dict[str, object]]:
    labels = {
        "REGIME-NORTH": "Joint northern E3/E77 release",
        "REGIME-SOUTH": "Southern E3 release",
        "REGIME-E3A": "E3A Yatsushiro-minami-Tanoura joint release",
    }
    rows: list[dict[str, object]] = []
    for _, cluster in clusters.iterrows():
        cluster_id = cluster["Reopening Cluster ID"]
        official_ids = {
            value.strip()
            for value in str(cluster["Official Interval IDs"]).split(";")
            if value.strip()
        }
        members = contrasts.loc[
            contrasts["Covering Official Interval ID"].isin(official_ids)
        ]
        if len(members) != int(cluster["Named Segment Count"]):
            raise ValueError(f"Cluster membership mismatch for {cluster_id}")
        rows.append(
            {
                "Candidate Regime ID": cluster_id,
                "Candidate Label": labels[cluster_id],
                "2026 Route/Corridor": cluster["Cluster Label"],
                "2026 Endpoint Pairs": cluster["Endpoint Pairs"],
                "2026 Restriction Record IDs": "",
                "2026 Official Interval IDs": cluster["Official Interval IDs"],
                "Observed States": "general_traffic_reopened",
                "First Observed": "",
                "Last Observed": "",
                "Last Active Observation": "",
                "First Lifted Observation": "",
                "2026 Reopening Lower Bound": cluster[
                    "2026 Restoration Hours Lower Bound"
                ],
                "2026 Reopening Upper Bound": cluster[
                    "2026 Restoration Hours Upper Bound"
                ],
                "2026 Outcome Gate": "pass_general_traffic_reopening",
                "2016 Comparator Endpoint Pairs": semicolon(
                    members["2016 Source Endpoint Pair"]
                ),
                "2016 Comparator Gate": "pass_official_named_or_covering_corridor",
                "Geometry Gate": "pass_exact_or_topology_gated_geometry",
                "ShakeMap Gate": "pass_both_events_valid",
                "Independence Gate": "pass_distinct_official_reopening_regime",
                "Final Gate Status": "eligible_current",
                "Counts As Independent Regime": True,
                "Exclusion/Waiting Reason": "",
                "Next Evidence Action": "retain; do not split nested named segments",
            }
        )
    return rows


def build_candidate_rows(
    restrictions: gpd.GeoDataFrame,
    intervals_2016: pd.DataFrame,
) -> list[dict[str, object]]:
    interval_pairs = set(intervals_2016["Endpoint Pair"])
    broad_e3a = "八代JCT|津奈木IC"
    if broad_e3a not in interval_pairs:
        raise ValueError("Missing official 2016 E3A covering interval")

    specs = [
        {
            "Candidate Regime ID": "CANDIDATE-E3A-NORTHSTUB",
            "Candidate Label": "E3A Yatsushiro JCT-Yatsushiro-minami",
            "2026 Route/Corridor": "E3A 南九州自動車道",
            "record_id": "整理ID20260801234125",
            "2026 Official Interval IDs": "",
            "2026 Outcome Gate": "wait_general_traffic_reopening",
            "2016 Comparator Endpoint Pairs": broad_e3a,
            "2016 Comparator Gate": "pass_official_covering_corridor",
            "Geometry Gate": "pending_topology_gate_after_outcome",
            "ShakeMap Gate": "pending_sampling_after_geometry",
            "Independence Gate": "pending_distinct_release_confirmation",
            "Final Gate Status": "monitoring_right_censored",
            "Counts As Independent Regime": False,
            "Exclusion/Waiting Reason": (
                "Still active at the latest official snapshot; emergency access or "
                "record disappearance cannot substitute for general reopening"
            ),
            "Next Evidence Action": (
                "monitor MLIT/NEXCO for a distinct all-traffic reopening endpoint"
            ),
        },
        {
            "Candidate Regime ID": "CANDIDATE-R324-GOTSU-CHIJU",
            "Candidate Label": "National Route 324 Gotsu-Chiju",
            "2026 Route/Corridor": "国道324号",
            "record_id": "整理ID20260803213208",
            "2026 Official Interval IDs": "OBS2026-R005",
            "2026 Outcome Gate": "pass_observed_active_to_lifted_interval",
            "2016 Comparator Endpoint Pairs": "",
            "2016 Comparator Gate": "fail_no_official_2016_named_comparator",
            "Geometry Gate": "not_evaluated_after_comparator_failure",
            "ShakeMap Gate": "not_evaluated_after_comparator_failure",
            "Independence Gate": "pass_distinct_observed_release",
            "Final Gate Status": "excluded_no_2016_comparator",
            "Counts As Independent Regime": False,
            "Exclusion/Waiting Reason": (
                "A 2026 completion transition exists, but the official 2016 road "
                "interval archive has no same or defensible covering corridor"
            ),
            "Next Evidence Action": (
                "retain in exclusion log; reconsider only if an official 2016 segment source is found"
            ),
        },
        {
            "Candidate Regime ID": "CANDIDATE-E77-MAP-CONFLICT",
            "Candidate Label": "E77 Kashima-Koike map-status duplicate",
            "2026 Route/Corridor": "E77 九州中央自動車道",
            "record_id": "整理ID26072817504900",
            "2026 Official Interval IDs": "MLIT2026-R003",
            "2026 Outcome Gate": "fail_conflicting_map_state_after_official_release",
            "2016 Comparator Endpoint Pairs": "嘉島JCT|小池高山IC",
            "2016 Comparator Gate": "pass_official_exact_corridor",
            "Geometry Gate": "pass_exact_reported_geometry",
            "ShakeMap Gate": "pass_both_events_valid",
            "Independence Gate": "fail_same_regime_as_REGIME-NORTH",
            "Final Gate Status": "excluded_duplicate_source_conflict",
            "Counts As Independent Regime": False,
            "Exclusion/Waiting Reason": (
                "The map record remains active after the source-validated official "
                "release and cannot create a second outcome or regime"
            ),
            "Next Evidence Action": "retain as a source-conflict audit; do not count",
        },
    ]

    rows: list[dict[str, object]] = []
    for spec in specs:
        observed = observation_summary(restrictions, record_id=spec.pop("record_id"))
        lower = observed["Last Active Observation"]
        upper = observed["First Lifted Observation"]
        spec["2026 Endpoint Pairs"] = observed.pop("Observed Endpoint Pair")
        spec.update(observed)
        spec["2026 Reopening Lower Bound"] = (
            (lower - EVENT_START_2026).total_seconds() / 3600
            if pd.notna(lower)
            else pd.NA
        )
        spec["2026 Reopening Upper Bound"] = (
            (upper - EVENT_START_2026).total_seconds() / 3600
            if pd.notna(upper)
            else pd.NA
        )
        rows.append(spec)
    return rows


def build_yokoe_candidate() -> dict[str, object]:
    if not YOKOE_GATE.exists() or not YOKOE_GEOMETRY.exists():
        raise ValueError(
            "Run audit_yokoe_bridge_repeated_recovery.py before rebuilding the regime inventory"
        )
    gate = pd.read_csv(YOKOE_GATE).iloc[0]
    geometry = pd.read_csv(YOKOE_GEOMETRY).iloc[0]
    if not bool(gate["Counts As Independent Regime"]):
        raise ValueError("Yokoe live official terminal record has not passed")
    return {
        "Candidate Regime ID": "REGIME-YOKOE",
        "Candidate Label": "Prefectural Route 338 Yokoe Bridge",
        "2026 Route/Corridor": "県道338号八代不知火線・横江大橋",
        "2026 Endpoint Pairs": f"{geometry['Start Location']}|{geometry['End Location']}",
        "2026 Restriction Record IDs": geometry["Restriction Record IDs"],
        "2026 Official Interval IDs": "YOKOE2026-FORECAST; YOKOE2026-CONFIRMATION",
        "Observed States": "general_traffic_reopened; lagging_archived_map_active",
        "First Observed": geometry["First Snapshot"],
        "Last Observed": "2026-08-19 live official portal check",
        "Last Active Observation": geometry["Latest Snapshot"],
        "First Lifted Observation": "2026-08-17 07:00:00+09:00",
        "2026 Reopening Lower Bound": gate["2026 Confirmed Restoration Hours"],
        "2026 Reopening Upper Bound": gate["2026 Confirmed Restoration Hours"],
        "2026 Outcome Gate": gate["2026 Outcome Gate"],
        "2016 Comparator Endpoint Pairs": "横江大橋|横江大橋",
        "2016 Comparator Gate": "pass_same_facility_date_precision",
        "Geometry Gate": geometry["Geometry Gate"],
        "ShakeMap Gate": "pass_both_events_valid",
        "Independence Gate": "pass_distinct_facility_and_confirmed_release",
        "Final Gate Status": "eligible_current",
        "Counts As Independent Regime": True,
        "Exclusion/Waiting Reason": "",
        "Next Evidence Action": (
            "retain as a same-facility descriptive case; do not pool with highway clusters "
            "without unit-type sensitivity analysis"
        ),
    }


def build_augmented_contrasts(clusters: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, cluster in clusters.iterrows():
        old = float(cluster["2016 Mainshock-to-Reopening Mean Hours"])
        new_lower = float(cluster["2026 Restoration Hours Lower Bound"])
        new_upper = float(cluster["2026 Restoration Hours Upper Bound"])
        rows.append(
            {
                "Regime ID": cluster["Reopening Cluster ID"],
                "Unit Type": "motorway_reopening_cluster",
                "Named Segment Count": int(cluster["Named Segment Count"]),
                "2016 MMI Mean": cluster["2016 MMI Mean Across Segments"],
                "2026 MMI Mean": cluster["2026 MMI Mean Across Segments"],
                "2016 PGA Mean (g)": cluster[
                    "2016 PGA Mean (g) Across Segments"
                ],
                "2026 PGA Mean (g)": cluster[
                    "2026 PGA Mean (g) Across Segments"
                ],
                "2016 Restoration Hours Lower Bound": old,
                "2016 Restoration Hours Upper Bound": old,
                "2026 Restoration Hours Lower Bound": new_lower,
                "2026 Restoration Hours Upper Bound": new_upper,
                "2026/2016 Ratio Lower Bound": new_lower / old,
                "2026/2016 Ratio Upper Bound": new_upper / old,
                "Outcome Gate": "pass",
                "Pooling Gate": "eligible_highway_descriptive_sample",
            }
        )
    yokoe = pd.read_csv(YOKOE_GATE).iloc[0]
    old_lower = float(yokoe["2016 Comparable Restoration Hours Lower Bound"])
    old_upper = float(yokoe["2016 Comparable Restoration Hours Upper Bound"])
    new = float(yokoe["2026 Confirmed Restoration Hours"])
    rows.append(
        {
            "Regime ID": "REGIME-YOKOE",
            "Unit Type": "same_bridge_repeated_damage",
            "Named Segment Count": 1,
            "2016 MMI Mean": yokoe["2016 Mean MMI"],
            "2026 MMI Mean": yokoe["2026 Mean MMI"],
            "2016 PGA Mean (g)": yokoe["2016 Mean PGA (g)"],
            "2026 PGA Mean (g)": yokoe["2026 Mean PGA (g)"],
            "2016 Restoration Hours Lower Bound": old_lower,
            "2016 Restoration Hours Upper Bound": old_upper,
            "2026 Restoration Hours Lower Bound": new,
            "2026 Restoration Hours Upper Bound": new,
            "2026/2016 Ratio Lower Bound": new / old_upper,
            "2026/2016 Ratio Upper Bound": new / old_lower,
            "Outcome Gate": "pass_live_official_terminal_record",
            "Pooling Gate": "same_asset_case_do_not_pool_without_unit_type_sensitivity",
        }
    )
    return pd.DataFrame(rows).sort_values("Regime ID").reset_index(drop=True)


def build_criteria() -> pd.DataFrame:
    rows = [
        ("G1", "2026 named spatial unit", "Official named endpoints or an explicitly documented covering corridor", "Reject route-name-only linkage"),
        ("G2", "2026 outcome", "Official all-traffic reopening time or bounded last-active to first-lifted interval", "A formal release overrides a lagging map state; emergency-only access and disappearance are not reopening"),
        ("G3", "2016 comparator", "Official exact or defensible covering named corridor with a dated endpoint", "Reject unsupported historical equivalence"),
        ("G4", "geometry", "Exact official geometry or topology-gated derivation with documented offsets", "Derive geometry only after outcome and comparator gates"),
        ("G5", "hazard support", "Valid samples from both version-pinned ShakeMap products", "Physical comparability does not remove model-generation uncertainty"),
        ("G6", "independence", "Distinct official reopening decision/time rather than a nested segment sharing a release", "One release mechanism contributes at most one independent regime"),
        ("G7", "claim boundary", "All gates pass before inclusion in the effective sample", "Eligible rows support feasibility and descriptive contrasts only"),
    ]
    return pd.DataFrame(rows, columns=["Gate ID", "Gate", "Pass Rule", "Conservative Rule"])


def build_watchlist(latest_snapshot: pd.Timestamp) -> pd.DataFrame:
    rows = [
        {
            "Source": "MLIT disaster damage-report page",
            "URL": "https://www.mlit.go.jp/saigai/saigai_260728.html",
            "Checked On": SOURCE_CHECK_DATE,
            "Latest Confirmed Release": "Report 44; 2026-08-18 10:00",
            "Local Data Through": "2026-08-18",
            "Update Status": "no_new_release_on_2026-08-19_check",
        },
        {
            "Source": "MLIT passable-road map archives",
            "URL": "https://www.mlit.go.jp/road/saigai/r8kumamoto/index.html",
            "Checked On": SOURCE_CHECK_DATE,
            "Latest Confirmed Release": "2026-08-18 09:00",
            "Local Data Through": latest_snapshot.isoformat(),
            "Update Status": "local_archive_current_at_check",
        },
        {
            "Source": "NEXCO West disaster releases",
            "URL": "https://www.w-nexco.co.jp/realtime/",
            "Checked On": SOURCE_CHECK_DATE,
            "Latest Confirmed Release": "No newly indexed distinct reopening after the retained sources",
            "Local Data Through": "Report 18; 2026-08-17 14:00",
            "Update Status": "continue_monitoring_E3A_north_stub",
        },
        {
            "Source": "Kyushu Regional Development Bureau Yatsushiro office releases",
            "URL": "https://www.qsr.mlit.go.jp/yatusiro/nt_list/nt4/",
            "Checked On": SOURCE_CHECK_DATE,
            "Latest Confirmed Release": "E3A Hinagu IC-Tanoura IC final; 2026-08-18 06:00",
            "Local Data Through": "Joint forecast and final release retained with SHA-256",
            "Update Status": "formal_release_overrides_lagging_map_state",
        },
        {
            "Source": "QSR/Kumamoto joint Yokoe Bridge release and prefectural map",
            "URL": "https://www.qsr.mlit.go.jp/content/000002804.pdf",
            "Checked On": SOURCE_CHECK_DATE,
            "Latest Confirmed Release": "Live official road register: exact address pair lifted 2026-08-17 07:00",
            "Local Data Through": latest_snapshot.isoformat(),
            "Update Status": "resolved_live_terminal_record_overrides_lagging_archive",
        },
    ]
    return pd.DataFrame(rows)


def write_readme(inventory: pd.DataFrame, latest_snapshot: pd.Timestamp) -> None:
    counts = inventory["Final Gate Status"].value_counts()
    eligible = inventory.loc[inventory["Counts As Independent Regime"]]
    monitoring = inventory.loc[
        inventory["Final Gate Status"].str.startswith("monitoring_")
    ]
    monitoring_phrase = (
        "candidate is" if len(monitoring) == 1 else "candidates are"
    )
    lines = [
        "# Independent reopening-regime expansion inventory",
        "",
        "## Purpose",
        "",
        "This folder is an experimental feasibility asset. It prevents nested named road segments from inflating the effective sample and preserves source-qualified candidates until they pass every inclusion gate. It is not a Results table and not an effect estimate.",
        "",
        "## Current result",
        "",
        f"- {len(eligible)} independent reopening regimes are currently eligible.",
        f"- {len(monitoring)} {monitoring_phrase} under active official-source monitoring: the right-censored E3A north stub.",
        f"- {int(counts.get('excluded_no_2016_comparator', 0))} completed 2026 candidate is excluded because no official 2016 named comparator is available.",
        f"- {int(counts.get('excluded_duplicate_source_conflict', 0))} record is retained only as a duplicate/source-conflict audit and cannot increase the sample.",
        f"- The latest local passable-map snapshot is {latest_snapshot.isoformat()}. The central pages had no newer map or damage report on {SOURCE_CHECK_DATE}, but the regional bureau's 18 August final release supplies the authoritative E3A endpoint.",
        "",
        "The independent-unit registry now contains 4 eligible regimes. The homogeneous motorway-release subset remains n=3; Yokoe Bridge is an exact same-facility descriptive case and must not be pooled into a common estimator without an explicit unit-type sensitivity analysis. The expanded evidence is therefore suitable for structured descriptive comparison, not an adjusted causal estimator.",
        "",
        "## Files",
        "",
        "- `inclusion_criteria.csv`: immutable conservative admission rules.",
        "- `candidate_regime_inventory.csv`: all retained eligible, monitoring, and excluded regimes.",
        "- `eligible_regime_inventory.csv`: the current effective feasibility sample.",
        "- `exclusion_and_waiting_log.csv`: explicit reasons candidates do not count.",
        "- `official_update_watchlist.csv`: official pages and the latest source check.",
        "- `YOKOE_BRIDGE_AUDIT.md` and `yokoe_bridge_*.csv`: eligible same-facility repeated-damage audit and live-source resolution.",
        "- `yokoe_bridge_live_portal_confirmation.csv`: structured snapshot of the dynamic terminal road-register record.",
        "- `augmented_independent_regime_contrasts.csv`: four-unit descriptive registry with an explicit unit-type pooling gate.",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/build_independent_reopening_regime_inventory.py",
        "```",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    restrictions = gpd.read_parquet(RESTRICTIONS)
    restrictions["Snapshot Time"] = pd.to_datetime(restrictions["Snapshot Time"])
    latest_snapshot = restrictions["Snapshot Time"].max()
    clusters = pd.read_csv(CLUSTERS)
    contrasts = pd.read_csv(CONTRASTS)
    intervals_2016 = pd.read_csv(INTERVALS_2016)
    geometry = pd.read_csv(GEOMETRY_AUDIT)

    if len(clusters) != 3 or int(clusters["Independent 2026 Reopening Regimes"].sum()) != 3:
        raise ValueError("Expected the audited three-regime baseline")
    if not set(contrasts["Endpoint Pair"]).issubset(set(geometry["Endpoint Pair"])):
        raise ValueError("At least one contrasted corridor lacks a geometry audit")

    rows = current_eligible_rows(clusters, contrasts)
    rows.extend(build_candidate_rows(restrictions, intervals_2016))
    rows.append(build_yokoe_candidate())
    inventory = pd.DataFrame(rows)
    column_order = [
        "Candidate Regime ID",
        "Candidate Label",
        "2026 Route/Corridor",
        "2026 Endpoint Pairs",
        "2026 Restriction Record IDs",
        "2026 Official Interval IDs",
        "Observed States",
        "First Observed",
        "Last Observed",
        "Last Active Observation",
        "First Lifted Observation",
        "2026 Reopening Lower Bound",
        "2026 Reopening Upper Bound",
        "2026 Outcome Gate",
        "2016 Comparator Endpoint Pairs",
        "2016 Comparator Gate",
        "Geometry Gate",
        "ShakeMap Gate",
        "Independence Gate",
        "Final Gate Status",
        "Counts As Independent Regime",
        "Exclusion/Waiting Reason",
        "Next Evidence Action",
    ]
    inventory = inventory[column_order].sort_values(
        ["Counts As Independent Regime", "Candidate Regime ID"],
        ascending=[False, True],
    )
    if inventory["Candidate Regime ID"].duplicated().any():
        raise ValueError("Candidate regime IDs must be unique")
    if int(inventory["Counts As Independent Regime"].sum()) != 4:
        raise ValueError("The independent-unit registry must contain four eligible regimes")

    criteria = build_criteria()
    eligible = inventory.loc[inventory["Counts As Independent Regime"]].copy()
    waiting = inventory.loc[~inventory["Counts As Independent Regime"]].copy()
    watchlist = build_watchlist(latest_snapshot)
    augmented_contrasts = build_augmented_contrasts(clusters)
    criteria.to_csv(OUT / "inclusion_criteria.csv", index=False)
    inventory.to_csv(OUT / "candidate_regime_inventory.csv", index=False)
    eligible.to_csv(OUT / "eligible_regime_inventory.csv", index=False)
    waiting.to_csv(OUT / "exclusion_and_waiting_log.csv", index=False)
    watchlist.to_csv(OUT / "official_update_watchlist.csv", index=False)
    augmented_contrasts.to_csv(
        OUT / "augmented_independent_regime_contrasts.csv", index=False
    )
    write_readme(inventory, latest_snapshot)
    print(
        "PASS: built independent reopening-regime inventory; "
        f"eligible={len(eligible)}, monitoring="
        f"{int(inventory['Final Gate Status'].str.startswith('monitoring_').sum())}, "
        f"excluded={int(inventory['Final Gate Status'].str.startswith('excluded_').sum())}."
    )


if __name__ == "__main__":
    main()
