# JavaScript Application Development

Elastic MDS content is also reachable from **JavaScript and TypeScript**: connect, run a `SELECT`, and read the result through a promise and an async-iterable - no callbacks, no MetaFluent protocol internals. It is the same content the [JDBC Application Development](Develop-JDBC.md) guide queries with SQL over a `ResultSet`; this guide queries it with the same SQL, over `connect()`/`.query()`/`for await`.

**Audience:** JavaScript and TypeScript developers. No prior MetaFluent knowledge assumed.

One difference from a typical database client is worth stating up front: the result here is **live** by construction. There is no separate refresh call to make or `ResultSet` to re-read - the result object is itself an async iterable, and `for await` is how you consume live updates as they arrive.

---

## The SDK

The client and two example applications ship in **js-metafluent-refresh-sdk**:

```
git clone --depth 1 -b dev git@github.com:MetaFluent/js-metafluent-refresh-sdk.git
```

This SDK is pre-1.0 and does not yet follow the milestone/stable-branch tagging convention the JDBC and JMS SDKs do - there is no `stable` branch with real content yet and no `MILESTONE-v*`/`RELEASE-v*` tags. `dev` is the branch to clone until that changes.

The SDK contains:

- `lib/metafluent-refresh-api.tgz` - the client library (`@metafluent/refresh-api`), a single, self-contained npm package with no dependencies of its own to install.
- `bin/smart-refresh-demo.js` / `examples/src/smart-refresh-demo.ts` - a command-line example application, prebuilt and its readable source.
- `examples/web/` - a browser example application's readable source.

The command-line example is ready to run as shipped - no `npm install` needed. The browser example ships as source only; see "Running the browser example" below.

For a browser-based client-side app, start from `examples/web/` and [Worked Example: Smart Refresh Web Demo](Example-Smart-Refresh-Web-Demo.md) instead of the command-line snippet below.

To build against the library:

```
npm install /path/to/lib/metafluent-refresh-api.tgz
```

To run the prebuilt example against a deployment, give it the session server host and a query:

```
node bin/smart-refresh-demo.js --host mf-session --port 8900 \
     "SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')"
```

`mf-session` is the conventional name for the session server your application connects to. Map it to your deployment's session host - the same way the [Quick Start](Quick-Start.md) maps `mf-api-gateway` - or use the `host:port` your operator gives you. (On the single-host Quick Start the session server runs on your own machine, so `localhost:8900` works there.) The tool prints the initial snapshot, then a line per live update as the market moves; press `Ctrl+C` to stop.

---

## A first query

`connect()` logs in; `.query()` runs a statement and resolves once the server has acked it. The result carries the current snapshot in `.rows`, and is itself an async iterable - each iteration is a live update, consumed with `for await`.

See this pattern in action in [Worked Example: smart-refresh-demo](Example-smart-refresh-demo.md) (command line) or [Worked Example: Smart Refresh Web Demo](Example-Smart-Refresh-Web-Demo.md) (browser).

---

## Live results

There is no `absolute(0)`-style refresh call and no cursor to step through: the `for await` loop itself is the live mechanism. Each time through the loop, `update.rows` is the full current snapshot in sort order - always ready to render as-is - and `update.changed` names just the `{ row, column }` positions that changed that tick, enough to update just what changed without redrawing everything. Call `result.close()` when you no longer need the data, and `connection.close()` when you're done with the connection entirely.

---

## Scope and transports

This client's SQL support covers single-table, no-join queries - the same subset described in [The SQL you can use](Develop-JDBC.md#the-sql-you-can-use), minus joins.

`connect()` defaults to a plain Node TCP socket (`NodeSocketTransportFactory`, from `js-metafluent-common`, re-exported so you never need to import that package directly). To run in a browser instead, pass a `BrowserWebSocketTransportFactory` as `transportFactory`:

```javascript
const { connect, BrowserWebSocketTransportFactory } = require("@metafluent/refresh-api");

const connection = await connect({
  host: "mf-session",
  port: 8900,
  userName: "guest",
  transportFactory: new BrowserWebSocketTransportFactory(),
});
```

---

## Running the browser example

The SDK's `examples/web/` is exactly this pattern, built out into a small live-updating table with a refresh-rate control:

```
cd examples/web
npm install
npm run dev
```

Open the printed URL with a query in it:

```
http://localhost:4173/?sql=SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')
```

Your session server needs to allow the browser's origin (`http://localhost:4173` by default) - see your deployment's `METAFLUENT_WEB_ORIGINS` setting. For a section-by-section walkthrough of `examples/web/src/main.ts` - connecting over WebSocket, rendering the live table, and the refresh-rate control - see [Worked Example: Smart Refresh Web Demo](Example-Smart-Refresh-Web-Demo.md).

---

## Where to go next

- [JDBC Application Development](Develop-JDBC.md) - query the same content with Java and JDBC.
- [Worked Example: Smart Refresh Web Demo](Example-Smart-Refresh-Web-Demo.md) - the browser example, section by section - start here if you're building a web app.
- [Worked Example: smart-refresh-demo](Example-smart-refresh-demo.md) - the command-line query tool, section by section.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Glossary](Glossary.md) - definitions of the terms used here.
