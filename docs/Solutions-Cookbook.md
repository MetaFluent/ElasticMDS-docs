# Solutions Cookbook

Market-data applications have always carried code that is not really about the application: code that normalises two feeds into one shape, computes a mid-price, maintains a curve from a set of instruments, or keeps a shared book current for a team. Elastic MDS does these things from a statement. The statement is declared once, runs centrally, is live, and serves every consumer the same rows.

This cookbook shows solutions to problems a desk would recognise, each built that way. Where a problem has more than one good answer, the page says what the choice turns on.

**Audience:** developers and analysts who know market data and want results without writing feed-handling code.
**Prerequisites:** a running deployment and one of the client guides under [Developing Applications](Develop-JDBC.md).

---

## Content is tables

The statements here read naturally once the content model is in view.

- A **schema** is a kind of record: `Quotes`, `Trades`, `Chains`.
- A **table** within a schema is a feed: `Quotes.RDF` holds the quote records the RDF feed delivers, `Quotes.BPIPE` those from BPIPE. A deployment with several feeds has several tables in the same schema.
- A **row** is one instrument, identified by its key, which is the feed's own symbol (a RIC on an LSEG feed, a ticker on a Bloomberg feed). Its **columns** are the feed's fields.
- A **view** is a table you define with a statement. Once defined it is content like any other, read by name by any client.

Every row is live: its values move as the feed moves, and its state says whether the values are current. The statements that follow select, convert and combine such rows, and the results they produce are live in the same way.

---

## How each solution is laid out

- **The problem**, as a desk would state it.
- **The solution**: the statement, and the rows it produces.
- **Choices**, where the problem has more than one good answer.
- **Using it**: how each kind of client reads the result, pointing at the developer guides.

---

## Solutions

- [One consolidated quote across feeds](Solution-Consolidated-Quote.md) - the same instruments from two feeds, in one result with common columns and a column that names the source.

---

## Where to go next

- [JDBC Application Development](Develop-JDBC.md) - the SQL you can use, and derived content with views.
- [JS Application Development](Develop-JS.md) - the same statements from JavaScript and TypeScript.
- [JMS Application Development](Develop-JMS.md) - subscribing to tables and views by name.
