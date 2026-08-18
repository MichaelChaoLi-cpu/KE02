#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
orthophoto_root="$repo_root/data/raw/plateau/mashiki/2020/orthophoto"
archive="$orthophoto_root/43443_mashiki-machi_2020_ortho_3_op.7z"
source_tiles="$orthophoto_root/source_tiles"
aoi_root="$orthophoto_root/aoi"
vrt="$aoi_root/mashiki_plateau_2020_source.vrt"
aoi="$aoi_root/mashiki_plateau_2020_reconstruction_validation_epsg3857.tif"
mesh_codes=(49301634 49301635 49301636 49301644 49301645 49301646 49301654 49301655 49301656)

if [[ ! -s "$archive" ]]; then
  printf 'missing archive: %s\n' "$archive" >&2
  exit 1
fi

mkdir -p "$source_tiles" "$aoi_root"

members=()
for mesh_code in "${mesh_codes[@]}"; do
  members+=("43443_mashiki-machi_ortho/${mesh_code}.tif")
done

bsdtar -xf "$archive" --strip-components 1 -C "$source_tiles" "${members[@]}"

for mesh_code in "${mesh_codes[@]}"; do
  tile="$source_tiles/${mesh_code}.tif"
  if [[ ! -s "$tile" ]]; then
    printf 'missing extracted tile: %s\n' "$tile" >&2
    exit 1
  fi
  printf 'verified %s\n' "$tile"
done

clean_gdal=(env -u PROJ_LIB -u PROJ_DATA -u GDAL_DATA)
"${clean_gdal[@]}" gdalbuildvrt "$vrt" "$source_tiles"/*.tif
"${clean_gdal[@]}" gdalwarp \
  -overwrite \
  -te_srs EPSG:4326 -te 130.80632 32.78266 130.82768 32.80000 \
  -t_srs EPSG:3857 -tr 0.5 0.5 -r cubic \
  -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 -co BIGTIFF=IF_SAFER \
  "$vrt" "$aoi"

env -u PROJ_LIB -u PROJ_DATA -u GDAL_DATA \
  UV_CACHE_DIR=/private/tmp/uv-cache uv run python \
  "$repo_root/src/data/normalize_geotiff_crs.py" --epsg 3857 "$aoi"

"${clean_gdal[@]}" gdalinfo -checksum "$aoi"
