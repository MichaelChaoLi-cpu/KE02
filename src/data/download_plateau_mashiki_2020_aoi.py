#!/usr/bin/env python3
"""Download only the Mashiki pilot meshes from the official PLATEAU 2020 ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

import requests
from remotezip import RemoteZip


ARCHIVE_URL = (
    "https://assets.cms.plateau.reearth.io/assets/7d/"
    "87c397-d921-4bf5-a182-91709a1677de/"
    "43443_mashiki-machi_2020_citygml_4_op.zip"
)
DATASET_URL = (
    "https://www.geospatial.jp/ckan/dataset/"
    "plateau-43443-mashiki-machi-2020"
)
RESOURCE_ID = "5837dc9c-75ca-4a59-a94d-573af4b564b2"
ARCHIVE_ROOT = "43443_mashiki-machi_2020_citygml_4_op"
MESH_CODES = (
    "49301634",
    "49301635",
    "49301636",
    "49301644",
    "49301645",
    "49301646",
    "49301654",
    "49301655",
    "49301656",
)
CITY_OBJECT_MEMBER = "{http://www.opengis.net/citygml/2.0}cityObjectMember"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_city_objects(path: Path) -> int:
    count = 0
    for _, element in ElementTree.iterparse(path, events=("end",)):
        if element.tag == CITY_OBJECT_MEMBER:
            count += 1
        element.clear()
    return count


def copy_member(archive: RemoteZip, member: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with archive.open(member) as source:
                shutil.copyfileobj(source, temporary, length=1024 * 1024)
            temporary.flush()
            os.fsync(temporary.fileno())
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    os.replace(temporary_path, destination)


def support_member(member: str) -> bool:
    if member.endswith("/"):
        return False
    relative = PurePosixPath(member).relative_to(ARCHIVE_ROOT)
    if not relative.parts:
        return False
    return (
        relative.parts[0] in {"codelists", "metadata", "specification"}
        or relative.name == "README.md"
        or relative.name.endswith("_indexmap_op.pdf")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "data/raw/plateau/mashiki/2020/citygml/aoi_source",
    )
    parser.add_argument(
        "--force", action="store_true", help="Replace files already present."
    )
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    response = requests.head(ARCHIVE_URL, timeout=60, allow_redirects=True)
    response.raise_for_status()
    server_metadata = {
        "content_length": int(response.headers.get("content-length", 0)) or None,
        "etag": response.headers.get("etag"),
        "last_modified": response.headers.get("last-modified"),
    }

    with RemoteZip(ARCHIVE_URL) as archive:
        names = archive.namelist()
        building_members: list[str] = []
        for mesh_code in MESH_CODES:
            suffix = f"/udx/bldg/{mesh_code}_bldg_6697_op.gml"
            matches = [name for name in names if name.endswith(suffix)]
            if len(matches) != 1:
                raise RuntimeError(
                    f"Expected one building member for {mesh_code}; found {matches}"
                )
            building_members.extend(matches)

        members = building_members + [name for name in names if support_member(name)]
        for member in members:
            relative = PurePosixPath(member).relative_to(ARCHIVE_ROOT)
            destination = output_root.joinpath(*relative.parts)
            if destination.is_file() and destination.stat().st_size > 0 and not args.force:
                print(f"exists  {destination}")
                continue
            copy_member(archive, member, destination)
            print(f"saved   {destination}")

    file_records = []
    total_city_objects = 0
    for mesh_code in MESH_CODES:
        path = output_root / "udx/bldg" / f"{mesh_code}_bldg_6697_op.gml"
        count = count_city_objects(path)
        total_city_objects += count
        file_records.append(
            {
                "mesh_code": mesh_code,
                "relative_path": str(path.relative_to(output_root)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "city_object_members": count,
            }
        )
        print(f"verified {mesh_code}: {count:,} city objects")

    manifest = {
        "dataset_url": DATASET_URL,
        "resource_id": RESOURCE_ID,
        "archive_url": ARCHIVE_URL,
        "archive_server_metadata": server_metadata,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection": {
            "reason": "Same nine 1 km meshes as the Mashiki FY2023 pilot AOI",
            "mesh_codes": list(MESH_CODES),
        },
        "files": file_records,
        "total_city_object_members": total_city_objects,
    }
    manifest_path = output_root.parent / "metadata.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"manifest {manifest_path}")
    print(f"total    {total_city_objects:,} city objects")


if __name__ == "__main__":
    main()
