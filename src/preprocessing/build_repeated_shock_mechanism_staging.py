#!/usr/bin/env python3
"""Assemble audited repeated-shock evidence into six staging products.

The staging tables preserve the heterogeneous outcome systems. They are inputs
to the standard data-preprocessing generator and are not final analysis files.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FEAS = ROOT / "data/exp/feasibility-check"
STAGING = ROOT / "data/exp/data-preprocessing/staging"
MASHIKI_CORRIDOR = (
    FEAS
    / "intervention-geometry"
    / "kumamoto_takamori_intervention_corridor.parquet"
)
RESTRICTIONS_2026 = (
    ROOT
    / "data/processed"
    / "kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
GEOGRAPHIC_CRS = "EPSG:4326"


def read_csv(relative_path: str) -> pd.DataFrame:
    return pd.read_csv(FEAS / relative_path, encoding="utf-8-sig", low_memory=False)


def write_staging(name: str, frame: pd.DataFrame) -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    path = STAGING / Path(name).with_suffix(".parquet")
    frame.to_parquet(path, index=False, engine="pyarrow")
    frame.to_csv(path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    print(f"Saved {len(frame):,} rows x {len(frame.columns)} cols -> {path.relative_to(ROOT)}")


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def build_case_geometries() -> gpd.GeoDataFrame:
    corridor = gpd.read_parquet(MASHIKI_CORRIDOR).to_crs(GEOGRAPHIC_CRS)
    if (
        len(corridor) != 1
        or not bool(corridor["Geometry Use Eligible"].iloc[0])
        or not bool(corridor["Completed Before 2026 Event"].iloc[0])
        or corridor.geometry.iloc[0].is_empty
    ):
        raise RuntimeError("The verified Mashiki corridor geometry contract failed.")
    mashiki = corridor.iloc[0]

    restrictions = gpd.read_parquet(RESTRICTIONS_2026).to_crs(GEOGRAPHIC_CRS)
    yokoe_rows = restrictions.loc[
        restrictions["Start Location"].astype(str).str.contains("鏡町宝出", na=False)
        & restrictions["End Location"].astype(str).str.contains("鏡町野崎", na=False)
        & restrictions["Restriction Reason"].astype(str).str.contains("橋梁損傷", na=False)
    ].copy()
    if yokoe_rows.empty:
        raise RuntimeError("The exact Yokoe bridge-damage segment was not found.")
    yokoe_geometry = yokoe_rows.geometry.union_all()
    if yokoe_geometry.is_empty:
        raise RuntimeError("The Yokoe bridge-damage geometry is empty.")

    return gpd.GeoDataFrame(
        [
            {
                "Case ID": "MASHIKI-CENTRAL",
                "Case Label": "Mashiki Central Line",
                "Adaptation Pathway": "corridor capacity expansion",
                "Geometry Role": "official aggregate planning corridor polygon",
                "Gate Unit": "nested corridor cluster",
                "Geometry Gate": True,
                "Geometry Gate Basis": "verified official aggregate corridor polygon",
                "Geometry Source Reference": str(mashiki["Geometry Source"]),
                "Geometry": mashiki["Geometry"],
            },
            {
                "Case ID": "YOKOE-BRIDGE",
                "Case Label": "Yokoe Bridge",
                "Adaptation Pathway": "structural reconstruction",
                "Geometry Role": "exact official bridge-damage restriction segment",
                "Gate Unit": "same physical bridge",
                "Geometry Gate": True,
                "Geometry Gate Basis": "exact official bridge-damage segment",
                "Geometry Source Reference": ", ".join(
                    sorted(yokoe_rows["Snapshot Archive"].dropna().unique())
                ),
                "Geometry": yokoe_geometry,
            },
        ],
        geometry="Geometry",
        crs=GEOGRAPHIC_CRS,
    )


def build_two_case_evidence() -> pd.DataFrame:
    mashiki_shaking = read_csv(
        "nied-2016-road-condition/mashiki_central_cross_event_shaking.csv"
    )
    mashiki_state = read_csv(
        "nied-2016-road-condition/same_corridor_cross_event_evidence.csv"
    )
    passage = read_csv(
        "intervention-geometry/kumamoto_takamori_probe_passage_snapshots.csv"
    )
    interventions = read_csv(
        "intervention-geometry/expanded_post_2016_intervention_inventory.csv"
    )
    yokoe = read_csv(
        "independent-reopening-regimes/yokoe_bridge_descriptive_contrast.csv"
    ).iloc[0]

    m2016 = mashiki_shaking.loc[mashiki_shaking["Event"].eq("2016 mainshock")].iloc[0]
    m2026 = mashiki_shaking.loc[mashiki_shaking["Event"].eq("2026 earthquake")].iloc[0]
    mashiki_project = interventions.loc[
        interventions["Intervention Unit ID"].eq("INT-KT-FOUR-LANING")
    ].iloc[0]
    passage_available = as_bool(passage["Passage Layer Available"])
    passage_observed = as_bool(passage["Observed Corridor-Aligned Passage"])
    first_passage = pd.to_datetime(
        passage.loc[passage_available & passage_observed, "Snapshot Time (JST)"]
    ).min()
    event_origin_2026 = pd.Timestamp("2026-07-28T16:27:15.512+09:00")
    first_passage_hours = (first_passage - event_origin_2026).total_seconds() / 3600
    mashiki_failure = "; ".join(
        mashiki_state.loc[
            mashiki_state["Event"].eq("2016 earthquake sequence"),
            ["Subsegment", "Corridor State Evidence"],
        ].apply(lambda row: f"{row.iloc[0]}: {row.iloc[1]}", axis=1)
    )

    yokoe_primary_lower = float(yokoe["2016 Comparable Restoration Hours Lower Bound"])
    yokoe_primary_upper = float(yokoe["2016 Comparable Restoration Hours Upper Bound"])
    yokoe_2026 = float(yokoe["2026 Confirmed Restoration Hours"])

    rows = [
        {
            "Case ID": "MASHIKI-CENTRAL",
            "Case Label": "Mashiki Central Line",
            "Adaptation Pathway": "corridor capacity expansion",
            "Adaptation Description": "Kumamoto-Takamori four-laning / Mashiki Central Line",
            "Adaptation Completion": mashiki_project["Opening Date"],
            "2016 Failure Evidence": mashiki_failure,
            "2026 Performance Evidence": (
                f"near-full probe passage first observed {first_passage_hours:.2f} hours "
                f"after origin; passage observed in "
                f"{int((passage_available & passage_observed).sum())}/"
                f"{int(passage_available.sum())} available snapshots"
            ),
            "2016 Mean MMI": m2016["MMI Mean"],
            "2026 Mean MMI": m2026["MMI Mean"],
            "2016 Mean PGA (g)": m2016["PGA Mean (g)"],
            "2026 Mean PGA (g)": m2026["PGA Mean (g)"],
            "Outcome Comparability": "non-equivalent restriction and probe-passage systems",
            "Evidence Level": "structured comparison",
            "Permissible Claim": "service-presence trajectory consistent with capacity tolerance",
            "Inference Ceiling": "no like-for-like restoration ratio and no causal effect",
            "Core Case": True,
        },
        {
            "Case ID": "YOKOE-BRIDGE",
            "Case Label": "Yokoe Bridge",
            "Adaptation Pathway": "structural reconstruction",
            "Adaptation Description": "reconstruction of the same bridge after 2016 damage",
            "Adaptation Completion": "2019-02-02",
            "2016 Failure Evidence": "same bridge closed after the 2016 mainshock",
            "2026 Performance Evidence": (
                f"general traffic restored {yokoe_2026:.2f} hours after the 2026 event"
            ),
            "2016 Mean MMI": yokoe["2016 Mean MMI"],
            "2026 Mean MMI": yokoe["2026 Mean MMI"],
            "2016 Mean PGA (g)": yokoe["2016 Mean PGA (g)"],
            "2026 Mean PGA (g)": yokoe["2026 Mean PGA (g)"],
            "Outcome Comparability": "matched full general-traffic reopening endpoint",
            "Evidence Level": "directional dominance",
            "Permissible Claim": (
                "faster same-asset restoration under stronger 2026 MMI and PGA"
            ),
            "Inference Ceiling": "no causal reconstruction effect",
            "Core Case": True,
        },
    ]
    result = pd.DataFrame(rows)
    result["MMI Difference (2026-2016)"] = (
        result["2026 Mean MMI"] - result["2016 Mean MMI"]
    )
    result["PGA Ratio (2026/2016)"] = (
        result["2026 Mean PGA (g)"] / result["2016 Mean PGA (g)"]
    )
    ordered = [
        "Case ID",
        "Case Label",
        "Adaptation Pathway",
        "Adaptation Description",
        "Adaptation Completion",
        "2016 Failure Evidence",
        "2026 Performance Evidence",
        "2016 Mean MMI",
        "2026 Mean MMI",
        "MMI Difference (2026-2016)",
        "2016 Mean PGA (g)",
        "2026 Mean PGA (g)",
        "PGA Ratio (2026/2016)",
        "Outcome Comparability",
        "Evidence Level",
        "Permissible Claim",
        "Inference Ceiling",
        "Core Case",
    ]
    return result[ordered]


def build_mashiki_event_state() -> pd.DataFrame:
    evidence = read_csv(
        "nied-2016-road-condition/same_corridor_cross_event_evidence.csv"
    )
    restriction = read_csv(
        "nied-2016-road-condition/mashiki_central_2016_restriction_snapshots.csv"
    )
    shaking = read_csv(
        "nied-2016-road-condition/mashiki_central_cross_event_shaking.csv"
    )
    passage = read_csv(
        "intervention-geometry/kumamoto_takamori_probe_passage_snapshots.csv"
    )
    m2016 = shaking.loc[shaking["Event"].eq("2016 mainshock")].iloc[0]
    m2026 = shaking.loc[shaking["Event"].eq("2026 earthquake")].iloc[0]
    restriction_hash = restriction["Source SHA-256"].dropna().astype(str).iloc[0]

    rows: list[dict[str, object]] = []
    for _, row in evidence.loc[
        evidence["Event"].eq("2016 earthquake sequence")
    ].iterrows():
        rows.append(
            {
                "Case ID": "MASHIKI-CENTRAL",
                "Event": "2016 mainshock",
                "Observation Time": f"{row['First Relevant Observation']}T00:00:00+09:00",
                "Subsegment": row["Subsegment"],
                "Observation Type": "official restriction summary",
                "Observation State": row["Corridor State Evidence"],
                "Measurement System": row["Measurement"],
                "Passage Layer Available": pd.NA,
                "Observed Corridor Passage": pd.NA,
                "Unique Corridor Traces": pd.NA,
                "Longitudinal Coverage Proxy": pd.NA,
                "Elapsed Hours Since Event": pd.NA,
                "Event-Time Bound": row["Event-Time Bound"],
                "MMI Mean": m2016["MMI Mean"],
                "PGA Mean (g)": m2016["PGA Mean (g)"],
                "Source SHA-256": restriction_hash,
                "Interpretation": (
                    "positive restriction-state evidence; calendar-day precision"
                ),
            }
        )

    origin = pd.Timestamp("2026-07-28T16:27:15.512+09:00")
    passage_available = as_bool(passage["Passage Layer Available"])
    passage_observed = as_bool(passage["Observed Corridor-Aligned Passage"])
    for idx, row in passage.iterrows():
        observed_time = pd.Timestamp(row["Snapshot Time (JST)"])
        if not passage_available.loc[idx]:
            state = "passage layer unavailable"
        elif passage_observed.loc[idx]:
            state = "corridor passage observed"
        else:
            state = "no corridor passage observed"
        rows.append(
            {
                "Case ID": "MASHIKI-CENTRAL",
                "Event": "2026 earthquake",
                "Observation Time": observed_time.isoformat(),
                "Subsegment": "official 3.5 km Mashiki Central polygon",
                "Observation Type": "probe passage snapshot",
                "Observation State": state,
                "Measurement System": "MLIT private-probe service-presence layer",
                "Passage Layer Available": passage_available.loc[idx],
                "Observed Corridor Passage": passage_observed.loc[idx],
                "Unique Corridor Traces": row["Unique Corridor-Aligned Traces"],
                "Longitudinal Coverage Proxy": row["Longitudinal Coverage Proxy"],
                "Elapsed Hours Since Event": (
                    observed_time - origin
                ).total_seconds()
                / 3600,
                "Event-Time Bound": "first positive state is an observation-time upper bound",
                "MMI Mean": m2026["MMI Mean"],
                "PGA Mean (g)": m2026["PGA Mean (g)"],
                "Source SHA-256": row["Archive SHA-256"],
                "Interpretation": row["Interpretation"],
            }
        )
    return pd.DataFrame(rows)


def build_yokoe_matched_endpoint() -> pd.DataFrame:
    contrast = read_csv(
        "independent-reopening-regimes/yokoe_bridge_descriptive_contrast.csv"
    ).iloc[0]
    rows = []
    endpoint_specs = [
        (
            "full general-traffic reopening",
            "primary matched endpoint",
            contrast["2016 Comparable Restoration Hours Lower Bound"],
            contrast["2016 Comparable Restoration Hours Upper Bound"],
        ),
        (
            "light-vehicle access",
            "2016 early-access sensitivity",
            contrast["2016 Light-Vehicle Access Hours Lower Bound"],
            contrast["2016 Light-Vehicle Access Hours Upper Bound"],
        ),
    ]
    t2026 = float(contrast["2026 Confirmed Restoration Hours"])
    for definition, role, t2016_lower, t2016_upper in endpoint_specs:
        t2016_lower = float(t2016_lower)
        t2016_upper = float(t2016_upper)
        ratio_lower = t2026 / t2016_upper
        ratio_upper = t2026 / t2016_lower
        rows.append(
            {
                "Case ID": "YOKOE-BRIDGE",
                "Endpoint Definition": definition,
                "Endpoint Role": role,
                "2016 Restoration Hours Lower Bound": t2016_lower,
                "2016 Restoration Hours Upper Bound": t2016_upper,
                "2026 Restoration Hours Lower Bound": t2026,
                "2026 Restoration Hours Upper Bound": t2026,
                "Restoration Ratio Lower Bound (2026/2016)": ratio_lower,
                "Restoration Ratio Upper Bound (2026/2016)": ratio_upper,
                "2016 Mean MMI": contrast["2016 Mean MMI"],
                "2026 Mean MMI": contrast["2026 Mean MMI"],
                "2016 Mean PGA (g)": contrast["2016 Mean PGA (g)"],
                "2026 Mean PGA (g)": contrast["2026 Mean PGA (g)"],
                "PGA Ratio (2026/2016)": contrast["PGA Mean Ratio (2026/2016)"],
                "Faster in 2026": ratio_upper < 1,
                "Hazard Direction": "2026 stronger under both MMI and PGA",
                "Outcome Gate": contrast["2026 Outcome Gate"],
                "Inference Ceiling": "directional same-asset contrast; no causal effect",
            }
        )
    return pd.DataFrame(rows)


def build_candidate_ledger() -> pd.DataFrame:
    local = read_csv("additional-intervention-screen/candidate_screen.csv")
    restored = read_csv(
        "rebuilt-bridge-crosswalk/official_2016_rebuilt_bridge_inventory.csv"
    )
    damage = read_csv("rebuilt-bridge-crosswalk/bridge_damage_crosswalk.csv")
    contextual = read_csv(
        "additional-reconstruction-candidates/candidate_audit.csv"
    )
    corridor = gpd.read_parquet(MASHIKI_CORRIDOR)
    mashiki_cluster_geometry_pass = (
        len(corridor) == 1
        and bool(corridor["Geometry Use Eligible"].iloc[0])
        and bool(corridor["Completed Before 2026 Event"].iloc[0])
        and not corridor.geometry.iloc[0].is_empty
    )
    if not mashiki_cluster_geometry_pass:
        raise RuntimeError("The verified Mashiki corridor-cluster geometry gate failed.")
    rows: list[dict[str, object]] = []

    for _, row in local.iterrows():
        retained = str(row["Intervention ID"]) in {"I001", "I002", "I003"}
        rows.append(
            {
                "Candidate ID": f"LOCAL-{row['Intervention ID']}",
                "Candidate Universe": "post-2016 local road projects",
                "Candidate Label": row["Asset Name"],
                "Route": row["Official Road Name"],
                "Location": row["Area"],
                "Adaptation Completion": row["Completion Status"],
                "2016 Evidence": (
                    f"{int(row['2016 Unique Points Within 100 m'])} stable points within 100 m"
                ),
                "2026 Evidence": (
                    f"{int(row['2026 Snapshots With Full-Road Passage'])}/"
                    f"{int(row['2026 Passage-Layer Snapshots'])} full-road passage snapshots"
                ),
                "Gate Unit": "nested corridor cluster" if retained else "project stage",
                "Identity Gate": bool(row["2016 Route Compatible"]),
                "Geometry Gate": (
                    mashiki_cluster_geometry_pass
                    if retained
                    else bool(row["Exact Project Geometry Available"])
                ),
                "Geometry Gate Basis": (
                    "verified official aggregate corridor polygon"
                    if retained
                    else "no exact project-stage geometry"
                ),
                "Hazard Gate": pd.NA if not retained else "metric dependent",
                "Outcome Gate": retained,
                "Core Status": (
                    "include as one nested Mashiki cluster"
                    if retained
                    else "exclude from core"
                ),
                "Exclusion Reason": (
                    ""
                    if retained
                    else str(row["Screen Status"])
                ),
                "Official Source": row["Official Source Layer"],
            }
        )

    for _, row in restored.iterrows():
        is_yokoe = str(row["Bridge Name"]).strip() == "横江大橋"
        rows.append(
            {
                "Candidate ID": f"RESTORED-BRIDGE-{int(row['Official Number']):03d}",
                "Candidate Universe": "2016 officially restored bridges",
                "Candidate Label": row["Bridge Name"],
                "Route": row["Route Name"],
                "Location": f"{row['Municipality']} {row['Location']}",
                "Adaptation Completion": "restored after 2016",
                "2016 Evidence": "official restored-bridge inventory",
                "2026 Evidence": (
                    "exact same-asset bridge-damage record"
                    if is_yokoe
                    else "no exact same-asset recurrence in audited 2026 records"
                ),
                "Gate Unit": "same physical bridge",
                "Identity Gate": is_yokoe,
                "Geometry Gate": is_yokoe,
                "Geometry Gate Basis": (
                    "exact official bridge crosswalk"
                    if is_yokoe
                    else "no exact 2026 same-asset geometry"
                ),
                "Hazard Gate": "pass" if is_yokoe else pd.NA,
                "Outcome Gate": is_yokoe,
                "Core Status": (
                    "include Yokoe Bridge core case"
                    if is_yokoe
                    else "exclude from core"
                ),
                "Exclusion Reason": "" if is_yokoe else "no exact 2026 recurrence",
                "Official Source": row["Source"],
            }
        )

    for idx, row in damage.reset_index(drop=True).iterrows():
        exact = row["Crosswalk Status"] == "pass_exact_same_asset"
        rows.append(
            {
                "Candidate ID": f"DAMAGE-2026-{idx + 1:03d}",
                "Candidate Universe": "2026 bridge-damage records",
                "Candidate Label": row["2016 Same-Route Rebuilt Bridges"]
                if pd.notna(row["2016 Same-Route Rebuilt Bridges"])
                else row["2026 Route Name"],
                "Route": row["2026 Route Name"],
                "Location": f"{row['2026 Start Location']} to {row['2026 End Location']}",
                "Adaptation Completion": pd.NA,
                "2016 Evidence": row["2016 Same-Route Rebuilt Bridges"],
                "2026 Evidence": "official bridge-damage record",
                "Gate Unit": "same physical bridge",
                "Identity Gate": exact,
                "Geometry Gate": exact,
                "Geometry Gate Basis": (
                    "exact official bridge-damage segment"
                    if exact
                    else "route or proximity evidence only"
                ),
                "Hazard Gate": "pass" if exact else pd.NA,
                "Outcome Gate": exact,
                "Core Status": (
                    "include Yokoe Bridge core case" if exact else "exclude from core"
                ),
                "Exclusion Reason": "" if exact else row["Crosswalk Status"],
                "Official Source": "Kumamoto official 2026 road register",
            }
        )

    for _, row in contextual.iterrows():
        rows.append(
            {
                "Candidate ID": f"CONTEXT-{row['Candidate ID']}",
                "Candidate Universe": "additional official reconstructions",
                "Candidate Label": row["Candidate"],
                "Route": pd.NA,
                "Location": pd.NA,
                "Adaptation Completion": row["Official Completion"],
                "2016 Evidence": (
                    f"{int(row['2016 NIED Records at Dominant Point'])} NIED records"
                ),
                "2026 Evidence": (
                    f"{int(row['2026 Positive Proximity Snapshots'])}/"
                    f"{int(row['2026 Available Passage Snapshots'])} proximity snapshots"
                ),
                "Gate Unit": "contextual asset or corridor",
                "Identity Gate": True,
                "Geometry Gate": False,
                "Geometry Gate Basis": "proximity-only outcome geometry",
                "Hazard Gate": "fail; 2026 substantially weaker",
                "Outcome Gate": False,
                "Core Status": "contextual mechanism case only",
                "Exclusion Reason": row["Core Sample Status"],
                "Official Source": row["Official Source"],
            }
        )
    result = pd.DataFrame(rows)
    assert len(local) == 12
    assert len(restored) == 37
    assert len(damage) == 13
    assert len(contextual) == 3
    assert result["Core Status"].str.contains("Yokoe").sum() == 2
    included = result["Core Status"].str.startswith("include")
    assert result.loc[included, "Identity Gate"].all()
    assert result.loc[included, "Geometry Gate"].all()
    assert result.loc[included, "Outcome Gate"].all()
    assert result.loc[included, "Hazard Gate"].isin(["pass", "metric dependent"]).all()
    return result


def build_claim_sensitivity() -> pd.DataFrame:
    rows = [
        {
            "Claim ID": "C1",
            "Claim": "Mashiki shows an observable 2026 service-presence trajectory",
            "Sensitivity Dimension": "MMI event comparability",
            "Scenario": "mean MMI",
            "Result": "pass; 8.653 in 2016 and 8.601 in 2026",
            "Classification": "robust for similar MMI",
            "Evidence": "version-pinned corridor ShakeMaps",
            "Inference Ceiling": "not a causal effect",
        },
        {
            "Claim ID": "C1",
            "Claim": "Mashiki shows an observable 2026 service-presence trajectory",
            "Sensitivity Dimension": "PGA event comparability",
            "Scenario": "mean PGA",
            "Result": "metric dependent; 0.963 g in 2016 and 0.609 g in 2026",
            "Classification": "measurement dependent",
            "Evidence": "version-pinned corridor ShakeMaps",
            "Inference Ceiling": "do not claim uniformly equal or stronger 2026 shaking",
        },
        {
            "Claim ID": "C1",
            "Claim": "Mashiki shows an observable 2026 service-presence trajectory",
            "Sensitivity Dimension": "observation coverage",
            "Scenario": "available passage snapshots",
            "Result": "pass; passage observed in 20 of 21 available snapshots",
            "Classification": "robust positive observation",
            "Evidence": "MLIT probe-passage snapshots",
            "Inference Ceiling": "absence is not impassability",
        },
        {
            "Claim ID": "C1",
            "Claim": "Mashiki shows an observable 2026 service-presence trajectory",
            "Sensitivity Dimension": "outcome equivalence",
            "Scenario": "restriction release versus probe passage",
            "Result": "fail; outcome systems differ",
            "Classification": "non-comparable outcome",
            "Evidence": "2016 restriction and 2026 passage audits",
            "Inference Ceiling": "no restoration-time ratio",
        },
        {
            "Claim ID": "C2",
            "Claim": "Yokoe reopened faster in 2026",
            "Sensitivity Dimension": "restoration endpoint",
            "Scenario": "full general-traffic reopening",
            "Result": "pass; 2026/2016 ratio below one",
            "Classification": "direction robust",
            "Evidence": "official matched full-reopening endpoints",
            "Inference Ceiling": "no causal reconstruction effect",
        },
        {
            "Claim ID": "C2",
            "Claim": "Yokoe reopened faster in 2026",
            "Sensitivity Dimension": "restoration endpoint",
            "Scenario": "2016 light-vehicle access",
            "Result": "pass; 2026/2016 ratio below one",
            "Classification": "direction robust",
            "Evidence": "official early-access sensitivity endpoint",
            "Inference Ceiling": "different traffic meaning retained",
        },
        {
            "Claim ID": "C2",
            "Claim": "Yokoe reopened faster despite stronger 2026 shaking",
            "Sensitivity Dimension": "hazard metric",
            "Scenario": "mean MMI",
            "Result": "pass; 8.670 in 2026 versus 7.134 in 2016",
            "Classification": "direction robust",
            "Evidence": "version-pinned bridge ShakeMaps",
            "Inference Ceiling": "hazard intensity is not damage equivalence",
        },
        {
            "Claim ID": "C2",
            "Claim": "Yokoe reopened faster despite stronger 2026 shaking",
            "Sensitivity Dimension": "hazard metric",
            "Scenario": "mean PGA",
            "Result": "pass; 0.558 g in 2026 versus 0.302 g in 2016",
            "Classification": "direction robust",
            "Evidence": "version-pinned bridge ShakeMaps",
            "Inference Ceiling": "hazard intensity is not damage equivalence",
        },
        {
            "Claim ID": "C3",
            "Claim": "The core cases are not selected only for favorable outcomes",
            "Sensitivity Dimension": "local-project denominator",
            "Scenario": "12 route-linked projects",
            "Result": (
                "pass; three nested stages satisfy the verified corridor-cluster "
                "linkage and nine projects are excluded"
            ),
            "Classification": "audit robust",
            "Evidence": "whole-road project screen and verified corridor geometry",
            "Inference Ceiling": "one intervention cluster",
        },
        {
            "Claim ID": "C3",
            "Claim": "The core cases are not selected only for favorable outcomes",
            "Sensitivity Dimension": "bridge denominator",
            "Scenario": "37 restored bridges versus 13 damage records",
            "Result": "pass; Yokoe is the sole exact same-asset recurrence",
            "Classification": "audit robust",
            "Evidence": "official bridge crosswalk",
            "Inference Ceiling": "one same-asset case",
        },
        {
            "Claim ID": "C3",
            "Claim": "Contextual reconstructions can join the core comparison",
            "Sensitivity Dimension": "hazard and geometry gates",
            "Scenario": "New Aso Ohkirihata and Route 57 Tateno",
            "Result": "fail; weaker 2026 hazard and proximity-only outcomes",
            "Classification": "unsupported for core",
            "Evidence": "additional reconstruction audit",
            "Inference Ceiling": "mechanism context only",
        },
        {
            "Claim ID": "C4",
            "Claim": "All reported facts use traceable source precedence",
            "Sensitivity Dimension": "source precedence",
            "Scenario": "live terminal record versus lagging archive",
            "Result": "pass with explicit override",
            "Classification": "source-rule robust",
            "Evidence": "official source gate",
            "Inference Ceiling": "report the override and retrieval time",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    outputs = {
        "two_case_evidence.parquet": build_two_case_evidence(),
        "mashiki_event_state.parquet": build_mashiki_event_state(),
        "yokoe_matched_endpoint.parquet": build_yokoe_matched_endpoint(),
        "candidate_ledger.parquet": build_candidate_ledger(),
        "case_geometries.parquet": build_case_geometries(),
        "claim_sensitivity.parquet": build_claim_sensitivity(),
    }
    for name, frame in outputs.items():
        if frame.empty:
            raise ValueError(f"{name} is empty")
        write_staging(name, frame)


if __name__ == "__main__":
    main()
