# Apple Health Connector

A self-hosted dashboard for your [Apple Health](https://www.apple.com/ios/health/)
data on Cloud in a Bottle. It ingests the metrics and workouts your iPhone and Apple
Watch collect — heart rate, sleep, activity, and per-workout GPS routes — stores
them in a private SQLite database on your own zone, and charts them in a web
dashboard. It also re-exposes that data to other Cloud in a Bottle apps through the
[health-data service spec](https://github.com/imbue-openhost/health-data-service-spec),
so anything else you run (fitness trackers, AI assistants, etc.) can read your
health history without touching Apple's cloud.

**Who it's for:** anyone who wants to own and explore their Apple Health data
off of Apple's servers, and Cloud in a Bottle users who want a single health-data source
their other apps can build on.

## How your data gets in

Apple Health has no public API, so data is loaded through
[Health Auto Export](https://www.healthyapps.dev/apps/health-auto-export/) (a
third-party iOS app), one of two ways:

### Automatic sync (recommended)

Point Health Auto Export at this app's ingest endpoint so new data syncs on a
schedule:

- **URL:** `https://<your-app>.<your-zone>/api/data`
- **Header:** `api-key: <key>` — copy the key from the app's **Settings** page.

The `/api/data` endpoint is intentionally public (it's how your phone reaches
it) but is gated by that per-install API key. Keep the key secret.

### Manual import

Export a `.zip` from Health Auto Export and upload it on the dashboard. Tips
that make this painless with large histories:

- Export **workouts** (and **metrics**) with **date range: all**, **format:
  JSON**, **v2**.
- **Include GPX** — this also populates route data into the JSON, which is what
  the dashboard uses for maps.
- Set **time grouping to minutes** (seconds is dramatically slower). Several
  hundred workouts export in a couple of minutes.
- The native Apple Health export can hang for hours on large heart-rate
  histories; Health Auto Export is much faster.
- Upload goes faster if you unzip and re-zip just the JSON — the original zip
  isn't actually compressed and the GPX files are redundant with the JSON route
  data.

## Links

- Apple Health — https://www.apple.com/ios/health/
- Health Auto Export (ingest tool) — https://www.healthyapps.dev/apps/health-auto-export/
- Health data service spec — https://github.com/imbue-openhost/health-data-service-spec
