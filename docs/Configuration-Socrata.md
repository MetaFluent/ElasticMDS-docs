# Configuration: Socrata Open Data Tables

The Socrata adapter serves datasets from a Socrata open-data site (for example data.cityofchicago.org) as tables. Each table is one JSON descriptor file. A dataset can also be published as a point set or a region set, the reference sets the [MFGeo](Develop-Geospatial.md) functions read.

**Audience:** Operator.

---

## Descriptor files

The adapter reads the descriptor directory, by default `$(METAFLUENT_CONFIG_RESOURCES)/socrata` (blueprint property `socrataAdapter.schemaDirectoryPath`). Every file ending `.json` is a table.

Examples ship as `.json.txt` files, which the adapter ignores. The adapter watches the directory: a `.json` file that appears there starts its table at once. So to add a table, copy an example to `<dataset>.json.txt`, edit it, then rename it to `<dataset>.json`. A change to a `.json` descriptor already in the directory, or its removal, takes effect when the adapter restarts.

### How rows are read

A table reads no rows when it starts, only its columns and its row count. Rows are read when a query asks for them: a query that names its keys reads just those rows, and a query that needs every row reads the table's keys page by page first. Rows in use are read again when the dataset changes.

---

## Descriptor fields

| Field | Meaning |
|---|---|
| `Schema`, `Table` | The table's name. Required; a point or region set gives `Table` only. |
| `URL` | The dataset's resource URL, `.../resource/<id>.json`. Required. |
| `Key` | The column that identifies a row. Defaults to the Socrata row identifier, `:id`. Always a STRING field: a row's key is the column's value as Socrata returns it, for a number column the number without trailing or leading zeros (`8`, not `8.0` or `08`). |
| `Columns` | Optional list of columns, each with `Name`, `FieldType` (STRING, DECIMAL, BOOLEAN, INTEGER, LONG or DOUBLE) and an optional `SizeHint`. Without it, every mappable column is exposed. |
| `DateTimeField` | The column that `TimeRangeStart` and `TimeRangeEnd` apply to. |
| `TimeRangeStart`, `TimeRangeEnd` | The table holds only the rows in this time range. |
| `TimeZone` | The time zone of the dataset's times. Required with a period back from now. |
| `PointSet` | Publishes the dataset as a point set. |
| `RegionSet` | Publishes the dataset as a region set. |

### Columns

Without `Columns`, text and timestamps are exposed as STRING, numbers as DECIMAL and booleans as BOOLEAN. A location or point column is exposed as two DECIMAL columns, `<column>_latitude` and `<column>_longitude`; declare it DECIMAL when you list it in `Columns`. A value missing from a row is NULL.

### Time windows

`TimeRangeStart` is a time (`2026-01-01T00:00:00`) or a period back from now:

- `-P14D`, `-P2W`, `-P1M` and `-P1Y` count back from the start of today.
- `-PT6H` and `-PT30M` count back from the start of the current hour or minute.

The window moves once a day (or hour, or minute), and the table reads its rows again when it does, so a row that has left the window leaves the table. A period back from now needs `TimeZone`, for example `America/Chicago`: it is the zone of the dataset's times, which decides when the day starts. A value that mixes a period with a duration (`-P1DT6H`) is refused. `TimeRangeEnd` is always a time.

### Point sets

`PointSet` takes the two columns that hold the coordinates, as number or text columns:

```json
"PointSet" : { "Latitude" : "<column>", "Longitude" : "<column>" }
```

The dataset becomes the point set `Points.<Table>`, with `PointNeighbourhoods.<Table>`.

### Region sets

`RegionSet` takes the multipolygon column:

```json
"RegionSet" : { "Geometry" : "<column>" }
```

Two optional members tune the set: `BandWidth`, in degrees (without it the adapter chooses one from the set's own edges), and `NeighbourTolerance`, in metres (default 100). The dataset becomes `Regions.<Table>` with its companion tables, including `RegionNeighbours.<Table>`. The tables are described in [Geospatial Functions](Develop-Geospatial.md#reference-sets).

---

## Examples

### A plain table

Crashes since the start of 2023, with selected columns and each crash's location:

```json
{
  "Schema" : "Chicago",
  "Table" : "Crashes",
  "URL" : "https://data.cityofchicago.org/resource/85ca-t3if.json",
  "Key" : "crash_record_id",
  "DateTimeField" : "crash_date",
  "TimeRangeStart" : "2023-01-01T00:00:00",
  "Columns" : [
    { "Name" : "crash_record_id", "FieldType" : "STRING", "SizeHint" : 128 },
    { "Name" : "crash_date", "FieldType" : "STRING", "SizeHint" : 30 },
    { "Name" : "injuries_total", "FieldType" : "INTEGER" },
    { "Name" : "location", "FieldType" : "DECIMAL" }
  ]
}
```

### A relative time window

Potholes patched in the last 14 days, as a point set:

```json
{
  "Table" : "PotholesPatched",
  "URL" : "https://data.cityofchicago.org/resource/wqdh-9gek.json",
  "DateTimeField" : "completion_date",
  "TimeRangeStart" : "-P14D",
  "TimeZone" : "America/Chicago",
  "PointSet" : { "Latitude" : "latitude", "Longitude" : "longitude" }
}
```

### A region set

The community areas, keyed by area number:

```json
{
  "Table" : "CommunityAreas",
  "URL" : "https://data.cityofchicago.org/resource/igwz-8jzy.json",
  "Key" : "area_numbe",
  "RegionSet" : { "Geometry" : "the_geom" }
}
```

---

## When a table does not start

A descriptor that does not fit its dataset stops that table from starting, and the reason is in the table's state and the log. The Socrata alerts `MF-SOC-001` to `MF-SOC-011` in the [Log Message Reference](Log-Message-Reference.md) give the meaning of each message and what to do.

---

## Where to go next

- [Geospatial Functions (MFGeo)](Develop-Geospatial.md) - use point and region sets in SQL.
- [Log Message Reference](Log-Message-Reference.md) - the Socrata alerts.
- [Configuration: Basics](Configuration-Basics.md) - where the adapter's settings live.
