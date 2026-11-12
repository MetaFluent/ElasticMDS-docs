# JavaScript Application Development

Elastic MDS content is also reachable from **JavaScript and TypeScript**: connect, run a `SELECT`, and read the result through a promise and an async-iterable - no callbacks, no MetaFluent protocol internals. It is the same content the [JDBC Application Development](Develop-JDBC.md) guide queries with SQL over a `ResultSet`; this guide queries it with the same SQL, over `connect()`/`.query()`/`for await`.

**Audience:** JavaScript and TypeScript developers. No prior MetaFluent knowledge assumed.

One difference from a typical database client is worth stating up front: the result here is **live** by construction. There is no separate refresh call to make or `ResultSet` to re-read - the result object is itself an async iterable, and `for await` is how you consume live updates as they arrive.

---

## The SDK

The client and an example application ship in **js-refresh-sdk**:

```
git clone --depth 1 -b dev git@github.com:MetaFluent/js-refresh-sdk.git
```

This SDK is pre-1.0 and does not yet follow the milestone/stable-branch tagging convention the JDBC and JMS SDKs do - there is no `stable` branch with real content yet and no `MILESTONE-v*`/`RELEASE-v*` tags. `dev` is the branch to clone until that changes.

The SDK contains:

- `lib/metafluent-smart-refresh.tgz` - the client library (`@metafluent/smart-refresh`), a single, self-contained npm package with no dependencies of its own to install.
- `bin/smart-refresh-demo.js` - the example application, prebuilt and ready to run with plain `node` - no `npm install` needed.
- `examples/src/smart-refresh-demo.ts` - the same example's readable source.

To build against the library:

```
npm install /path/to/lib/metafluent-smart-refresh.tgz
```

To run the prebuilt example against a deployment, give it the session server host and a query:

```
node bin/smart-refresh-demo.js --host localhost --port 8900 \
     "SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')"
```

This assumes the session server runs on the same machine; when it runs elsewhere, pass that machine's hostname as `--host`. The tool prints the initial snapshot, then a line per live update as the market moves; press `Ctrl+C` to stop.

---

## A first query

`connect()` logs in; `.query()` runs a statement and resolves once the server has acked it. The result carries the current snapshot in `.rows`, and is itself an async iterable - each iteration is a live update:

```javascript
const { connect } = require("@metafluent/smart-refresh");

const connection = await connect({ host: "localhost", port: 8900, userName: "guest" });
const result = await connection.query(
  "SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')"
);

console.log(result.columns.map((c) => c.name));
console.table(result.rows);

for await (const update of result) {
  console.log(`${update.changed.length} cell(s) changed`);
  console.table(update.rows);
}

result.close();
connection.close();
```

For the full command-line tool this snippet is drawn from, see [Worked Example: smart-refresh-demo](Example-smart-refresh-demo.md).

---

## Live results

There is no `absolute(0)`-style refresh call and no cursor to step through: the `for await` loop itself is the live mechanism. Each time through the loop, `update.rows` is the full current snapshot in sort order - always ready to render as-is - and `update.changed` names just the `{ row, column }` positions that changed that tick, enough to flash the right cells without redrawing everything. Call `result.close()` when you no longer need the data, and `connection.close()` when you're done with the connection entirely.

---

## Scope and transports

This client covers the same single-table, no-join query scope the rest of the JS port does today - the SQL subset is the one described in [The SQL you can use](Develop-JDBC.md#the-sql-you-can-use), minus joins.

`connect()` defaults to a plain Node TCP socket (`NodeSocketTransportFactory`, from `mf-js-common`, re-exported so you never need to import that package directly). To run in a browser instead, pass a `BrowserWebSocketTransportFactory` as `transportFactory`:

```javascript
const { connect, BrowserWebSocketTransportFactory } = require("@metafluent/smart-refresh");

const connection = await connect({
  host: "localhost",
  port: 8900,
  userName: "guest",
  transportFactory: new BrowserWebSocketTransportFactory(),
});
```

---

## Where to go next

- [JDBC Application Development](Develop-JDBC.md) - query the same content with Java and JDBC.
- [Worked Example: smart-refresh-demo](Example-smart-refresh-demo.md) - the command-line query tool, section by section.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Glossary](Glossary.md) - definitions of the terms used here.
