"""
==========================================================
 DATA FILE — EDIT EVERYTHING HERE.
 You should never need to touch dashboard.py.
==========================================================

HOW DATES WORK:
    d(0) = today, d(1) = tomorrow, d(2) = two days out, ...
    Dates are stored as text in "YYYY-MM-DD" format (ISO format —
    the international standard). You can also hardcode a date like
    "2026-12-25" for holidays and birthdays.

HOW TIMES WORK:
    Use "H:MM AM/PM" — e.g. "8:00 AM" or "5:30 PM". Same spelling
    every time, or sorting within a day will break.
"""

from datetime import date, timedelta

TODAY = date.today()


def d(days_from_today):
    """Return a date N days from today as ISO text ('YYYY-MM-DD')."""
    return (TODAY + timedelta(days=days_from_today)).isoformat()


# ------------------------------------------------------------------
# PEOPLE & COLORS
# Add a new family member = add ONE line here. Everything else
# (agenda, monthly grid, legend) picks it up automatically.
# ------------------------------------------------------------------
PEOPLE_COLORS = {
    "Justin": "#d97706",   # amber (dark enough to read on white)
    "Jessie": "#2563eb",   # blue
    "Darci":  "#db2777",   # pink
    "Mila":   "#7c3aed",   # purple
    "Family": "#16a34a",   # green — events for everybody
}

# ------------------------------------------------------------------
# HOME / WEATHER — lat & long for the forecast (Open-Meteo, free,
# no API key). Change these if you move.
# ------------------------------------------------------------------
HOME_COORDS  = (38.386, -82.604)   # Catlettsburg, KY
HOME_LABEL   = "Catlettsburg"

# ------------------------------------------------------------------
# COUNTDOWNS — shown top-right. date must be "YYYY-MM-DD".
# Past dates are hidden automatically the next day.
# ------------------------------------------------------------------
COUNTDOWNS = [
    {"date": "2026-10-31", "label": "Trunk or treat"},
    {"date": "2027-01-09", "label": "Frozen Sasquatch 25k"},
]

# ------------------------------------------------------------------
# CALENDAR EVENTS
# One event = one {...} block. Copy a block, change the values.
# "person" must match a key in PEOPLE_COLORS.
# ------------------------------------------------------------------
EVENTS = [
    # ---- TODAY ----
    {"date": d(0), "time": "8:00 AM",  "person": "Justin", "title": "Safety walkthrough — floor 2"},
    {"date": d(0), "time": "4:30 PM",  "person": "Family", "title": "Pick up car"},
    {"date": d(0), "time": "5:30 PM",  "person": "Darci",  "title": "Soccer practice"},
    {"date": d(0), "time": "8:30 PM",  "person": "Jessie", "title": "Book club"},

    # ---- TOMORROW ----
    {"date": d(1), "time": "5:00 PM",  "person": "Family", "title": "Burgers at Kiefer's"},
    {"date": d(1), "time": "7:30 AM",  "person": "Justin", "title": "Tempo run — 5 mi"},
    {"date": d(1), "time": "12:30 PM", "person": "Mila",   "title": "Pediatrician checkup"},
    {"date": d(1), "time": "6:30 PM",  "person": "Family", "title": "Game night"},

    # ---- REST OF THE WEEK ----
    {"date": d(2), "time": "9:00 AM",  "person": "Jessie", "title": "Mila swim class"},
    {"date": d(2), "time": "6:00 PM",  "person": "Justin", "title": "Gym — push day"},

    {"date": d(3), "time": "8:00 AM",  "person": "Justin", "title": "Work — EHS audit prep"},
    {"date": d(3), "time": "3:30 PM",  "person": "Darci",  "title": "Art class"},
    {"date": d(3), "time": "7:00 PM",  "person": "Family", "title": "Small group"},

    {"date": d(4), "time": "10:00 AM", "person": "Jessie", "title": "Grocery run"},
    {"date": d(4), "time": "4:30 PM",  "person": "Justin", "title": "Pick up Darci"},

    # ---- WEEKEND ----
    {"date": d(5), "time": "7:00 AM",  "person": "Justin", "title": "Long run — 10 mi"},
    {"date": d(5), "time": "9:00 AM",  "person": "Family", "title": "Darci soccer game"},
    {"date": d(5), "time": "6:00 PM",  "person": "Family", "title": "Movie night"},

    {"date": d(6), "time": "10:00 AM", "person": "Family", "title": "Church"},
    {"date": d(6), "time": "5:00 PM",  "person": "Family", "title": "Meal prep for the week"},

    # ---- FIXED DATES (hardcoded ISO dates work too) ----
    {"date": "2026-10-31", "time": "6:00 PM", "person": "Family", "title": "Trunk or treat @ church"},
]

# ------------------------------------------------------------------
# DINNER MENU — Mon through Sun. Edit the meals, keep the day keys.
# ------------------------------------------------------------------
DINNER_MENU = {
    "Mon": "Chicken thighs, rice, broccoli",
    "Tue": "Taco night",
    "Wed": "Spaghetti & meatballs",
    "Thu": "Breakfast for dinner",
    "Fri": "Homemade pizza night",
    "Sat": "Grill out — burgers & corn",
    "Sun": "Roast chicken & potatoes",
}

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
FAMILY_NAME     = "Bartram"
REFRESH_MINUTES = 5                  # page reloads itself this often
CHART_SYMBOL    = "QQQ"              # sparkline symbol (Yahoo Finance)
CHART_INTERVAL  = "60"               # 60-minute bars
# NOTE: the chart is now a tiny static sparkline built at deploy time
# from Yahoo Finance data — no JavaScript, so it renders on the old
# Android frame (the TradingView widget didn't). QQQ = Nasdaq-100,
# the index NQ futures track.
