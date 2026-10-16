# Family Dashboard

Dark-theme family dashboard: weekly agenda + monthly calendar, dinner menu, NQ 1H chart. One Python script generates one HTML file.

## Run it

```
cd C:\Users\Justin\family_dashboard
python dashboard.py
start index.html
```

That's it. The page refreshes itself every 5 minutes. **Re-run `python dashboard.py` whenever you change `data.py`** — the HTML doesn't update itself.

Want it to rebuild automatically? Skip the HTML route and run:

```
python server.py
```

then open http://localhost:8000 — it rebuilds the page on every refresh, so edits to `data.py` show up with no re-run.

## Where the data lives — `data.py`

Everything you'd ever edit is at the top of `data.py`, clearly marked:

- **Events** — each event is one `{...}` block. Copy a block, change the values. `d(0)` = today, `d(3)` = three days out, or hardcode `"2026-12-25"`.
- **Dinner menu** — plain text, Mon–Sun.
- **Colors** — add a person by adding one line to `PEOPLE_COLORS`. Agenda, month grid, and legend all pick it up automatically.
- **Chart / refresh settings** — symbol, interval, refresh minutes.

## "Add this to the calendar" flow (the fun part)

Since events are plain Python data in one file, you can just tell me:

> "Add soccer practice for Darci Thursday 3:30"

I edit `data.py`, re-run `python dashboard.py`, and it's on the dashboard. The data/presentation split is exactly what makes that work — the dashboard script never needs to change.

Same flow works if you later switch to `server.py` — even easier, no re-run step.

## Connecting real calendar data later

When you outgrow hand-edited events, the shape of the data doesn't have to change — only where it comes from. The rest of the code reads `EVENTS`, so you'd write a small function that populates `EVENTS` from an API instead:

- **Google Calendar** — free API; a small script fetches events and writes them into `data.py` (or straight into the EVENTS list). Each family member gets their own calendar → own color.
- **iCal/Apple Calendar** — most providers give you a private `.ics` URL. A ~20-line reader with the `icalendar` package turns that into events.
- **Cron it** — once there's a fetcher, run it on a schedule (you already know this pattern) and the dashboard stays current with zero manual edits.

## Deploying it later

- **Cheapest:** it's one static HTML file — drop `dashboard.html` on any free static host (GitHub Pages, Netlify, Cloudflare Pages) and open it on the TV's browser.
- **Live data:** run `server.py` on a mini PC / Raspberry Pi at home and open `http://<its-ip>:8000` from any device on your network. No internet hosting needed.
- **Public:** put the `server.py` machine behind Tailscale (free) so only your devices can reach it.

## Files

| File | What it is |
|---|---|
| `data.py` | **Everything you edit.** Events, menu, colors, settings. |
| `dashboard.py` | The builder — reads data, writes HTML. Read to learn, don't edit. |
| `server.py` | Optional tiny web server that rebuilds on every refresh. |
| `dashboard.html` | The output. Generated — don't edit by hand. |
| `README.md` | This file. |
