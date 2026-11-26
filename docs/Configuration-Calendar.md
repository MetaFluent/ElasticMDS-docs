# Configuration: Business Calendars

The calendar adapter publishes business calendars - which days are business days for a market or a site - as tables that SQL and functions read. Calendars come from files, and the adapter is built so that other kinds of source can be added. Its projector is `deploy-mf-projector-calendar`, image `mf-projector-calendar`.

**Audience:** Operator, Developer.

---

## What you configure

- **Sources.** A source is a directory of two CSV files holding calendars: their ranges, weekend rules and exception days.
- **A calendar set.** A set is a named collection of calendars, for example `Site`. One JSON descriptor says which sources the set draws from, in order of preference, and optionally an overrides source and code mapping.
- **Tables.** Each set is published as four tables carrying the set's name. Date functions read these tables, and so can any SQL query.

Examples ship in the deployment's config resources: `calendars/sample/` with sample `SIFMA_US` and `TARGET2` calendars for 2025 to 2027, `calendars/site-overrides/overrides.csv` (a header and a commented example) and `calendar-sets/Site.json.txt`. The sample calendars are worked out from the usual holiday rules. They are not a market's published calendar; for production, supply calendars from your own authoritative source.

---

## Settings

Set these on the projector that carries the calendar adapter.

| Property | Default | Meaning |
|---|---|---|
| `calendarAdapter.descriptorDirectoryPath` | `$(METAFLUENT_CONFIG_RESOURCES)/calendar-sets` | Directory of set descriptors. |
| `calendarAdapter.calendarDirectoryPath` | `$(METAFLUENT_CONFIG_RESOURCES)/calendars` | The calendar root, one sub-directory per source. |
| `calendarAdapter.snapshotDirectoryPath` | `$(METAFLUENT_DATA_DIR)/calendar-snapshots` | Where each set's calendars are saved between runs. Made when missing; must be writable. |
| `calendarAdapter.minimumQueryIntervalMilliseconds` | 1000 | Least time between two reads of a table's content by one statement. |
| `calendarAdapter.changeSettleMilliseconds` | 250 | How long a source's directory must be quiet after a change before it is read again. |

The adapter does not start when the descriptor directory or the calendar root is not configured or does not exist (`MF-CAL-001`), or when a descriptor cannot be used or names a source with no directory (`MF-CAL-002`).

---

## Source files

The calendar root holds one directory per source, for example `calendars/vendor-a/`. A source has two files and both are required. They are UTF-8 CSV with a header line. A field may be quoted with double quotes, and a quote inside a field is written twice. Blank lines and lines starting with `#` are skipped. Dates are `yyyy-MM-dd`.

The header must be exactly the file's columns, in any order. A missing or an extra column fails the read.

### calendars.csv

Columns: `calendar,description,weekend,weekend_from,first_date,last_date`.

- A calendar has one line with an empty `weekend_from`. It gives the description, the range (`first_date` and `last_date`, both required) and the weekend from the start.
- `weekend` is three-letter day names (`MON TUE WED THU FRI SAT SUN`) separated by spaces or commas (a field with commas is quoted). Empty means no weekend.
- A weekend that changed is one more line per change: `calendar`, `weekend` and `weekend_from` (the first date of the new rule), with `description`, `first_date` and `last_date` empty.
- A calendar's name cannot contain `+` or `/`.

### days.csv

Columns: `calendar,date,day_type,description`.

| `day_type` | Meaning |
|---|---|
| `HOLIDAY` | Not a business day. |
| `WORKING` | A business day despite the weekend rule. |
| `EARLY_CLOSE` | A business day, shortened. |

A calendar with no lines here is its weekend rule alone. A `days.csv` with only its header means no exception days.

### Example

`calendars/vendor-a/calendars.csv`:

```
calendar,description,weekend,weekend_from,first_date,last_date
SIFMA_US,US bond market,SAT SUN,,2025-01-01,2027-12-31
TARGET2,Euro payments,SAT SUN,,2025-01-01,2027-12-31
```

`calendars/vendor-a/days.csv`:

