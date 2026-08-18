#!/usr/bin/env python3
"""Download a bounded GSI XYZ layer and build a provenance-preserving GeoTIFF.

The source PNG tiles remain untouched under ``tiles/<z>/<x>/<y>.png``.  The
GeoTIFF is a derived convenience product in EPSG:3857 and is cropped to the
requested longitude/latitude bounding box.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import struct
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


GSI_XYZ_ROOT = "https://cyberjapandata.gsi.go.jp/xyz"
WEB_MERCATOR_ORIGIN = 20037508.342789244
WEB_MERCATOR_WIDTH = WEB_MERCATOR_ORIGIN * 2


@dataclass(frozen=True)
class TileResult:
    x: int
    y: int
    url: str
    relative_path: str
    status: str
    byte_count: int
    sha256: str
    error: str


def longitude_to_tile_x(longitude: float, zoom: int) -> int:
    return int((longitude + 180.0) / 360.0 * (2**zoom))


def latitude_to_tile_y(latitude: float, zoom: int) -> int:
    latitude = max(min(latitude, 85.05112878), -85.05112878)
    latitude_radians = math.radians(latitude)
    return int(
        (
            1.0
            - math.asinh(math.tan(latitude_radians)) / math.pi
        )
        / 2.0
        * (2**zoom)
    )


def validate_png(payload: bytes) -> None:
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("response is not a PNG")
    width, height = struct.unpack(">II", payload[16:24])
    if (width, height) != (256, 256):
        raise ValueError(f"unexpected PNG dimensions: {width}x{height}")


def validate_jpeg(payload: bytes) -> None:
    if len(payload) < 4 or payload[:2] != b"\xff\xd8":
        raise ValueError("response is not a JPEG")
    offset = 2
    while offset + 9 < len(payload):
        if payload[offset] != 0xFF:
            offset += 1
            continue
        marker = payload[offset + 1]
        offset += 2
        if marker in (0xD8, 0xD9):
            continue
        if marker == 0xDA:
            break
        segment_length = int.from_bytes(payload[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(payload):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = int.from_bytes(payload[offset + 3 : offset + 5], "big")
            width = int.from_bytes(payload[offset + 5 : offset + 7], "big")
            if (width, height) != (256, 256):
                raise ValueError(
                    f"unexpected JPEG dimensions: {width}x{height}"
                )
            return
        offset += segment_length
    raise ValueError("JPEG dimensions could not be read")


def validate_image(payload: bytes, extension: str) -> None:
    if extension == "png":
        validate_png(payload)
    else:
        validate_jpeg(payload)


def fetch_tile(
    layer: str,
    zoom: int,
    x: int,
    y: int,
    tile_root: Path,
    retries: int,
    extension: str,
) -> TileResult:
    destination = tile_root / str(zoom) / str(x) / f"{y}.{extension}"
    relative_path = destination.relative_to(tile_root.parent).as_posix()
    url = f"{GSI_XYZ_ROOT}/{layer}/{zoom}/{x}/{y}.{extension}"

    if destination.is_file() and destination.stat().st_size > 0:
        payload = destination.read_bytes()
        try:
            validate_image(payload, extension)
        except ValueError:
            destination.unlink()
        else:
            return TileResult(
                x=x,
                y=y,
                url=url,
                relative_path=relative_path,
                status="existing",
                byte_count=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                error="",
            )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "KE02-research-data-acquisition/1.0"},
    )
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
            validate_image(payload, extension)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(f".{extension}.part")
            temporary.write_bytes(payload)
            temporary.replace(destination)
            return TileResult(
                x=x,
                y=y,
                url=url,
                relative_path=relative_path,
                status="downloaded",
                byte_count=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
                error="",
            )
        except urllib.error.HTTPError as exc:
            last_error = str(exc)
            if exc.code == 404:
                break
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))

    return TileResult(
        x=x,
        y=y,
        url=url,
        relative_path=relative_path,
        status="failed",
        byte_count=0,
        sha256="",
        error=last_error,
    )


def write_manifest(results: list[TileResult], destination: Path) -> None:
    fields = list(asdict(results[0]).keys())
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def write_vrt(
    results: list[TileResult],
    tile_root: Path,
    destination: Path,
    zoom: int,
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
    band_count: int,
) -> None:
    tile_count_x = max_x - min_x + 1
    tile_count_y = max_y - min_y + 1
    raster_width = tile_count_x * 256
    raster_height = tile_count_y * 256
    tile_span = WEB_MERCATOR_WIDTH / (2**zoom)
    pixel_span = tile_span / 256
    upper_left_x = -WEB_MERCATOR_ORIGIN + min_x * tile_span
    upper_left_y = WEB_MERCATOR_ORIGIN - min_y * tile_span
    available = [result for result in results if result.status != "failed"]

    lines = [
        f'<VRTDataset rasterXSize="{raster_width}" rasterYSize="{raster_height}">',
        "  <SRS>EPSG:3857</SRS>",
        (
            "  <GeoTransform>"
            f"{upper_left_x:.12f}, {pixel_span:.12f}, 0.0, "
            f"{upper_left_y:.12f}, 0.0, {-pixel_span:.12f}"
            "</GeoTransform>"
        ),
    ]
    color_names = ("Red", "Green", "Blue", "Alpha")[:band_count]
    for band, color_name in enumerate(color_names, start=1):
        lines.append(f'  <VRTRasterBand dataType="Byte" band="{band}">')
        lines.append(f"    <ColorInterp>{color_name}</ColorInterp>")
        for result in available:
            source_path = tile_root.parent / result.relative_path
            relative_source = source_path.relative_to(destination.parent).as_posix()
            destination_x = (result.x - min_x) * 256
            destination_y = (result.y - min_y) * 256
            lines.extend(
                [
                    "    <SimpleSource>",
                    (
                        "      <SourceFilename relativeToVRT=\"1\">"
                        f"{relative_source}</SourceFilename>"
                    ),
                    f"      <SourceBand>{band}</SourceBand>",
                    '      <SrcRect xOff="0" yOff="0" xSize="256" ySize="256"/>',
                    (
                        f'      <DstRect xOff="{destination_x}" '
                        f'yOff="{destination_y}" xSize="256" ySize="256"/>'
                    ),
                    "    </SimpleSource>",
                ]
            )
        lines.append("  </VRTRasterBand>")
    lines.append("</VRTDataset>")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_geotiff(
    vrt_path: Path,
    output_path: Path,
    bbox: tuple[float, float, float, float],
) -> None:
    west, south, east, north = bbox
    earth_radius = 6378137.0

    def longitude_to_mercator_x(longitude: float) -> float:
        return earth_radius * math.radians(longitude)

    def latitude_to_mercator_y(latitude: float) -> float:
        latitude = max(min(latitude, 85.05112878), -85.05112878)
        return earth_radius * math.log(
            math.tan(math.pi / 4.0 + math.radians(latitude) / 2.0)
        )

    upper_left_x = longitude_to_mercator_x(west)
    upper_left_y = latitude_to_mercator_y(north)
    lower_right_x = longitude_to_mercator_x(east)
    lower_right_y = latitude_to_mercator_y(south)
    clean_environment = os.environ.copy()
    # An activated Conda environment can point Homebrew GDAL at an incompatible
    # PROJ/GDAL database.  This operation already uses source-CRS coordinates,
    # so let GDAL resolve its own compiled-in resource locations.
    clean_environment.pop("PROJ_LIB", None)
    clean_environment.pop("PROJ_DATA", None)
    clean_environment.pop("GDAL_DATA", None)
    subprocess.run(
        [
            "gdal_translate",
            "-of",
            "GTiff",
            "-projwin",
            str(upper_left_x),
            str(upper_left_y),
            str(lower_right_x),
            str(lower_right_y),
            "-co",
            "TILED=YES",
            "-co",
            "COMPRESS=DEFLATE",
            "-co",
            "PREDICTOR=2",
            "-co",
            "BIGTIFF=IF_SAFER",
            str(vrt_path),
            str(output_path),
        ],
        check=True,
        env=clean_environment,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--acquisition-date", required=True)
    parser.add_argument(
        "--bbox",
        required=True,
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    parser.add_argument("--zoom", type=int, default=18)
    parser.add_argument(
        "--extension",
        choices=("png", "jpg"),
        default="png",
        help="source tile image extension; GSI seamlessphoto uses jpg",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="build a transparent mosaic while retaining failed tiles in the manifest",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    band_count = 3 if args.extension == "jpg" else 4
    west, south, east, north = args.bbox
    if not (west < east and south < north):
        raise SystemExit("bbox must be WEST SOUTH EAST NORTH")

    min_x = longitude_to_tile_x(west, args.zoom)
    max_x = longitude_to_tile_x(east, args.zoom)
    min_y = latitude_to_tile_y(north, args.zoom)
    max_y = latitude_to_tile_y(south, args.zoom)
    coordinates = [
        (x, y)
        for x in range(min_x, max_x + 1)
        for y in range(min_y, max_y + 1)
    ]

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    tile_root = output_dir / "tiles"
    print(
        f"{args.name}: downloading {len(coordinates)} tiles "
        f"({min_x}:{max_x}, {min_y}:{max_y})"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                fetch_tile,
                args.layer,
                args.zoom,
                x,
                y,
                tile_root,
                args.retries,
                args.extension,
            )
            for x, y in coordinates
        ]
        results = [future.result() for future in futures]
    results.sort(key=lambda result: (result.y, result.x))

    manifest_path = output_dir / "tile_manifest.tsv"
    write_manifest(results, manifest_path)
    failures = [result for result in results if result.status == "failed"]
    metadata = {
        "name": args.name,
        "source": "Geospatial Information Authority of Japan (GSI)",
        "source_layer": args.layer,
        "source_url_template": (
            f"{GSI_XYZ_ROOT}/{args.layer}/{{z}}/{{x}}/{{y}}.{args.extension}"
        ),
        "acquisition_date": args.acquisition_date,
        "retrieval_date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "zoom": args.zoom,
        "bbox_wgs84": {
            "west": west,
            "south": south,
            "east": east,
            "north": north,
        },
        "tile_range": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
        },
        "tile_count_expected": len(results),
        "tile_count_available": len(results) - len(failures),
        "tile_count_failed": len(failures),
        "derived_geotiff_crs": "EPSG:3857",
        "attribution": "Geospatial Information Authority of Japan",
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if failures and not args.allow_missing:
        raise SystemExit(
            f"{len(failures)} tile downloads failed; inspect {manifest_path}"
        )

    vrt_path = output_dir / f"{args.name}.vrt"
    write_vrt(
        results,
        tile_root,
        vrt_path,
        args.zoom,
        min_x,
        max_x,
        min_y,
        max_y,
        band_count,
    )
    output_path = output_dir / f"{args.name}.tif"
    if output_path.exists():
        output_path.unlink()
    build_geotiff(vrt_path, output_path, tuple(args.bbox))
    print(f"created {output_path}")


if __name__ == "__main__":
    main()
