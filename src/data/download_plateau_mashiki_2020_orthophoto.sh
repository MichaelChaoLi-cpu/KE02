#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
orthophoto_root="$repo_root/data/raw/plateau/mashiki/2020/orthophoto"
archive="$orthophoto_root/43443_mashiki-machi_2020_ortho_3_op.7z"
partial="$archive.part"
url="https://gic-plateau.s3.ap-northeast-1.amazonaws.com/2020/ortho/43443_mashiki-machi_2020_ortho_3_op.7z"

mkdir -p "$orthophoto_root"

if [[ -s "$archive" ]]; then
  printf 'exists  %s\n' "$archive"
else
  curl -fL --retry 5 --retry-all-errors --continue-at - \
    --output "$partial" "$url"
  mv "$partial" "$archive"
  printf 'saved   %s\n' "$archive"
fi

shasum -a 256 "$archive"
ls -lh "$archive"