```
calendar,date,day_type,description
SIFMA_US,2026-11-26,HOLIDAY,Thanksgiving Day
SIFMA_US,2026-11-27,EARLY_CLOSE,Day after Thanksgiving
TARGET2,2026-05-01,HOLIDAY,Labour Day
```

### Lines that cannot be used

A line that cannot be used is left out and the rest of the file is used. Each is listed in the log at `INFO` with its file, line number and reason, and one alert (`MF-CAL-006`) is raised per source per read with the count. The cases:

- In `calendars.csv`: a name with `+` or `/`; a weekend day that is not one of the seven names; dates that do not parse; a `last_date` before the `first_date`; a second line with an empty `weekend_from` for the same calendar; a weekend-change line with a description or dates; a calendar with only weekend-change lines; a wrong number of fields.
- In `days.csv`: an unknown `day_type`; a calendar the source does not define; a date outside the calendar's range; a second line for the same calendar and date; a wrong number of fields.

---

## Set descriptor

A set is one JSON file named `<set>.json` in the descriptor directory. Files not ending `.json` are ignored, so the shipped example `Site.json.txt` is used by renaming it.

```json
{
  "Set": "Site",
  "Sources": ["vendor-a", "internal"],
  "Overrides": "site-overrides",
  "CodeMap": { "vendor-a": { "NYB": "SIFMA_US", "TGT": "TARGET2" } }
}
```

| Field | Meaning |
|---|---|
| `Set` | The set's name. Required. |
| `Sources` | The sources, in order of preference. Required. Each must have a directory under the calendar root. |
| `Overrides` | Optional. The source whose directory holds the overrides file. |
| `CodeMap` | Optional. Per source, maps the source's own calendar codes to the set's calendar names. A code not mapped keeps its name. Each entry must be for one of the `Sources`. |

Each calendar comes whole from the first source that has it: its range, weekend rules and days. A later source's calendar of the same name is not used and not merged. Two sets may share sources.

---

## Overrides

The overrides source's directory holds `overrides.csv`, with columns `calendar,date,action,description`. `calendar` is the set's name for the calendar. Each line applies to one date of one calendar, in file order.

| `action` | Effect |
|---|---|
| `ADD_HOLIDAY` | Makes the date a holiday. |
| `REMOVE_HOLIDAY` | Removes a holiday. |
| `ADD_WORKING` | Makes the date a business day despite the weekend rule. |
| `REMOVE_WORKING` | Removes a working day. |

```
calendar,date,action,description
SIFMA_US,2026-12-31,ADD_HOLIDAY,Closed by the desk for year end
```

An added day's `source` is the overrides source. A holiday removed by an override has no row in `CalendarDays`.

An override that changes nothing is listed in the log at `INFO` with its reason, and `MF-CAL-008` is raised once per read with the count. That covers a calendar the set does not have, a date outside the calendar's range, and a day that is already (or is not) a holiday or working day as the action expects.

### What each override did

The adapter's REST API lists, for each set, every line of its overrides file with what it did when the set was last read. This is where a removed holiday can be seen, since it leaves no row in `CalendarDays`.

```
GET /api/calendar/v1/<adapter id>/sets/Site/overrides
```

Each entry has its `position` in the file, `calendar`, `date`, `action`, `description`, `applied` (`true` when it changed the set) and `reason` (what it did, or why it changed nothing). `GET /api/calendar/v1/<adapter id>/sets` lists the sets themselves, each with its sources, its number of calendars and whether its last read failed.

---

## The tables

A set named `Site` is published as four tables, each with the set's name in its own schema.

### Calendars.Site

One row per calendar. Key column `calendar` (STRING).

| Column | Type | Meaning |
|---|---|---|
| `description` | STRING | The calendar's description. |
| `first_date`, `last_date` | DATE | The range of dates the calendar covers. |
| `weekend` | STRING | The weekend rule in force today, for example `SAT,SUN`. |
| `sources` | STRING | The source that supplied the calendar, with ` + <overrides source>` appended when an override changed it, for example `vendor-a + site-overrides`. |

### CalendarDays.Site

