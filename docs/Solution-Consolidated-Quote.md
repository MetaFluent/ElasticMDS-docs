# Solutions Cookbook: One Consolidated Quote Across Feeds

**Audience:** developers and analysts reading quotes from more than one feed.
**Prerequisites:** a deployment with two or more quote feeds, and a client from one of the developer guides.

---

## The problem

A desk takes quotes from two feeds. Each names its instruments its own way and its fields its own way: on the LSEG feed an instrument is a RIC and the quote is `BID` and `ASK`; on the Bloomberg feed it is a ticker and the quote is `PX_BID` and `PX_ASK`. Every application that wants to see both has so far carried the code that reads both, renames the fields and tags each quote with where it came from.

---

## The solution

One statement reads both feeds: a `SELECT` per feed, each converting that feed's columns to a common shape, combined with `UNION ALL`.

```sql
SELECT RIC AS SYMBOL, 'RDF' AS SOURCE, BID, ASK
  FROM Quotes.RDF WHERE RIC IN ('VOD.L', 'BG.L')
UNION ALL
SELECT TICKER AS SYMBOL, 'BPIPE' AS SOURCE, PX_BID AS BID, PX_ASK AS ASK
  FROM Quotes.BPIPE WHERE TICKER IN ('SAB LN Equity', 'WG LN Equity')
```

| SYMBOL | SOURCE | BID | ASK |
|---|---|---|---|
| VOD.L | RDF | 162.65 | 162.70 |
| BG.L | RDF | 1312.5 | 1313.0 |
| SAB LN Equity | BPIPE | 2240.0 | 2241.0 |
| WG LN Equity | BPIPE | 1484.5 | 1485.0 |

How the branches combine:

- **Columns align by position.** Every branch selects the same number of columns, of the same types, in the same order, and the result takes its column names from the first branch. Renaming a feed's column (`PX_BID AS BID`) is how a branch fits the common shape; each branch's `WHERE` applies to its own table.
- **A constant names the source.** `'RDF' AS SOURCE` is a column like any other, with that value in every row of its branch, so each row says which feed it came from. The key column gets a name of your own, `SYMBOL` here, since each feed names its symbols its own way.
- **The result is live.** A row updates as its feed does, and a row's data state is its own: if one feed goes stale, that branch's rows show it while the others keep updating.

---

## Choices

**A query or a view?** As a query, the result is yours: it runs under your session, so the rows you see are the rows you are entitled to on each feed. That is the right form for feeds under row-level access control, which real-time feeds normally are, and it is the form shown above.

A view makes a result shared content that every consumer reads by name. A view cannot be shared when the rows it combines come from a feed with row-level access control, and Elastic MDS refuses to define one, naming the feed, so for entitled feeds the consolidated quote stays a query that each application runs. Views are described under [Derived content with views](Develop-JDBC.md#derived-content-with-views).

---

## Using it

- **JDBC:** run the statement with `executeQuery` and read the live `ResultSet`, as in [JDBC Application Development](Develop-JDBC.md).
- **JavaScript / TypeScript:** pass the statement to `.query()` and iterate the result, as in [JS Application Development](Develop-JS.md).
- **JMS:** a JMS application subscribes to tables and views by name ([JMS Application Development](Develop-JMS.md)); the consolidated quote reaches it as a view where the feeds allow one.

---

## Where to go next

- [Solutions Cookbook](Solutions-Cookbook.md) - the other solutions, and the content model behind them.
- [The SQL you can use](Develop-JDBC.md#the-sql-you-can-use) - everything a statement may contain.
