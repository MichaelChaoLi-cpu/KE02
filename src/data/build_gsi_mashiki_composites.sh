#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
gsi_root="${project_root}/data/raw/gsi/orthophoto_z18/mashiki"
combined_root="${gsi_root}/combined"

mkdir -p "${combined_root}"

clean_gdal=(env -u PROJ_LIB -u PROJ_DATA -u GDAL_DATA)

"${clean_gdal[@]}" gdalwarp \
  -overwrite -srcalpha -dstalpha \
  -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 \
  "${gsi_root}/2016-04-16_post_mainshock_nishihara_supplement/mashiki_2016-04-16_post_mainshock_nishihara.tif" \
  "${gsi_root}/2016-04-16_post_mainshock/mashiki_2016-04-16_post_mainshock.tif" \
  "${combined_root}/mashiki_2016-04-16_post_mainshock_combined.tif"

"${clean_gdal[@]}" gdalwarp \
  -overwrite -srcalpha -dstalpha \
  -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 \
  "${gsi_root}/2026-07-29_08-02_post_event_kumamoto2_supplement/mashiki_2026-07-29_08-02_post_event_kumamoto2.tif" \
  "${gsi_root}/2026-08-03_post_event/mashiki_2026-08-03_post_event.tif" \
  "${combined_root}/mashiki_2026-07-29_08-03_post_event_combined.tif"
