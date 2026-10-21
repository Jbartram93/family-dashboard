"""
==========================================================
 DASHBOARD BUILDER — reads data.py, writes index.html
 Run:  python dashboard.py
 (Or let GitHub Actions do it on every push / every 30 min)
==========================================================

BIG PICTURE (how this file works):
  1. Import your data from data.py
  2. Fetch live extras: weather (Open-Meteo) + QQQ sparkline (Yahoo)
  3. Build each section of the page as HTML strings
  4. Write everything out to index.html

PYTHON IDEAS SHOWN HERE (each marked where used):
  - f-strings, loops, list comprehensions, dictionaries
  - urllib.request: fetching URLs with no external packages
  - zoneinfo: correct time zones even when GitHub's servers run UTC
  - try/except: the page still builds if the internet hiccups
"""

import calendar
import json
import urllib.request
from datetime import datetime, timedelta

from data import (
    PEOPLE_COLORS, EVENTS, DINNER_MENU, COUNTDOWNS, TODOS,
    HOME_COORDS, HOME_LABEL,
    FAMILY_NAME, REFRESH_MINUTES, CHART_SYMBOL, CHART_INTERVAL,
)

OUTPUT_FILE = "index.html"  # 'index.html' = clean URL on GitHub Pages

# ------------------------------------------------------------------
# "NOW" — in the family's time zone.
# GitHub's build servers run UTC, so without this, "today" would
# flip at 8 PM local time. zoneinfo fixes that. On Windows without
# the tzdata package it falls back to local time (which IS Eastern
# for Justin, so it's still correct).
# ------------------------------------------------------------------
try:
    from zoneinfo import ZoneInfo
    NOW = datetime.now(ZoneInfo("America/New_York"))
except Exception:
    NOW = datetime.now()  # fallback: builder's local time

TODAY = NOW.date()


# ==================================================================
# SMALL HELPERS
# ==================================================================

def person_color(person):
    """Safe dictionary read: unknown name -> gray, no crash."""
    return PEOPLE_COLORS.get(person, "#8b949e")


def time_sort_key(time_text):
    """'8:30 PM' -> time object so events sort chronologically
    (text sorting would put '5:30 PM' before '8:00 AM').
    Non-time labels like 'ALL DAY' sort to the start of the day."""
    try:
        return datetime.strptime(time_text, "%I:%M %p").time()
    except ValueError:
        return datetime.strptime("12:00 AM", "%I:%M %p").time()


def event_datetime(event):
    """Full datetime for an event (needed for 'next up' ordering).
    Attached to the same time zone as NOW so comparison works —
    naive vs aware datetimes can't be compared in Python."""
    day = datetime.strptime(event["date"], "%Y-%m-%d").date()
    naive = datetime.combine(day, time_sort_key(event["time"]))
    return naive.replace(tzinfo=NOW.tzinfo)


def human_time(dt):
    """'14:30' -> '2:30 PM' (lstrip('0') turns '04:30' -> '4:30')."""
    return dt.strftime("%I:%M %p").lstrip("0")


