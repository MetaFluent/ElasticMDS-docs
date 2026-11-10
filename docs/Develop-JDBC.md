# JDBC Application Development

Elastic MDS content is also reachable over standard **JDBC**: you connect with the MetaFluent JDBC driver, run a `SELECT`, and read rows through a `ResultSet` - the API you already know. It is the same content the [JMS Application Development](Develop-JMS.md) guide subscribes to; JMS *streams* it to you, JDBC lets you *query* it with SQL.

**Audience:** Java developers (the JDBC model is standard; only the driver and connection are MetaFluent-specific). No prior MetaFluent knowledge assumed.

One difference from an ordinary database is worth stating up front: a MetaFluent result set is **live**. The rows track the market - re-read the `ResultSet` and you see current values, for as long as you keep it open.

---

## The SDK

The driver and the example applications ship in the **MetaFluent JDBC SDK** (`jdbc-sdk`). The current milestone is on the `stable` branch:

```
git clone --depth 1 -b stable git@github.com:MetaFluent-Dist-NN/jdbc-sdk.git
```

To use a specific milestone, clone its tag instead - for example `-b MILESTONE-v6.2.0`. Milestone tags follow the `MILESTONE-v<major>.<minor>.<patch>` convention; releases are tagged `RELEASE-v<major>.<minor>.<patch>`.

The SDK contains:

- `lib/metafluent.jdbc.jar` - the JDBC driver (`com.metafluent.jdbc.rtc.DriverImpl`). Add this one jar to your classpath to build against Elastic MDS.
- `examples/src/...` - the source for the example applications, `FirstQuery` and `JDBCTestApp`.
- `bin/JDBCTestApp.jar` - both examples prebuilt (with the driver bundled), so you can run them without building.

The driver registers itself, so `DriverManager` finds it automatically. Connection URLs take the form `jdbc:metafluent://<host>:<port>`, where the host and port are those of the session server (default port `8900`). If your environment needs the driver named explicitly, add `-Djdbc.drivers=com.metafluent.jdbc.rtc.DriverImpl`.

To run the prebuilt `JDBCTestApp` against a deployment, give it the session server host and a query:

```
java -jar bin/JDBCTestApp.jar -host localhost -head 20 \
     "SELECT RIC,DSPLY_NAME,BID,BIDSIZE,ASK,ASKSIZE,TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L','REX.L','WG.L')"
```

This assumes the session server runs on the same machine. When it runs on a different machine, replace `localhost` with that machine's hostname. `-port` sets a session port other than `8900`, and `-head` limits the rows shown. The table refreshes once a second as the content changes; press `Ctrl+C` to stop. Put the query in double quotes, so the single quotes around values reach the server unchanged.

---

## A first query

`FirstQuery` is the smallest complete MetaFluent JDBC application. Its structure is the standard JDBC pattern: get a `Connection`, create a `Statement`, execute a `SELECT`, and read the `ResultSet`. The code below is the actual example; it is in the SDK at `examples/src/com/metafluent/examples/firstquery/FirstQuery.java`.

```java
package com.metafluent.examples.firstquery;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Properties;

/**
 * The smallest complete MetaFluent JDBC application: connect, run one SELECT, and redisplay the
 * live result set once a second. The optional argument is the session server host (default localhost).
 */
public class FirstQuery {

	public static void main(String[] args) throws Exception {
		Properties properties = new Properties();
		properties.setProperty("com.metafluent.jdbc.application-name", "FirstQuery");
		properties.setProperty("com.metafluent.jdbc.application-version", "1.0.0");
		properties.setProperty("com.metafluent.jdbc.user", "guest");

		// The MetaFluent JDBC driver connects through the session server (port 8900).
		String host = args.length > 0 ? args[0] : "localhost";
		String url = "jdbc:metafluent://" + host + ":8900";

		try (Connection connection = DriverManager.getConnection(url, properties);
			 Statement statement = connection.createStatement(ResultSet.TYPE_SCROLL_SENSITIVE,
					 ResultSet.CONCUR_UPDATABLE)) {

			ResultSet resultSet = statement.executeQuery(
					"SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 " +
					"FROM Quotes.RDF WHERE RIC IN ('SAB.L', 'BG.L', 'REX.L', 'WG.L')");

			// A MetaFluent result set is live. absolute(0) refreshes it to the current values
			// and positions it before the first row.
			while (true) {
				resultSet.absolute(0);
				while (resultSet.next()) {
					System.out.printf("%-8s %-24s %10.4f %10.4f %10.4f%n",
							resultSet.getString("RIC"), resultSet.getString("DSPLY_NAME"),
							resultSet.getDouble("BID"), resultSet.getDouble("ASK"), resultSet.getDouble("TRDPRC_1"));
				}
				System.out.println();
				Thread.sleep(1000);   // redisplay once a second
			}
		}
	}
}
```

To run it against a session server on the same machine:

```
java -cp bin/JDBCTestApp.jar com.metafluent.examples.firstquery.FirstQuery
```

