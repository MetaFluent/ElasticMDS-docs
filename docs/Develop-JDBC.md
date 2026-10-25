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
- `examples/src/...` - the source for the example applications, including `JDBCTestApp`.
- `bin/JDBCTestApp.jar` - the example prebuilt, so you can run it without building.

The driver registers itself, so `DriverManager` finds it automatically. Connection URLs take the form `jdbc:metafluent://<host>:<port>`, where the host and port are those of the session server (default port `8900`). If your environment needs the driver named explicitly, add `-Djdbc.drivers=com.metafluent.jdbc.rtc.DriverImpl`.

To run the prebuilt example against a deployment, give it the session server host and a query:

```
java -jar bin/JDBCTestApp.jar -host localhost -head 20 \
     "SELECT RIC,DSPLY_NAME,BID,BIDSIZE,ASK,ASKSIZE,TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L','REX.L','WG.L')"
```

This assumes the session server runs on the same machine. When it runs on a different machine, replace `localhost` with that machine's hostname. `-port` sets a session port other than `8900`, and `-head` limits the rows shown. The table refreshes once a second as the content changes; press `Ctrl+C` to stop. Put the query in double quotes, so the single quotes around values reach the server unchanged.

---

## A first query

`JDBCTestApp` (in the SDK) is a complete, console-based query client. Its structure is the standard JDBC pattern: get a `Connection`, create a `Statement`, execute a `SELECT`, and read the `ResultSet`.

```java
import java.sql.*;
import java.util.Properties;

public class FirstQuery {
    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        props.setProperty("com.metafluent.jdbc.application-name", "FirstQuery");
        props.setProperty("com.metafluent.jdbc.application-version", "1.0.0");
        props.setProperty("com.metafluent.jdbc.user", "guest");

        // The MetaFluent JDBC provider connects through the session server (port 8900).
        String url = "jdbc:metafluent://localhost:8900";

        try (Connection conn = DriverManager.getConnection(url, props);
             Statement stmt = conn.createStatement(ResultSet.TYPE_SCROLL_SENSITIVE,
                                                   ResultSet.CONCUR_UPDATABLE)) {

            ResultSet rs = stmt.executeQuery(
                "SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 " +
                "FROM Quotes.RDF WHERE RIC IN ('SAB.L', 'BG.L', 'REX.L', 'WG.L')");

            // A MetaFluent result set is live. Re-scroll it to see current values.
            while (true) {
                rs.beforeFirst();
                while (rs.next()) {
                    System.out.printf("%-8s %-24s %10.4f %10.4f %10.4f%n",
                        rs.getString("RIC"), rs.getString("DSPLY_NAME"),
                        rs.getDouble("BID"), rs.getDouble("ASK"), rs.getDouble("TRDPRC_1"));
                }
                Thread.sleep(1000);   // redisplay once a second
            }
        }
    }
}
```

The example connects to a session server on the same machine. When the session server runs on a different machine, replace `localhost` in the URL with that machine's hostname.

---

## Live results

Notice the `Statement` is created `TYPE_SCROLL_SENSITIVE`. That is what makes the difference: the result set stays open and its rows reflect the live content, so re-reading it (`beforeFirst()` then `next()`, or `absolute(...)`) shows the current market rather than a one-time snapshot. A query is a standing view over the content, not a point-in-time fetch. Close the `ResultSet` (or the `Connection`) when you no longer need the data.

---

## The SQL you can use

Elastic MDS accepts **a subset of SQL-92** - a read-only query surface (`SELECT` and `CREATE VIEW ... SELECT`; there is no `INSERT`/`UPDATE`/`DELETE` of content). What is supported:

- **Projections:** columns, `*`, `table.*`, column aliases with `AS`, arithmetic (`+ - * /`), aggregates (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`), and library functions such as `MFMath.AVG(BID, ASK) AS MID`.
- **`WHERE`:** `= <> < <= > >=`, `LIKE` / `NOT LIKE`, `IN` / `NOT IN`, combined with `AND` / `OR`.
- **Joins:** a single equi-join between primary keys (`a.key = b.key`).
- **`GROUP BY`, `ORDER BY`.**
- **`CREATE VIEW ... SELECT`** (see below).

Some standard SQL is **not** supported, and a few clauses are accepted by the parser but do nothing - so avoid relying on them: `HAVING`, `DISTINCT`, `BETWEEN`, `IS [NOT] NULL`, `CASE`, `CAST`, subqueries, outer joins, joins of three or more tables, and `UNION` / `INTERSECT` / `EXCEPT`. The exact, exhaustive grammar will be covered in the SQL reference.

The row key is available as the column `_KEY` (often aliased, e.g. `SELECT _KEY AS RIC, ...`). Table names are schema-qualified (`Quotes.RDF`) - the same content model described in [Dynamic Data Conventions](Dynamic-Data-Conventions.md).

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
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Architecture: Basics](Architecture-Basics.md) - the model behind the API.
- [Glossary](Glossary.md) - definitions of the terms used here.
