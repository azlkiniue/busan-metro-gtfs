# Busan Metro GTFS

A [GTFS](https://gtfs.org/) feed for the urban railway network of Busan, South Korea: Busan Metro Lines 1–4, the Busan–Gimhae Light Rail Transit (BGL) and the Donghae Line metropolitan service. Schedules come from the operators' published timetables; station locations and track geometry come from OpenStreetMap.

- **Download the feed:** [gtfs.zip](https://azlkiniue.github.io/busan-metro-gtfs/gtfs.zip)
- **Browse it:** [project page](https://azlkiniue.github.io/busan-metro-gtfs/) and [timetables with route maps](https://azlkiniue.github.io/busan-metro-gtfs/timetables/)

## Coverage

| Line | Operator | Terminals | Stations | Trips (Mon–Fri / Sat / Sun) | Timetable source |
|---|---|---|---|---|---|
| Line 1 | Busan Transportation Corporation (Humetro) | Dadaepo Beach – Nopo | 40 | 368 / 347 / 332 | Humetro open API |
| Line 2 | Busan Transportation Corporation (Humetro) | Jangsan – Yangsan | 43 | 356 / 334 / 308 | Humetro open API |
| Line 3 | Busan Transportation Corporation (Humetro) | Suyeong – Daejeo | 17 | 320 / 300 / 284 | Humetro open API |
| Line 4 | Busan Transportation Corporation (Humetro) | Minam – Anpyeong | 14 | 310 / 296 / 278 | Humetro open API |
| Busan–Gimhae LRT | Busan-Gimhae Light Rail Transit Operation Co., Ltd. | Sasang – Kaya Univ. | 21 | 394 / 364 / 364 | [bglrt.com](https://www.bglrt.com/00011/00149.web) station timetables |
| Donghae Line | Korea Railroad Corporation (Korail) | Bujeon – Taehwagang | 23 | 105 / 93 / 93 | Korail timetable effective 1 Sep 2026 |

Trip counts include both directions. The Donghae Line count includes trains that start or end at Mangyang, next to the depot.

## Feed conventions

| Topic | Convention |
|---|---|
| Files | `agency`, `routes`, `stops`, `trips`, `stop_times`, `shapes`, `calendar`, `transfers`, `feed_info` |
| Services | `WD` (Mon–Fri), `SAT` and `SUN`. Korail's single holiday timetable is used for both `SAT` and `SUN`. |
| Routes | `route_id` 1, 2, 3, 4, `BGL`, `Donghae`; all `route_type` 1 (metro) |
| Stop IDs | Lines 1–4: Humetro station numbers (e.g. `119` Seomyeon), also used as `stop_code`.<br>BGL: `901`–`921` (the operator's website code), with `stop_code` 1–21 as shown on station signs.<br>Donghae Line: Korail station numbers `K110`–`K132`. |
| Directions | `direction_id` 1 runs toward the higher station number (Dadaepo Beach → Nopo, Sasang → Kaya Univ., Bujeon → Taehwagang); 0 is the reverse |
| Trip IDs | `{terminal stop_id}_{route_id}_{direction_id}_{service_id}_{train number}`. BGL does not publish train numbers, so its trips are numbered in order of departure. |
| Stop times | Humetro and BGL publish times to the minute. Arrivals and departures are placed at `:15`/`:45` (Lines 1–4) and `:20`/`:40` (BGL) within that minute. The Donghae Line uses Korail's exact arrival and departure times. Trains after midnight use hours `24:xx`. |
| Shapes | One shape per line and direction from OpenStreetMap, ending exactly at the terminal stations |
| Transfers | 11 interchange stations, `transfer_type` 2 with a 180 s minimum |
| Accessibility | All stations and trips are marked wheelchair accessible |

## Data sources

| Data | Source |
|---|---|
| Lines 1–4 timetables | Busan Transportation Corporation open API ([data.go.kr dataset 15000522](https://www.data.go.kr/data/15000522/openapi.do)), collected in 2025 |
| BGL timetables | Per-station timetables on the [operator's website](https://www.bglrt.com/00011/00149.web) (weekday, Saturday and holiday columns), collected in October 2026 |
| Donghae Line timetable | "동해선 전동열차 시각표" (XLSX) from [Korail's timetable page](https://www.korail.com/ticket/reserve/train-timeTable), effective 1 September 2026 |
| Stations and track geometry | [OpenStreetMap](https://www.openstreetmap.org/) route relations, exported with overpass-turbo |
| Station names and numbers | Operators' official route maps |

## Repository layout

| Path | Contents |
|---|---|
| [`gtfs/`](gtfs/) | The feed as plain text files |
| [`gtfs.zip`](gtfs.zip) | The zipped feed (built by `zip_gen.py`) |
| [`route.geojson`](route.geojson) | Line geometry (one LineString per route, `id` = `route_id`) and stations (one Point per stop, `id` = `stop_id`, `name` = English name, optional `ref` = `stop_code`). Edited with QGIS ([`route.qgz`](route.qgz)). |
| [`timetable.csv`](timetable.csv), [`timetable_bgl.csv`](timetable_bgl.csv), [`timetable_donghae.csv`](timetable_donghae.csv) | Raw timetables for each operator |
| `timetable_gen*.py` | Download the raw timetables |
| `generate_*.py` | Build the GTFS files from `route.geojson` and the timetables |
| [`html/`](html/) | Static website: landing page plus timetables generated with GTFS-to-HTML |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | Publishes `html/` and `gtfs.zip` to GitHub Pages on every push to `main` |

## Rebuilding the feed

The scripts need Python 3.13 with `requests`, `lxml` and `tqdm`. They are declared in [`pixi.toml`](pixi.toml), which currently lists only `win-64`; add your platform (for example `osx-arm64` or `linux-64`) to `platforms` before running `pixi install`. Run every command from the repository root.

1. **Update the timetables** (only for the operators whose schedules changed).

   ```bash
   pixi run python timetable_gen.py
   ```

   Lines 1–4. Set `service_key` in the script to your data.go.kr key first. The script appends to `timetable.csv`, so delete the old file before a full refresh.

   ```bash
   pixi run python timetable_gen_bgl.py
   ```

   BGL. Writes `timetable_bgl.csv`.

   ```bash
   pixi run python timetable_gen_donghae.py
   ```

   Donghae Line. Writes `timetable_donghae.csv`. When Korail publishes a new timetable, update `url` in the script to the new XLSX link.

2. **Update stations or geometry** in `route.geojson` if needed. Keep each LineString starting and ending exactly on its terminal stations. `sort_route.py` sorts the features by `id`.

3. **Generate the GTFS files.** Each script writes its `.txt` file to the repository root; move the files into `gtfs/` afterwards. `agency.txt`, `routes.txt`, `calendar.txt` and `feed_info.txt` are edited by hand.

   ```bash
   pixi run python generate_stops.py
   ```

   ```bash
   pixi run python generate_shapes.py
   ```

   ```bash
   pixi run python generate_trips.py
   ```

   ```bash
   pixi run python generate_stop_times.py
   ```

   ```bash
   pixi run python generate_transfers.py
   ```

4. **Zip the feed** from the files in `gtfs/`.

   ```bash
   pixi run python zip_gen.py
   ```

5. **Validate** with the [MobilityData GTFS Validator](https://github.com/MobilityData/gtfs-validator). The current feed has no errors.

   ```bash
   java -jar gtfs-validator-8.0.1-cli.jar -i gtfs.zip -o validation -c kr
   ```

## Timetable website

`html/index.html` is the landing page. `html/timetables/` is generated from `gtfs.zip` with [GTFS-to-HTML](https://gtfstohtml.com/) 2.13.5 using its default options, except:

- one timetable per page (`groupTimetablesIntoPages: false`)
- `menuType: "jump"`
- `mapStyleUrl: "https://tiles.openfreemap.org/styles/liberty"`

After regenerating, re-apply these changes so the output fits the site:

- `index.html`:
  - title "Busan Metro Timetables", heading "Busan Metro Routes"
  - a "Back to Home" link under the heading
  - labels that include the direction, e.g. "Line 1 - Nopo to Dadaepo Beach"
- `map.html`: a map-only copy of `index.html` that calls `createSystemMap(noGeocoder = true)`. It is embedded on the landing page.
- `js/system-map.js`: `createSystemMap(noGeocoder = false)` skips `addGeocoder` when `noGeocoder` is true.
- `css/overview_styles.css`: add the `.back-to-home` rule.
- `css/timetable_styles.css`:
  - `height: 80vh` on `.table-container`
  - a sticky `thead`
- Each timetable page's `<title>` names the route's own operator.
- Remove `js/maplibre-gl.js.map`. It is a 6 MB source map that the site doesn't need.

## Known limitations

- Public holidays are not modelled; there is no `calendar_dates.txt`. On Korean public holidays the operators run their Sunday/holiday timetable.
- Each timetable is a snapshot (see [Data sources](#data-sources)). The Donghae Line extension from Taehwagang to Bukulsan, planned for December 2026, is not included.
- For Lines 1–4 and BGL, the seconds in `stop_times.txt` are a convention, because the source timetables only give minutes.
- Transfer times are a uniform 180 s estimate, not measured walking times.
- This is an independent project, not an official feed from the operators.

## License

The code is released under the [MIT License](LICENSE). Station locations and track geometry are derived from OpenStreetMap data, © OpenStreetMap contributors, available under the [Open Database License](https://opendatacommons.org/licenses/odbl/). Timetables are compiled from the operators' published schedules.
