#!/usr/bin/env bash
# Extract the text of every page of the given works with Tesseract (Arabic), for the in-book search.
# Usage (from the library folder):  tools/ocr.sh 25 26
# Needs: poppler-utils (pdftoppm, pdfinfo), imagemagick (convert), tesseract with the "ara" model.
# Pages that are sideways are fixed by putting the angle in rot/<id> (90, 180 or 270) before running.
set -e
cd "$(dirname "$0")/.."
export OMP_THREAD_LIMIT=1
ocr_page() {
  id="$1"; p="$2"
  out="ocr/$id/$(printf %04d "$p").txt"
  [ -s "$out" ] && return
  tmp=$(mktemp -d)
  pdftoppm -r 170 -gray -f "$p" -l "$p" -png "pdfs/$id.pdf" "$tmp/pg" 2>/dev/null
  img=$(ls "$tmp"/pg*.png 2>/dev/null | head -1)
  if [ -n "$img" ]; then
    rot=$(cat "rot/$id" 2>/dev/null || true)
    if [ -n "$rot" ] && [ "$rot" != "0" ]; then convert "$img" -rotate "$rot" "$img"; fi
    tesseract "$img" stdout -l ara --psm 3 2>/dev/null > "$out.part" && mv "$out.part" "$out"
  fi
  rm -rf "$tmp"
}
export -f ocr_page
for id in "$@"; do
  mkdir -p "ocr/$id"
  n=$(pdfinfo "pdfs/$id.pdf" 2>/dev/null | awk '/^Pages/{print $2}')
  seq 1 "$n" | xargs -P "$(nproc)" -I{} bash -c "ocr_page $id {}"
  echo "$id: $(ls ocr/$id | wc -l) of $n pages"
done