def fetch_json(url, seconds=8):
    """GET a URL and parse JSON. stdlib-only (no pip installs).
    Raises on network failure — callers wrap in try/except."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=seconds) as resp:
        return json.loads(resp.read().decode())


# ==================================================================
# LIVE DATA 1: WEATHER (Open-Meteo — free, no API key)
# ==================================================================

def weather_tagline(code, pop_max, next_rain_hour, temp):
    """Turn numbers into one human sentence. Keep it honest & short."""
    if pop_max >= 50:
        return f"Rain likely around {next_rain_hour} — grab the jacket"
    if pop_max >= 30:
        return "Chance of rain later — check the sky"
    if temp <= 40:
        return "Cold one — layer up"
    if temp >= 85:
        return "Hot one — hydrate"
    return "Clear skies — good day for it"


def build_weather():
    """Current temp + 6-hour strip + one-line tagline.
    If the fetch fails, return a placeholder — never break the page."""
    lat, lon = HOME_COORDS
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&hourly=temperature_2m,precipitation_probability"
        "&temperature_unit=fahrenheit"
        "&forecast_days=2&time_zone=America%2FNew_York"
    )
    try:
        data = fetch_json(url)
        cur = data["current"]
        temp = round(cur["temperature_2m"])

        # Hourly strip: next 6 hours starting from this hour
        # NOTE: Open-Meteo's hourly key is "time" (singular)
        times  = data["hourly"]["time"]
        temps  = data["hourly"]["temperature_2m"]
        probs  = data["hourly"]["precipitation_probability"]
        now_hr = NOW.strftime("%Y-%m-%dT%H:00")
        start  = times.index(now_hr) if now_hr in times else 0

        cells, pop_max, next_rain_hour = [], 0, "later"
        for i in range(start, min(start + 6, len(times))):
            hour = datetime.fromisoformat(times[i])
            pop = probs[i] or 0
            pop_max = max(pop_max, pop)
            if pop >= 50 and next_rain_hour == "later":
                next_rain_hour = human_time(hour)
            cells.append(
                f'<div class="wx-hour"><b>{human_time(hour).replace(":00", "")}'
                f'</b>{temps[i]:.0f}°<span>{pop}%</span></div>'
            )

        tagline = weather_tagline(cur["weather_code"], pop_max, next_rain_hour, temp)
        return (
            f'<div class="wx-now">{temp}°</div>'
            f'<div class="wx-hours">{"".join(cells)}</div>'
            f'<div class="wx-tag">{tagline}</div>'
        )
    except Exception:
        return '<div class="wx-tag">Weather unavailable</div>'


# ==================================================================
# LIVE DATA 2: QQQ SPARKLINE (Yahoo Finance — free, no key)
# Static SVG built at deploy time. Zero JavaScript, so it renders
# even on the frame's ancient Android 6 browser (TradingView didn't).
# ==================================================================

def build_sparkline():
    try:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{CHART_SYMBOL}"
               f"?interval={CHART_INTERVAL}m&range=5d")
        data = fetch_json(url)
        meta = data["chart"]["result"][0]["meta"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None][-24:]  # last 24 hourly bars
        if len(closes) < 2:
            raise ValueError("not enough data")

        # Map prices onto SVG coordinates (y flipped: high price = top)
        w, h, pad = 170, 44, 3
        lo, hi = min(closes), max(closes)
        span = (hi - lo) or 1
        pts = []
        for i, c in enumerate(closes):
            x = pad + i * (w - 2 * pad) / (len(closes) - 1)
            y = h - pad - (c - lo) / span * (h - 2 * pad)
            pts.append(f"{x:.1f},{y:.1f}")

        price   = closes[-1]
        prev    = meta.get("chartPreviousClose", price)
        change  = (price - prev) / prev * 100
        updown  = "up" if change >= 0 else "down"
        sign    = "+" if change >= 0 else ""

        return f"""
        <div class="spark-head">
          <span>NQ · {CHART_SYMBOL} · 1H</span>
          <span class="spark-price {updown}">{price:,.2f} <em>{sign}{change:.1f}%</em></span>
        </div>
        <svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">
          <polyline class="spark-line {updown}" points="{' '.join(pts)}"/>
        </svg>"""
    except Exception:
        return '<div class="spark-head"><span>NQ · QQQ</span></div><div class="wx-tag">Chart unavailable</div>'


# ==================================================================
# SECTION: NEXT UP (hero card — the single most important thing)
# ==================================================================

def build_next_up():
    """Find the next event (today or later), show a big countdown.
    Built at deploy time; the scheduled rebuild keeps it fresh."""
    upcoming = sorted(
        [e for e in EVENTS if event_datetime(e) >= NOW.replace(second=0, microsecond=0)],
        key=event_datetime,
    )
    if not upcoming:
        return '<div class="nu-label">NEXT UP</div><div class="nu-title">Nothing scheduled</div>'

    e = upcoming[0]
    dt = event_datetime(e)
    color = person_color(e["person"])

    # Countdown text: hours+minutes for today, otherwise day name/count
    delta = dt - NOW
    if delta.days == 0:
        total_mins = int(delta.total_seconds() // 60) + 1
        if total_mins <= 1:
            countdown = "NOW"
        elif total_mins < 60:
            countdown = f"IN {total_mins} MIN"
        else:
            hrs = total_mins // 60
            mins = total_mins % 60
            countdown = f"IN {hrs} HR {mins} MIN" if mins else f"IN {hrs} HR"
    elif delta.days == 1:
        countdown = "TOMORROW"
    elif delta.days < 7:
        countdown = dt.strftime("%A").upper()
    else:
        countdown = f"IN {delta.days} DAYS"

    return (
        f'<div class="nu-label" style="color:{color}">NEXT UP · {e["person"].upper()}</div>'
        f'<div class="nu-title">{e["title"]}</div>'
        f'<div class="nu-when">{human_time(dt)}'
        f'<span class="nu-count">{countdown}</span></div>'
    )


# ==================================================================
# SECTION: PER-PERSON COLUMNS (7-day mini agenda each)
# ==================================================================

def build_person_columns():
    cols = []
    # Everyone except the "Family" pseudo-person gets a column
    for person in [p for p in PEOPLE_COLORS if p != "Family"]:
        rows = []
        for offset in range(7):
            day = TODAY + timedelta(days=offset)
            iso = day.isoformat()
            # Their events + anything for the whole family
            day_events = sorted(
                [e for e in EVENTS if e["date"] == iso
                 and e["person"] in (person, "Family")],
                key=lambda e: time_sort_key(e["time"]),
            )
            for e in day_events:
                day_label = "Today" if offset == 0 else day.strftime("%a")
                rows.append(
                    f'<div class="pc-row"><b>{day_label}</b>'
                    f'{human_time(datetime.strptime(e["time"], "%I:%M %p"))}'
                    f'<span>{e["title"]}</span></div>'
                )
        body = "".join(rows) or '<div class="pc-empty">Nothing this week</div>'
        cols.append(
            f'<div class="pc"><div class="pc-head" '
            f'style="color:{person_color(person)}">{person.upper()}</div>{body}</div>'
        )
    return "".join(cols)


# ==================================================================
# SECTION: TO-DO BOARD (one column per person, clickable circles)
# ==================================================================

def build_todos():
    """Circles the family can tap on the frame. Two moving parts:
    HTML: <div class="todo" data-key="..."> — one per item.
    JS:   one small script (the ONLY JavaScript on the page) that
          toggles a 'done' class and saves state to localStorage,
          namespaced per person+item+date so it auto-resets daily.
    """
    cols = []
    for person, items in TODOS.items():
        color = person_color(person)
        rows = []
        for idx, item in enumerate(items):
            # data-key embeds the date so localStorage entries expire
            # naturally when the day changes — no reset logic needed.
            rows.append(
                f'<div class="todo" data-key="todo/{TODAY.isoformat()}/{person}/{idx}">'
                f'<span class="circle"></span>{item}</div>'
            )
        if not rows:
            rows.append('<div class="pc-empty">Nothing today</div>')
        cols.append(
            f'<div class="pc todo-col"><div class="pc-head" '
            f'style="color:{color}">{person.upper()}</div>{"".join(rows)}</div>'
        )
    board = "".join(cols)

    # The page's only script: click -> toggle checkmark -> persist.
    # localStorage has no expiry, so the date inside the key IS the
    # reset mechanism. Old days' entries are just ignored and overwritten.
    # Also runs the LIVE CLOCK — ticks on the device using its own clock
    # (build time is the no-JS fallback; this corrects it every second).
    script = """