One row per exception day. Key column `calendar_day` (STRING, `<calendar>/<yyyy-MM-dd>`, for example `SIFMA_US/2026-11-26`).

| Column | Type | Meaning |
|---|---|---|
| `calendar` | STRING | The calendar. |
| `date` | DATE | The day. |
| `day_type` | STRING | `HOLIDAY`, `WORKING` or `EARLY_CLOSE`. |
| `description` | STRING | The day's description. |
| `source` | STRING | The source or overrides source that gave the row. |

### CalendarYearRows.Site

One row per calendar and year. Key column `calendar_year` (STRING, `<calendar>/<year>`, for example `SIFMA_US/2026`).

| Column | Type | Meaning |
|---|---|---|
| `calendar` | STRING | The calendar. |
| `year` | INTEGER | The year. |
| `business_days` | STRING | 365 or 366 characters, one per day from 1 January: `1` a business day, `0` not. Weekend rules, holidays and working days are already applied. |

A date outside a calendar's `first_date` to `last_date` is not covered. In the first and last year's string, the days outside the range follow the weekend rule only and are not answers, so a reader checks the range.

### CalendarYears.Site

The year rows read by calendar. Read it one calendar at a time:

```sql
SELECT * FROM CalendarYears.Site WHERE calendar = 'SIFMA_US'
```

A query that names no calendar is refused. For the calendar asked for, the table gives first the calendar's own row and then one row per year.

- **The own row** has key `calendar_year` equal to the calendar's key, and the columns `calendar`, `status`, `first_date`, `last_date` and `reason`.
- **The year rows** have the same columns as `CalendarYearRows`.

`status` is `KNOWN` when the set has the calendar: `first_date` and `last_date` are its range and `reason` is empty. `status` is `UNKNOWN` when the set has no such calendar: `reason` says so (for example `no calendar SIFMA_UX in Calendars.Site`), the dates are blank and there are no year rows. If the calendar is added later, an open statement sees the own row change to `KNOWN` and the year rows arrive.

#### Joint calendars

A key of several calendar names joined by `+` is answered as one calendar:

```sql
SELECT * FROM CalendarYears.Site WHERE calendar = 'SIFMA_US+TARGET2'
```

A day is a business day when it is one in every part, and the range is the dates every part covers. The status is `UNKNOWN` if any part is unknown (the reason names the part) or if the parts cover no date in common. Nothing is stored for a joint calendar. The key may be written in any order and with spaces (`TARGET2 + SIFMA_US`); it is read as the names sorted and joined without spaces.

---

## Changes while running

The adapter watches each source directory. When a file is made, changed or removed, it is read again, whole, once the directory has been quiet for `changeSettleMilliseconds`, for every set that names the source. No restart is needed.

Open statements receive only what changed. Adding a holiday changes that day's row in `CalendarDays` and that year's row for the calendar (one row), and the same year's row for any joint calendar being read that includes it.

---

## When files cannot be read

A file that is missing or unreadable, or a header that is not the file's columns, fails that read. This is different from a bad line, which is left out while the rest is used.

- **After the set is published.** The tables stay as they are and their state is STRESSED until a read succeeds. `MF-CAL-005` is raised (rate-limited). The set reads again when the files change.
- **At start.** After each successful read, the adapter saves the set's calendars in its snapshot directory. If the files cannot be read at start and saved calendars exist, the set starts from them, STRESSED, and `MF-CAL-004` says when they were saved. With nothing saved, the set's tables are in INITIALIZATION_ERROR with the reason and `MF-CAL-003`, and they are not offered. The set starts by itself once the files can be read.

The calendar alerts `MF-CAL-001` to `MF-CAL-011` in the [Log Message Reference](Log-Message-Reference.md) give the meaning of each message and what to do.

---

## Access

A calendar set's tables are open to whoever may read the tables. Access is not per row.

---

## Where to go next

- [Log Message Reference](Log-Message-Reference.md) - the calendar alerts.
- [Configuration: Basics](Configuration-Basics.md) - where the adapter's settings live.
- [Image Catalog](Image-Catalog.md) - the calendar projector image.
