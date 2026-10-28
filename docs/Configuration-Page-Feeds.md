# Configuration: Page Feeds

Some sources deliver each item as a terminal page - a block of ANSI text with cursor-positioning codes - in a single field. A page feed tells MetaFluent to keep each item's page and publish it as one text field per screen row, so subscribers read and query the rows like any other columns. This page shows how to mark a feed as a page feed in the ETA adapter and in the MAMA adapter.

**Audience:** Operator, Architect.

---

## What subscribers see

By default the page arrives in the field `STORY_TEXT`. For a page feed, MetaFluent publishes it as 25 text fields, `ROW80_1` to `ROW80_25`, each exactly 80 characters wide. The page's table has the key (for example `RIC`) and the row fields as its columns; the page data field and the feed's other fields are not offered as columns.

- An **image** publishes every row.
- An **update** publishes only the rows it changed.
- When a new image arrives for an item, MetaFluent blanks the page first and then applies the image (`resetOnImage` is `true`). Set `resetOnImage` to `false` to apply each image to the page as it stands, which is how MetaFluent ES (V5) behaved - useful if your site relied on that.
- An image that carries no page data marks the item stale with the message `MetaFluent: No page data field STORY_TEXT in image` (showing the field name you configured).
- An update without page data changes nothing.

---

## The pageMetadata settings

Both adapters use the same `pageMetadata` object. Every setting is optional, and an empty object `{}` takes all the defaults.

| Setting | Meaning | Default |
|---|---|---|
| `pageDataField` | The field carrying the page data. | `STORY_TEXT` |
| `pageRowFieldFormat` | The names of the row fields; `%d` stands for the row number, starting at 1. | `ROW80_%d` |
| `rows`, `columns` | The page size. | 25 rows x 80 columns |
| `resetOnImage` | `true` blanks the page before each image is applied; `false` applies the image to the page as it stands. | `true` |

---

## ETA adapter

In `feeds.json`, an array of feed entries, mark a feed as a page feed with `"pageData": true` and add `pageMetadata` (required when `pageData` is `true`; use `{}` for all defaults):

```json
{
  "feedName": "PAGES",
  "keyName": "RIC",
  "pageData": true,
  "pageMetadata": {
    "pageDataField": "STORY_TEXT",
    "pageRowFieldFormat": "ROW80_%d",
    "rows": 25,
    "columns": 80,
    "resetOnImage": true
  }
}
```

In the service's dictionary, the page data field must be a BUFFER field (`STORY_TEXT` is, in the standard RDM dictionary) and the row fields must be string fields.

The feed entry is where a feed is marked as a page feed. A service the adapter discovers at run time without a feed entry is an ordinary feed.

---

## MAMA adapter

In the bridge specification (`mama-spec.json`: bridges, then transports, then feeds), a feed entry with a `pageMetadata` object is a page feed - no separate flag is needed:

```json
{
  "feedName": "PAGES",
  "keyName": "RIC",
  "pageMetadata": {
    "pageDataField": "STORY_TEXT",
    "pageRowFieldFormat": "ROW80_%d",
    "rows": 25,
    "columns": 80,
    "resetOnImage": true
  }
}
```

The page data field can be an OPAQUE or a STRING field in the feed's dictionary, and the row fields must be string fields.

---

## Recognise and fix a configuration mistake

If the page data field or a row field is missing from the dictionary or has the wrong type, or the page size is invalid, that feed's table does not start. Its state is `INITIALIZATION_ERROR`, visible in the adapter's operational state, and the adapter logs a warning that names the field:

```
Page configuration error for feed PAGES: page row field ROW80_1 is not in the dictionary
```

To fix it, add the named field to the dictionary with the right type, or change `pageMetadata` to match the fields your dictionary has, then restart the adapter. Your other feeds keep running while you correct it.

---

## Where to go next

- [Deployment: Basics - MAMA feeds](Deployment-Basics.md#mama-feeds) - install OpenMAMA and the bridge specification.
- [Deployment: Without Docker - MAMA feeds](Deployment-Without-Docker.md#mama-feeds) - the same setup for an installation package.
- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - read the adapter's operational state.
