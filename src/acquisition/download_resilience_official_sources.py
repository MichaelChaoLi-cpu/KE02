"""Download compact official sources for the repeated-earthquake resilience study.

The script never overwrites an existing file. It records retrieval metadata and
SHA-256 hashes in a CSV manifest so later preprocessing can be reproduced.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


USER_AGENT = "KE02-research-acquisition/1.0 (official public data)"


STATIC_SOURCES = [
    (
        "mlit_traffic_census_2015_kumamoto_locations.csv",
        "https://www.mlit.go.jp/road/census/h27/data/csv/kasyo43.csv",
        "MLIT 2015 Kumamoto road-traffic census location-level basic table",
    ),
    (
        "mlit_traffic_census_2015_kumamoto_hourly.csv",
        "https://www.mlit.go.jp/road/census/h27/data/csv/zkntrf43.csv",
        "MLIT 2015 Kumamoto road-traffic census hourly traffic table",
    ),
    (
        "mlit_traffic_census_2021_kumamoto_locations.csv",
        "https://www.mlit.go.jp/road/census/r3/data/csv/kasyo43.csv",
        "MLIT 2021 Kumamoto road-traffic census location-level basic table",
    ),
    (
        "mlit_traffic_census_2021_kumamoto_hourly.csv",
        "https://www.mlit.go.jp/road/census/r3/data/csv/zkntrf43.csv",
        "MLIT 2021 Kumamoto road-traffic census hourly traffic table",
    ),
    (
        "mlit_2026_damage_report_06_2026-07-30_0630.pdf",
        "https://www.mlit.go.jp/common/002014313.pdf",
        "MLIT 2026 Kumamoto earthquake report 6 with E77 closure at the 05:00 road-status timestamp",
    ),
    (
        "mlit_2026_damage_report_07_2026-07-30_1030.pdf",
        "https://www.mlit.go.jp/common/002014352.pdf",
        "MLIT 2026 Kumamoto earthquake report 7 with E77 absent from closures at the 09:00 road-status timestamp",
    ),
    (
        "nexco_2026_kumamoto_road_status_report_03_2026-07-29_0100.pdf",
        "https://www.w-nexco.co.jp/emc/emcpdfs/20260729013804-01.pdf",
        "NEXCO West 2026 Kumamoto earthquake road status report 3 with closure starts",
    ),
    (
        "nexco_2026_kumamoto_road_status_report_05_2026-07-30_0950.pdf",
        "https://www.w-nexco.co.jp/emc/emcpdfs/20260730095002-01.pdf",
        "NEXCO West 2026 Kumamoto earthquake road status report 5 with reopening time",
    ),
    (
        "nexco_2026_kumamoto_road_status_report_07_2026-07-31_1800.pdf",
        "https://www.w-nexco.co.jp/emc/emcpdfs/20260731200251-01.pdf",
        "NEXCO West 2026 Kumamoto earthquake road status report 7 with emergency access time",
    ),
    (
        "nexco_2026_kumamoto_road_status_report_17_2026-08-13_2000.pdf",
        "https://www.w-nexco.co.jp/emc/emcpdfs/20260813201943-01.pdf",
        "NEXCO West 2026 Kumamoto earthquake road status report 17 with general reopening time",
    ),
    (
        "nexco_2026_kumamoto_road_status_report_18_2026-08-17_1400.pdf",
        "https://www.w-nexco.co.jp/emc/emcpdfs/20260817140053-01.pdf",
        "NEXCO West 2026 Kumamoto earthquake road status report 18 confirming reopening",
    ),
    (
        "qsr_2026_e3a_reopening_forecast_2026-08-17_1400.pdf",
        "https://www.qsr.mlit.go.jp/yatusiro/newstopics_files/20260817/20260817_kisha.pdf",
        "Kyushu Regional Development Bureau joint release announcing general traffic on E3A Yatsushiro-minami IC-Tanoura IC",
    ),
    (
        "qsr_2026_e3a_hinagu_tanoura_reopening_final_2026-08-18_0600.pdf",
        "https://www.qsr.mlit.go.jp/yatusiro/newstopics_files/20260818/20260818_kisha.pdf",
        "Kyushu Regional Development Bureau final release for E3A Hinagu IC-Tanoura IC",
    ),
    (
        "mlit_2016_damage_report_2016-04-17_1300.pdf",
        "https://www.mlit.go.jp/common/001127940.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_damage_report_2016-04-18_0600.pdf",
        "https://www.mlit.go.jp/common/001127953.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_damage_report_2016-04-21_0600.pdf",
        "https://www.mlit.go.jp/common/001128776.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_damage_report_2016-04-26_0430.pdf",
        "https://www.mlit.go.jp/common/001129380.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_damage_report_2016-04-26_1300.pdf",
        "https://www.mlit.go.jp/common/001129563.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_damage_report_2016-05-27_1200.pdf",
        "https://www.mlit.go.jp/common/001133025.pdf",
        "MLIT 2016 disaster report with road locations and restriction times",
    ),
    (
        "mlit_2016_road_recovery_timeline_overview.pdf",
        "https://www.mlit.go.jp/common/001129766.pdf",
        "MLIT 2016 road disruption and recovery timeline overview",
    ),
    (
        "mlit_2016_road_restoration_2016-04-20_0500.pdf",
        "https://www.mlit.go.jp/common/001128508.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-21_0600.pdf",
        "https://www.mlit.go.jp/common/001128837.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-22_0600.pdf",
        "https://www.mlit.go.jp/common/001128859.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-25_0600.pdf",
        "https://www.mlit.go.jp/common/001129180.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-26_0600.pdf",
        "https://www.mlit.go.jp/common/001129387.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-27_0600.pdf",
        "https://www.mlit.go.jp/common/001129718.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-04-28_0600.pdf",
        "https://www.mlit.go.jp/common/001129978.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mlit_2016_road_restoration_2016-05-09_0700.pdf",
        "https://www.mlit.go.jp/common/001130823.pdf",
        "MLIT 2016 general-road restoration map",
    ),
    (
        "mashiki_evacu_route_site_progress_2021-08-31.pdf",
        "https://www.town.mashiki.lg.jp/kiji0034786/3_4786_9683_up_v2iyyrgw.pdf",
        "Mashiki evacuation-route and evacuation-site progress table",
    ),
    (
        "kumamoto_takamori_four_laning_recovery_roadmap_2026.pdf",
        "https://www.pref.kumamoto.jp/uploaded/attachment/312427.pdf",
        "Kumamoto recovery roadmap with four-laning completion dates",
    ),
    (
        "mashiki_2016_response_verification_report_2017-11.pdf",
        "https://www.town.mashiki.lg.jp/kiji0032410/3_2410_1633_up_j7cvpcog.pdf",
        "Mashiki 2016 earthquake response verification report",
    ),
    (
        "mashiki_urban_master_plan_current_conditions_2026.pdf",
        "https://www.town.mashiki.lg.jp/kiji0034980/3_4980_12304_up_2rtryrhi.pdf",
        "Mashiki urban master plan chapter documenting completed and post-2016 urban-planning roads",
    ),
    (
        "mashiki_east_west_section3_opening_newsletter_2025.pdf",
        "https://www.town.mashiki.lg.jp/kiji0037309/3_7309_22390_up_0nvz8usl.pdf",
        "Mashiki newsletter confirming the 16 March 2025 partial opening of East-West Line section 3",
    ),
    (
        "mashiki_second_north_south_opening_council_2026.pdf",
        "https://www.town.mashiki.lg.jp/kiji0037967/3_7967_shiryou1_4sah7wxp.pdf",
        "Mashiki council record confirming the February 2026 partial opening of Second North-South Line section 1",
    ),
    (
        "mashiki_yokomachi_kiyama_bridge_opening_council_2023.pdf",
        "https://www.town.mashiki.lg.jp/kiji0036503/3_6503_shiryou1_ia50k1uo.pdf",
        "Mashiki council record confirming the 3 September 2023 opening of Kiyama Bridge and surrounding Yokomachi roads",
    ),
]

REPORT_INDEX_URL = "https://www.pref.kumamoto.jp/soshiki/222/276831.html"

ARCGIS_LAYERS = [
    (
        "mashiki_road_network_routes",
        "https://services8.arcgis.com/axHvRSDfbBIXHkRF/ArcGIS/rest/services/"
        "%E9%81%93%E8%B7%AF%E7%B6%B2%E5%9B%B3/FeatureServer/1",
    ),
    (
        "mashiki_urban_planning_transport_facilities",
        "https://services8.arcgis.com/axHvRSDfbBIXHkRF/ArcGIS/rest/services/"
        "%E9%83%BD%E5%B8%82%E8%A8%88%E7%94%BB%E6%B1%BA%E5%AE%9A%E6%83%85%E5%A0%B1/FeatureServer/6",
    ),
    (
        "mashiki_urban_planning_land_readjustment",
        "https://services8.arcgis.com/axHvRSDfbBIXHkRF/ArcGIS/rest/services/"
        "%E9%83%BD%E5%B8%82%E8%A8%88%E7%94%BB%E6%B1%BA%E5%AE%9A%E6%83%85%E5%A0%B1/FeatureServer/10",
    ),
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return {
            "status": "existing",
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
            "content_type": "",
            "last_modified": "",
            "etag": "",
        }

    with urllib.request.urlopen(request(url), timeout=120) as response:
        headers = response.headers
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=f".{destination.name}.", suffix=".part", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            while chunk := response.read(1024 * 1024):
                temporary.write(chunk)
    if temporary_path.stat().st_size == 0:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Empty download: {url}")
    temporary_path.replace(destination)
    return {
        "status": "downloaded",
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "content_type": headers.get_content_type(),
        "last_modified": headers.get("Last-Modified", ""),
        "etag": headers.get("ETag", ""),
    }


def discover_prefecture_reports() -> list[tuple[str, str, str]]:
    with urllib.request.urlopen(request(REPORT_INDEX_URL), timeout=60) as response:
        html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(html)
    reports: list[tuple[str, str, str]] = []
    for href, text in parser.links:
        match = re.search(r"第\s*(\d+)\s*報", text)
        if not match or not href.lower().endswith(".pdf"):
            continue
        number = int(match.group(1))
        url = urllib.parse.urljoin(REPORT_INDEX_URL, href)
        reports.append((f"kumamoto_prefecture_2026_damage_report_{number:02d}.pdf", url, text))
    unique = {name: (name, url, text) for name, url, text in reports}
    result = [unique[name] for name in sorted(unique)]
    if len(result) < 2:
        raise RuntimeError(f"Unexpected report discovery result: {len(result)} PDFs")
    return result


def fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(request(url), timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def export_arcgis_layer(
    name: str, layer_url: str, root: Path, project_root: Path
) -> list[dict[str, Any]]:
    layer_dir = root / "mashiki_arcgis"
    layer_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = layer_dir / f"{name}_metadata.json"
    geojson_path = layer_dir / f"{name}.geojson"

    metadata_url = f"{layer_url}?f=pjson"
    metadata = fetch_json(metadata_url)
    if "error" in metadata:
        raise RuntimeError(f"ArcGIS metadata error for {name}: {metadata['error']}")
    if not metadata_path.exists():
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not geojson_path.exists():
        object_id = metadata.get("objectIdField", "OBJECTID")
        page_size = int(metadata.get("maxRecordCount", 2000))
        features: list[dict[str, Any]] = []
        offset = 0
        while True:
            query = urllib.parse.urlencode(
                {
                    "where": "1=1",
                    "outFields": "*",
                    "outSR": "4326",
                    "f": "geojson",
                    "resultOffset": offset,
                    "resultRecordCount": page_size,
                    "orderByFields": object_id,
                }
            )
            page = fetch_json(f"{layer_url}/query?{query}")
            if "error" in page:
                raise RuntimeError(f"ArcGIS query error for {name}: {page['error']}")
            batch = page.get("features", [])
            features.extend(batch)
            if len(batch) < page_size:
                break
            offset += len(batch)
        collection = {
            "type": "FeatureCollection",
            "name": name,
            "source": layer_url,
            "features": features,
        }
        geojson_path.write_text(
            json.dumps(collection, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    rows = []
    for path, url, title in [
        (metadata_path, metadata_url, f"{name} metadata"),
        (geojson_path, layer_url, f"{name} GeoJSON export"),
    ]:
        rows.append(
            {
                "source_group": "Mashiki ArcGIS",
                "title": title,
                "source_url": url,
                "local_path": path.relative_to(project_root).as_posix(),
                "status": "exported" if path == geojson_path else "metadata",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "content_type": "application/geo+json" if path == geojson_path else "application/json",
                "last_modified": "",
                "etag": "",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    project_root = args.root.resolve()
    raw_root = project_root / "data" / "raw" / "official_resilience"
    rows: list[dict[str, Any]] = []

    for filename, url, title in STATIC_SOURCES:
        if filename.startswith("mlit_traffic_census_"):
            group = "mlit_traffic_census"
        elif filename.startswith("mlit_2016_"):
            group = "mlit_2016_roads"
        elif filename.startswith("mlit_2026_"):
            group = "mlit_2026_roads"
        elif filename.startswith("nexco_2026_"):
            group = "nexco_2026_roads"
        elif filename.startswith("qsr_2026_"):
            group = "qsr_2026_roads"
        else:
            group = "interventions"
        destination = raw_root / group / filename
        result = download_file(url, destination)
        rows.append(
            {
                "source_group": group,
                "title": title,
                "source_url": url,
                "local_path": destination.relative_to(project_root).as_posix(),
                **result,
            }
        )

    for filename, url, title in discover_prefecture_reports():
        destination = raw_root / "kumamoto_prefecture_2026_damage_reports" / filename
        result = download_file(url, destination)
        rows.append(
            {
                "source_group": "Kumamoto Prefecture 2026 damage reports",
                "title": title,
                "source_url": url,
                "local_path": destination.relative_to(project_root).as_posix(),
                **result,
            }
        )

    for name, layer_url in ARCGIS_LAYERS:
        rows.extend(export_arcgis_layer(name, layer_url, raw_root, project_root))

    retrieved_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["retrieved_at_utc"] = retrieved_at

    manifest = raw_root / "manifest.csv"
    fieldnames = [
        "source_group",
        "title",
        "source_url",
        "local_path",
        "status",
        "bytes",
        "sha256",
        "content_type",
        "last_modified",
        "etag",
        "retrieved_at_utc",
    ]
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "manifest": manifest.relative_to(project_root).as_posix(),
        "records": len(rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
        "downloaded": sum(row["status"] == "downloaded" for row in rows),
        "existing": sum(row["status"] == "existing" for row in rows),
        "arcgis_files": sum(row["source_group"] == "Mashiki ArcGIS" for row in rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
