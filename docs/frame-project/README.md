# Frame Project — AEEZO PF1007L → Home HQ kiosk

Converting the kitchen frame (AEEZO PF1007L, Allwinner A33, Android 6.0.1,
WebView 44) into a Wes Bos "Home HQ" kiosk frame — the same setup shown in
@wellavelino's tweet (Frameo + Home HQ = 1.9 s load, 0 jank, OTA updates).

Reference repo: https://github.com/wesbos/photo-frame-dashboard
Tweet: https://x.com/wellavelino/status/2112243166053101918

## Current state (2026-10-19)

| Item | Status |
|---|---|
| Dashboard (this repo) | ✅ live, WebView-44-safe CSS (no var()/grid/gap) |
| Auto Reload | ✅ set on frame (Idle 300 / Error 60 / reconnects ON) |
| USB ADB | ❌ absent on stock firmware (T3 failed — "no USB ADB") |
| Network ADB | ❓ untested (T3b) — needs one ADB-enable or T3c exploit |
| Root | ⚠️ "root available: yes" in Fully, but not exposed via ADB |
| Home HQ kiosk | ⬜ not installed yet |

## Conversion plan (in order)

1. **Get ADB once** — try in this order (Wes's test sequence):
   - T3: USB ADB (needs USB debugging enabled frame-side, or it may just work on some units)
   - T3b: network ADB (needs the frame to have it enabled — ours doesn't)
   - T3c: temporary ADB via the AiMOR connection (DNS redirect trick — needs router DNS control)
   - Route U: SD-card FEL → U-Boot (no ADB needed, but needs SD card + the full guide)
2. **Backup** — full eMMC image before anything else (script does this automatically once ADB works)
3. **Install Home HQ APK** — `adb install -r homehq.apk`
4. **Set dashboard URL** — `adb shell am start -n com.wesbos.homehq/.MainActivity --es url https://jbartram93.github.io/family-dashboard/`
5. **Set as Home app** — boots straight into the dashboard (Android 6 = manual chooser, see kiosk-readme.md)
6. **(Root path only) Upgrade WebView** 44 → 106 per allwinner-a33-pf1007l.md
7. **Retire Fully Kiosk** after Home HQ proves stable for a week

## Files

- `mac-frame-fix.sh` — one-command Mac script: ADB check → root gate → full backup
- `kiosk-readme.md` — Home HQ kiosk docs (start-at-boot, gestures, navigation service)
- `building-for-the-frame.md` — WebView 106 feature matrix (what CSS/JS is safe post-upgrade)

## Notes

- Fully remote admin: 192.168.1.60:2323 (pw in frame_healer.py) — toggle dies on reboot
- Frame's WiFi (AIC8800) randomizes MAC + IP every boot — root cause of every "it stopped
  updating" incident this week. MAC pin requires root; Home HQ's auto-retry makes it moot.
- Auto-heal watchdog: `frame_healer.py` cron on the mini PC (15 min, silent)
