# Function Libraries

A statement can compute values the source never sent: a mid-price, a conflation condition, a value read from another table. The functions that compute them come from **function libraries**, named sets of functions such as `MFMath` and `MFUtil`. The same functions are available to every client API, because they are part of the statement rather than of the API that sends it.

**Audience:** developers writing statements that compute derived values, whichever client API they use.

---

## Calling a function

A function is called by its library's name and its own name, with its arguments in parentheses:

```sql
SELECT RIC, BID, ASK, MFMath.AVG(BID, ASK) AS MID FROM Quotes.RDF
```

A function can appear in the select list, where its value becomes a column of the result, and in the `WHERE` clause, where it decides which rows or updates are delivered. `MFUtil.UPDATED(MFUtil.TIMER(250, 'MILLISECONDS'))` in a `WHERE` clause delivers at most one update per 250 ms, as [JMS Application Development](Develop-JMS.md) shows.

A deployment publishes each of its libraries as a table of type `FUNCTION_TABLE` in the `_Functions_` schema. Tools that browse tables list them with the other tables, as [Browsing the tables](Develop-JDBC.md#browsing-the-tables) describes for JDBC.

---

## Listing a library's functions

The functions a library offers are listed by the gateway's [REST API](REST-API.md), in the `functions` collection of the `library-adapter` API. Each function has:

| Field | Meaning |
|-------|---------|
| `name` | The function's name, as a statement calls it. |
| `returnType` | The type of the value it returns, such as `DECIMAL` or `BOOLEAN`. |
| `description` | What it computes. |
| `generatingRows` | `true` when it generates rows from its input's whole result, instead of computing a value per row. |
| `readingRowState` | `true` when it reads the state of the row it is part of. |

Select the library by its name. Every container that hosts the library returns the same list, so the response has one list per container. This lists the name and description of each `MFMath` function:

```
curl -s "http://mf-api-gateway:9090/api/library-adapter/v1/library=MFMath/functions/*/name,description"
```

The `*` selects every function in the collection, and the fields after it are the ones returned. Put a function's name in its place to read that function, such as `.../library=MFMath/functions/AVG`, or a test on a field to filter the collection, such as `.../functions/returnType=DECIMAL/name` for the names of the functions that return a `DECIMAL`.

---

## Where to go next

- [REST API](REST-API.md) - addressing instances, collections and fields through the gateway.
- [JDBC Application Development](Develop-JDBC.md) - the SQL you can use, and derived content with views.
- [JMS Application Development](Develop-JMS.md) - selectors and conflation.
