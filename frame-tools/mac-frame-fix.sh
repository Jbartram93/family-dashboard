#!/bin/bash
# ============================================================
# FRAME FIX — all-in-one. On the Mac, run ONLY this:
#
#   git clone https://github.com/Jbartram93/family-dashboard.git jd
#   cd jd/frame-tools && bash mac-frame-fix.sh
#
# It clones Wes Bos's PF1007L toolkit itself, checks the frame
# over USB, verifies root identity, and takes a FULL backup.
# Writes nothing to the frame before the backup succeeds.
# ============================================================
set -euo pipefail

REPO="$HOME/frame-hack"
[ -d "$REPO/.git" ] || git clone --depth 1 https://github.com/wesbos/photo-frame-dashboard.git "$REPO"
cd "$REPO"

echo "== 1/4 adb =="
if command -v adb >/dev/null; then
  ADB="adb"
else
  echo "-- downloading Google platform-tools (no brew needed)"
  curl -L -sS -o pt.zip https://dl.google.com/android/repository/platform-tools-latest-darwin.zip
  unzip -oq pt.zip && rm pt.zip
  ADB="$REPO/platform-tools/adb"
fi
"$ADB" version | head -1

echo "== 2/4 USB check — frame plugged in? =="
"$ADB" kill-server >/dev/null 2>&1 || true
"$ADB" start-server >/dev/null
"$ADB" devices -l
STATE=$("$ADB" get-state 2>/dev/null || echo none)
if [ "$STATE" = "device" ]; then
  echo "-- ADB: already authorized"
elif "$ADB" devices | grep -q unauthorized; then
  echo "-- tap 'Allow USB debugging' on the FRAME screen now (60s window)"
  for i in $(seq 1 30); do
    sleep 2
    STATE=$("$ADB" get-state 2>/dev/null || echo none)
    [ "$STATE" = "device" ] && break
  done
  [ "$STATE" = "device" ] || { echo "XX never authorized — replug, rerun"; exit 1; }
else
  echo "-- no USB ADB on this unit. NOTHING IS WRONG — this unit needs the"
  echo "   Wi-Fi route instead. Send this output to Hermes and say 'no usb adb'."
  exit 2
fi

echo "== 3/4 identity + root gate =="
HW=$("$ADB" shell getprop ro.hardware | tr -d '\r')
REL=$("$ADB" shell getprop ro.build.version.release | tr -d '\r')
FIRM=$("$ADB" shell getprop ro.build.display.id | tr -d '\r')
ID=$("$ADB" shell id | tr -d '\r')
echo "hardware=$HW  android=$REL"
echo "firmware=$FIRM"
echo "id=$ID"
echo "$HW" | grep -q sun8i || { echo "XX not the A33 board — STOP, send output to Hermes"; exit 3; }
echo "$ID" | grep -q "uid=0" || { echo "XX ADB present but not root — send output to Hermes ('no root')"; exit 3; }
echo "-- root ADB confirmed ✓"

echo "== 4/4 FULL BACKUP (every partition) =="
STAMP=$(date +%Y%m%d-%H%M%S)
BK="$HOME/frame-backup-$STAMP"; mkdir -p "$BK"
"$ADB" shell "cat /proc/partitions" | tr -d '\r'
OK=0; FAIL=0
for PART in $("$ADB" shell 'ls /dev/block/mmcblk0*' | tr -d '\r' | grep -E 'mmcblk0(p[0-9]+)?$'); do
  NAME=$(basename "$PART")
  echo "   pulling $NAME ..."
  if "$ADB" pull "$PART" "$BK/$NAME.img"; then OK=$((OK+1)); else FAIL=$((FAIL+1)); echo "   !! $NAME failed"; fi
done
echo "-- pulled $OK partitions, $FAIL failed"
du -sh "$BK"
echo ""
echo "██████████████████████████████████████████"
echo "██  BACKUP COMPLETE → $BK"
echo "██  Now paste THIS WHOLE OUTPUT to Hermes."
echo "██████████████████████████████████████████"
