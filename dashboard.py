"""
==========================================================
 DASHBOARD BUILDER — reads data.py, writes dashboard.html
 Run:  python dashboard.py
==========================================================

BIG PICTURE (how this file works):
  1. Import your data from data.py
  2. Build each section of the page as a big text string (HTML)
  3. Write everything out to dashboard.html

You open ONE file in your browser and it refreshes itself.
Re-run this script whenever data.py changes.

PYTHON IDEAS SHOWN HERE (each marked with a comment where used):
  - f-strings:        dropping variables inside text:  f"Hello {name}"
  - lists & loops:    building many <div>s from many events
  - list.append():    collecting strings into a list, then joining
  - "".join(list):    gluing a list of strings into one string
  - list comprehensions:  [f"<p>{x}</p>" for x in items]  — a loop in one line
  - dictionaries:     data["key"] lookups (events, colors, menu)
  - the datetime & calendar modules: real date math
  - functions:        one function per page section, so each is small
"""

import calendar  # stdlib: tells us days-in-month, weekday of the 1st
from datetime import datetime, timedelta

# Import everything you're allowed to edit from data.py
from data import (
    PEOPLE_COLORS, EVENTS, DINNER_MENU,
    FAMILY_NAME, REFRESH_MINUTES, CHART_SYMBOL, CHART_INTERVAL,
)

OUTPUT_FILE = "index.html"  # 'index.html' = clean URL on GitHub Pages later

TODAY = datetime.now().date()


# ==================================================================
# SMALL HELPERS
# ==================================================================

def person_color(person):
    """Look up a person's color. .get() returns gray if name not found
    instead of crashing — a safe way to read dictionaries."""
    return PEOPLE_COLORS.get(person, "#8b949e")


def time_sort_key(time_text):
    """Convert '8:30 PM' -> a 24-hour time object so events sort in
    real chronological order (plain text sorting would put '5:30 PM'
    before '8:00 AM' because '5' < '8')."""
    return datetime.strptime(time_text, "%I:%M %p").time()


def date_label(date_obj, short=False):
    """Format a date for humans: 'Fri, Oct 16' (or 'Fri, Oct 16' short)."""
    if short:
        return date_obj.strftime("%a %d")          # 'Fri 16'
    return date_obj.strftime("%a, %b %d")          # 'Fri, Oct 16'


# ==================================================================
# SECTION 1: WEEKLY AGENDA (next 7 days, grouped by day)
# ==================================================================

def build_agenda():
    """Loop over the next 7 days, collect that day's events, and
    build one HTML block per day."""
    html_parts = []

    for offset in range(7):  # 0 = today, 1 = tomorrow, ... 6
        day = TODAY + timedelta(days=offset)
        iso = day.isoformat()  # 'YYYY-MM-DD' — matches how events store dates

        # A list comprehension: keep only events for this day.
        # (Same as a for-loop with an if, written in one line.)
        day_events = sorted(
            [e for e in EVENTS if e["date"] == iso],
            key=lambda e: time_sort_key(e["time"]),  # real time order, not text order
        )

        if not day_events:
            continue  # skip empty days so the agenda stays tight

        # Friendly heading: today/tomorrow get special names
        if offset == 0:
            heading = f"Today — {date_label(day)}"
        elif offset == 1:
            heading = f"Tomorrow — {date_label(day)}"
        else:
            heading = date_label(day)

        html_parts.append(f'<div class="day-heading">{heading}</div>')

        for event in day_events:
            color = person_color(event["person"])
            # The colored bar on the left of each row is this div's
            # border-left, colored per person.
            html_parts.append(
                f'<div class="event" style="border-left-color:{color}">'
                f'<span class="event-time">{event["time"]}</span>'
                f'<span class="event-title">{event["title"]}</span>'
                f'<span class="event-person" style="color:{color}">{event["person"]}</span>'
                f'</div>'
            )

    if not html_parts:
        html_parts.append('<div class="empty">No events this week. Add some in data.py!</div>')

    return "\n".join(html_parts)  # glue all strings into one big string


# ==================================================================
# SECTION 2: MONTHLY CALENDAR (zoomed out, current month)
# ==================================================================

