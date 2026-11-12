# Geospatial Functions (MFGeo)

**MFGeo** is a function library you use in SQL, the way you use `MFMath`. It answers location questions - how far apart two points are, which region a point is in, which point of a set is nearest - and the answers are live: when a row's coordinates change, or a reference set changes, the result follows.

**Audience:** Application developers writing SQL against Elastic MDS (JDBC or JMS), and the operators who configure the reference sets.

Coordinates are WGS84 latitude and longitude in degrees. Distances are geodesic metres on the WGS84 ellipsoid.

---

## The functions

Every function is called with the library prefix, for example `MFGeo.DISTANCE(...)`.

| Function | Returns | Meaning |
|---|---|---|
| `DISTANCE(lat1, lon1, lat2, lon2 [, precision])` | DECIMAL | The geodesic distance in metres, to `precision` decimal places (default 2). |
| `WITHIN(lat, lon, centreLat, centreLon, metres)` | BOOLEAN | Whether the point is within the distance of a centre, boundary included. |
| `WITHIN_BOX(lat, lon, north, west, south, east)` | BOOLEAN | Whether the point is inside a latitude/longitude box, edges included. |
| `VALID(lat, lon)` | BOOLEAN | True when both coordinates are present, numeric, in range and not both 0. |
| `CELL(lat, lon, precision)` | STRING | The geohash cell containing the point, at a precision of 1 to 12 characters. |
| `REGION(lat, lon, 'Regions.<set>')` | STRING | The key of the region of a region set that contains the point. |
| `BAND(lat, lon, 'Regions.<set>')` | DECIMAL | The point's band in a region set. |
| `NEAREST(lat, lon, 'Points.<set>', metres)` | STRING | The key of the nearest point of a point set within the distance. |
| `NEAR(lat, lon, 'Points.<set>', metres)` | BOOLEAN | Whether some point of a point set is within the distance. |
| `NEARCELL(lat, lon, 'Points.<set>', metres)` | STRING | The geohash cell whose 3 x 3 block holds every point within the distance. |

### Distance and shape tests

- `DISTANCE` is NULL when a coordinate is missing, not numeric or out of range.
- `WITHIN` includes the boundary. It is false when an input is missing, not numeric or out of range, or the radius is negative.
- `WITHIN_BOX` includes the edges. A west value greater than the east value is a box that crosses the 180th meridian. It is false when an input is missing, not numeric or out of range, or north is below south.
- `VALID` is a quick check to put in a `WHERE` before using a row's coordinates.
- `CELL` is NULL when a coordinate is missing, not numeric or out of range.

### Reference-set lookups

`REGION`, `NEAREST` and `NEAR` name a [reference set](#reference-sets) as a string literal.

- `REGION` returns the key of the region containing the point. A point on a boundary is in the region. A point in several regions gets the smallest key; a point in none gets NULL. It is NULL when a coordinate is missing, not numeric or out of range.
- `NEAREST` returns the key of the nearest point within the distance, boundary included. Of two equally near points it returns the smaller key. When none is within the distance it returns NULL.
- `NEAR` is true when some point of the set is within the distance, boundary included. It is false when none is, or an input is unusable.

### Functions behind the lookups

`BAND` and `NEARCELL` describe how `REGION`, `NEAREST` and `NEAR` read a set, and applications rarely call them.

- `BAND` returns a point's band in a region set, `floor(lat / band width)`. It is NULL when a coordinate is missing, not numeric or out of range, or the set has no band width.
- `NEARCELL` is NULL when an input is unusable, the block would reach a pole, or the radius is wider than a cell.

---

## Reference sets

The reference sets are published by the Socrata adapter from a dataset; see [Socrata Open Data Tables](Configuration-Socrata.md) for the descriptor that publishes each kind.

### Point sets

A point set `Points.<set>` has one row per point: the dataset's key and columns, plus `lat` and `lon` (DECIMAL) and `cell` (the point's geohash at precision 12). Its companion `PointNeighbourhoods.<set>` is what `NEAREST` and `NEAR` read. Applications rarely query it directly.

### Region sets

