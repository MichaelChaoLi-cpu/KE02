#!/usr/bin/env python3
"""Assign an authoritative EPSG CRS to a GeoTIFF without resampling pixels."""

from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.crs import CRS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--epsg", type=int, required=True)
    arguments = parser.parse_args()
    with rasterio.open(arguments.path, "r+") as dataset:
        transform = dataset.transform
        shape = (dataset.height, dataset.width, dataset.count)
        dataset.crs = CRS.from_epsg(arguments.epsg)
    with rasterio.open(arguments.path) as dataset:
        if dataset.crs.to_epsg() != arguments.epsg:
            raise RuntimeError(f"failed to assign EPSG:{arguments.epsg}")
        if dataset.transform != transform or (
            dataset.height,
            dataset.width,
            dataset.count,
        ) != shape:
            raise RuntimeError("CRS assignment changed raster structure")
    print(f"assigned EPSG:{arguments.epsg} to {arguments.path}")


if __name__ == "__main__":
    main()