<script>
(function(){
  function tickClock(){
    var el = document.getElementById('live-clock');
    if (!el) return;
    var now = new Date();
    var h = now.getHours(), m = now.getMinutes();
    var ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    el.innerHTML = h + ':' + (m < 10 ? '0' : '') + m + '<small>' + ampm + '</small>';
  }
  tickClock();
  setInterval(tickClock, 1000);

  var boxes = document.querySelectorAll('.todo');
  boxes.forEach(function(el){
    var key = el.getAttribute('data-key');
    if (localStorage.getItem(key) === '1') el.classList.add('done');
    el.addEventListener('click', function(){
      var on = el.classList.toggle('done');
      localStorage.setItem(key, on ? '1' : '0');
    });
  });
})();
</script>"""
    return board + script

def build_countdowns():
    items = []
    for c in COUNTDOWNS:
        target = datetime.strptime(c["date"], "%Y-%m-%d").date()
        days = (target - TODAY).days
        if days >= 0:  # past dates disappear automatically
            items.append(f'<div class="cd"><b>{days}</b> days · {c["label"]}</div>')
    return "".join(items)


# ==================================================================
# SECTION: DINNER MENU (Mon–Sun, today highlighted)
# ==================================================================

def build_dinner():
    today_index = TODAY.weekday()  # Mon=0 ... Sun=6, matches dict order
    parts = []
    for i, (day, meal) in enumerate(DINNER_MENU.items()):
        highlight = " today-row" if i == today_index else ""
        parts.append(
            f'<div class="menu-row{highlight}"><span class="menu-day">{day}</span>'
            f'<span class="menu-meal">{meal}</span></div>'
        )
    return "".join(parts)


# ==================================================================
# SECTION: MONTH GRID (zoomed out, current month)
# ==================================================================

def build_month():
    year, month = TODAY.year, TODAY.month
    first_mon0, days_in_month = calendar.monthrange(year, month)
    first_sun0 = (first_mon0 + 1) % 7  # convert Mon-start to Sun-start

    events_by_date = {}
    for e in EVENTS:
        events_by_date.setdefault(e["date"], []).append(e)

    parts = ['<table class="month-grid">']
    parts.append("<tr>" + "".join(
        f"<th>{d}</th>" for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    ) + "</tr>")

    cells = [""] * first_sun0 + list(range(1, days_in_month + 1))
    while len(cells) % 7:
        cells.append("")

    for i, cell in enumerate(cells):
        if i % 7 == 0:
            parts.append("<tr>")
        if cell == "":
            parts.append('<td class="blank"></td>')
        else:
            iso = datetime(year, month, cell).date().isoformat()
            today = " today" if cell == TODAY.day else ""
            chips = "".join(
                f'<div class="chip" style="background:{person_color(e["person"])}1a;'
                f'color:{person_color(e["person"])}">{e["title"][:18]}</div>'
                for e in events_by_date.get(iso, [])
            )
            parts.append(f'<td class="month-cell{today}">{cell}{chips}</td>')
        if i % 7 == 6:
            parts.append("</tr>")

    parts.append("</table>")
    return "".join(parts)


# ==================================================================
# PAGE SHELL — light theme, big type, readable across a room
# ==================================================================

CSS = """
  /* THEME — 2015-browser compatible (no CSS variables, no grid).
     The frame's WebView 44 drops var() and grid, so everything is
     hardcoded here. Change colors in ALL the marked spots.
     Deep turquoise theme: bg #2e8f83, cards #f0faf6, lines #6fbfae. */
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #2e8f83;   /* THEME: turquoise wall */
    color: #1c1b18;
    font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 19px;
    padding: 26px 30px;
  }
  b, th { font-variant-numeric: tabular-nums; }

  /* Header sits directly on the turquoise wall -> white text for contrast */
  .clock, .wx-now, .wx-hour b { color: #ffffff; }
  .date-line, .wx-tag, .countdowns, .footer { color: #d5f0ea; }
  .wx-hour { color: #bfe3da; }
  .cd b { color: #ffd166; }

  .grid { display: flex; }  /* old-WebView "grid": flex row, widths below */
  .grid > div { margin-right: 16px; }
  .grid > div:last-child { margin-right: 0; }
  /* hero row: NEXT UP wide, dinner + market split the rest */
  .hero-row > div:nth-child(1) { width: 51%; }
  .hero-row > div:nth-child(2), .hero-row > div:nth-child(3) { width: 24.5%; }
  /* person + todo columns: 4 equal columns */
  .people-row > div { flex: 1; min-width: 0; }
  .card {
    background: #f0faf6;   /* THEME: pale mint card */
    border: 1px solid #6fbfae;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
    margin-bottom: 18px;
  }
  h2 {
    font-size: 13px; letter-spacing: 2px; color: #8f8a80;
    text-transform: uppercase; margin-bottom: 10px; font-weight: 700;
  }

  /* ---------- HEADER (flexbox, stacks on narrow screens) ---------- */
  .header { display: flex; align-items: flex-start; margin-bottom: 18px; }
  .header > div:nth-child(1) { width: 30%; min-width: 220px; }
  .header > div:nth-child(2) { width: 45%; }
  .header > div:nth-child(3) { width: 25%; }
  .clock { font-size: 66px; font-weight: 800; letter-spacing: -2px; line-height: 1; }
  .clock small { font-size: 34px; font-weight: 700; margin-left: 6px; }
  .date-line { font-size: 21px; font-weight: 700; letter-spacing: 2px;
    color: #6d6860; margin-top: 6px; }
  .weather { border-left: 1px solid #6fbfae; padding-left: 24px; }
  .wx-now { font-size: 44px; font-weight: 800; }
  .wx-hours { display: flex; margin: 6px 0; }
  .wx-hour { font-size: 14px; color: #6d6860; line-height: 1.3; margin-right: 14px; }
  .wx-hour b { display: block; color: #1c1b18; }
  .wx-hour span { color: #4a90d9; }
  .wx-tag { font-style: italic; color: #6d6860; font-size: 16px; }
  .countdowns { text-align: right; color: #6d6860; font-size: 15px; }
  .cd b { font-size: 19px; color: #d97706; }

  /* ---------- HERO: NEXT UP ---------- */
  .next-up { border-left: 8px solid #d97706; }
  .nu-label { font-size: 13px; font-weight: 800; letter-spacing: 2px; }
  .nu-title { font-size: 40px; font-weight: 800; letter-spacing: -.5px; margin: 4px 0; }
  .nu-when { font-size: 24px; color: #6d6860; }
  .nu-count { margin-left: 14px; background: #1c1b18; color: #fff;
    padding: 3px 12px; border-radius: 999px; font-size: 17px; font-weight: 700; }

  /* ---------- DINNER + SPARK ---------- */
  .menu-row { display: flex; padding: 5px 0; font-size: 16px; }
  .menu-day { font-weight: 800; min-width: 44px; margin-right: 12px; }
  .menu-meal { flex: 1; }
  .today-row .menu-day, .today-row .menu-meal { color: #16a34a; font-weight: 700; }

  .spark-head { display: flex; justify-content: space-between; font-size: 13px;
    letter-spacing: 1px; font-weight: 700; color: #8f8a80; }
  .spark-price { color: #1c1b18; letter-spacing: 0; }
  .spark-price em { font-style: normal; }
  .spark-price.up em { color: #16a34a; }
  .spark-price.down em { color: #dc2626; }
  .spark { width: 100%; height: 44px; margin-top: 8px; }
  .spark-line { fill: none; stroke-width: 2.5; }
  .spark-line.up { stroke: #16a34a; }
  .spark-line.down { stroke: #dc2626; }

  /* ---------- PERSON COLUMNS (4-across via inline-block+flex fallback) ---------- */
  .pc-head { font-size: 14px; font-weight: 800; letter-spacing: 2px;
    border-bottom: 2px solid currentColor; padding-bottom: 6px; margin-bottom: 8px; }
  .pc-row { font-size: 15px; padding: 4px 0; border-bottom: 1px solid #c9e8e0; }
  .pc-row b { display: inline-block; min-width: 46px; color: #6d6860; }
  .pc-row span { margin-left: 8px; }
  .pc-empty { color: #b5afa4; font-size: 15px; padding: 4px 0; }

  /* ---------- TO-DO BOARD ---------- */
  .todo { display: flex; align-items: center; font-size: 15px;
    padding: 6px 0; border-bottom: 1px solid #c9e8e0; cursor: pointer;
    user-select: none; -webkit-user-select: none; }
  .todo:last-child { border-bottom: none; }
  .circle { width: 20px; height: 20px; border-radius: 50%;
    border: 2.5px solid #b5afa4; flex-shrink: 0; position: relative;
    transition: background .15s, border-color .15s; }
  .todo.done .circle { background: #16a34a; border-color: #16a34a; }
  .todo.done .circle::after { content: '\\2713'; color: #fff; position: absolute;
    left: 0; top: 0; bottom: 0; right: 0; display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 800; }
  .todo.done { color: #b5afa4; text-decoration: line-through; }

  /* ---------- MONTH ---------- */
  .month-grid { width: 100%; border-collapse: collapse; table-layout: fixed; }
  .month-grid th { font-size: 12px; color: #8f8a80; text-align: left; padding: 4px; }
  .month-cell { vertical-align: top; height: 62px; padding: 4px;
    border: 1px solid #c9e8e0; font-size: 13px; color: #8f8a80; }
  .month-cell.blank { background: #2e8f83; }
  .month-cell.today { background: #d9770614; border: 2px solid #d97706;
    color: #1c1b18; font-weight: 800; }
  .chip { font-size: 12px; padding: 1px 5px; margin-top: 2px; border-radius: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .footer { color: #d5f0ea; font-size: 13px; margin-top: 14px; text-align: right; }
"""


def build_page():
    """Assemble the full HTML document from all the sections."""
    # NOTE: %-d (day without zero-padding) is Linux-only strftime and
    # crashes on Windows — build it from NOW.day instead.
    date_line = f"{NOW.strftime('%A · %B')} {NOW.day}".upper()

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <!-- Auto-refresh: the browser reloads the page every N seconds. -->
  <meta http-equiv="refresh" content="{REFRESH_MINUTES * 60}">
  <title>{FAMILY_NAME} Family Dashboard</title>
  <style>{CSS}</style>
</head>
<body>

  <div class="header">
    <div>
      <div class="clock"><span id="live-clock">{NOW.strftime('%I:%M').lstrip('0')}<small>{NOW.strftime('%p')}</small></span></div>
      <div class="date-line">{date_line}</div>
    </div>
    <div class="weather">
      {build_weather()}
    </div>
    <div class="countdowns">{build_countdowns()}</div>
  </div>

  <div class="grid hero-row">
    <div class="card next-up">{build_next_up()}</div>
    <div class="card"><h2>Dinner</h2>{build_dinner()}</div>
    <div class="card"><h2>Market</h2>{build_sparkline()}</div>
  </div>

  <div class="grid people-row">
    {build_person_columns()}
  </div>

  <div class="grid people-row">
    {build_todos()}
  </div>

  <div class="card">
    <h2>{TODAY.strftime('%B %Y')}</h2>
    {build_month()}
  </div>

  <div class="footer">build {NOW.strftime('%b %d, %I:%M %p')} ET · updates every 5 min · {HOME_LABEL}</div>

</body>
</html>"""


# ==================================================================
# RUN
# ==================================================================

if __name__ == "__main__":
    html = build_page()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Done -> {OUTPUT_FILE}  ({len(EVENTS)} events)")