def build_month():
    """Build a sun-start month grid. Each day cell shows small
    color-coded chips for that day's events."""
    year, month = TODAY.year, TODAY.month
    month_name = TODAY.strftime("%B %Y")

    # calendar.monthrange gives two numbers:
    #   [0] = weekday of the 1st (Mon=0..Sun=6)  -> we convert to Sun-start
    #   [1] = number of days in the month (28-31)
    first_weekday_mon0, days_in_month = calendar.monthrange(year, month)
    first_weekday_sun0 = (first_weekday_mon0 + 1) % 7  # shift so Sun=0

    events_by_date = {}  # dictionary: 'YYYY-MM-DD' -> list of events
    for e in EVENTS:
        events_by_date.setdefault(e["date"], []).append(e)
        # setdefault: "give me the list for this key, or create an
        # empty one first." A common dictionary pattern.

    parts = [f'<div class="month-title">{month_name}</div>']
    parts.append('<table class="month-grid">')

    # Header row: day-of-week names
    parts.append("<tr>" + "".join(
        f'<th>{d}</th>' for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    ) + "</tr>")

    # Leading blanks so the 1st lands on the correct weekday column
    cells = [""] * first_weekday_sun0
    cells += list(range(1, days_in_month + 1))
    while len(cells) % 7 != 0:  # pad the last row so the table is even
        cells.append("")

    for i, cell in enumerate(cells):
        if i % 7 == 0:  # start a new table row every 7 cells
            parts.append("<tr>")

        if cell == "":
            parts.append('<td class="blank"></td>')
        else:
            day_date = datetime(year, month, cell).date()
            iso = day_date.isoformat()
            is_today = " today" if cell == TODAY.day else ""

            # Small chips: one per event, colored by person
            chips = []
            for e in events_by_date.get(iso, []):
                color = person_color(e["person"])
                short_title = e["title"][:16] + ("…" if len(e["title"]) > 16 else "")
                chips.append(
                    f'<div class="chip" style="background:{color}22;'
                    f'border-left:3px solid {color}">{short_title}</div>'
                )

            parts.append(
                f'<td class="month-cell{is_today}">'
                f'<div class="day-num">{cell}</div>{"".join(chips)}</td>'
            )

        if i % 7 == 6:  # close the row at the end of the week
            parts.append("</tr>")

    parts.append("</table>")
    return "\n".join(parts)


# ==================================================================
# SECTION 3: DINNER MENU (Mon–Sun, today highlighted)
# ==================================================================

def build_dinner():
    """One row per day. Python knows today's weekday:
    .weekday() -> Mon=0, Tue=1, ... Sun=6 — which matches our
    'Mon'..'Sun' key order in DINNER_MENU."""
    today_index = TODAY.weekday()
    day_keys = list(DINNER_MENU.keys())  # ['Mon', 'Tue', ...]

    parts = []
    for i, day in enumerate(day_keys):
        highlight = " today-row" if i == today_index else ""
        parts.append(
            f'<div class="menu-row{highlight}">'
            f'<span class="menu-day">{day}</span>'
            f'<span class="menu-meal">{DINNER_MENU[day]}</span>'
            f'</div>'
        )
    return "\n".join(parts)


# ==================================================================
# SECTION 4: NQ FUTURES CHART (TradingView embed)
# ==================================================================

def build_chart():
    """TradingView's free widget, loaded as an <iframe> (an embedded
    page inside our page). It runs in your browser (JavaScript);
    Python just writes the snippet into the page. Symbol and interval
    come from data.py so you can change them without touching HTML."""
    return f"""
    <!-- Advanced Chart Widget: works with any symbol TradingView's
         free tier serves. Crypto, stocks, and index symbols like
         NQ/CME_MINI are paid-feed-only here, so this defaults to a
         Nasdaq-100 proxy ETF. Change the symbol in data.py. -->
    <iframe
      src="https://www.tradingview-widget.com/embed-widget/advanced-chart/?locale=en&interval={CHART_INTERVAL}&theme=dark&timezone=America%2FNew_York&style=1&hide_side_toolbar=1&with_dateranges=0&allow_symbol_change=0&symbol={CHART_SYMBOL.replace('%', '%25').replace('&', '%26')}"
      style="width:100%;height:560px;border:none;margin:0 -20px -20px;"
    ></iframe>
    """


# ==================================================================
# SECTION 5: THE PAGE SHELL (CSS + putting sections together)
# ==================================================================

