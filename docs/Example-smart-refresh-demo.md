# Worked Example: smart-refresh-demo

`smart-refresh-demo`, in the SDK, is a small command-line query tool: give it a host and a SQL statement and it connects, runs the query, prints the initial snapshot, then prints each live update as the market moves. For the smallest possible program, start with [A first query](Develop-JS.md#a-first-query) - this example is that same pattern with command-line argument handling added.

This page walks through the file section by section. The code below is the actual example, with the argument-parsing details elided as `// ...`; the complete file is in the SDK at `examples/src/smart-refresh-demo.ts`, and `bin/smart-refresh-demo.js` contains it prebuilt.

**Audience:** JavaScript and TypeScript developers who have read [JavaScript Application Development](Develop-JS.md).

---

## Running it

```
node bin/smart-refresh-demo.js --host localhost --port 8900 \
     "SELECT RIC, DSPLY_NAME, BID, ASK, TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L')"
```

The query is the last argument; put it in double quotes so the single quotes around values reach the server unchanged. Press `Ctrl+C` to stop.

---

## 1. Command-line options

`parseArgs()` reads the options and treats everything else as the SQL statement:

| Option | Default | Meaning |
|---|---|---|
| `--host` | `localhost` | Session server host. |
| `--port` | `8900` | Session server port. |
| `--user` | empty | User name for the connection. |

```javascript
function parseArgs(argv) {
  const args = { host: "localhost", port: 8900, userName: "" };
  const sqlParts = [];
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--host":
        args.host = argv[++i];
        break;
      // ...
      default:
        sqlParts.push(argv[i]);
    }
  }
  if (sqlParts.length === 0) {
    throw new Error("Usage: smart-refresh-demo [--host h] [--port p] [--user u] <SQL query>");
  }
  return { ...args, sql: sqlParts.join(" ") };
}
```

---

## 2. Connect and run the query

`connect()` logs in; `.query()` runs the statement and resolves once the server has acked it and assigned a shard (see [A first query](Develop-JS.md#a-first-query)):

```javascript
const connection = await connect({ host: args.host, port: args.port, userName: args.userName });
const result = await connection.query(args.sql);
```

---

## 3. The initial snapshot

The result carries its column metadata and the current snapshot the moment `.query()` resolves - nothing further to fetch for the first screenful:

```javascript
log(`Columns: ${result.columns.map((c) => c.name).join(", ")}`);
console.table(result.rows);
```

---

## 4. Streaming live updates, then shutting down

The result is itself an async iterable (see [Live results](Develop-JS.md#live-results)): each time through the loop is one live update, with the full current snapshot in `update.rows` and the changed cell positions in `update.changed`. This example stops after 15 ticks; a long-running tool would simply keep iterating until told to stop.

```javascript
let ticks = 0;
for await (const update of result) {
  log(`Tick ${++ticks}: ${update.changed.length} cell(s) changed`);
  console.table(update.rows);
  if (ticks >= 15) {
    break;
  }
}

result.close();
connection.close();
```

---

## Where to go next

- [JavaScript Application Development](Develop-JS.md) - the SDK, the live result model, and transports.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
- [Glossary](Glossary.md) - definitions of the terms used here.
