#!/bin/zsh
# One tall PDF page from a built household page.
# usage: generator/tools/pdf.sh <household.html> <pageHeightPx from measure.py> <out.pdf>
T=$(mktemp -d)
C="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HERE=$(cd "$(dirname "$0")" && pwd)
SRC="$1"
BASE="file://$(cd "$(dirname "$SRC")" && pwd | sed 's/ /%20/g')/"
PH=$2; S=$(( (PH+3)/4 )); L=()
for i in 0 1 2 3; do
  h=$S; [ $i -eq 3 ] && h=$((PH-3*S))
  sed -e "s#<head>#<head><base href=\"$BASE\">#" -e "s#</style>#html,body{overflow:hidden}.page{width:390px;max-width:none;margin:-$((i*S))px 0 0}</style>#" "$SRC" > $T/slice.html
  "$C" --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=390,$h --virtual-time-budget=6000 --screenshot=$T/p$i.png "file://$T/slice.html#all" 2>/dev/null
  sips -s format jpeg -s formatOptions 90 $T/p$i.png --out $T/p$i.jpg >/dev/null; L+=($T/p$i.jpg)
done
swift "$HERE/img2pdf.swift" "$3" 390 $PH $L
rm -rf $T