When the session server runs on a different machine, give its hostname as the argument (`... FirstQuery myhost`). The four rows are redisplayed once a second as the market moves; press `Ctrl+C` to stop.

For the full command-line query tool, see [Worked Example: JDBCTestApp](Example-JDBCTestApp.md).

---

## Live results

Notice the `Statement` is created `TYPE_SCROLL_SENSITIVE`. That is what makes the difference: the result set stays open and its rows reflect the live content, so re-reading it shows the current market rather than a one-time snapshot. To re-read, call `absolute(0)`: it refreshes the rows to their current values and positions the cursor before the first row, and you then step through with `next()` as usual. A query is a standing view over the content, not a point-in-time fetch. Close the `ResultSet` (or the `Connection`) when you no longer need the data.

---

## Data state: rows and statements

Live data can be degraded for a while: a source disconnects, or part of the cluster is recovering. The driver tells you in two ways, one for each row and one for the statement as a whole.

### Each row's state

Every row carries its own state in two columns, `_STATE` and `_STATE_TEXT`. Select them by name to see them; `SELECT *` returns the table's columns without them:

```java
ResultSet resultSet = statement.executeQuery(
		"SELECT RIC, BID, ASK, _STATE, _STATE_TEXT " +
		"FROM Quotes.RDF WHERE RIC IN ('SAB.L', 'BG.L')");
```

`_STATE` is a byte code and `_STATE_TEXT` says why, for display:

| `_STATE` | State | Meaning |
|---|---|---|
| 1 | OK | The row is current. |
| 2 | STALE | The row's values may not be current. It stays readable, and it becomes OK again by itself when its data recovers. |
| 3 | INVALID | The row's item can never be served, for example a key the source does not know. Correct the query rather than waiting for the row. |
| 4 | DENIED | You are not entitled to the row's content. This can change while the query runs, as entitlements change. |
| 5 | CLOSED | The source closed the row's item. It may become available again later. |

