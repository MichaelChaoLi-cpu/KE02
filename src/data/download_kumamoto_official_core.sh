#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
raw="$repo_root/data/raw"

download() {
  local destination="$1"
  local url="$2"
  mkdir -p "$(dirname "$destination")"
  if [[ -s "$destination" ]]; then
    printf 'exists  %s\n' "$destination"
    return
  fi
  curl -fL --retry 5 --retry-all-errors --silent --show-error \
    -o "$destination" "$url"
  printf 'saved   %s\n' "$destination"
}

# GSI interpreted damage and active-fault GeoTIFF archives.
download "$raw/gsi/2016/landslide/gsi_2016_kumamoto_landslide_kml.zip" \
  "https://www.gsi.go.jp/common/000143456.zip"
download "$raw/gsi/2026/landslide/gsi_2026_kumamoto_yatsushiro_landslide_geojson.zip" \
  "https://www1.gsi.go.jp/geowww/saigai/20260728_kumamoto/hokai/kumamoto_yatsushiro0814.zip"
download "$raw/gsi/reference/active_fault_geotiff/gsi_active_fault_181_aso.zip" \
  "https://www1.gsi.go.jp/geowww/katsudanso/geotiff/181.zip"
download "$raw/gsi/reference/active_fault_geotiff/gsi_active_fault_182_kumamoto_revised.zip" \
  "https://www1.gsi.go.jp/geowww/katsudanso/geotiff/182.zip"
download "$raw/gsi/reference/active_fault_geotiff/gsi_active_fault_193_yatsushiro_revised.zip" \
  "https://www1.gsi.go.jp/geowww/katsudanso/geotiff/193.zip"
download "$raw/gsi/reference/active_fault_geotiff/gsi_active_fault_194_hinagu.zip" \
  "https://www1.gsi.go.jp/geowww/katsudanso/geotiff/194.zip"

# USGS event metadata and version-pinned ShakeMap products.
for event_spec in \
  "2016 us20005hzn atlas 1594162199388" \
  "2016 us20005iis atlas 1594162257045" \
  "2026 us6000tgb9 us 1785310381887"; do
  read -r year event_id source revision <<< "$event_spec"
  event_dir="$raw/usgs/$year/$event_id"
  download "$event_dir/event.geojson" \
    "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=$event_id&format=geojson"
  product_root="https://earthquake.usgs.gov/product/shakemap/$event_id/$source/$revision/download"
  for product in raster.zip shape.zip grid.xml stationlist.json rupture.json info.json; do
    download "$event_dir/$product" "$product_root/$product"
  done
done

# MLIT road restriction, passability, and ETC2.0 mean-speed snapshots.
road_root="https://www.mlit.go.jp/road/saigai/r8kumamoto"
for stem in \
  map \
  260729data 2607291200data \
  2607300800data 2607301200data 2607301600data \
  2607310800data 2607311600data \
  2608011800data 2608021800data \
  2608031200data 2608031600data \
  2608041300data 2608041600data \
  2608051300data 2608061300data 2608071600data \
  2608080900data 2608090900data 2608101200data \
  2608111500data 2608121200data 2608131200data \
  2608140900data 2608170900data; do
  download "$raw/mlit/2026/road_passability/$stem.zip" "$road_root/$stem.zip"
done

# Versioned official damage-report snapshots.
download "$raw/reports/2016/kumamoto_prefecture_damage_report_2025-04-11.pdf" \
  "https://www.pref.kumamoto.jp/uploaded/attachment/277850.pdf"
download "$raw/reports/2026/fdma_damage_report_no55_2026-08-17.pdf" \
  "https://www.fdma.go.jp/disaster/info/items/20260728kumamotojishin55.pdf"
download "$raw/reports/2026/mlit_damage_report_no43_2026-08-17.pdf" \
  "https://www.mlit.go.jp/common/002016935.pdf"
download "$raw/reports/2026/mlit_damage_location_maps_2026-08-17.pdf" \
  "https://www.mlit.go.jp/common/002016930.pdf"

# z14 orthophoto tiles used only for coverage and cloud screening.
for tile_spec in \
  "mashiki 20160414kumamoto_0415dol1 14145 6610" \
  "mashiki 20160414kumamoto_0416dol1 14145 6610" \
  "mashiki 20260729kumamoto_kumamoto1_0803do 14145 6610" \
  "mashiki 20260729kumamoto_kumamoto2_0729_0802do 14145 6610" \
  "uki 20160414kumamoto_0415dol3 14139 6618" \
  "uki 20160414kumamoto_0416dol2 14139 6618" \
  "uki 20260729kumamoto_kumamoto3_0731_0801do 14139 6618" \
  "uki 20260729kumamoto_kumamoto4_0730do 14139 6618" \
  "hikawa 20160414kumamoto_0415dol3 14139 6622" \
  "hikawa 20160414kumamoto_0416dol2 14139 6622" \
  "hikawa 20160414kumamoto_0420dol05 14139 6622" \
  "hikawa 20260729kumamoto_yatsushiro_0729do 14139 6622" \
  "hikawa 20260729kumamoto_kumamoto4_0730do 14139 6622"; do
  read -r site layer x y <<< "$tile_spec"
  download "$raw/gsi/orthophoto_quicklook/$site/${layer}_z14_${x}_${y}.png" \
    "https://cyberjapandata.gsi.go.jp/xyz/$layer/14/$x/$y.png"
done

printf '\nZIP integrity check\n'
while IFS= read -r -d '' archive; do
  unzip -t "$archive" >/dev/null
  printf 'ok      %s\n' "$archive"
done < <(find "$raw" -type f -name '*.zip' -print0)