A region set `Regions.<set>` has one row per region: the dataset's key and columns. A region's geometry stays inside the platform. It is never sent to clients; applications get answers such as the key `REGION` returns, not shapes. The companion tables `RegionEdges.<set>`, `RegionBands.<set>` and `RegionBandEdges.<set>` are what `REGION` reads.

### Region neighbours

`RegionNeighbours.<set>` lists every pair of regions within the set's neighbour tolerance, in both orders. Its columns:

| Column | Meaning |
|---|---|
| `pair` | The key: `<region>/<neighbour>`, with `\` and `/` in a key escaped. |
| `region` | The region. |
| `neighbour` | The neighbouring region. |
| `gap` | DECIMAL metres to the millimetre; 0 when the regions touch or overlap. |

Corners count: regions meeting only at a corner are neighbours. The tolerance is set per region set (100 m by default). To narrow it, use plain SQL:

```sql
SELECT n.neighbour, n.gap
FROM RegionNeighbours.CommunityAreas AS n
WHERE n.region = '1' AND n.gap <= 20
```

---

## Using them in SQL

The examples use Chicago open data served through the Socrata adapter: crimes, 311 service requests and traffic crashes, a speed camera point set, a pothole point set, and the community areas region set.

### In a select list

```sql
SELECT id,
       MFGeo.REGION(location_latitude, location_longitude, 'Regions.CommunityAreas') AS AREA
FROM Chicago.Crimes
```

### In a WHERE

Pothole complaints with no pothole patched within 50 m (the point set holds the patches of the last 14 days):

```sql
SELECT sr.sr_number, sr.street_address
FROM Chicago.ServiceRequests AS sr
WHERE sr.sr_type = 'Pothole in Street Complaint'
  AND NOT MFGeo.NEAR(sr.latitude, sr.longitude, 'Points.PotholesPatched', 50)
```

### As a join key

A table can be joined on a function's value. Each crash with its nearest speed camera within 150 m:

```sql
SELECT c.crash_record_id, cam.address
FROM Chicago.Crashes AS c
JOIN Points.SpeedCameras AS cam
  ON cam.location_id = MFGeo.NEAREST(c.location_latitude, c.location_longitude, 'Points.SpeedCameras', 150)
```

The `ON` is one equality: the joined table's key against an expression over the `FROM` table's columns. A plain `JOIN` (or `INNER JOIN`) drops the rows with no match.

### GROUP BY over a join

Crashes per camera after it went live:

```sql
SELECT cam.location_id, COUNT(*) AS crashes
FROM Chicago.Crashes AS c
JOIN Points.SpeedCameras AS cam
  ON cam.location_id = MFGeo.NEAREST(c.location_latitude, c.location_longitude, 'Points.SpeedCameras', 150)
WHERE c.crash_date >= cam.go_live_date
GROUP BY cam.location_id
```

Change `>=` to `<` for the crashes before it went live.

### Rates by region

Crimes per 1000 residents by community area, joining a region set and a population table:

```sql
SELECT ca.community, acs.total_population,
       COUNT(*) AS crimes,
       COUNT(*) * 1000 / acs.total_population AS per_1000
FROM Chicago.Crimes AS c
JOIN Regions.CommunityAreas AS ca
  ON ca.area_numbe = MFGeo.REGION(c.location_latitude, c.location_longitude, 'Regions.CommunityAreas')
JOIN Chicago.ACS AS acs
  ON acs.community_area = ca.community
GROUP BY ca.community, acs.total_population
```

### GROUP BY a function

```sql
SELECT MFGeo.REGION(location_latitude, location_longitude, 'Regions.CommunityAreas') AS AREA,
       COUNT(*) AS CRIMES
FROM Chicago.Crimes
GROUP BY MFGeo.REGION(location_latitude, location_longitude, 'Regions.CommunityAreas')
```

### One distance per point set

`NEAREST` and `NEAR` calls over one point set in one statement use the same distance. A statement that uses two different distances over one point set is refused with an error that says so.

---

## Where to go next

- [Socrata Open Data Tables](Configuration-Socrata.md) - publish a dataset as a table, a point set or a region set.
- [JDBC Application Development](Develop-JDBC.md) - the SQL you can use, including joins.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the content model behind the tables.
