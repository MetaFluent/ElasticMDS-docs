# Worked Example: Smart Refresh Web Demo

The Smart Refresh web demo, in the SDK, is a small client-side web app: it reads a SQL query out
of its own URL, connects from the browser, and renders a live table that flashes cells as the
market moves, with a control for how fast. For the smallest possible program, start with [A first
query](Develop-JS.md#a-first-query) - this example is that same `connect()`/`.query()`/`for await`
pattern with a browser transport, a URL-driven query, and an actual UI built around it.

This page walks through the app section by section. The code below is the actual example, with
some argument-handling and DOM-plumbing details elided as `// ...`; the complete files are in the
SDK at `web/src/main.ts`, `web/src/table.ts`, and `web/src/rate.ts`, and `web/index.html` contains
it prebuilt.

**Audience:** developers building a client-side web app on Elastic MDS, who have read
[JavaScript Application Development](Develop-JS.md).

---

## Running it

```
cd web
npm run serve
```

Then open, with a query in the URL - there is no default, so this is required:

```
http://localhost:4173/?sql=SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')
```

Add `&rate=<hz>` to start at a specific refresh rate (default 4/sec); the on-page slider changes
it live afterward.

---

## 1. Reading the query and refresh rate from the URL

Both come from the page's own query string, so a running demo's URL is itself the thing to
bookmark or send someone - there is nothing else to configure to reproduce what you're looking at:

```javascript
const params = new URLSearchParams(window.location.search);
const sql = params.get("sql");
// ...
if (!sql) {
  setStatus("no query", "error");
  queryEl.textContent = "Add a query to the URL, e.g. ?sql=SELECT RIC, BID, ASK FROM Quotes.RDF WHERE RIC IN ('VOD.L')";
  return;
}
queryEl.textContent = sql;

const initialRateHz = Number(params.get("rate")) || DEFAULT_RATE_HZ;
```

---

## 2. Connect, over WebSocket

The one difference from a Node application: pass `BrowserWebSocketTransportFactory` as
`transportFactory`. Browsers have no raw TCP sockets, so `connect()`'s default
`NodeSocketTransportFactory` cannot run here - this is the only connection-level change a browser
app needs to make:

```javascript
let connection;
try {
  connection = await connect({
    host: import.meta.env.VITE_SESSION_HOST,
    port: Number(import.meta.env.VITE_SESSION_PORT),
    userName: "guest",
    applicationName: "smart-refresh-demo",
    transportFactory: new BrowserWebSocketTransportFactory(),
  });
} catch (err) {
  setStatus("connection failed", "error");
  console.error(err);
  return;
}
```

A connection failure here is usually either the session server being unreachable, or the
browser's origin not being allowed by the server's `METAFLUENT_WEB_ORIGINS` setting - a WebSocket
handshake a server rejects on origin looks like an ordinary connection failure from the client
side, with no more specific error to distinguish it.

---

## 3. Run the query and render the initial snapshot

The same pattern as [A first query](Develop-JS.md#a-first-query): `.query()` resolves once the
server has acked the statement and the result carries its column metadata and current snapshot
immediately - nothing further to fetch for the first screenful.

```javascript
let result;
try {
  result = await connection.query(sql);
} catch (err) {
  setStatus("query failed", "error");
  console.error(err);
  connection.close();
  return;
}

table.setColumns(result.columns);
table.render(result.rows);
result.refreshRate = initialRateHz;
```

`ResultTable.setColumns()`/`.render()` (`web/src/table.ts`) build an ordinary HTML `<table>` by
hand - deliberately not a grid library. A grid library earns its weight on sorting, filtering, and
virtualizing large datasets; this demo has none of those needs, and a handful of cells flashing on
change is simplest as direct DOM updates:

```javascript
setColumns(columns) {
  this.columns = columns;
  this.container.innerHTML = "";
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column.name;
    headerRow.appendChild(th);
  }
  // ...
}
```

---

## 4. Streaming live updates - flashing changed cells

The result is itself an async iterable. Each tick, `update.rows` is the full current snapshot and
`update.changed` names the `{ row, column }` positions that changed - enough to flash exactly the
right cells without redrawing everything from scratch:

```javascript
for await (const update of result) {
  table.flashChanges(update.rows, update.changed);
}
```

`flashChanges()` re-renders the (small) table, then restarts a CSS flash animation on each changed
cell - removing and re-adding the class alone would not restart an already-running animation, so it
forces a reflow in between:

```javascript
flashChanges(rows, changed) {
  this.render(rows);
  if (!this.flashEnabled) {
    return;
  }
  const bodyRows = tbody.querySelectorAll("tr");
  for (const { row, column } of changed) {
    const tr = bodyRows[row];
    if (!tr) {
      continue;
    }
    const columnIndex = this.columns.findIndex((c) => c.name === column);
    const td = tr.children[columnIndex];
    if (td) {
      flash(td);
    }
  }
}

function flash(cell) {
  cell.classList.remove("flash");
  void cell.offsetWidth; // force a reflow so the browser "forgets" the animation was running
  cell.classList.add("flash");
}
```

Row identity and re-sorting are already handled upstream - `LiveResult` diffs by each row's own
identity, not array position, so a result that re-sorts with no value actually changing reports no
changes at all. `flashChanges()` only ever needs to know which `(row, column)` positions in the
*current* array to flash.

---

## 5. The refresh-rate control

A single slider (0-100) maps log-scaled onto `MIN_RATE_HZ`..`MAX_RATE_HZ` (`web/src/rate.ts`), so
one control usefully covers both a slow trickle and a fast "Beast Mode" ceiling:

```javascript
export function hzToSlider(hz) {
  const clamped = Math.min(MAX_RATE_HZ, Math.max(MIN_RATE_HZ, hz));
  const t = (Math.log(clamped) - Math.log(MIN_RATE_HZ)) / (Math.log(MAX_RATE_HZ) - Math.log(MIN_RATE_HZ));
  return Math.round(t * 100);
}

export function sliderToHz(value) {
  const t = value / 100;
  return Math.exp(Math.log(MIN_RATE_HZ) + t * (Math.log(MAX_RATE_HZ) - Math.log(MIN_RATE_HZ)));
}
```

Moving the slider sets `result.refreshRate` directly - the live result's own refresh rate is just
a property to assign, not a separate call to restart anything:

```javascript
rateInput.addEventListener("input", () => {
  const hz = sliderToHz(Number(rateInput.value));
  result.refreshRate = hz;
  rateLabel.textContent = formatRate(hz);
});
```

---

## 6. Releasing the connection

A browser app does not get a `Ctrl+C` to catch - the page itself closing is the equivalent moment,
so cleanup happens on `beforeunload` instead:

```javascript
window.addEventListener("beforeunload", () => {
  result.close();
  connection.close();
});
```

---

## 7. The one browser-specific plumbing detail: a dependency-free `Buffer` shim

This codebase's wire codec uses Node's `Buffer` throughout, which browsers don't have natively.
`web/src/main.ts` imports a small polyfill first, before anything else, specifically so it exists
by the time a real `connect()`/`.query()` call needs it:

```javascript
import "./buffer-polyfill"; // must be the first import - see that file's comment
```

This is not a general-purpose `Buffer` reimplementation - it's a short, from-scratch shim covering
only the handful of methods the codec actually calls (reading/writing fixed-width integers,
encoding strings, base64), built on nothing but the browser's own `Uint8Array`/`DataView`/
`TextEncoder`/`TextDecoder`. It is deliberately not a third-party package: this product's
customers include institutions that do not allow downloading third-party content at all, even for
development, so every dependency in this SDK is either something you already have (Node, a
browser) or something MetaFluent controls directly - nothing resolved from a public package
registry. You will not need to touch this file for an ordinary web app; it exists so `Buffer`
simply works.

---

## Where to go next

- [JavaScript Application Development](Develop-JS.md) - the SDK, the live result model, and transports.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Glossary](Glossary.md) - definitions of the terms used here.
