#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
plateau_root="${project_root}/data/raw/plateau/mashiki/2023"
ortho_root="${plateau_root}/orthophoto"
city_root="${plateau_root}/citygml"
ortho_archive="${ortho_root}/43443_mashiki-machi_aac_2023_ortho_1_op.zip"
city_archive="${city_root}/43443_mashiki-machi_city_2023_citygml_2_op.zip"
mesh_codes=(49301634 49301635 49301636 49301644 49301645 49301646 49301654 49301655 49301656)

mkdir -p "${ortho_root}/source_tiles" "${ortho_root}/aoi" "${city_root}/aoi_source"

for mesh_code in "${mesh_codes[@]}"; do
  unzip -o "${ortho_archive}" "${mesh_code}.tif" -d "${ortho_root}/source_tiles"
  unzip -o "${city_archive}" \
    "udx/bldg/${mesh_code}_bldg_6697_op.gml" \
    "udx/tran/${mesh_code}_tran_6697_op.gml" \
    -d "${city_root}/aoi_source"
done

unzip -o "${city_archive}" \
  'codelists/*' 'metadata/*' README.md 43443_2023_indexmap_op.pdf \
  specification/43443_city_2023_specification_op.pdf \
  -d "${city_root}/aoi_source"

clean_gdal=(env -u PROJ_LIB -u PROJ_DATA -u GDAL_DATA)
"${clean_gdal[@]}" gdalbuildvrt \
  "${ortho_root}/aoi/mashiki_plateau_fy2023_source.vrt" \
  "${ortho_root}"/source_tiles/*.tif

"${clean_gdal[@]}" gdalwarp \
  -overwrite \
  -te_srs EPSG:4326 -te 130.80632 32.78266 130.82768 32.80000 \
  -t_srs EPSG:3857 -tr 0.5 0.5 -r cubic \
  -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 -co BIGTIFF=IF_SAFER \
  "${ortho_root}/aoi/mashiki_plateau_fy2023_source.vrt" \
  "${ortho_root}/aoi/mashiki_plateau_fy2023_pre_2026_baseline_epsg3857.tif"
