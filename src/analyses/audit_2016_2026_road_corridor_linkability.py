#!/usr/bin/env python3
"""Audit whether official 2016 road-recovery evidence links to 2026 corridors.

This is a feasibility/process analysis. It transcribes the dated corridor events
from physical page 11 (printed page 10) of the official MLIT overview, extracts
aggregate closure counts from eight dated MLIT maps, and matches route/end-point
labels to the processed 2026 restriction archive. It does not create a road-level
restoration outcome.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_2016 = ROOT / "data/raw/official_resilience/mlit_2016_roads"
OVERVIEW = RAW_2016 / "mlit_2016_road_recovery_timeline_overview.pdf"
FINAL_DAMAGE_REPORT = RAW_2016 / "mlit_2016_damage_report_2016-05-27_1200.pdf"
RAW_NEXCO_2026 = ROOT / "data/raw/official_resilience/nexco_2026_roads"
RAW_MLIT_2026 = ROOT / "data/raw/official_resilience/mlit_2026_roads"
RAW_QSR_2026 = ROOT / "data/raw/official_resilience/qsr_2026_roads"
NEXCO_REPORT_03 = RAW_NEXCO_2026 / "nexco_2026_kumamoto_road_status_report_03_2026-07-29_0100.pdf"
NEXCO_REPORT_05 = RAW_NEXCO_2026 / "nexco_2026_kumamoto_road_status_report_05_2026-07-30_0950.pdf"
NEXCO_REPORT_17 = RAW_NEXCO_2026 / "nexco_2026_kumamoto_road_status_report_17_2026-08-13_2000.pdf"
NEXCO_REPORT_18 = RAW_NEXCO_2026 / "nexco_2026_kumamoto_road_status_report_18_2026-08-17_1400.pdf"
MLIT_REPORT_06 = RAW_MLIT_2026 / "mlit_2026_damage_report_06_2026-07-30_0630.pdf"
MLIT_REPORT_07 = RAW_MLIT_2026 / "mlit_2026_damage_report_07_2026-07-30_1030.pdf"
QSR_E3A_FORECAST = (
    RAW_QSR_2026 / "qsr_2026_e3a_reopening_forecast_2026-08-17_1400.pdf"
)
QSR_E3A_FINAL = (
    RAW_QSR_2026
    / "qsr_2026_e3a_hinagu_tanoura_reopening_final_2026-08-18_0600.pdf"
)
RESTRICTIONS_2026 = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
SNAPSHOT_COVERAGE_2026 = (
    ROOT / "data/processed/kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
)
OUT = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage"
FEASIBILITY_OUT = ROOT / "data/exp/feasibility-check"


EVENTS_2016 = [
    ("2016-04-14", "kyushu_expressway", "九州自動車道", "南関IC", "えびのIC", "closed_for_inspection", "all_traffic"),
    ("2016-04-14", "kyushu_chuo_expressway", "九州中央自動車道", "嘉島JCT", "小池高山IC", "closed_for_inspection", "all_traffic"),
    ("2016-04-15", "kyushu_expressway", "九州自動車道", "南関IC", "益城熊本空港IC", "reopened", "general_traffic"),
    ("2016-04-15", "kyushu_expressway", "九州自動車道", "松橋IC", "えびのIC", "reopened", "general_traffic"),
    ("2016-04-16", "kyushu_expressway", "九州自動車道", "古賀IC", "栗野IC", "closed_for_inspection", "all_traffic"),
    ("2016-04-16", "kyushu_chuo_expressway", "九州中央自動車道", "嘉島JCT", "小池高山IC", "closed_for_inspection", "all_traffic"),
    ("2016-04-16", "kyushu_expressway", "九州自動車道", "古賀IC", "植木IC", "reopened", "general_traffic"),
    ("2016-04-16", "kyushu_expressway", "九州自動車道", "八代IC", "栗野IC", "reopened", "general_traffic"),
    ("2016-04-16", "national_routes_3_57_aggregate", "国道3号・57号", "", "", "six_sections_closed", "all_traffic"),
    ("2016-04-16", "national_routes_3_57_aggregate", "国道3号・57号", "", "", "four_sections_reopened", "general_traffic"),
    ("2016-04-18", "milk_road", "ミルクロード", "", "", "opened", "vehicles_under_4t"),
    ("2016-04-19", "kyushu_expressway", "九州自動車道", "植木IC", "益城熊本空港IC", "opened", "freight_and_support_vehicles"),
    ("2016-04-20", "national_route_443", "国道443号", "", "", "opened", "general_traffic"),
    ("2016-04-22", "green_road_minamiaso", "グリーンロード南阿蘇", "", "", "opened", "general_traffic"),
    ("2016-04-26", "kyushu_expressway", "九州自動車道", "嘉島JCT", "八代IC", "reopened", "general_traffic"),
    ("2016-04-26", "kyushu_chuo_expressway", "九州中央自動車道", "嘉島JCT", "小池高山IC", "reopened", "general_traffic"),
]


OFFICIAL_2026_COVERAGE = {
    "嘉島JCT|益城熊本空港IC": "NEXCO2026-R001",
    "嘉島JCT|小池高山IC": "MLIT2026-R003",
    "八代IC|松橋IC": "NEXCO2026-R002",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", "", text).replace("インターチェンジ", "IC")


def canonical_pair(start: object, end: object) -> str:
    values = sorted(value for value in (normalize_text(start), normalize_text(end)) if value)
    return "|".join(values) if len(values) == 2 else ""


def classify_2026_route(value: object) -> str:
    text = normalize_text(value)
    if text == "九州自動車道":
        return "kyushu_expressway"
    if "九州中央自動車道" in text:
        return "kyushu_chuo_expressway"
    if "南九州西回り自動車道" in text or "南九州自動車道(西回り)" in text or text == "南九州自動車道":
        return "minami_kyushu_expressway"
    if "北側復旧道路" in text and "57号" in text:
        return "national_route_57_north_recovery"
    if text in {"3号", "国道3号"}:
        return "national_route_3"
    if "443号" in text:
        return "national_route_443"
    return ""


def extract_highway_closure_intervals() -> pd.DataFrame:
    """Parse dated expressway closure intervals from physical page 19."""
    result = subprocess.run(
        [
            "pdftotext",
            "-f",
            "19",
            "-l",
            "19",
            "-layout",
            str(FINAL_DAMAGE_REPORT),
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    current_route = ""
    current_start = ""
    current_end = ""
    rows: list[dict[str, object]] = []
    time_pattern = re.compile(
        r"(?P<sm>\d{1,2})/(?P<sd>\d{1,2})\s*(?P<sh>\d{1,2}):(?P<smin>\d{2})"
        r"[（(]規制開始[）)]\s*[～~]\s*"
        r"(?P<em>\d{1,2})/(?P<ed>\d{1,2})\s*(?P<eh>\d{1,2}):(?P<emin>\d{2})"
        r"[（(]規制解除[）)]"
    )
    for raw_line in result.stdout.splitlines():
        line = unicodedata.normalize("NFKC", raw_line).strip()
        route_match = re.search(r"道路名\s*:\s*(.+)$", line)
        if route_match:
            current_route = route_match.group(1).strip()
            current_start = ""
            current_end = ""
            continue
        time_match = time_pattern.search(line)
        if not time_match or not current_route:
            continue
        segment_text = line[: time_match.start()].strip()
        segment_text = re.sub(r"^区間名\s*:\s*", "", segment_text)
        if "~" in segment_text:
            start, end = segment_text.split("~", 1)
            current_start, current_end = start.strip(), end.strip()
        if not current_start or not current_end:
            continue
        route_key = classify_2026_route(current_route)
        if not route_key:
            continue
        started = datetime(
            2016,
            int(time_match.group("sm")),
            int(time_match.group("sd")),
            int(time_match.group("sh")),
            int(time_match.group("smin")),
        )
        ended = datetime(
            2016,
            int(time_match.group("em")),
            int(time_match.group("ed")),
            int(time_match.group("eh")),
            int(time_match.group("emin")),
        )
        rows.append(
            {
                "Interval ID": f"MLIT2016-I{len(rows) + 1:03d}",
                "Route Key": route_key,
                "Route Name": current_route,
                "From Location": current_start,
                "To Location": current_end,
                "Endpoint Pair": canonical_pair(current_start, current_end),
                "Restriction Start": started,
                "Restriction End": ended,
                "Observed Closure Hours": (ended - started).total_seconds() / 3600,
                "Source PDF": FINAL_DAMAGE_REPORT.relative_to(ROOT).as_posix(),
                "Source Physical Page": 19,
                "Source Printed Page": 19,
                "Source SHA256": sha256_file(FINAL_DAMAGE_REPORT),
                "Evidence Unit": "named_highway_interval",
                "Interpretation Limit": "Named official interval; route equivalence still requires endpoint and geometry checks",
            }
        )
    intervals = pd.DataFrame(rows)
    if intervals.empty:
        raise ValueError("No relevant highway closure intervals parsed")
    return intervals


def pdf_compact_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return normalize_text(result.stdout)


def build_official_2026_reopening_intervals() -> pd.DataFrame:
    """Create source-validated covering-corridor reopening intervals."""
    report03 = pdf_compact_text(NEXCO_REPORT_03)
    report05 = pdf_compact_text(NEXCO_REPORT_05)
    report17 = pdf_compact_text(NEXCO_REPORT_17)
    report18 = pdf_compact_text(NEXCO_REPORT_18)
    mlit_report06 = pdf_compact_text(MLIT_REPORT_06)
    mlit_report07 = pdf_compact_text(MLIT_REPORT_07)
    qsr_e3a_forecast = pdf_compact_text(QSR_E3A_FORECAST)
    qsr_e3a_final = pdf_compact_text(QSR_E3A_FINAL)
    checks = [
        (report03, ["益城熊本空港IC~えびのIC", "7月28日16時27分"]),
        (report05, ["益城熊本空港IC~松橋IC", "9時04分"]),
        (report17, ["松橋IC~えびのIC", "8月14日", "6時00分"]),
        (report18, ["8/14(金曜)6:00", "一般車両通行可"]),
        (
            mlit_report06,
            ["■道路(7/3005:00時点)", "E77九州中央道(嘉島JCT~小池高山IC)", "3路線17区間"],
        ),
        (
            mlit_report07,
            ["■道路(7/3009:00時点)", "2路線12区間", "E3九州道(松橋IC~えびのIC)"],
        ),
        (
            qsr_e3a_forecast,
            [
                "八代JCT~田浦IC間",
                "7月28日(火曜)",
                "16時27分~",
                "八代南IC~田浦IC",
                "8月18日(火曜)6時00分頃",
            ],
        ),
        (
            qsr_e3a_final,
            ["8月18日6時00分", "日奈久ICから田浦IC間の通行止めを解除"],
        ),
    ]
    for text, tokens in checks:
        missing = [token for token in tokens if token not in text]
        if missing:
            raise ValueError(f"Official report validation failed; missing {missing}")

    rows = [
        {
            "Official 2026 Interval ID": "NEXCO2026-R001",
            "Route Key": "kyushu_expressway",
            "Route Name": "E3 九州自動車道",
            "From Location": "益城熊本空港IC",
            "To Location": "松橋IC",
            "Endpoint Pair": canonical_pair("益城熊本空港IC", "松橋IC"),
            "Restriction Start": pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo"),
            "General Traffic Reopening": pd.Timestamp("2026-07-30 09:04", tz="Asia/Tokyo"),
            "Reopening Time Precision": "minute",
            "Observed Closure Hours": (pd.Timestamp("2026-07-30 09:04", tz="Asia/Tokyo") - pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo")).total_seconds() / 3600,
            "Start Source PDF": NEXCO_REPORT_03.relative_to(ROOT).as_posix(),
            "Start Source Page": 1,
            "Start Source SHA256": sha256_file(NEXCO_REPORT_03),
            "End Source PDF": NEXCO_REPORT_05.relative_to(ROOT).as_posix(),
            "End Source Page": 1,
            "End Source SHA256": sha256_file(NEXCO_REPORT_05),
            "Interpretation": "The official reopening section contains Mashiki Kumamoto Airport IC-Kashima JCT.",
        },
        {
            "Official 2026 Interval ID": "NEXCO2026-R002",
            "Route Key": "kyushu_expressway",
            "Route Name": "E3 九州自動車道",
            "From Location": "松橋IC",
            "To Location": "えびのIC",
            "Endpoint Pair": canonical_pair("松橋IC", "えびのIC"),
            "Restriction Start": pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo"),
            "General Traffic Reopening": pd.Timestamp("2026-08-14 06:00", tz="Asia/Tokyo"),
            "Reopening Time Precision": "approximately_hour",
            "Observed Closure Hours": (pd.Timestamp("2026-08-14 06:00", tz="Asia/Tokyo") - pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo")).total_seconds() / 3600,
            "Start Source PDF": NEXCO_REPORT_03.relative_to(ROOT).as_posix(),
            "Start Source Page": 1,
            "Start Source SHA256": sha256_file(NEXCO_REPORT_03),
            "End Source PDF": NEXCO_REPORT_17.relative_to(ROOT).as_posix(),
            "End Source Page": 1,
            "End Source SHA256": sha256_file(NEXCO_REPORT_17),
            "Confirmation Source PDF": NEXCO_REPORT_18.relative_to(ROOT).as_posix(),
            "Confirmation Source Page": 4,
            "Confirmation Source SHA256": sha256_file(NEXCO_REPORT_18),
            "Interpretation": "The official reopening section contains Matsuhashi IC-Yatsushiro IC.",
        },
        {
            "Official 2026 Interval ID": "MLIT2026-R003",
            "Route Key": "kyushu_chuo_expressway",
            "Route Name": "E77 九州中央自動車道",
            "From Location": "嘉島JCT",
            "To Location": "小池高山IC",
            "Endpoint Pair": canonical_pair("嘉島JCT", "小池高山IC"),
            "Restriction Start": pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo"),
            "General Traffic Reopening": pd.Timestamp("2026-07-30 09:04", tz="Asia/Tokyo"),
            "Reopening Time Precision": "minute_harmonized",
            "Observed Closure Hours": (pd.Timestamp("2026-07-30 09:04", tz="Asia/Tokyo") - pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo")).total_seconds() / 3600,
            "Start Source PDF": MLIT_REPORT_06.relative_to(ROOT).as_posix(),
            "Start Source Page": 2,
            "Start Source SHA256": sha256_file(MLIT_REPORT_06),
            "End Source PDF": NEXCO_REPORT_05.relative_to(ROOT).as_posix(),
            "End Source Page": 1,
            "End Source SHA256": sha256_file(NEXCO_REPORT_05),
            "Confirmation Source PDF": MLIT_REPORT_07.relative_to(ROOT).as_posix(),
            "Confirmation Source Page": 2,
            "Confirmation Source SHA256": sha256_file(MLIT_REPORT_07),
            "Interpretation": "MLIT report 6 lists the full E77 Kashima JCT-Koike Takayama IC corridor closed at the 05:00 road-status timestamp, while report 7 no longer lists E77 at 09:00; NEXCO independently records the connecting Kashima JCT-Mashiki TB release at 09:04. The harmonized minute endpoint is assigned to the joint northern release regime.",
        },
        {
            "Official 2026 Interval ID": "QSR2026-R004",
            "Route Key": "minami_kyushu_expressway",
            "Route Name": "E3A 南九州自動車道",
            "From Location": "八代南IC",
            "To Location": "田浦IC",
            "Endpoint Pair": canonical_pair("八代南IC", "田浦IC"),
            "Restriction Start": pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo"),
            "General Traffic Reopening": pd.Timestamp("2026-08-18 06:00", tz="Asia/Tokyo"),
            "Reopening Time Precision": "minute",
            "Observed Closure Hours": (
                pd.Timestamp("2026-08-18 06:00", tz="Asia/Tokyo")
                - pd.Timestamp("2026-07-28 16:27", tz="Asia/Tokyo")
            ).total_seconds()
            / 3600,
            "Start Source PDF": QSR_E3A_FORECAST.relative_to(ROOT).as_posix(),
            "Start Source Page": 1,
            "Start Source SHA256": sha256_file(QSR_E3A_FORECAST),
            "End Source PDF": QSR_E3A_FINAL.relative_to(ROOT).as_posix(),
            "End Source Page": 1,
            "End Source SHA256": sha256_file(QSR_E3A_FINAL),
            "Confirmation Source PDF": QSR_E3A_FORECAST.relative_to(ROOT).as_posix(),
            "Confirmation Source Page": 1,
            "Confirmation Source SHA256": sha256_file(QSR_E3A_FORECAST),
            "Interpretation": (
                "The joint official release assigns one general-traffic reopening time "
                "to Yatsushiro-minami IC-Tanoura IC. The final regional-bureau release "
                "confirms Hinagu IC-Tanoura IC at 06:00. Both nested segments therefore "
                "belong to one E3A reopening regime; the formal release overrides the "
                "lagging passable-map state."
            ),
        },
    ]
    return pd.DataFrame(rows)


def extract_snapshot_counts() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pattern = re.compile(r"mlit_2016_road_restoration_(\d{4}-\d{2}-\d{2})_(\d{4})\.pdf")
    for path in sorted(RAW_2016.glob("mlit_2016_road_restoration_*.pdf")):
        match = pattern.fullmatch(path.name)
        if not match:
            continue
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        compact = normalize_text(result.stdout)
        national = re.search(r"国道\((\d+)路線(\d+)箇所\)", compact)
        local = re.search(r"県道・政令市道\((\d+)箇所\)", compact)
        kumamoto_national = re.search(
            r"<熊本県>国道.*?など計(\d+)箇所", compact
        )
        local_section = compact[local.start() :] if local else ""
        kumamoto_prefectural = re.search(r"<熊本県>(\d+)箇所", local_section)
        kumamoto_city = re.search(r"<熊本市>(\d+)箇所", local_section)
        if not national or not local:
            raise ValueError(f"Could not parse closure totals from {path.name}")
        rows.append(
            {
                "Snapshot Time": pd.Timestamp(f"{match.group(1)} {match.group(2)[:2]}:{match.group(2)[2:]}"),
                "National Route Count": int(national.group(1)),
                "National Closure Sites": int(national.group(2)),
                "Prefectural and Municipal Closure Sites": int(local.group(1)),
                "Kumamoto National Closure Sites": (
                    int(kumamoto_national.group(1)) if kumamoto_national else pd.NA
                ),
                "Kumamoto Prefectural Closure Sites": (
                    int(kumamoto_prefectural.group(1)) if kumamoto_prefectural else pd.NA
                ),
                "Kumamoto City Closure Sites": (
                    int(kumamoto_city.group(1)) if kumamoto_city else pd.NA
                ),
                "Source PDF": path.relative_to(ROOT).as_posix(),
                "Source SHA256": sha256_file(path),
            }
        )
    counts = pd.DataFrame(rows).sort_values("Snapshot Time").reset_index(drop=True)
    if len(counts) != 8:
        raise ValueError(f"Expected eight dated MLIT maps, found {len(counts)}")
    return counts


def build_event_ledger() -> pd.DataFrame:
    source_hash = sha256_file(OVERVIEW)
    columns = [
        "Event Date",
        "Route Key",
        "Route Name",
        "From Location",
        "To Location",
        "Reported Event State",
        "Access Scope",
    ]
    events = pd.DataFrame(EVENTS_2016, columns=columns)
    events.insert(0, "Event ID", [f"MLIT2016-{index:03d}" for index in range(1, len(events) + 1)])
    events["Endpoint Pair"] = [
        canonical_pair(start, end)
        for start, end in zip(events["From Location"], events["To Location"], strict=True)
    ]
    events["Source PDF"] = OVERVIEW.relative_to(ROOT).as_posix()
    events["Source Physical Page"] = 11
    events["Source Printed Page"] = 10
    events["Source SHA256"] = source_hash
    events["Evidence Unit"] = "corridor_event"
    events["Interpretation Limit"] = (
        "Official corridor-level event; not a stable road-segment restoration observation"
    )
    return events


def build_linkage(
    events: pd.DataFrame,
    intervals: pd.DataFrame,
    restrictions: pd.DataFrame,
) -> pd.DataFrame:
    work = restrictions.copy()
    work["Route Key"] = work["Route Name"].map(classify_2026_route)
    work = work.loc[work["Route Key"].ne("")].copy()
    work["Endpoint Pair"] = [
        canonical_pair(start, end)
        for start, end in zip(work["Start Location"], work["End Location"], strict=True)
    ]

    evidence_2016 = pd.concat(
        [
            events[["Route Key", "Route Name", "Endpoint Pair"]],
            intervals[["Route Key", "Route Name", "Endpoint Pair"]],
        ],
        ignore_index=True,
    ).drop_duplicates()
    route_keys = sorted(set(evidence_2016["Route Key"]) | set(work["Route Key"]))
    rows: list[dict[str, object]] = []
    for route_key in route_keys:
        old = evidence_2016.loc[evidence_2016["Route Key"].eq(route_key)]
        new = work.loc[work["Route Key"].eq(route_key)]
        old_pairs = sorted(value for value in old["Endpoint Pair"].unique() if value)
        new_pairs = sorted(value for value in new["Endpoint Pair"].unique() if value)
        exact_pairs = sorted(set(old_pairs) & set(new_pairs))
        old_endpoints = {part for pair in old_pairs for part in pair.split("|")}
        new_endpoints = {part for pair in new_pairs for part in pair.split("|")}
        shared_endpoints = sorted(old_endpoints & new_endpoints)

        if exact_pairs:
            status = "exact_endpoint_pair"
        elif not old.empty and not new.empty and shared_endpoints:
            status = "shared_endpoint_only"
        elif not old.empty and not new.empty:
            status = "route_label_only"
        elif not old.empty:
            status = "2016_only"
        else:
            status = "2026_only"

        if route_key == "national_routes_3_57_aggregate":
            interpretation = "2016 route-group totals lack section identity; no defensible 2026 segment match."
        elif route_key == "national_route_57_north_recovery":
            interpretation = "The 2026 restriction concerns post-2016 replacement infrastructure; a 2016 same-segment outcome is structurally unavailable."
        elif status == "exact_endpoint_pair":
            interpretation = "Candidate repeated corridor with the same named endpoints in both event records."
        elif status == "shared_endpoint_only":
            interpretation = "Candidate route-level comparison; endpoints overlap but the reported sections differ."
        elif status == "route_label_only":
            interpretation = "Route label repeats, but segment equivalence is unverified."
        else:
            interpretation = "No cross-event corridor counterpart in the current evidence."

        rows.append(
            {
                "Route Key": route_key,
                "2016 Event Count": len(old),
                "2016 Route Names": "; ".join(sorted(old["Route Name"].unique())),
                "2016 Endpoint Pairs": "; ".join(old_pairs),
                "2026 Unique Record Count": int(new["Restriction Record ID"].nunique()),
                "2026 Feature-Snapshot Rows": len(new),
                "2026 Route Names": "; ".join(sorted(new["Route Name"].dropna().astype(str).unique())),
                "2026 Endpoint Pairs": "; ".join(new_pairs),
                "Exact Endpoint Pairs": "; ".join(exact_pairs),
                "Shared Endpoints": "; ".join(shared_endpoints),
                "Linkability Status": status,
                "Interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def build_matched_corridor_outcome_gate(
    intervals: pd.DataFrame,
    official_2026_intervals: pd.DataFrame,
    restrictions: pd.DataFrame,
    coverage: pd.DataFrame,
) -> pd.DataFrame:
    """Test whether exact repeated corridors have an explicit 2026 endpoint."""
    work = restrictions.copy()
    work["Route Key"] = work["Route Name"].map(classify_2026_route)
    work["Endpoint Pair"] = [
        canonical_pair(start, end)
        for start, end in zip(work["Start Location"], work["End Location"], strict=True)
    ]
    old_pairs = set(intervals["Endpoint Pair"].dropna()) - {""}
    new_pairs = set(work["Endpoint Pair"].dropna()) - {""}
    exact_pairs = sorted(old_pairs & new_pairs)
    observed_snapshots = coverage.loc[
        coverage["Restriction Layer Available"], "Snapshot Time"
    ].sort_values()
    latest_snapshot = observed_snapshots.max()
    rows: list[dict[str, object]] = []

    for endpoint_pair in exact_pairs:
        old = intervals.loc[intervals["Endpoint Pair"].eq(endpoint_pair)].sort_values(
            "Restriction Start"
        )
        new = work.loc[work["Endpoint Pair"].eq(endpoint_pair)].sort_values(
            "Snapshot Time"
        )
        active = new.loc[
            new["Observation State"].isin(
                ["active_full_closure", "active_emergency_access_only"]
            )
        ]
        lifted = new.loc[new["Observation State"].eq("restriction_lifted")]
        first_active = active["Snapshot Time"].min() if not active.empty else pd.NaT
        first_lifted = lifted["Snapshot Time"].min() if not lifted.empty else pd.NaT
        explicit_transition = (
            pd.notna(first_active)
            and pd.notna(first_lifted)
            and first_lifted > first_active
        )
        last_present = new["Snapshot Time"].max()
        present_latest = bool((new["Snapshot Time"] == latest_snapshot).any())
        later_snapshots = observed_snapshots.loc[observed_snapshots > last_present]
        first_absent_after_last = (
            later_snapshots.iloc[0] if not later_snapshots.empty else pd.NaT
        )

        covering_id = OFFICIAL_2026_COVERAGE.get(endpoint_pair, "")
        covering = official_2026_intervals.loc[
            official_2026_intervals["Official 2026 Interval ID"].eq(covering_id)
        ]
        has_covering_reopening = len(covering) == 1

        if has_covering_reopening:
            covering_row = covering.iloc[0]
            gate = "eligible_official_covering_corridor_reopening"
            endpoint = covering_row["General Traffic Reopening"]
            interpretation = (
                "A source-validated official reopening interval fully contains the exact named pair; "
                "the endpoint is eligible with the stated time precision."
            )
        elif explicit_transition:
            gate = "eligible_observed_active_to_lifted"
            endpoint = first_lifted
            interpretation = "The same named endpoint pair is explicitly observed active and later lifted."
        elif present_latest and not active.empty:
            gate = "right_censored_active_at_latest_snapshot"
            endpoint = pd.NaT
            interpretation = "The corridor remains explicitly restricted in the latest official snapshot."
        else:
            gate = "status_unknown_after_nonreporting"
            endpoint = pd.NaT
            interpretation = "The corridor disappears from later snapshots; non-reporting is not evidence of reopening."

        reported_starts = active["Restriction Start Time"].dropna()
        if has_covering_reopening:
            reported_start = covering.iloc[0]["Restriction Start"]
        else:
            reported_start = reported_starts.min() if not reported_starts.empty else pd.NaT
        lower_bound_hours = (
            (last_present - reported_start).total_seconds() / 3600
            if pd.notna(reported_start) and pd.notna(last_present) and not has_covering_reopening
            else pd.NA
        )
        restoration_hours = (
            (endpoint - reported_start).total_seconds() / 3600
            if pd.notna(endpoint) and pd.notna(reported_start)
            else pd.NA
        )
        route_names = sorted(set(old["Route Name"].astype(str)) | set(new["Route Name"].dropna().astype(str)))
        rows.append(
            {
                "Endpoint Pair": endpoint_pair,
                "Route Key": old["Route Key"].iloc[0],
                "Route Names": "; ".join(route_names),
                "2016 Interval Count": len(old),
                "2016 Closure Hours": "; ".join(
                    f"{value:.2f}" for value in old["Observed Closure Hours"]
                ),
                "2026 Unique Record Count": int(new["Restriction Record ID"].nunique()),
                "2026 Observation States": "; ".join(sorted(new["Observation State"].dropna().unique())),
                "2026 Reported Restriction Start": reported_start,
                "2026 First Active Snapshot": first_active,
                "2026 Last Present Snapshot": last_present,
                "2026 First Snapshot Absent After Last Presence": first_absent_after_last,
                "Present in Latest Snapshot": present_latest,
                "Latest Official Snapshot": latest_snapshot,
                "Explicit Same-Pair Lifted Snapshot": first_lifted,
                "Observed Duration Lower Bound (hours)": lower_bound_hours,
                "Restoration Endpoint": endpoint,
                "Restoration Time (hours)": restoration_hours,
                "Covering Official Interval ID": covering_id,
                "Covering Reopening Time Precision": (
                    covering.iloc[0]["Reopening Time Precision"] if has_covering_reopening else ""
                ),
                "Restoration Outcome Eligible": bool(has_covering_reopening or explicit_transition),
                "2026 Outcome Gate": gate,
                "Interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def write_audited_question_feasibility(outcome_gate: pd.DataFrame) -> None:
    eligible = int(outcome_gate["Restoration Outcome Eligible"].sum())
    exact_pairs = len(outcome_gate)
    rows = [
        {
            "ID": "RQ1",
            "Audited Status": "weakly-testable",
            "Evidence Now Available": f"{exact_pairs} exact named 2016-2026 highway corridor pairs; official 2016 closure intervals; {eligible} source-validated 2026 covering-corridor reopening endpoints; valid 2016/2026 ShakeMap samples for all exact pairs",
            "Binding Gap": f"Only {eligible} exact pair(s) are fully covered by a source-validated 2026 reopening interval; no road-level common-support or counterfactual sample",
            "Permissible Claim": "Pilot corridor restoration contrasts and censored-duration bounds only",
        },
        {
            "ID": "RQ2",
            "Audited Status": "weakly-testable",
            "Evidence Now Available": "20 completed intervention candidates; 12 candidate route-name matches; Route 57 North Recovery Road is observed in the 2026 restriction archive",
            "Binding Gap": "Zero interventions have verified completed-subsegment geometry or treatment eligibility",
            "Permissible Claim": "Intervention evidence-readiness and named case studies only",
        },
        {
            "ID": "RQ3",
            "Audited Status": "not-yet-testable",
            "Evidence Now Available": "Versioned road restrictions and a partial official road network",
            "Binding Gap": "No validated passability panel, stable community nodes, or linked hospital/shelter travel-time outcome",
            "Permissible Claim": "No service-access or isolation effect claim",
        },
        {
            "ID": "RQ4",
            "Audited Status": "not-yet-testable",
            "Evidence Now Available": "Administrative geography and partial road geometry",
            "Binding Gap": "No outcome-linked terrain, demographic vulnerability, remoteness, or redundancy panel with subgroup support",
            "Permissible Claim": "No inequality or heterogeneity claim",
        },
        {
            "ID": "RQ5",
            "Audited Status": "partly-testable",
            "Evidence Now Available": "Explicit observation-coverage table, missingness rules, alternative restriction states, failed building-proxy gates, censoring rules, and formal-release-over-map source precedence",
            "Binding Gap": "Full repeated-shock sensitivity analysis awaits an estimable primary outcome and treatment/exposure sample",
            "Permissible Claim": "Measurement-boundary and evidence-gate results",
        },
    ]
    audited = pd.DataFrame(rows)
    audited.to_csv(FEASIBILITY_OUT / "audited_question_feasibility.csv", index=False)
    status_counts = audited["Audited Status"].value_counts()
    lines = [
        "# Audited Feasibility Judgment",
        "",
        "This evidence audit supersedes the filename/column-keyword diagnostic in `question_feasibility.csv`. The bundled scanner does not read Parquet or PDF evidence and therefore remains intentionally conservative.",
        "",
        "## Status",
        "",
        f"- `partly-testable`: {int(status_counts.get('partly-testable', 0))}",
        f"- `weakly-testable`: {int(status_counts.get('weakly-testable', 0))}",
        f"- `not-yet-testable`: {int(status_counts.get('not-yet-testable', 0))}",
        "",
        "## Decision",
        "",
        f"The official records now support {exact_pairs} exact named repeated-corridor pilot cases, and {eligible} have a source-validated 2026 restoration endpoint. This is enough for transparent pilot contrasts but not for an adjusted repeated-shock estimator. Preserve RQ1 as the target and expand the corridor sample rather than changing the question or advancing to manuscript handoff.",
        "",
        "## Reproducible Evidence",
        "",
        "- `audited_question_feasibility.csv`: question-level evidence judgment.",
        "- `2016-road-recovery-linkage/matched_corridor_2026_outcome_gate.csv`: exact-corridor endpoint gate.",
        "- `2016-road-recovery-linkage/mlit_2016_highway_closure_intervals.csv`: official 2016 start/end intervals.",
        "- `2016-road-recovery-linkage/corridor_linkage_audit.csv`: cross-event route/endpoint matching.",
    ]
    (FEASIBILITY_OUT / "AUDITED_README.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_readme(
    counts: pd.DataFrame,
    events: pd.DataFrame,
    intervals: pd.DataFrame,
    linkage: pd.DataFrame,
    outcome_gate: pd.DataFrame,
) -> None:
    exact = linkage.loc[linkage["Linkability Status"].eq("exact_endpoint_pair")]
    shared = linkage.loc[linkage["Linkability Status"].eq("shared_endpoint_only")]
    first = counts.iloc[0]
    last = counts.iloc[-1]
    lines = [
        "# 2016-2026 Road Corridor Linkability Audit",
        "",
        "## Result",
        "",
        f"- The official MLIT overview yields {len(events)} dated corridor events, and the final damage report yields {len(intervals)} named highway closure intervals.",
        f"- Route keys with at least one exact named endpoint pair across 2016 and 2026: {len(exact)}.",
        f"- Total exact endpoint pairs across those route keys: {sum(1 for value in exact['Exact Endpoint Pairs'] for pair in str(value).split('; ') if pair)}.",
        f"- Route keys with shared but non-identical endpoints: {len(shared)}.",
        f"- The eight dated maps show national-road closure sites falling from {int(first['National Closure Sites'])} to {int(last['National Closure Sites'])}, and prefectural/municipal closure sites from {int(first['Prefectural and Municipal Closure Sites'])} to {int(last['Prefectural and Municipal Closure Sites'])} between {first['Snapshot Time']:%Y-%m-%d %H:%M} and {last['Snapshot Time']:%Y-%m-%d %H:%M}.",
        "",
        "## Strongest Candidate",
        "",
        "- Kyushu Chuo Expressway, Kashima JCT-Koike Takayama IC, is an exact named repeated corridor: the same endpoints are explicitly recorded as closed/reopened in 2016 and as restricted in 2026.",
        "- Kyushu Expressway also contains exact repeated endpoint pairs, including Mashiki Kumamoto Airport IC-Kashima JCT and Matsuhashi IC-Yatsushiro IC, alongside additional shared-endpoint sections.",
        "- Minami Kyushu Expressway has a repeated route and a shared endpoint at Yatsushiro JCT, but no identical reported section in the current records.",
        "- National Route 57 North Recovery Road is a post-2016 replacement corridor observed as restricted in 2026; it is an intervention-performance case, not a same-segment before/after comparison.",
        "",
        "## Feasibility Judgment",
        "",
        "The new sources materially improve feasibility from aggregate map counts to several named corridor intervals. They still do not supply a complete 2016 local-road panel or a counterfactual sample for the central quasi-experimental claim. The exact corridors should be retained as pilot cases while the comparison sample is expanded.",
        f"Of the {len(outcome_gate)} exact pairs, {int(outcome_gate['Restoration Outcome Eligible'].sum())} have source-validated general-traffic reopening endpoints through official covering corridors. The E77 endpoint uses a harmonized minute from adjacent official MLIT status reports and the NEXCO connecting-section release; its source precision remains explicit.",
        "",
        "## Files",
        "",
        "- `mlit_2016_corridor_events.csv`: source-bound event transcription.",
        "- `mlit_2016_highway_closure_intervals.csv`: automatically parsed named start/end intervals.",
        "- `mlit_2016_snapshot_closure_counts.csv`: automated extraction from eight dated maps.",
        "- `corridor_linkage_audit.csv`: route and endpoint linkage to the 2026 restriction archive.",
        "- `matched_corridor_2026_outcome_gate.csv`: exact-pair censoring and restoration-endpoint audit.",
        "- `official_2026_highway_reopening_intervals.csv`: source-validated covering-corridor start/end intervals.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if (
        not OVERVIEW.exists()
        or not FINAL_DAMAGE_REPORT.exists()
        or not RESTRICTIONS_2026.exists()
        or not SNAPSHOT_COVERAGE_2026.exists()
        or any(
            not path.exists()
            for path in [
                NEXCO_REPORT_03,
                NEXCO_REPORT_05,
                NEXCO_REPORT_17,
                NEXCO_REPORT_18,
                MLIT_REPORT_06,
                MLIT_REPORT_07,
            ]
        )
    ):
        raise FileNotFoundError("Required 2016 reports or 2026 processed restrictions missing")
    OUT.mkdir(parents=True, exist_ok=True)
    counts = extract_snapshot_counts()
    events = build_event_ledger()
    intervals = extract_highway_closure_intervals()
    official_2026_intervals = build_official_2026_reopening_intervals()
    restrictions = pd.read_parquet(RESTRICTIONS_2026)
    coverage = pd.read_parquet(SNAPSHOT_COVERAGE_2026)
    required = {
        "Route Name",
        "Restriction Record ID",
        "Restriction Feature ID",
        "Start Location",
        "End Location",
        "Snapshot Time",
    }
    missing = sorted(required - set(restrictions.columns))
    if missing:
        raise ValueError(f"Missing 2026 variables: {missing}")
    linkage = build_linkage(events, intervals, restrictions)
    outcome_gate = build_matched_corridor_outcome_gate(
        intervals, official_2026_intervals, restrictions, coverage
    )

    events.to_csv(OUT / "mlit_2016_corridor_events.csv", index=False)
    intervals.to_csv(OUT / "mlit_2016_highway_closure_intervals.csv", index=False)
    official_2026_intervals.to_csv(OUT / "official_2026_highway_reopening_intervals.csv", index=False)
    counts.to_csv(OUT / "mlit_2016_snapshot_closure_counts.csv", index=False)
    linkage.to_csv(OUT / "corridor_linkage_audit.csv", index=False)
    outcome_gate.to_csv(OUT / "matched_corridor_2026_outcome_gate.csv", index=False)
    write_readme(counts, events, intervals, linkage, outcome_gate)
    write_audited_question_feasibility(outcome_gate)

    print(f"Saved: {OUT.relative_to(ROOT)}")
    print(
        "Checks: "
        f"{len(events)} corridor events; {len(intervals)} named intervals; {len(counts)} dated maps; "
        f"{int(linkage['Linkability Status'].eq('exact_endpoint_pair').sum())} exact route key; "
        f"{int(linkage['Linkability Status'].eq('shared_endpoint_only').sum())} shared-endpoint route key."
    )
    print(
        "Outcome gate: "
        f"{len(outcome_gate)} exact pairs; "
        f"{int(outcome_gate['Restoration Outcome Eligible'].sum())} eligible restoration endpoint."
    )


if __name__ == "__main__":
    main()
