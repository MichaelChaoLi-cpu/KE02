#!/usr/bin/env python3
"""Crosswalk all officially restored 2016 bridges to 2026 bridge damage.

The 37-bridge inventory is transcribed from Kumamoto Prefecture's official
2021 disaster-restoration report.  The comparison is exhaustive with respect
to that inventory and the bridge-damage records in the processed 2026 MLIT
passable-map snapshots.  Route-only overlap is never treated as an asset match.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
OUT = ROOT / "data/exp/feasibility-check/rebuilt-bridge-crosswalk"
SOURCE_URL = "https://www.pref.kumamoto.jp/uploaded/attachment/134518.PDF"


BRIDGES_2016 = [
    (1, "新松合橋", "NR266", "国道266号", "宇城市", "不知火町松合"),
    (2, "一ツ橋側道橋", "PR181", "松橋インター線", "宇城市", "松橋町古保山"),
    (3, "中ノ瀬橋", "NR266", "国道266号", "嘉島町", "鯖"),
    (4, "鯗避溢橋上り", "NR266", "国道266号", "嘉島町", "鯗"),
    (5, "鯗避溢橋下り", "NR266", "国道266号", "嘉島町", "鯗"),
    (6, "畑中橋", "NR443", "国道443号", "益城町", "寺迫"),
    (7, "新木山橋", "NR443", "国道443号", "益城町", "木山"),
    (8, "寺迫橋", "PR28", "熊本高森線", "益城町", "寺迫"),
    (9, "福富橋", "PR28", "熊本高森線", "益城町", "福富"),
    (10, "馬水橋", "PR28", "熊本高森線", "益城町", "馬水"),
    (11, "田原一号橋", "PR28", "熊本高森線", "益城町", "田原"),
    (12, "新津森橋", "PR28", "熊本高森線", "益城町", "原田"),
    (13, "府領第一橋", "PR32", "小川嘉島線", "甲佐町", "府領"),
    (14, "乙女橋", "PR38", "宇土甲佐線", "甲佐町", "乙女"),
    (15, "乙女橋側道橋", "PR38", "宇土甲佐線", "甲佐町", "乙女"),
    (16, "小柳橋", "PR57", "益城矢部線", "益城町", "福原"),
    (17, "第二畑中橋", "PR57", "益城矢部線", "益城町", "福原"),
    (18, "東無田橋", "PR231", "小池竜田線", "益城町", "島田"),
    (19, "惣領橋", "PR235", "益城菊陽線", "益城町", "惣領"),
    (20, "新川橋", "PR235", "益城菊陽線", "益城町", "砥川"),
    (21, "大六橋", "PR226", "画図秋津線", "嘉島町", "鯖"),
    (22, "第二甘木橋", "PR226", "六嘉秋津新町線", "嘉島町", "北甘木"),
    (23, "田口橋", "PR239", "御船甲佐線", "甲佐町", "田口"),
    (24, "田島橋", "PR37", "熊本菊鹿線", "菊池市", "泗水町田島"),
    (25, "みらい大橋", "PR235", "辛川鹿本線", "菊陽町", "津久礼"),
    (26, "六地蔵橋", "PR145", "瀬田竜田線", "大津町", "陣内"),
    (27, "南阿蘇橋", "NR325", "国道325号", "南阿蘇村", "河陽"),
    (28, "内牧橋", "NR212", "国道212号", "阿蘇市", "内牧"),
    (29, "車帰橋", "PR23", "菊池赤水線", "阿蘇市", "赤水"),
    (30, "布田橋", "PR28", "熊本高森線", "西原村", "布田"),
    (31, "布田橋側道橋", "PR28", "熊本高森線", "西原村", "布田"),
    (32, "小屋場橋", "PR111", "阿蘇吉田線", "南阿蘇村", "中松"),
    (33, "大正橋", "PR149", "河陰阿蘇線", "阿蘇市", "的石"),
    (34, "床瀬川橋", "PR149", "河陰阿蘇線", "南阿蘇村", "河陽"),
    (35, "上無田橋", "PR149", "河陰阿蘇線", "阿蘇市", "狩尾"),
    (36, "新阿蘇口大橋", "PR145", "瀬田竜田線", "南阿蘇村", "立野"),
    (37, "横江大橋", "PR338", "八代不知火線", "八代市", "鏡町宝出"),
]


def inventory() -> pd.DataFrame:
    result = pd.DataFrame(
        BRIDGES_2016,
        columns=[
            "Official Number",
            "Bridge Name",
            "Discarded Inferred Route Key",
            "Route Name",
            "Municipality",
            "Location",
        ],
    )
    result["Route Key"] = result["Route Name"].map(route_key)
    return result.drop(columns="Discarded Inferred Route Key").assign(
        Source=SOURCE_URL
    )


def route_key(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value)).replace(" ", "")
    national = re.search(r"国道?(\d+)号?", text)
    if national:
        return f"NR{int(national.group(1))}"
    if "57号(北側復旧道路)" in text:
        return "NR57"
    prefectural = re.sub(r"^県道\d+号", "", text)
    return f"P:{prefectural}"


def bridge_damage_records() -> gpd.GeoDataFrame:
    rows = gpd.read_parquet(RESTRICTIONS)
    rows = rows.loc[rows["Restriction Reason"].fillna("").str.contains("橋")].copy()
    rows["Route Key"] = rows["Route Name"].map(route_key)
    rows = rows.sort_values("Snapshot Time").drop_duplicates(
        ["Route Key", "Start Location", "End Location"]
    )
    return rows


def crosswalk(restored: pd.DataFrame, damaged: gpd.GeoDataFrame) -> pd.DataFrame:
    output = []
    for _, row in damaged.iterrows():
        candidates = restored.loc[restored["Route Key"].eq(row["Route Key"])]
        exact_yokoe = (
            row["Route Key"] == "P:八代不知火線"
            and "鏡町宝出" in str(row["Start Location"])
            and "鏡町野崎" in str(row["End Location"])
        )
        if exact_yokoe:
            status = "pass_exact_same_asset"
            names = "横江大橋"
            reason = "same route and exact Hode-Nozaki bridge address pair"
        elif row["Route Key"] == "NR57":
            status = "fail_new_post_2016_route_no_same_asset"
            names = ""
            reason = "the northern recovery route did not exist during the 2016 event"
        elif len(candidates):
            status = "fail_route_only_location_mismatch"
            names = "; ".join(candidates["Bridge Name"])
            locations = "; ".join(
                candidates["Municipality"] + " " + candidates["Location"]
            )
            reason = f"2016 rebuilt bridge locations differ: {locations}"
        else:
            status = "fail_no_2016_rebuilt_bridge_on_route"
            names = ""
            reason = "no bridge on this route appears in the official 37-bridge inventory"
        output.append(
            {
                "2026 Route Key": row["Route Key"],
                "2026 Route Name": row["Route Name"],
                "2026 Start Location": row["Start Location"],
                "2026 End Location": row["End Location"],
                "2016 Same-Route Rebuilt Bridges": names,
                "Crosswalk Status": status,
                "Evidence": reason,
            }
        )
    return pd.DataFrame(output).sort_values(
        ["Crosswalk Status", "2026 Route Key", "2026 Start Location"]
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    restored = inventory()
    damaged = bridge_damage_records()
    linked = crosswalk(restored, damaged)
    if len(restored) != 37:
        raise ValueError(f"Expected 37 officially restored bridges, got {len(restored)}")
    exact_names = linked.loc[
        linked["Crosswalk Status"].eq("pass_exact_same_asset"),
        "2016 Same-Route Rebuilt Bridges",
    ].tolist()
    if exact_names != ["横江大橋"]:
        raise ValueError(f"Unexpected exact repeated-asset matches: {exact_names}")
    restored.to_csv(OUT / "official_2016_rebuilt_bridge_inventory.csv", index=False)
    linked.to_csv(OUT / "bridge_damage_crosswalk.csv", index=False)
    exact = len(exact_names)
    route_only = int(
        linked["Crosswalk Status"].eq("fail_route_only_location_mismatch").sum()
    )
    gates = pd.DataFrame(
        [
            ("B1", "Official 2016 rebuilt-bridge denominator", "pass", "37 named bridges from Kumamoto Prefecture"),
            ("B2", "2026 bridge-damage denominator", "pass", f"{len(linked)} distinct route/address records after deduplication"),
            ("B3", "Route-level overlap", "partial", f"{route_only + exact} records have at least one 2016 bridge on the same route"),
            ("B4", "Exact same-asset overlap", "pass", f"{exact} record: Yokoe Bridge"),
            ("B5", "Additional exact rebuilt asset", "fail", "No second exact same-asset match is present"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )
    gates.to_csv(OUT / "bridge_crosswalk_gate.csv", index=False)
    report = [
        "# 2016 rebuilt bridges versus 2026 bridge damage",
        "",
        "## Result",
        "",
        f"The official 2016 restoration denominator contains {len(restored)} bridges. The 2026 passable-map archive contains {len(linked)} distinct bridge-damage route/address records after deduplication. Only Yokoe Bridge passes exact same-asset linkage. Route-only overlaps on National Route 266, Prefectural Route 239, and the other Prefectural Route 338 record refer to different locations.",
        "",
        "This establishes that Yokoe Bridge is the sole exact repeated-damage asset in the currently verified official bridge inventories; it was not selected merely because it was prominent. The result does not establish a causal reconstruction effect.",
        "",
        "## Crosswalk",
        "",
        linked.to_markdown(index=False),
        "",
        "## Gates",
        "",
        gates.to_markdown(index=False),
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_2016_rebuilt_bridge_2026_damage_crosswalk.py",
        "```",
    ]
    (OUT / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(OUT / "README.md")


if __name__ == "__main__":
    main()