These are the same states a JMS stream carries; see [Dynamic Data Conventions](Dynamic-Data-Conventions.md#stream-state).

A row goes STALE when its source marks the item stale (a row joined to a stale item goes STALE with it), or when the driver cannot refresh the rows from their server. Each recovers by itself: the source sends the item again, or the next refresh succeeds. Act on the code and display the text; the text is for people, not for parsing.

```java
resultSet.absolute(0);
while (resultSet.next()) {
	boolean stale = resultSet.getByte("_STATE") == 2;
	System.out.printf("%-8s %10.4f %10.4f %s%n", resultSet.getString("RIC"),
			resultSet.getDouble("BID"), resultSet.getDouble("ASK"),
			stale ? "STALE: " + resultSet.getString("_STATE_TEXT") : "");
}
```

Row state is the signal for everyday interruptions. A query that does not select `_STATE` reads the same rows and values; it just does not see their state.

### The statement's state

Elastic MDS also reports on the statement as a whole. You do not need to select anything to see it:

- **Degraded.** `ResultSet.getWarnings()` returns a `SQLWarning`, "The statement's result is degraded: ...", with the reason. The rows stay readable. The warning goes away by itself when the statement is OK again, and `clearWarnings()` hides it until a different warning arises.
- **Failed.** The next use of the result set throws a `SQLException`, "The statement failed after it was acknowledged: ...", with the reason. A failed statement does not recover: close the result set and run the query again if you still need the data.

A good pattern is to check `getWarnings()` each time you refresh the result set, and to treat a `SQLException` from the result set as the end of that query.

### Connection interruptions

The driver recovers from a lost connection by itself, for as long as the session lasts; your `ResultSet` keeps working and needs no action from your application.

- While the driver reconnects, rows keep updating, and neither the rows nor the statement change state because of the interruption alone. If a row's data cannot be refreshed in the meantime, that row goes STALE and recovers as described above.
- If Elastic MDS has to start your statement again after the interruption, the rows you already have stay readable, marked STALE, until the restarted statement's rows replace them.
- The driver writes an INFO line to your application's log when it loses the connection and when it reconnects. If an interruption lasts longer than the session's retry limit allows, it also logs one WARNING, `MF-RFR-007` (see the [Log Message Reference](Log-Message-Reference.md)).

When the session itself ends, its statements end with it: a statement already answered fails (the next use of the result set throws a `SQLException`, "The statement failed after it was acknowledged: The session ended: ..."), and an `executeQuery` still waiting for its answer throws.

---

## The SQL you can use

Elastic MDS accepts **a subset of SQL-92** - a read-only query surface (`SELECT` and `CREATE VIEW ... SELECT`; there is no `INSERT`/`UPDATE`/`DELETE` of content). What is supported:

- **Select list:** columns, `*`, `table.*`, column aliases with `AS`, arithmetic (`+ - * / %`), library functions such as `MFMath.AVG(BID, ASK) AS MID`, and a scalar sub-select of one column, alone or as an operand, such as `BID - (SELECT BID FROM Quotes.RDF WHERE RIC = 'VOD.L') AS VS_VOD`. A scalar sub-select that selects one aggregate may refer to the outer row through one equality, such as `(SELECT COUNT(*) FROM Trades.RDF AS t WHERE t.RIC = q.RIC) AS TRADES`.
- **`WHERE`:** `= <> < <= > >=`, `[NOT] LIKE`, `[NOT] BETWEEN`, `IS [NOT] NULL`, `[NOT] IN` over a list or a sub-select, `[NOT] EXISTS (SELECT ...)`, and a comparison with a scalar sub-select, combined with `AND`, `OR`, `NOT` and parentheses.
- **Joins:** `JOIN` / `INNER JOIN` or `LEFT JOIN`, each with an `ON` of one equality. The equality is on the joined table's key, and either the other table's key, a column of it (a foreign key), or an expression over the `FROM` table's columns, such as a library function. A foreign key matches the joined table's key by its text: a number matches when it is written with the same digits, so `8` matches the key `8` and `8.0` does not. Several joins may chain through earlier joined tables.
- **Derived tables:** `FROM (SELECT ...) AS d`, and a grouped derived table joined on its grouping column, such as `LEFT JOIN (SELECT RIC, COUNT(*) AS TRADES FROM Trades.RDF GROUP BY RIC) AS t ON t.RIC = q.RIC`: each row reads its group's values. Several can be joined to one table, which gives aggregates from several tables per key without the row multiplication a join before `GROUP BY` would cause. `LEFT JOIN` keeps a row with no group; `JOIN` keeps only the rows with one.
- **Grouping:** `GROUP BY` columns or expressions, the aggregates `SUM`, `AVG`, `COUNT` (including `COUNT(DISTINCT ...)`), `MIN` and `MAX`, `HAVING`, and `SELECT DISTINCT`.
- **Ordering and limits:** `ORDER BY` columns, expressions, aliases or select-list positions, `ASC` or `DESC`; `LIMIT`, `OFFSET`, `TOP` and `FETCH FIRST`. `Statement.setMaxRows` also limits the rows; the smaller limit applies.
- **`UNION` and `UNION ALL`** of `SELECT`s from tables, with an `ORDER BY` or `LIMIT` over the whole union.
- **`CREATE VIEW ... SELECT`** (see below).

Not supported: `CASE`, `CAST`, the `||` operator, `INTERSECT` / `EXCEPT`, `RIGHT` and `FULL OUTER JOIN`, `CROSS` and `NATURAL` joins, comma joins and `JOIN ... USING`. A statement that uses something outside the subset fails: `executeQuery` throws an `SQLException` whose message names what is not supported.

The row key is available as the column `_KEY` (often aliased, e.g. `SELECT _KEY AS RIC, ...`). Table names are schema-qualified (`Quotes.RDF`) - the same content model described in [Dynamic Data Conventions](Dynamic-Data-Conventions.md).

---

## Browsing the tables

Tools that browse a database through `DatabaseMetaData` see the tables you can query. `getCatalogs`, `getSchemas`, `getTableTypes` and `getTables` return every table, narrowed by the names and patterns you pass, as the JDBC documentation describes.

`getColumns` returns the columns of tables with a fixed set of columns, such as tables read from a relational database or from files. A market-data table such as `Quotes.RDF` is listed by `getTables`, and `getColumns` returns no columns for it: its fields are those of the [content model](Dynamic-Data-Conventions.md).

```java
DatabaseMetaData metadata = connection.getMetaData();
try (ResultSet columns = metadata.getColumns(null, null, "%", null)) {
	while (columns.next()) {
		System.out.printf("%s.%s %-16s %s%n", columns.getString("TABLE_SCHEM"), columns.getString("TABLE_NAME"),
				columns.getString("COLUMN_NAME"), columns.getString("TYPE_NAME"));
	}
}
```

The other `DatabaseMetaData` calls that return a result set, such as `getPrimaryKeys` and `getIndexInfo`, throw `SQLFeatureNotSupportedException`.

---

## Derived content with views

A `SELECT` can compute new columns - the `MFMath.AVG(BID, ASK) AS MID` above is a derived mid-price the source never sent. `CREATE VIEW` turns such a query into a named, reusable table that others can subscribe to or query:

```sql
CREATE VIEW Quotes.MyBook AS
  SELECT RIC, DSPLY_NAME, BID, ASK, MFMath.AVG(BID, ASK) AS MID
  FROM Quotes.RDF WHERE RIC IN ('SAB.L', 'BG.L', 'REX.L', 'WG.L')
```

The view is live like any other content: its rows update as the underlying market moves. Defining derived content once, centrally, is often better than every application computing it for itself.

---

## Where to go next

- [JMS Application Development](Develop-JMS.md) - subscribe to the same content and stream it.
- [Worked Example: JDBCTestApp](Example-JDBCTestApp.md) - the full command-line query tool, section by section.
- [Developing with TLS](Develop-TLS.md) - connect over TLS.
- [Geospatial Functions (MFGeo)](Develop-Geospatial.md) - distance, region and nearest-point functions in SQL, including as join keys.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Architecture: Basics](Architecture-Basics.md) - the model behind the API.
- [Glossary](Glossary.md) - definitions of the terms used here.