CSS = """
  /* Dark theme: near-black background, light text, big fonts so it
     reads from across the room. */
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 20px;
    padding: 24px 32px;
  }

  h1 { font-size: 34px; letter-spacing: 1px; }
  h1 .accent { color: #e3b341; }

  .header {
    display: flex; justify-content: space-between; align-items: baseline;
    border-bottom: 1px solid #21262d; padding-bottom: 14px; margin-bottom: 22px;
  }
  .header .meta { color: #8b949e; font-size: 16px; }

  /* The page is a grid: 2 columns, sections flow into slots. */
  .grid {
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 22px;
  }

  .card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px;
  }

  .card h2 {
    font-size: 22px; text-transform: uppercase; letter-spacing: 2px;
    color: #8b949e; margin-bottom: 14px;
  }

  /* --- Agenda --- */
  .day-heading {
    color: #e3b341; font-weight: 700; font-size: 21px;
    margin: 16px 0 8px;
  }
  .day-heading:first-child { margin-top: 0; }

  .event {
    display: flex; gap: 14px; align-items: baseline;
    background: #0d1117; border-left: 5px solid;  /* color set inline */
    border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;
  }
  .event-time   { color: #8b949e; min-width: 90px; font-variant-numeric: tabular-nums; }
  .event-title  { flex: 1; }
  .event-person { font-size: 15px; font-weight: 600; }

  .legend { display: flex; gap: 18px; margin-bottom: 10px; font-size: 15px; }
  .legend span::before {
    content: ''; display: inline-block; width: 12px; height: 12px;
    border-radius: 3px; margin-right: 6px; background: var(--c);
  }

  /* --- Month grid --- */
  .month-title { font-size: 24px; font-weight: 700; margin-bottom: 10px; }
  .month-grid { width: 100%; border-collapse: collapse; table-layout: fixed; }
  .month-grid th {
    color: #8b949e; font-size: 14px; font-weight: 600;
    padding: 6px 4px; text-align: left;
  }
  .month-cell {
    vertical-align: top; height: 88px; padding: 4px;
    border: 1px solid #21262d; font-size: 14px;
  }
  .month-cell.blank { background: #0d1117; }
  .month-cell.today { background: #e3b34114; border: 1px solid #e3b341; }
  .day-num { color: #8b949e; margin-bottom: 3px; }
  .month-cell.today .day-num { color: #e3b341; font-weight: 700; }

  .chip {
    font-size: 12px; padding: 2px 5px; margin-bottom: 2px;
    border-radius: 4px; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis;
  }

  /* --- Dinner menu --- */
  .menu-row {
    display: flex; gap: 16px; padding: 10px 12px; margin-bottom: 6px;
    background: #0d1117; border-radius: 6px; border-left: 5px solid #30363d;
  }
  .menu-row.today-row { border-left-color: #3fb950; background: #3fb95014; }
  .menu-day  { font-weight: 700; min-width: 48px; }
  .menu-meal { flex: 1; }

  /* --- Chart --- */
  #tv_chart { height: 560px; margin: 0 -20px -20px; }  /* bleed to card edge */

  .footer { color: #484f58; font-size: 14px; margin-top: 18px; text-align: right; }
"""


def build_page():
    """Assemble the full HTML document from all the sections."""

    # Legend: one colored swatch per family member (loop over dict)
    legend = "".join(
        f'<span style="--c:{color}">{name}</span>'
        for name, color in PEOPLE_COLORS.items()
    )

    generated_at = datetime.now().strftime("%I:%M %p").lstrip("0")

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
    <h1>{FAMILY_NAME} <span class="accent">Family Dashboard</span></h1>
    <div class="meta">{date_label(TODAY, short=False)} &nbsp;·&nbsp; refreshes every {REFRESH_MINUTES} min</div>
  </div>

  <div class="grid">
    <div class="card" style="grid-row: span 2">
      <h2>This Week</h2>
      <div class="legend">{legend}</div>
      {build_agenda()}
    </div>

    <div class="card">
      <h2>Dinner This Week</h2>
      {build_dinner()}
    </div>

    <div class="card">
      <h2>NQ Futures · 1H</h2>
      {build_chart()}
    </div>
  </div>

  <div class="grid" style="margin-top: 22px">
    <div class="card" style="grid-column: 1 / -1">
      <h2>Month View</h2>
      {build_month()}
    </div>
  </div>

  <div class="footer">generated {generated_at} · edit data.py then re-run: python dashboard.py</div>

</body>
</html>"""


# ==================================================================
# RUN
# ==================================================================

if __name__ == "__main__":
    # This special if-block only runs when you execute the file
    # directly (python dashboard.py), not when another file imports it.
    html = build_page()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Done -> {OUTPUT_FILE}  ({len(EVENTS)} events, menu for {len(DINNER_MENU)} days)")
